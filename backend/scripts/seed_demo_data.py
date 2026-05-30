#!/usr/bin/env python3
"""
MISSING-03: Seed demo data for local development.
Creates a demo user + one pre-computed analysis so the UI can be tested
without needing to run a real Claude API call.

Run once after: alembic upgrade head
  python scripts/seed_demo_data.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime, timezone, timedelta
from app.db.session import AsyncSessionLocal, engine
from app.models.user import User, PlanType
from app.models.analysis import Analysis, LeaseType
from app.core.security import hash_password
from app.core.logging import setup_logging, log


DEMO_CLAUSES = [
    {
        "clause_id": "C001",
        "clause_type": "SECURITY_DEPOSIT",
        "verbatim_excerpt": "Security Deposit: Rs 1,12,000 (Four months)",
        "risk_level": "CRITICAL",
        "legal_status": "ILLEGAL",
        "plain_english": "The deposit is double what the law allows. You can legally refuse to pay more than ₹56,000 (2 months).",
        "legal_citation": "Model Tenancy Act 2021, Section 11(2)",
        "negotiation_suggestion": "Security deposit revised to ₹56,000 (2 months' rent) per MTA 2021 Section 11(2).",
        "fairness_weight": 1,
        "is_actionable": True,
    },
    {
        "clause_id": "C002",
        "clause_type": "UTILITY_AND_SERVICES",
        "verbatim_excerpt": "Landlord reserves right to disconnect electricity and water supply for non-payment.",
        "risk_level": "CRITICAL",
        "legal_status": "ILLEGAL",
        "plain_english": "This is completely illegal. Your landlord cannot cut your electricity or water for any reason. This clause is void and unenforceable.",
        "legal_citation": "Model Tenancy Act 2021, Section 23",
        "negotiation_suggestion": "Delete this clause entirely. It violates MTA 2021 §23 and is unenforceable.",
        "fairness_weight": 1,
        "is_actionable": True,
    },
    {
        "clause_id": "C003",
        "clause_type": "DISPUTE_RESOLUTION",
        "verbatim_excerpt": "All disputes through private arbitration only. Tenant waives all rights to approach Rent Tribunal.",
        "risk_level": "CRITICAL",
        "legal_status": "ILLEGAL",
        "plain_english": "You cannot be forced to give up your right to the Rent Tribunal. This clause is void — you can always approach the Rent Authority regardless of what this says.",
        "legal_citation": "Model Tenancy Act 2021, Section 30",
        "negotiation_suggestion": "Replace with: 'Disputes shall be resolved per the dispute resolution hierarchy under MTA 2021: Rent Authority → Rent Court → Rent Tribunal.'",
        "fairness_weight": 1,
        "is_actionable": True,
    },
]

DEMO_LETTER = """Dear Mr./Ms. [Landlord Name],

Re: Counter-Proposal — Lease Agreement for Flat 12B, Prestige Towers, Whitefield, Bengaluru

I have reviewed the proposed lease agreement and write to request the following amendments before execution. Each request is grounded in applicable Indian tenancy law.

**1. Security Deposit — Clause 1 (ILLEGAL)**
The proposed deposit of ₹1,12,000 (4 months) violates Section 11(2) of the Model Tenancy Act 2021, which caps residential security deposits at 2 months' rent (₹56,000). I request the deposit be corrected to ₹56,000.

**2. Utility Disconnection — Clause 3 (ILLEGAL)**
Section 23 of the MTA 2021 explicitly prohibits landlords from disconnecting water, electricity, or any essential service under any circumstance. This clause is void ab initio and must be deleted.

**3. Dispute Resolution — Clause 7 (ILLEGAL)**
Section 30 of the MTA 2021 provides that a tenant's right to approach the Rent Authority, Rent Court, and Rent Tribunal cannot be contractually waived. This clause is unenforceable. Please replace with standard MTA dispute resolution language.

I am keen to proceed with the tenancy and look forward to your response on these points.

Yours sincerely,
[Your Name]
[Date]

---
*This counter-proposal was drafted with the assistance of LeaseLens AI, citing the Model Tenancy Act 2021.*
*This is not legal advice. For CRITICAL findings, consult an advocate registered with the Bar Council of India.*"""


async def seed() -> None:
    setup_logging()

    async with AsyncSessionLocal() as db:
        # Check if demo user already exists
        from sqlalchemy import select
        existing = await db.execute(
            select(User).where(User.email == "demo@leaselens.in")
        )
        if existing.scalar_one_or_none():
            print("Demo user already exists. Skipping seed.")
            return

        user = User(
            email="demo@leaselens.in",
            hashed_password=hash_password("DemoPass123"),
            full_name="Demo Tenant",
            plan=PlanType.FREE,
            is_verified=True,
            is_active=True,
            monthly_analysis_count=1,
            total_analysis_count=1,
            monthly_reset_date=datetime.now(timezone.utc),
        )
        db.add(user)
        await db.flush()

        analysis = Analysis(
            user_id=user.id,
            jurisdiction="Bengaluru, Karnataka, India",
            original_filename="demo_bengaluru_lease.txt",
            lease_type=LeaseType.RESIDENTIAL,
            pages_analyzed=1,
            fairness_score=22,
            lease_summary={
                "property_address": "Flat 12B, Prestige Towers, Whitefield, Bengaluru 560066",
                "landlord_name": "Rajesh Kumar",
                "tenant_name": "Ananya Singh",
                "lease_start": "2024-03-01",
                "lease_end": "2025-01-31",
                "monthly_rent": 28000,
                "currency": "INR",
                "security_deposit": 112000,
                "lease_type": "RESIDENTIAL",
            },
            risk_summary={
                "critical_count": 3,
                "high_count": 3,
                "medium_count": 1,
                "low_count": 0,
                "missing_clauses": ["NOTICE_PERIOD", "MAINTENANCE_OBLIGATIONS", "REGISTRATION_COMPLIANCE"],
                "illegal_clauses": ["UTILITY_AND_SERVICES", "DISPUTE_RESOLUTION"],
            },
            clauses=DEMO_CLAUSES,
            top_3_priorities=[
                {
                    "priority": 1,
                    "clause_id": "C001",
                    "reason": "Security deposit is ₹1,12,000 — double the legal cap of ₹56,000",
                    "suggested_response_letter_snippet": "The deposit must be reduced to ₹56,000 per MTA 2021 §11(2).",
                },
                {
                    "priority": 2,
                    "clause_id": "C002",
                    "reason": "Utility disconnection clause is explicitly illegal under MTA 2021 §23",
                    "suggested_response_letter_snippet": "Clause 3 must be deleted — utility disconnection by landlord is a criminal offence.",
                },
                {
                    "priority": 3,
                    "clause_id": "C003",
                    "reason": "Waiving Rent Tribunal rights is void under MTA 2021 §30",
                    "suggested_response_letter_snippet": "Replace arbitration-only clause with standard MTA dispute resolution hierarchy.",
                },
            ],
            counter_proposal_letter=DEMO_LETTER,
            processing_time_ms=18420,
            tokens_used=4250,
            model_used="claude-sonnet-4-20250514",
            purge_after=datetime.now(timezone.utc) + timedelta(days=90),
        )
        db.add(analysis)
        await db.commit()

        print(f"\n✅ Demo data seeded successfully!")
        print(f"   Email:    demo@leaselens.in")
        print(f"   Password: DemoPass123")
        print(f"   Analysis: {analysis.id} (score: 22/100 — Predatory)")
        print(f"\n   Open http://localhost:5173/login to try the demo.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
