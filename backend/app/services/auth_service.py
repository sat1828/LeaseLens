"""
Authentication and quota management service.
BUG-07 FIX: Atomic quota check+increment — no race condition possible.
BUG-08: Email verification support (graceful if SendGrid not configured).
BUG-09: Password reset support.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, text
from fastapi import HTTPException, status
from app.models.user import User, PlanType
from app.core.security import hash_password, verify_password, create_access_token
from app.core.config import settings
from app.core.logging import log


async def register_user(
    db: AsyncSession,
    email: str,
    password: str,
    full_name: Optional[str] = None,
) -> User:
    result = await db.execute(select(User).where(User.email == email.lower().strip()))
    if result.scalar_one_or_none():
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered.")

    user = User(
        email=email.lower().strip(),
        hashed_password=hash_password(password),
        full_name=full_name,
        plan=PlanType.FREE,
        monthly_analysis_count=0,
        total_analysis_count=0,
        monthly_reset_date=datetime.now(timezone.utc),
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    await db.flush()
    log.info("auth.register", user_id=str(user.id), email=email)
    return user


async def login_user(db: AsyncSession, email: str, password: str) -> tuple[User, str]:
    result = await db.execute(select(User).where(User.email == email.lower().strip()))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account has been deactivated.")

    await db.execute(
        update(User).where(User.id == user.id).values(
            last_login_at=datetime.now(timezone.utc)
        )
    )
    token = create_access_token(str(user.id))
    log.info("auth.login", user_id=str(user.id))
    return user, token


async def check_and_consume_quota(db: AsyncSession, user: User) -> None:
    """
    BUG-07 FIX: Atomically checks quota AND increments in ONE database statement.
    Race-condition safe: two simultaneous requests for the same user — exactly one wins.
    Returns normally if quota consumed. Raises HTTP 429 if quota exceeded.
    """
    now = datetime.now(timezone.utc)
    limit = (
        settings.FREE_ANALYSES_PER_MONTH
        if user.plan == PlanType.FREE
        else settings.PRO_ANALYSES_PER_MONTH
    )

    # Single atomic statement combining check + reset + increment.
    # The WHERE clause ensures the UPDATE only fires if quota is not exceeded.
    # If it fires → row returned → quota consumed.
    # If it doesn't fire → no row returned → quota exceeded.
    result = await db.execute(
        text("""
            UPDATE users
            SET
                monthly_analysis_count = CASE
                    WHEN EXTRACT(YEAR  FROM monthly_reset_date AT TIME ZONE 'UTC') !=
                         EXTRACT(YEAR  FROM :now::timestamptz)
                      OR EXTRACT(MONTH FROM monthly_reset_date AT TIME ZONE 'UTC') !=
                         EXTRACT(MONTH FROM :now::timestamptz)
                    THEN 1
                    ELSE monthly_analysis_count + 1
                END,
                monthly_reset_date = CASE
                    WHEN EXTRACT(YEAR  FROM monthly_reset_date AT TIME ZONE 'UTC') !=
                         EXTRACT(YEAR  FROM :now::timestamptz)
                      OR EXTRACT(MONTH FROM monthly_reset_date AT TIME ZONE 'UTC') !=
                         EXTRACT(MONTH FROM :now::timestamptz)
                    THEN :now::timestamptz
                    ELSE monthly_reset_date
                END,
                total_analysis_count = total_analysis_count + 1,
                updated_at = :now::timestamptz
            WHERE
                id = :user_id
                AND (
                    -- New month → always allow (counter resets to 1)
                    EXTRACT(YEAR  FROM monthly_reset_date AT TIME ZONE 'UTC') !=
                    EXTRACT(YEAR  FROM :now::timestamptz)
                 OR EXTRACT(MONTH FROM monthly_reset_date AT TIME ZONE 'UTC') !=
                    EXTRACT(MONTH FROM :now::timestamptz)
                    -- Same month → only if under limit
                 OR monthly_analysis_count < :limit
                )
            RETURNING monthly_analysis_count
        """),
        {"user_id": str(user.id), "now": now.isoformat(), "limit": limit},
    )

    row = result.fetchone()

    if row is None:
        # UPDATE matched zero rows = quota exceeded (atomically verified)
        log.info("quota.exceeded", user_id=str(user.id), plan=str(user.plan), limit=limit)
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            f"Monthly limit reached ({limit} analysis on your {user.plan} plan). "
            f"Upgrade to Pro for unlimited analyses at /pricing",
            headers={"Retry-After": "2592000"},  # 30 days
        )

    log.info("quota.consumed", user_id=str(user.id), new_count=row[0], limit=limit)


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def send_verification_email(email: str, user_id: str) -> None:
    """BUG-08: Send verification email. Gracefully skipped if SendGrid not configured."""
    if not settings.SENDGRID_API_KEY:
        log.warning("email.verification.skipped", reason="SENDGRID_API_KEY not set in .env")
        return

    token = create_access_token(f"verify:{user_id}", expires_delta=timedelta(hours=24))
    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"

    try:
        import sendgrid  # type: ignore[import]
        from sendgrid.helpers.mail import Mail  # type: ignore[import]
        message = Mail(
            from_email=settings.FROM_EMAIL,
            to_emails=email,
            subject="Verify your LeaseLens account",
            html_content=f"""
            <div style="font-family:sans-serif;max-width:480px;margin:auto;padding:24px">
              <h2 style="color:#1E3A5F">Verify your email to start protecting yourself</h2>
              <p style="color:#475569;font-size:14px">
                Click below to verify your email. This link expires in 24 hours.
              </p>
              <a href="{verify_url}"
                 style="display:inline-block;background:#1E3A5F;color:white;
                        padding:12px 24px;border-radius:10px;text-decoration:none;
                        font-weight:600;font-size:14px;margin:16px 0">
                Verify Email →
              </a>
              <p style="color:#94A3B8;font-size:12px">
                If you didn't create a LeaseLens account, ignore this email.
              </p>
            </div>
            """,
        )
        sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
        sg.send(message)
        log.info("email.verification.sent", email=email)
    except ImportError:
        log.warning("email.verification.skipped", reason="sendgrid package not installed")
    except Exception as e:
        log.error("email.verification.failed", email=email, error=str(e))
        # Don't raise — email failure must not block registration


async def send_password_reset_email(email: str, reset_url: str) -> None:
    """BUG-09: Send password reset email."""
    if not settings.SENDGRID_API_KEY:
        log.warning("email.reset.skipped", reason="SENDGRID_API_KEY not set")
        return

    try:
        import sendgrid  # type: ignore[import]
        from sendgrid.helpers.mail import Mail  # type: ignore[import]
        message = Mail(
            from_email=settings.FROM_EMAIL,
            to_emails=email,
            subject="Reset your LeaseLens password",
            html_content=f"""
            <div style="font-family:sans-serif;max-width:480px;margin:auto;padding:24px">
              <h2 style="color:#1E3A5F">Reset your password</h2>
              <p style="color:#475569;font-size:14px">
                Click below to reset your password. This link expires in 1 hour.
              </p>
              <a href="{reset_url}"
                 style="display:inline-block;background:#1E3A5F;color:white;
                        padding:12px 24px;border-radius:10px;text-decoration:none;
                        font-weight:600;font-size:14px;margin:16px 0">
                Reset Password →
              </a>
              <p style="color:#94A3B8;font-size:12px">
                If you didn't request this, ignore this email. Your password won't change.
              </p>
            </div>
            """,
        )
        sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
        sg.send(message)
        log.info("email.reset.sent", email=email)
    except ImportError:
        log.warning("email.reset.skipped", reason="sendgrid package not installed")
    except Exception as e:
        log.error("email.reset.failed", email=email, error=str(e))
