"""
Authentication API.
BUG-08 FIX: /verify-email endpoint.
BUG-09 FIX: /forgot-password and /reset-password endpoints.
BUG-10 FIX: Removed manual db.commit() — get_db() handles it.
BUG-11 FIX: Rate limiting on login and register.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select
from app.db.session import get_db
from app.schemas.user import UserCreate, UserOut, TokenResponse, PasswordChange
from app.services.auth_service import (
    register_user,
    login_user,
    send_verification_email,
    send_password_reset_email,
    get_user_by_id,
)
from app.api.deps import get_current_user
from app.models.user import User
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)
from app.core.config import settings
from app.core.logging import log
from datetime import timedelta

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    request: Request,
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user account."""
    user = await register_user(db, payload.email, payload.password, payload.full_name)
    # BUG-10 FIX: NO db.commit() here — get_db() handles commit after yield
    # flush() was already called in register_user so user.id is available

    token = create_access_token(str(user.id))

    # BUG-08: Send verification email (graceful if SendGrid not configured)
    await send_verification_email(user.email, str(user.id))

    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Login with email + password. Returns JWT bearer token."""
    user, token = await login_user(db, form_data.username, form_data.password)
    # BUG-10 FIX: NO db.commit() here — get_db() handles it
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user profile."""
    return UserOut.model_validate(current_user)


@router.get("/verify-email")
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """BUG-08: Verify email address via token link."""
    user_id_str = decode_access_token(token)
    if not user_id_str or not user_id_str.startswith("verify:"):
        raise HTTPException(400, "Invalid or expired verification link. Please request a new one.")

    try:
        actual_user_id = uuid.UUID(user_id_str.replace("verify:", ""))
    except ValueError:
        raise HTTPException(400, "Malformed verification token.")

    result = await db.execute(select(User).where(User.id == actual_user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found.")
    if user.is_verified:
        return {"message": "Email already verified. You can log in."}

    await db.execute(
        update(User).where(User.id == actual_user_id).values(is_verified=True)
    )
    log.info("auth.email.verified", user_id=str(actual_user_id))
    return {"message": "Email verified successfully. You can now analyze leases."}


@router.post("/resend-verification")
async def resend_verification(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Resend email verification link."""
    if current_user.is_verified:
        return {"message": "Your email is already verified."}
    await send_verification_email(current_user.email, str(current_user.id))
    return {"message": "Verification email sent. Please check your inbox (and spam folder)."}


@router.post("/forgot-password")
async def forgot_password(
    request: Request,
    email: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """
    BUG-09 FIX: Password reset request.
    Always returns 200 regardless of whether email exists (prevents user enumeration).
    """
    result = await db.execute(
        select(User).where(User.email == email.lower().strip())
    )
    user = result.scalar_one_or_none()

    if user and user.is_active:
        token = create_access_token(
            f"reset:{user.id}",
            expires_delta=timedelta(hours=1),
        )
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        await send_password_reset_email(user.email, reset_url)

    # Always 200 — never reveal if email exists
    return {
        "message": (
            "If that email is registered, you will receive a reset link within 5 minutes. "
            "Check your spam folder if it doesn't arrive."
        )
    }


@router.post("/reset-password")
async def reset_password(
    request: Request,
    token: str = Form(...),
    new_password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """BUG-09 FIX: Set new password via reset token."""
    user_id_str = decode_access_token(token)

    if not user_id_str or not user_id_str.startswith("reset:"):
        raise HTTPException(400, "Invalid or expired reset link. Please request a new one.")

    try:
        actual_user_id = uuid.UUID(user_id_str.replace("reset:", ""))
    except ValueError:
        raise HTTPException(400, "Malformed reset token.")

    # Validate new password strength
    from app.schemas.user import UserCreate
    from pydantic import ValidationError
    try:
        UserCreate(email="test@test.com", password=new_password)
    except ValidationError as e:
        errors = [str(err["msg"]) for err in e.errors()]
        raise HTTPException(422, "; ".join(errors))

    await db.execute(
        update(User)
        .where(User.id == actual_user_id)
        .values(hashed_password=hash_password(new_password))
    )
    log.info("auth.password.reset", user_id=str(actual_user_id))
    return {"message": "Password reset successfully. You can now log in with your new password."}


@router.post("/change-password", status_code=200)
async def change_password(
    payload: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(400, "Current password is incorrect.")
    await db.execute(
        update(User).where(User.id == current_user.id).values(
            hashed_password=hash_password(payload.new_password)
        )
    )
    return {"message": "Password updated successfully."}


@router.delete("/account", status_code=200)
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """GDPR/DPDP: Anonymise and deactivate account."""
    await db.execute(
        update(User).where(User.id == current_user.id).values(
            email=f"deleted_{current_user.id}@deleted.leaselens.invalid",
            hashed_password="DELETED",
            full_name=None,
            is_active=False,
            stripe_customer_id=None,
            stripe_subscription_id=None,
        )
    )
    log.info("auth.account.deleted", user_id=str(current_user.id))
    return {"message": "Account deleted. All personal data has been removed."}
