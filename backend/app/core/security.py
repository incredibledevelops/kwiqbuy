from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import secrets
import string
import uuid

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        return False


def generate_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _create_token(
    subject: str,
    expires_delta: timedelta,
    token_type: str,
    extra: Optional[Dict[str, Any]] = None,
) -> tuple[str, str, datetime]:
    """
    Returns (encoded_token, jti, expires_at_utc).
    The jti is needed by the revocation layer.
    """
    now = datetime.now(timezone.utc)
    expires_at = now + expires_delta
    jti = str(uuid.uuid4())
    payload: Dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
        "jti": jti,
        "type": token_type,
    }
    if extra:
        payload.update(extra)
    encoded = jwt.encode(
        payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded, jti, expires_at


# ---------- Staff / vendor / rider / admin ----------

def create_access_token(
    subject: str, extra: Optional[Dict[str, Any]] = None
) -> str:
    token, _jti, _exp = _create_token(
        subject,
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "access",
        extra,
    )
    return token


def create_access_token_with_meta(
    subject: str, extra: Optional[Dict[str, Any]] = None
) -> tuple[str, str, datetime]:
    return _create_token(
        subject,
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "access",
        extra,
    )


def create_refresh_token(subject: str) -> str:
    token, _jti, _exp = _create_token(
        subject,
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        "refresh",
    )
    return token


def create_refresh_token_with_meta(subject: str) -> tuple[str, str, datetime]:
    return _create_token(
        subject,
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        "refresh",
    )


# ---------- Customer ----------

def create_customer_access_token(
    phone: str, customer_id: str, extra: Optional[Dict[str, Any]] = None
) -> str:
    payload = {"phone": phone, "cid": customer_id}
    if extra:
        payload.update(extra)
    token, _jti, _exp = _create_token(
        subject=phone,
        expires_delta=timedelta(days=settings.CUSTOMER_TOKEN_EXPIRE_DAYS),
        token_type="customer_access",
        extra=payload,
    )
    return token


def create_customer_refresh_token(phone: str, customer_id: str) -> str:
    token, _jti, _exp = _create_token(
        subject=phone,
        expires_delta=timedelta(days=settings.CUSTOMER_REFRESH_EXPIRE_DAYS),
        token_type="customer_refresh",
        extra={"cid": customer_id},
    )
    return token


def decode_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
    except JWTError as exc:
        raise ValueError(f"Invalid token: {exc}") from exc


def token_expiry_from_payload(payload: Dict[str, Any]) -> datetime:
    """Return the exp claim as an aware UTC datetime."""
    exp = payload.get("exp")
    if not exp:
        return datetime.now(timezone.utc)
    return datetime.fromtimestamp(int(exp), tz=timezone.utc)
