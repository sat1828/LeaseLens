"""
LeaseLens FastAPI Application — Production Grade
BUG-17 FIX: CORS localhost origins only in non-production.
BUG-18 FIX: Security headers added (CSP + HSTS + X-Frame etc).
BUG-22 FIX: Startup config validation — fails fast on missing critical keys.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.logging import setup_logging, log
from app.api import auth, analyze, payments

setup_logging()

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    # BUG-22 FIX: Validate critical config at startup
    warnings: list[str] = []
    errors: list[str] = []

    if not settings.ANTHROPIC_API_KEY:
        if settings.APP_ENV == "production":
            errors.append("ANTHROPIC_API_KEY is not set — AI analysis will fail for all users")
        else:
            warnings.append("ANTHROPIC_API_KEY is not set — AI analysis will fail")

    if settings.APP_ENV == "production":
        if not settings.FIELD_ENCRYPTION_KEY:
            errors.append("FIELD_ENCRYPTION_KEY is not set — encrypted data will be lost on restart")
        if settings.APP_SECRET_KEY == "change-this-in-production-minimum-32-characters":
            errors.append("APP_SECRET_KEY is still the default value — JWT security is compromised")
        if not settings.FRONTEND_URL or "localhost" in settings.FRONTEND_URL:
            warnings.append("FRONTEND_URL points to localhost — CORS may block production frontend")

    for w in warnings:
        log.warning("config.startup.warning", issue=w)

    if errors:
        error_text = "\n".join(f"  • {e}" for e in errors)
        raise RuntimeError(
            f"STARTUP FAILED — critical configuration errors:\n{error_text}\n"
            "Fix these in your environment variables before starting."
        )

    log.info("leaselens.startup", env=settings.APP_ENV, version="1.0.0")
    yield
    log.info("leaselens.shutdown")


app = FastAPI(
    title="LeaseLens API",
    description="AI-powered lease analysis to protect tenants.",
    version="1.0.0",
    docs_url="/api/docs" if settings.APP_ENV != "production" else None,
    redoc_url="/api/redoc" if settings.APP_ENV != "production" else None,
    lifespan=lifespan,
)

# ── Rate limiting ─────────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS (BUG-17 FIX: localhost only in non-production) ──────────────────────
_cors_origins = [settings.FRONTEND_URL]
if settings.APP_ENV != "production":
    _cors_origins += [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
    max_age=86400,
)

# ── BUG-18 FIX: Security headers on every response ───────────────────────────
@app.middleware("http")
async def security_headers(request: Request, call_next) -> Response:
    response = await call_next(request)
    api_url = settings.FRONTEND_URL

    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

    if settings.APP_ENV == "production":
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )
        response.headers["Content-Security-Policy"] = (
            f"default-src 'self'; "
            f"script-src 'self'; "
            f"style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            f"font-src 'self' https://fonts.gstatic.com; "
            f"connect-src 'self' {api_url}; "
            f"img-src 'self' data: blob:; "
            f"frame-ancestors 'none'; "
            f"base-uri 'self'; "
            f"form-action 'self'"
        )

    return response


# ── Global error handler — never leak stack traces ───────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.error("unhandled.exception", path=str(request.url.path), error=str(exc), exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error. Our team has been notified."},
    )


# ── Request logging (skip health to reduce noise) ────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next) -> Response:
    response = await call_next(request)
    if not request.url.path.startswith("/health"):
        log.info(
            "http",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
        )
    return response


# ── Routers ───────────────────────────────────────────────────────────────────
PREFIX = settings.API_PREFIX
app.include_router(auth.router, prefix=PREFIX)
app.include_router(analyze.router, prefix=PREFIX)
app.include_router(payments.router, prefix=PREFIX)


@app.get("/health", tags=["System"])
async def health():
    return {"status": "healthy", "service": "LeaseLens API", "version": "1.0.0"}


@app.get("/", tags=["System"])
async def root():
    return {"service": "LeaseLens API", "docs": "/api/docs", "health": "/health"}
