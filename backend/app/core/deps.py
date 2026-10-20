from typing import Any, Optional

from beanie import PydanticObjectId
from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings
from app.core.security import decode_token
from app.crud import customer as customer_crud
from app.crud import idempotency as idempotency_crud
from app.crud import revoked_token as revoked_crud
from app.crud import vendor as vendor_crud
from app.models.customer import Customer
from app.models.user import User, UserRole
from app.models.vendor import Vendor, VendorStatus

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login"
)
oauth2_customer_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/customer-auth/request-otp"
)


# ---------- Idempotency ----------

async def get_idempotency_key(
    x_idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key"),
) -> Optional[str]:
    return x_idempotency_key


async def check_idempotency(key: Optional[str], endpoint: str) -> Optional[dict[str, Any]]:
    if not key:
        return None
    record = await idempotency_crud.get(key, endpoint)
    if record and record.response_body:
        return record.response_body
    return None


async def store_idempotency(
    key: Optional[str],
    endpoint: str,
    body: dict[str, Any],
    status_code: int = 200,
) -> None:
    if not key:
        return
    try:
        await idempotency_crud.save(key, endpoint, body, status_code)
    except Exception:
        import logging
        logging.getLogger(__name__).exception("idempotency store failed")


# ---------- Helpers ----------

def _client_ip(request: Request) -> Optional[str]:
    try:
        xff = request.headers.get("x-forwarded-for")
        if xff:
            return xff.split(",")[0].strip()
        if request.client:
            return request.client.host
    except Exception:
        pass
    return None


async def _ensure_not_revoked(payload: dict) -> None:
    jti = payload.get("jti")
    if jti and await revoked_crud.is_revoked(jti):
        raise HTTPException(401, "Token has been revoked")


# ---------- Auth ----------

async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
) -> User:
    creds_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
    except ValueError:
        raise creds_exc
    if payload.get("type") != "access":
        raise creds_exc

    await _ensure_not_revoked(payload)

    user_id = payload.get("sub")
    if not user_id:
        raise creds_exc
    try:
        user = await User.get(PydanticObjectId(user_id))
    except Exception:
        raise creds_exc
    if not user or not user.is_active:
        raise creds_exc
    return user


async def get_current_admin(
    request: Request,
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(403, "Admin access required")

    # Enforce IP allowlist if configured
    if settings.ADMIN_IP_ALLOWLIST_ENABLED:
        from app.crud import platform_settings as ps_crud
        plat = await ps_crud.get_settings()
        if plat.admin_ip_allowlist:
            ip = _client_ip(request)
            if not ip or ip not in plat.admin_ip_allowlist:
                raise HTTPException(
                    403,
                    "Admin access is restricted from this network.",
                )

    return current_user


async def get_current_staff_or_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in (UserRole.ADMIN, UserRole.STAFF):
        raise HTTPException(403, "Staff or admin access required")
    return current_user


async def get_current_rider(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.RIDER:
        raise HTTPException(403, "Rider access required")
    return current_user


async def get_current_rider_or_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in (UserRole.RIDER, UserRole.ADMIN):
        raise HTTPException(403, "Rider or admin access required")
    return current_user


async def get_current_vendor(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.VENDOR:
        raise HTTPException(403, "Vendor access required")
    if not current_user.vendor_id:
        raise HTTPException(403, "Vendor account is not linked to a business")
    vendor = await vendor_crud.get_by_id(str(current_user.vendor_id))
    if not vendor:
        raise HTTPException(403, "Linked vendor no longer exists")
    if vendor.status == VendorStatus.CLOSED:
        raise HTTPException(403, "Vendor account is closed")
    return current_user


# ---------- Customer auth ----------

async def get_current_customer(
    token: str = Depends(oauth2_customer_scheme),
) -> Customer:
    creds_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate customer credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
    except ValueError:
        raise creds_exc
    if payload.get("type") != "customer_access":
        raise creds_exc

    await _ensure_not_revoked(payload)

    phone = payload.get("sub")
    if not phone:
        raise creds_exc
    customer = await customer_crud.get_by_phone(phone)
    if not customer:
        raise creds_exc
    return customer


async def get_optional_customer(
    token: Optional[str] = Depends(
        OAuth2PasswordBearer(
            tokenUrl=f"{settings.API_V1_PREFIX}/customer-auth/request-otp",
            auto_error=False,
        )
    ),
) -> Optional[Customer]:
    if not token:
        return None
    try:
        payload = decode_token(token)
    except ValueError:
        return None
    if payload.get("type") != "customer_access":
        return None
    jti = payload.get("jti")
    if jti and await revoked_crud.is_revoked(jti):
        return None
    phone = payload.get("sub")
    if not phone:
        return None
    return await customer_crud.get_by_phone(phone)
