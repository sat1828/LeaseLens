from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.stripe_service import (
    create_checkout_session,
    create_portal_session,
    handle_webhook,
)

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/checkout/{plan}")
async def checkout(
    plan: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create Stripe Checkout session. Returns redirect URL."""
    plan = plan.upper()
    if plan not in ("PRO", "TEAM"):
        raise HTTPException(400, "Invalid plan. Choose PRO or TEAM.")
    url = await create_checkout_session(current_user, plan)
    return {"checkout_url": url}


@router.post("/portal")
async def billing_portal(current_user: User = Depends(get_current_user)):
    """Redirect to Stripe Customer Portal to manage/cancel subscription."""
    url = await create_portal_session(current_user)
    return {"portal_url": url}


@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Stripe webhook endpoint. Verified by Stripe signature — no auth header."""
    return await handle_webhook(request, db)


@router.get("/plans")
async def get_plans():
    """Return plan details for the pricing page (no auth required)."""
    return {
        "plans": [
            {
                "id": "FREE",
                "name": "Free",
                "price_inr": 0,
                "analyses_per_month": 1,
                "features": [
                    "1 lease analysis per month",
                    "All 9 Indian jurisdictions",
                    "Full clause-by-clause breakdown",
                    "Fairness Score 0–100",
                    "Counter-proposal letter",
                ],
                "cta": "Get Started Free",
                "popular": False,
            },
            {
                "id": "PRO",
                "name": "Pro",
                "price_inr": 299,
                "analyses_per_month": "Unlimited",
                "features": [
                    "Unlimited analyses",
                    "All Indian jurisdictions",
                    "PDF letter download",
                    "Email letter directly",
                    "90-day analysis history",
                    "Priority support",
                ],
                "cta": "Start Pro — ₹299/mo",
                "popular": True,
            },
            {
                "id": "TEAM",
                "name": "Team",
                "price_inr": 1499,
                "analyses_per_month": "Unlimited + API",
                "features": [
                    "Everything in Pro",
                    "White-label letters",
                    "REST API access",
                    "Global jurisdictions",
                    "Bulk analysis",
                    "Dedicated account manager",
                    "NGO/legal aid discounts",
                ],
                "cta": "Start Team — ₹1,499/mo",
                "popular": False,
            },
        ]
    }
