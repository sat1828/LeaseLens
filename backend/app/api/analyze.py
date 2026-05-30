"""
Analysis API endpoints.
BUG-10 FIX: Removed manual db.commit() — get_db() handles it.
BUG-11 FIX: Rate limiting on POST /analyze/.
BUG-12 FIX: IP address and user agent captured in audit log.
BUG-13 FIX: History returns real COUNT total, not page length.
"""
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, Depends, BackgroundTasks, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, update, func

from app.db.session import get_db, AsyncSessionLocal
from app.api.deps import get_current_user
from app.models.user import User
from app.models.analysis import Analysis, AuditLog, LeaseType
from app.services.pdf_service import extract_text_from_pdf, validate_pdf_size
from app.services.ai_service import analyze_lease
from app.services.auth_service import check_and_consume_quota
from app.core.logging import log

router = APIRouter(prefix="/analyze", tags=["Analysis"])


@router.post("/", status_code=201)
async def create_analysis(
    request: Request,                               # BUG-11: needed by slowapi
    background_tasks: BackgroundTasks,
    file: Optional[UploadFile] = File(None),
    lease_text: Optional[str] = Form(None),
    jurisdiction: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Analyze a lease. Accepts PDF file or raw text. Quota-controlled per plan."""
    await check_and_consume_quota(db, current_user)

    extracted_text = ""
    page_count = 1
    filename = "text_input"

    if file and file.filename:
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(400, "Only PDF files are accepted.")
        file_bytes = await file.read()
        validate_pdf_size(file_bytes)
        extracted_text, page_count = await extract_text_from_pdf(file_bytes, file.filename)
        filename = file.filename
        del file_bytes  # PDF bytes never linger in memory
    elif lease_text and lease_text.strip():
        if len(lease_text.strip()) < 100:
            raise HTTPException(422, "Lease text too short (minimum 100 characters).")
        extracted_text = lease_text.strip()
        filename = "pasted_text"
    else:
        raise HTTPException(400, "Provide either a PDF file or lease_text field.")

    start_ms = int(time.time() * 1000)
    result = await analyze_lease(extracted_text, jurisdiction)
    elapsed_ms = int(time.time() * 1000) - start_ms

    lease_type_str = result.get("lease_summary", {}).get("lease_type", "UNKNOWN")
    try:
        lease_type = LeaseType[lease_type_str]
    except KeyError:
        lease_type = LeaseType.UNKNOWN

    analysis = Analysis(
        user_id=current_user.id,
        jurisdiction=jurisdiction,
        original_filename=filename,
        lease_type=lease_type,
        pages_analyzed=page_count,
        fairness_score=result.get("fairness_score"),
        lease_summary=result.get("lease_summary"),
        risk_summary=result.get("risk_summary"),
        clauses=result.get("clauses"),
        top_3_priorities=result.get("top_3_negotiation_priorities"),
        counter_proposal_letter=result.get("counter_proposal_letter"),
        processing_time_ms=result.get("_processing_time_ms", elapsed_ms),
        tokens_used=result.get("_tokens_used"),
        model_used=result.get("_model"),
        purge_after=datetime.now(timezone.utc) + timedelta(days=90),
    )
    db.add(analysis)
    await db.flush()        # BUG-10 FIX: flush gets the UUID; commit handled by get_db()
    analysis_id = str(analysis.id)
    # BUG-10 FIX: NO manual db.commit() here — get_db() calls it after yield

    # BUG-12 FIX: capture IP + user agent for audit log
    client_ip = request.client.host if request.client else None
    user_agent_str = request.headers.get("user-agent", "")[:500]  # cap length

    background_tasks.add_task(
        _log_analysis_bg,
        analysis_id,
        str(current_user.id),
        jurisdiction,
        client_ip,
        user_agent_str,
    )

    log.info(
        "analysis.complete",
        user_id=str(current_user.id),
        analysis_id=analysis_id,
        score=result.get("fairness_score"),
        elapsed_ms=elapsed_ms,
    )

    return {
        "analysis_id": analysis_id,
        "jurisdiction": jurisdiction,
        **{k: v for k, v in result.items() if not k.startswith("_")},
        "processing_time_ms": elapsed_ms,
        "legal_disclaimer": result.get(
            "legal_disclaimer",
            "LeaseLens provides AI-assisted analysis for informational purposes only. "
            "Not legal advice. For CRITICAL findings, consult a qualified advocate "
            "registered with the Bar Council of India."
        ),
    }


@router.get("/history")
async def get_analysis_history(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    limit = min(max(limit, 1), 50)
    offset = max(offset, 0)

    # BUG-13 FIX: real COUNT query, not len(results)
    count_result = await db.execute(
        select(func.count(Analysis.id)).where(
            Analysis.user_id == current_user.id,
            Analysis.is_deleted == 0,
        )
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(Analysis)
        .where(Analysis.user_id == current_user.id, Analysis.is_deleted == 0)
        .order_by(desc(Analysis.created_at))
        .limit(limit)
        .offset(offset)
    )
    analyses = result.scalars().all()

    return {
        "items": [
            {
                "id": str(a.id),
                "jurisdiction": a.jurisdiction,
                "fairness_score": a.fairness_score,
                "original_filename": a.original_filename,
                "lease_type": a.lease_type.value if a.lease_type else "UNKNOWN",
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in analyses
        ],
        "total": total,       # BUG-13 FIX: real total
        "limit": limit,
        "offset": offset,
        "has_more": (offset + limit) < total,
    }


@router.get("/{analysis_id}")
async def get_analysis(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        analysis_uuid = uuid.UUID(analysis_id)
    except ValueError:
        raise HTTPException(400, "Invalid analysis ID format.")

    result = await db.execute(
        select(Analysis).where(
            Analysis.id == analysis_uuid,
            Analysis.user_id == current_user.id,
            Analysis.is_deleted == 0,
        )
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(404, "Analysis not found or access denied.")

    return {
        "analysis_id": str(analysis.id),
        "jurisdiction": analysis.jurisdiction,
        "fairness_score": analysis.fairness_score,
        "lease_summary": analysis.lease_summary,
        "risk_summary": analysis.risk_summary,
        "clauses": analysis.clauses,
        "top_3_negotiation_priorities": analysis.top_3_priorities,
        "counter_proposal_letter": analysis.counter_proposal_letter,
        "processing_time_ms": analysis.processing_time_ms,
        "legal_disclaimer": (
            "LeaseLens provides AI-assisted analysis for informational purposes only. "
            "Not legal advice. For CRITICAL findings, consult a qualified advocate "
            "registered with the Bar Council of India."
        ),
        "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
    }


@router.delete("/{analysis_id}", status_code=200)
async def delete_analysis(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        analysis_uuid = uuid.UUID(analysis_id)
    except ValueError:
        raise HTTPException(400, "Invalid analysis ID.")

    await db.execute(
        update(Analysis).where(
            Analysis.id == analysis_uuid,
            Analysis.user_id == current_user.id,
        ).values(is_deleted=1)
    )
    return {"message": "Analysis deleted."}


async def _log_analysis_bg(
    analysis_id: str,
    user_id: str,
    jurisdiction: str,
    ip_address: Optional[str] = None,   # BUG-12 FIX
    user_agent: Optional[str] = None,   # BUG-12 FIX
) -> None:
    """Background audit log — uses its own session to avoid concurrency issues."""
    try:
        async with AsyncSessionLocal() as session:
            entry = AuditLog(
                user_id=uuid.UUID(user_id),
                action="lease.analyzed",
                resource_type="analysis",
                resource_id=analysis_id,
                ip_address=ip_address,
                user_agent=user_agent,
                extra_data={"jurisdiction": jurisdiction},
            )
            session.add(entry)
            await session.commit()
    except Exception as e:
        log.error("audit.log.failed", error=str(e))
