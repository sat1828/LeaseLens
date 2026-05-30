"""
PDF text extraction service.
Primary: PyMuPDF native text extraction (fast, accurate for digital PDFs).
Fallback: Tesseract OCR (for scanned/image-only pages).
BUG-06 FIX: All CPU work runs in a dedicated thread pool — never blocks the async event loop.
PDF bytes are NEVER written to disk or stored after extraction.
"""
import asyncio
import fitz  # PyMuPDF
import io
from concurrent.futures import ThreadPoolExecutor
from typing import Tuple
from fastapi import HTTPException
from app.core.config import settings
from app.core.logging import log

# Dedicated thread pool for PDF work — isolated from asyncio's default executor.
# 4 workers: supports 4 concurrent PDF extractions without blocking each other.
_PDF_THREAD_POOL = ThreadPoolExecutor(
    max_workers=4,
    thread_name_prefix="leaselens-pdf",
)


async def extract_text_from_pdf(file_bytes: bytes, filename: str = "") -> Tuple[str, int]:
    """
    Async wrapper: delegates CPU-bound PDF extraction to thread pool.
    Returns (extracted_text, page_count).
    Never blocks the event loop.
    """
    loop = asyncio.get_running_loop()
    try:
        return await loop.run_in_executor(
            _PDF_THREAD_POOL,
            _extract_sync,
            file_bytes,
            filename,
        )
    except ValueError as e:
        msg = str(e)
        status = 400 if "pages" in msg.lower() else 422
        raise HTTPException(status, msg)


def _extract_sync(file_bytes: bytes, filename: str) -> Tuple[str, int]:
    """
    Synchronous extraction. Runs in thread pool — safe to block here.
    Do NOT call this directly from async code.
    """
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as e:
        raise ValueError(
            f"Cannot open PDF: {e}. "
            "Ensure the file is not password-protected or corrupted."
        )

    page_count = len(doc)
    if page_count > settings.MAX_PDF_PAGES:
        doc.close()
        raise ValueError(
            f"PDF has {page_count} pages — limit is {settings.MAX_PDF_PAGES}. "
            "Split the document or upload the relevant lease pages only."
        )

    log.info("pdf.start", filename=filename, pages=page_count)

    parts = []
    ocr_pages = 0

    for i, page in enumerate(doc):
        # Primary: native text extraction with reading-order sort=True
        text = page.get_text("text", sort=True).strip()

        # OCR fallback for image-only pages (< 50 chars native)
        if len(text) < 50 and settings.ENABLE_OCR:
            ocr_text = _try_ocr(page, i)
            if ocr_text:
                text = ocr_text
                ocr_pages += 1

        if text:
            parts.append(f"--- PAGE {i + 1} ---\n{text}")

    doc.close()

    combined = "\n\n".join(parts)

    if len(combined.strip()) < 200:
        raise ValueError(
            "Could not extract readable text from this PDF. "
            "If it is a scanned document, ensure scan quality is at least 200 DPI, "
            "or try a text-based (digitally-created) PDF."
        )

    # Cap at 200K chars to prevent adversarially large documents
    MAX_CHARS = 200_000
    if len(combined) > MAX_CHARS:
        log.warning("pdf.text.capped", original_chars=len(combined), capped_to=MAX_CHARS)
        combined = combined[:MAX_CHARS]

    log.info("pdf.done", chars=len(combined), pages=page_count, ocr_pages=ocr_pages)
    return combined, page_count


def _try_ocr(page: fitz.Page, page_num: int) -> str:
    """Tesseract OCR fallback. Only called for image-only pages."""
    try:
        import pytesseract
        from PIL import Image
        pix = page.get_pixmap(dpi=200)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        return pytesseract.image_to_string(img, lang="eng", config="--psm 1").strip()
    except ImportError:
        return ""  # Tesseract not installed — skip OCR
    except Exception as e:
        log.warning("ocr.failed", page=page_num + 1, error=str(e))
        return ""


def validate_pdf_size(file_bytes: bytes) -> None:
    """Fast-fail before extraction on oversized files."""
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > settings.MAX_PDF_SIZE_MB:
        raise HTTPException(
            400,
            f"File size {size_mb:.1f} MB exceeds the {settings.MAX_PDF_SIZE_MB} MB limit. "
            "Compress the PDF or upload only the relevant pages."
        )
