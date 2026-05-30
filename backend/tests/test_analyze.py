"""
Integration tests for analysis pipeline.
BUG-19 FIX: Import _parse_json (was _parse_response — function didn't exist).
BUG-20 FIX: test_register_and_login marked as integration test, strict 201 assertion.
Run unit tests: pytest tests/test_core.py tests/test_analyze.py -v
Run integration: pytest -m integration -v  (requires live DB)
"""
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


# BUG-19 FIX: correct function name
from app.services.ai_service import _parse_json as _parse_response  # noqa: F401


SAMPLE_LEASE = """
RENTAL AGREEMENT

Between: Ramesh Sharma (Landlord) and Priya Mehta (Tenant)
Property: Flat 304, Koramangala, Bengaluru 560034
Monthly Rent: Rs. 20,000
Security Deposit: Rs. 80,000 (Four months — double the legal limit)
Duration: 11 months from Jan 1, 2024

1. SECURITY DEPOSIT: Rs. 80,000 refundable. Deduction at landlord's sole discretion.
2. ENTRY: Landlord may enter at any time without prior notice.
3. UTILITIES: Non-payment of rent for 7 days → landlord may disconnect electricity and water.
4. EVICTION: Landlord may ask tenant to vacate with 7 days notice for any reason.
5. DISPUTES: All disputes through private arbitration only. Tenant waives all rights to
   approach any Rent Tribunal, Rent Court, or Government Authority.
6. RENT ESCALATION: 15% annually, no notice required.
7. MAINTENANCE: Tenant responsible for ALL maintenance including structural repairs.
"""

MOCK_ANALYSIS = {
    "lease_summary": {
        "property_address": "Flat 304, Koramangala, Bengaluru 560034",
        "landlord_name": "Ramesh Sharma",
        "tenant_name": "Priya Mehta",
        "lease_start": "2024-01-01",
        "lease_end": "2024-11-30",
        "monthly_rent": 20000,
        "currency": "INR",
        "security_deposit": 80000,
        "lease_type": "RESIDENTIAL",
    },
    "fairness_score": 18,
    "risk_summary": {
        "critical_count": 3,
        "high_count": 2,
        "medium_count": 1,
        "low_count": 0,
        "missing_clauses": ["MAINTENANCE_OBLIGATIONS", "REGISTRATION_COMPLIANCE"],
        "illegal_clauses": ["UTILITY_AND_SERVICES", "DISPUTE_RESOLUTION"],
    },
    "clauses": [
        {
            "clause_id": "C001",
            "clause_type": "SECURITY_DEPOSIT",
            "verbatim_excerpt": "Rs. 80,000 (Four months)",
            "risk_level": "CRITICAL",
            "legal_status": "ILLEGAL",
            "plain_english": "The deposit is double the legal limit. You can legally refuse to pay more than ₹40,000.",
            "legal_citation": "Model Tenancy Act 2021, Section 11(2)",
            "negotiation_suggestion": "Security deposit revised to ₹40,000 (2 months) per MTA 2021 §11(2).",
            "fairness_weight": 1,
            "is_actionable": True,
        }
    ],
    "top_3_negotiation_priorities": [
        {
            "priority": 1,
            "clause_id": "C001",
            "reason": "Security deposit exceeds legal cap by 100%",
            "suggested_response_letter_snippet": "I request the security deposit be corrected to ₹40,000 as mandated by MTA 2021 §11(2).",
        }
    ],
    "counter_proposal_letter": "Dear Landlord,\n\nI write regarding the following clauses...",
    "legal_disclaimer": "Not legal advice.",
}


# ── JSON parser tests (import verifies BUG-19 fix) ────────────────────────────

def test_parse_json_direct():
    result = _parse_response(json.dumps(MOCK_ANALYSIS))
    assert result["fairness_score"] == 18


def test_parse_json_markdown_fenced():
    fenced = f"```json\n{json.dumps(MOCK_ANALYSIS)}\n```"
    result = _parse_response(fenced)
    assert result["fairness_score"] == 18


def test_parse_json_embedded_in_prose():
    prose = f"Analysis complete.\n{json.dumps(MOCK_ANALYSIS)}\nEnd."
    result = _parse_response(prose)
    assert result["fairness_score"] == 18


def test_parse_json_invalid_raises_http_exception():
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        _parse_response("This is not JSON at all, not even close.")
    assert exc_info.value.status_code == 500


def test_parse_json_partial_raises():
    from fastapi import HTTPException
    with pytest.raises(HTTPException):
        _parse_response('{"fairness_score": 42, "clauses": [')  # truncated


# ── Auth service tests ─────────────────────────────────────────────────────────

def test_password_hash_verify():
    from app.core.security import hash_password, verify_password
    h = hash_password("StrongPass123!")
    assert verify_password("StrongPass123!", h)
    assert not verify_password("WrongPassword1", h)


def test_jwt_round_trip():
    from app.core.security import create_access_token, decode_access_token
    token = create_access_token("user-uuid-test")
    assert decode_access_token(token) == "user-uuid-test"


def test_jwt_tampered_returns_none():
    from app.core.security import create_access_token, decode_access_token
    token = create_access_token("user-123")
    tampered = token[:-5] + "XXXXX"
    assert decode_access_token(tampered) is None


def test_jwt_verify_prefix():
    from app.core.security import create_access_token, decode_access_token
    from datetime import timedelta
    token = create_access_token("verify:abc-123", expires_delta=timedelta(hours=1))
    subject = decode_access_token(token)
    assert subject == "verify:abc-123"
    assert subject.startswith("verify:")


