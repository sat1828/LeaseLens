"""
Stripe payment service.
BUG-14 FIX: Stripe customer ID written to DB immediately at creation — not waiting for webhook.
BUG-15 FIX: invoice.payment_failed handled — downgrades after 3 failed attempts.
"""
import stripe
import uuid as _uuid
from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from app.core.config import settings
from app.models.user import User, PlanType
from app.core.logging import log

stripe.api_key = settings.STRIPE_SECRET_KEY

PLAN_PRICE_MAP: dict[str, str] = {
    "PRO": settings.STRIPE_PRO_PRICE_ID,
    "TEAM": settings.STRIPE_TEAM_PRICE_ID,
}


async def create_checkout_session(user: User, plan: str) -> str:
    """
    Create a Stripe Checkout session.
    BUG-14 FIX: Customer ID is saved to DB immediately if newly created —
    not waiting for the checkout.session.completed webhook (which may be delayed).
    """
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(503, "Payment system not configured. Contact support.")

    price_id = PLAN_PRICE_MAP.get(plan)
    if not price_id:
        raise HTTPException(400, f"Plan '{plan}' is not configured. Contact support.")

    customer_id = user.stripe_customer_id

    if not customer_id:
        # Create customer in Stripe
        customer = stripe.Customer.create(
            email=user.email,
            name=user.full_name or "",
            metadata={"user_id": str(user.id), "plan": plan},
        )
        customer_id = customer.id

        # BUG-14 FIX: Save immediately — do not wait for webhook
        from app.db.session import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            await session.execute(
                update(User)
                .where(User.id == user.id)
                .values(stripe_customer_id=customer_id)
            )
            await session.commit()
        log.info("stripe.customer.created", user_id=str(user.id), customer_id=customer_id)

    session = stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=["card"],
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        # BUG-36 FIX: redirect to /analyze not /dashboard (which doesn't exist)
        success_url=f"{settings.FRONTEND_URL}/analyze?upgraded=true&plan={plan}",
        cancel_url=f"{settings.FRONTEND_URL}/pricing?cancelled=1",
        client_reference_id=str(user.id),
        metadata={"user_id": str(user.id), "plan": plan},
        allow_promotion_codes=True,
    )

    log.info("stripe.checkout.created", user_id=str(user.id), plan=plan)
    return session.url


async def create_portal_session(user: User) -> str:
    """Stripe Customer Portal for subscription management/cancellation."""
    if not user.stripe_customer_id:
        raise HTTPException(404, "No active subscription found.")
    session = stripe.billing_portal.Session.create(
        customer=user.stripe_customer_id,
        return_url=f"{settings.FRONTEND_URL}/pricing",
    )
    return session.url


async def handle_webhook(request: Request, db: AsyncSession) -> dict:
    """
    Process Stripe webhook events. Verified by Stripe signature.
    BUG-15 FIX: handles invoice.payment_failed after 3 attempts.
    """
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(503, "Webhook not configured.")

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(400, "Invalid webhook signature.")
    except Exception as e:
        raise HTTPException(400, f"Webhook parse error: {str(e)}")

    event_type = event["type"]
    log.info("stripe.webhook.received", event_type=event_type)

    # ── checkout.session.completed → upgrade plan ─────────────────────────
    if event_type == "checkout.session.completed":
        session_obj = event["data"]["object"]
        user_id_str = session_obj.get("client_reference_id")
        plan = session_obj.get("metadata", {}).get("plan", "PRO")
        customer_id = session_obj.get("customer")
        subscription_id = session_obj.get("subscription")

        if user_id_str:
            try:
                uid = _uuid.UUID(user_id_str)
                await db.execute(
                    update(User).where(User.id == uid).values(
                        plan=PlanType[plan],
                        stripe_customer_id=customer_id,
                        stripe_subscription_id=subscription_id,
                    )
                )
                await db.commit()
                log.info("stripe.user.upgraded", user_id=user_id_str, plan=plan)
            except Exception as e:
                log.error("stripe.upgrade.failed", user_id=user_id_str, error=str(e))

    # ── subscription deleted/paused → downgrade to FREE ──────────────────
    elif event_type in ("customer.subscription.deleted", "customer.subscription.paused"):
        subscription = event["data"]["object"]
        customer_id = subscription.get("customer")
        if customer_id:
            await db.execute(
                update(User).where(User.stripe_customer_id == customer_id).values(
                    plan=PlanType.FREE,
                    stripe_subscription_id=None,
                )
            )
            await db.commit()
            log.info("stripe.user.downgraded", customer_id=customer_id)

    # ── BUG-15 FIX: invoice.payment_failed → downgrade after 3 failures ──
    elif event_type == "invoice.payment_failed":
        invoice = event["data"]["object"]
        customer_id = invoice.get("customer")
        attempt_count = invoice.get("attempt_count", 0)

        log.warning(
            "stripe.payment.failed",
            customer_id=customer_id,
            attempt=attempt_count,
        )

        if attempt_count >= 3 and customer_id:
            await db.execute(
                update(User)
                .where(User.stripe_customer_id == customer_id)
                .values(plan=PlanType.FREE, stripe_subscription_id=None)
            )
            await db.commit()
            log.warning(
                "stripe.payment.downgraded_after_failures",
                customer_id=customer_id,
                attempts=attempt_count,
            )

    return {"status": "processed", "event": event_type}
