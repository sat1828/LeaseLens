# ══════════════════════════════════════════════════════════
# LeaseLens Backend Dockerfile
# BUG-44 FIX: Runs as non-root user (uid 1001)
# ══════════════════════════════════════════════════════════
FROM python:3.12-slim

# System dependencies: tesseract for OCR, libgl for PyMuPDF, curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-hin \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# BUG-44 FIX: Create non-root user before installing packages
RUN groupadd --system --gid 1001 appgroup && \
    useradd --system --uid 1001 --gid 1001 --no-create-home appuser

WORKDIR /app

# Install Python deps as root (writing to system site-packages), then hand off
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Give ownership to non-root user
RUN chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

EXPOSE 8000

# Default: dev server (docker-compose overrides CMD for production)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
