"""
Security: password hashing, JWT tokens, field encryption.
BUG-16 FIX: Ephemeral Fernet key raises RuntimeError in production
            instead of silently losing all encrypted data on restart.
"""
import warnings
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Any
from jose import jwt, JWTError
from cryptography.fernet import Fernet

# Silence passlib's cosmetic bcrypt version warning
logging.getLogger("passlib").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", ".*bcrypt.*")
warnings.filterwarnings("ignore", ".*trapped.*")

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

from app.core.config import settings

# Bcrypt hard limit is 72 bytes — always truncate before hashing
_MAX_BCRYPT_BYTES = 72


def _truncate(password: str) -> str:
    """Truncate password to 72 UTF-8 bytes (bcrypt hard limit)."""
    encoded = password.encode("utf-8")
    if len(encoded) > _MAX_BCRYPT_BYTES:
        encoded = encoded[:_MAX_BCRYPT_BYTES]
    return encoded.decode("utf-8", errors="ignore")


def hash_password(password: str) -> str:
    return pwd_context.hash(_truncate(password))


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(_truncate(plain), hashed)
    except Exception:
        return False


def create_access_token(subject: Any, expires_delta: Optional[timedelta] = None) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return jwt.encode(
        {"sub": str(subject), "exp": expire, "iat": datetime.now(timezone.utc)},
        settings.APP_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(
            token, settings.APP_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload.get("sub")
    except JWTError:
        return None


_fernet_instance: Optional[Fernet] = None


def get_cipher() -> Fernet:
    """
    BUG-16 FIX:
    - Production without FIELD_ENCRYPTION_KEY → hard RuntimeError (not silent data loss)
    - Development without FIELD_ENCRYPTION_KEY → ephemeral key with loud warning
    """
    global _fernet_instance
    if _fernet_instance is None:
        key = settings.FIELD_ENCRYPTION_KEY

        if not key:
            if settings.APP_ENV == "production":
                raise RuntimeError(
                    "CRITICAL: FIELD_ENCRYPTION_KEY is not set in production.\n"
                    "Generate with:\n"
                    "  python -c \"from cryptography.fernet import Fernet; "
                    "print(Fernet.generate_key().decode())\"\n"
                    "Then add FIELD_ENCRYPTION_KEY=<key> to your environment variables."
                )
            # Development: warn loudly, use ephemeral key
            import structlog
            structlog.get_logger().warning(
                "security.ephemeral_key",
                warning="FIELD_ENCRYPTION_KEY not set. "
                        "Encrypted data will be LOST on server restart. "
                        "Acceptable in development; FATAL in production.",
            )
            key = Fernet.generate_key().decode()

        try:
            _fernet_instance = Fernet(
                key.encode() if isinstance(key, str) else key
            )
        except Exception as e:
            raise RuntimeError(
                f"Invalid FIELD_ENCRYPTION_KEY: {e}. "
                "Re-generate with: python -c \"from cryptography.fernet import Fernet; "
                "print(Fernet.generate_key().decode())\""
            )
    return _fernet_instance


def encrypt_text(text: str) -> str:
    return get_cipher().encrypt(text.encode()).decode()


def decrypt_text(token: str) -> str:
    return get_cipher().decrypt(token.encode()).decode()
