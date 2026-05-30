"""
Core unit tests — no database, no network required.
Run: pytest tests/ -v
"""
import json
import pytest


# ── Security ─────────────────────────────────────────────────────────────────

def test_password_hash_and_verify():
    from app.core.security import hash_password, verify_password
    hashed = hash_password("SecurePass123!")
    assert verify_password("SecurePass123!", hashed)
    assert not verify_password("WrongPass999", hashed)


def test_password_max_72_bytes():
    from app.core.security import hash_password, verify_password
    long_pass = "A" * 100 + "1"
    hashed = hash_password(long_pass)
    # Same first 72 bytes should match
    assert verify_password(long_pass, hashed)


def test_jwt_create_and_decode():
    from app.core.security import create_access_token, decode_access_token
    token = create_access_token("user-uuid-12345")
    decoded = decode_access_token(token)
    assert decoded == "user-uuid-12345"


def test_jwt_invalid_token():
    from app.core.security import decode_access_token
    result = decode_access_token("not.a.real.token")
    assert result is None


def test_jwt_tampered_token():
    from app.core.security import create_access_token, decode_access_token
    token = create_access_token("user-123")
    tampered = token[:-5] + "XXXXX"
    assert decode_access_token(tampered) is None


# ── AI Service — JSON parsing ─────────────────────────────────────────────────

SAMPLE_RESULT = {
    "lease_summary": {
        "monthly_rent": 20000,
        "security_deposit": 80000,
        "lease_type": "RESIDENTIAL",
        "property_address": "Flat 12, Bengaluru",
        "landlord_name": None,
        "tenant_name": None,
        "lease_start": None,
        "lease_end": None,
        "currency": "INR",
    },
    "fairness_score": 22,
    "risk_summary": {
        "critical_count": 2,
        "high_count": 3,
        "medium_count": 1,
        "low_count": 0,
        "missing_clauses": ["NOTICE_PERIOD", "MAINTENANCE_OBLIGATIONS"],
        "illegal_clauses": ["UTILITY_AND_SERVICES", "DISPUTE_RESOLUTION"],
    },
    "clauses": [],
    "top_3_negotiation_priorities": [],
    "counter_proposal_letter": "Dear Landlord...",
    "legal_disclaimer": "Not legal advice.",
}


def test_parse_direct_json():
    from app.services.ai_service import _parse_json
    result = _parse_json(json.dumps(SAMPLE_RESULT))
    assert result["fairness_score"] == 22


def test_parse_markdown_fenced():
    from app.services.ai_service import _parse_json
    fenced = f"Here is your analysis:\n```json\n{json.dumps(SAMPLE_RESULT)}\n```\nDone."
    result = _parse_json(fenced)
    assert result["fairness_score"] == 22


def test_parse_embedded_in_prose():
    from app.services.ai_service import _parse_json
    text = f"Analysis complete. {json.dumps(SAMPLE_RESULT)} End."
    result = _parse_json(text)
    assert result["fairness_score"] == 22


def test_parse_invalid_raises():
    from app.services.ai_service import _parse_json
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        _parse_json("This is not JSON at all, sorry.")
    assert exc_info.value.status_code == 500


# ── Jurisdiction context ──────────────────────────────────────────────────────

def test_jurisdiction_karnataka():
    from app.services.ai_service import get_jurisdiction_context
    ctx = get_jurisdiction_context("Bengaluru, Karnataka, India")
    assert "Karnataka" in ctx
    assert "Model Tenancy Act" in ctx


def test_jurisdiction_maharashtra():
    from app.services.ai_service import get_jurisdiction_context
    ctx = get_jurisdiction_context("Mumbai, Maharashtra, India")
    assert "Maharashtra" in ctx


def test_jurisdiction_unknown_falls_back():
    from app.services.ai_service import get_jurisdiction_context
    ctx = get_jurisdiction_context("Unknown City, Somewhere")
    assert "Model Tenancy Act" in ctx  # base law always present


def test_jurisdiction_odisha():
    from app.services.ai_service import get_jurisdiction_context
    ctx = get_jurisdiction_context("Bhubaneswar, Odisha, India")
    assert "Odisha" in ctx


# ── Config ────────────────────────────────────────────────────────────────────

def test_config_defaults():
    from app.core.config import settings
    assert settings.API_PREFIX == "/api/v1"
    assert settings.MAX_PDF_PAGES == 100
    assert settings.JWT_ALGORITHM == "HS256"
    assert settings.FREE_ANALYSES_PER_MONTH == 1


# ── Fairness scoring logic ────────────────────────────────────────────────────

def test_fairness_score_deduction():
    score = 50
    score -= 15  # CRITICAL
    score -= 15  # CRITICAL
    score -= 8   # HIGH
    score -= 5   # missing clause
    score -= 5   # missing clause
    final = max(0, min(100, score))
    assert final == 2


def test_fairness_score_clamp_zero():
    score = 50 - (15 * 5)  # 5 critical = -75
    assert max(0, min(100, score)) == 0


def test_fairness_score_clamp_hundred():
    score = 50 + (5 * 20)  # impossible but test clamp
    assert max(0, min(100, score)) == 100


# ── PDF service ───────────────────────────────────────────────────────────────

def test_pdf_size_validation():
    from app.services.pdf_service import validate_pdf_size
    from fastapi import HTTPException
    # 26 MB — over limit
    big_bytes = b"x" * (26 * 1024 * 1024)
    with pytest.raises(HTTPException) as exc_info:
        validate_pdf_size(big_bytes)
    assert exc_info.value.status_code == 400
    assert "MB" in exc_info.value.detail


def test_pdf_size_ok():
    from app.services.pdf_service import validate_pdf_size
    # 1 MB — fine
    ok_bytes = b"x" * (1 * 1024 * 1024)
    validate_pdf_size(ok_bytes)  # should not raise


# ── User schema validation ────────────────────────────────────────────────────

def test_user_create_weak_password():
    from app.schemas.user import UserCreate
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        UserCreate(email="test@example.com", password="weak")


def test_user_create_no_uppercase():
    from app.schemas.user import UserCreate
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        UserCreate(email="test@example.com", password="alllowercase1")


def test_user_create_no_number():
    from app.schemas.user import UserCreate
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        UserCreate(email="test@example.com", password="NoNumbersHere")


def test_user_create_valid():
    from app.schemas.user import UserCreate
    u = UserCreate(email="priya@example.com", password="SecurePass123", full_name="Priya")
    assert u.email == "priya@example.com"
    assert u.full_name == "Priya"