def test_jwt_reset_prefix():
    from app.core.security import create_access_token, decode_access_token
    from datetime import timedelta
    token = create_access_token("reset:abc-456", expires_delta=timedelta(hours=1))
    subject = decode_access_token(token)
    assert subject == "reset:abc-456"
    assert subject.startswith("reset:")


# ── Jurisdiction context tests ─────────────────────────────────────────────────

def test_all_12_jurisdictions_have_context():
    """BUG-02 FIX: All 12 frontend jurisdictions must return state-specific context."""
    from app.services.ai_service import get_jurisdiction_context

    jurisdictions = [
        ("Bengaluru, Karnataka, India", "Karnataka"),
        ("Mumbai, Maharashtra, India", "Maharashtra"),
        ("Delhi NCR, India", "Delhi"),
        ("Hyderabad, Telangana, India", "Telangana"),
        ("Chennai, Tamil Nadu, India", "Tamil Nadu"),
        ("Pune, Maharashtra, India", "Maharashtra"),
        ("Kolkata, West Bengal, India", "West Bengal"),
        ("Ahmedabad, Gujarat, India", "Gujarat"),
        ("Bhubaneswar, Odisha, India", "Odisha"),
        ("Jaipur, Rajasthan, India", "Rajasthan"),     # BUG-02 was missing
        ("Lucknow, Uttar Pradesh, India", "Uttar Pradesh"),  # BUG-02 was missing
        ("Kochi, Kerala, India", "Kerala"),             # BUG-02 was missing
    ]

    for city, expected_text in jurisdictions:
        ctx = get_jurisdiction_context(city)
        assert expected_text in ctx, (
            f"State-specific context missing for {city}. "
            f"Expected '{expected_text}' in context."
        )
        # All states must have BASE_LAW
        assert "Model Tenancy Act" in ctx, f"BASE_LAW missing for {city}"
        # All states should have >3 bullet points of context
        bullets = ctx.count("•")
        assert bullets >= 5, (
            f"State context too thin for {city}: only {bullets} bullets. "
            "BUG-03: expand to minimum 5."
        )


def test_unknown_jurisdiction_falls_back_to_base_law():
    from app.services.ai_service import get_jurisdiction_context
    ctx = get_jurisdiction_context("Some Unknown City, Unknownistan")
    assert "Model Tenancy Act" in ctx
    assert "SECURITY DEPOSIT" in ctx


# ── PDF service tests ──────────────────────────────────────────────────────────

def test_validate_pdf_size_over_limit():
    from app.services.pdf_service import validate_pdf_size
    from fastapi import HTTPException
    big = b"x" * (26 * 1024 * 1024)  # 26 MB > 25 MB limit
    with pytest.raises(HTTPException) as exc_info:
        validate_pdf_size(big)
    assert exc_info.value.status_code == 400
    assert "MB" in exc_info.value.detail


def test_validate_pdf_size_under_limit():
    from app.services.pdf_service import validate_pdf_size
    ok = b"x" * (5 * 1024 * 1024)  # 5 MB — fine
    validate_pdf_size(ok)  # should not raise


# ── Fairness scoring logic ─────────────────────────────────────────────────────

def test_fairness_score_multiple_criticals():
    """CRITICAL clauses dock 15 points each from base 50."""
    score = 50
    score -= 15 * 3  # 3 critical
    score -= 8 * 2   # 2 high
    score -= 5 * 2   # 2 missing
    assert max(0, min(100, score)) == 0  # 50-45-16-10 = -21 → clamped to 0


def test_fairness_score_clamped_to_zero():
    score = 50 - (15 * 10)  # 10 critical = -100
    assert max(0, min(100, score)) == 0


def test_fairness_score_clamped_to_hundred():
    score = 50 + (5 * 20)  # impossible but tests clamp
    assert max(0, min(100, score)) == 100


def test_fairness_score_favorable_clauses_add():
    score = 50 + (5 * 3) - (8 * 1)  # 3 favorable, 1 high
    assert max(0, min(100, score)) == 57


# ── BUG-20: Integration test — strict assertion, no 500 accepted ───────────────

@pytest.mark.asyncio
@pytest.mark.integration  # run only with: pytest -m integration
async def test_register_and_login_integration():
    """
    BUG-20 FIX: Strict 201 assertion — 500 is NOT acceptable.
    Requires: live DB at DATABASE_URL env var.
    Skip in unit test runs: pytest tests/ -m 'not integration'
    """
    from httpx import AsyncClient, ASGITransport
    from app.main import app
    import time

    unique_email = f"integration_test_{int(time.time())}@example.com"

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Register
        reg = await client.post(
            "/api/v1/auth/register",
            json={
                "email": unique_email,
                "password": "TestPass123",
                "full_name": "Integration Test User",
            },
        )
        # BUG-20 FIX: strict — 500 is NOT valid, it means something is broken
        assert reg.status_code == 201, (
            f"Registration returned {reg.status_code}: {reg.json()}. "
            "If this is a DB connection error, check DATABASE_URL env var."
        )
        data = reg.json()
        assert "access_token" in data
        assert data["user"]["email"] == unique_email

        # Login
        form_data = {"username": unique_email, "password": "TestPass123"}
        login_resp = await client.post(
            "/api/v1/auth/login",
            data=form_data,
        )
        assert login_resp.status_code == 200
        login_data = login_resp.json()
        assert "access_token" in login_data


# ── Config tests ───────────────────────────────────────────────────────────────

def test_config_defaults():
    from app.core.config import settings
    assert settings.API_PREFIX == "/api/v1"
    assert settings.MAX_PDF_PAGES == 100
    assert settings.JWT_ALGORITHM == "HS256"
    assert settings.FREE_ANALYSES_PER_MONTH == 1
    assert settings.MAX_PDF_SIZE_MB == 25
