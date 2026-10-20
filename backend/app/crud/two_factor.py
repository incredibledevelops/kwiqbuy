import secrets
from datetime import datetime, timezone
from typing import Optional

import pyotp
from beanie import PydanticObjectId

from app.models.two_factor import Admin2FA


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def get_for_user(user_id: str) -> Optional[Admin2FA]:
    try:
        uid = PydanticObjectId(user_id)
    except Exception:
        return None
    return await Admin2FA.find_one(Admin2FA.user_id == uid)


async def is_enabled(user_id: str) -> bool:
    doc = await get_for_user(user_id)
    return bool(doc and doc.enabled)


async def start_setup(user_id: str, email: str, issuer: str):
    uid = PydanticObjectId(user_id)
    secret = pyotp.random_base32()
    uri = pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name=issuer)

    existing = await Admin2FA.find_one(Admin2FA.user_id == uid)
    if existing:
        existing.secret = secret
        existing.enabled = False
        existing.verified_at = None
        existing.recovery_codes = []
        existing.updated_at = _now()
        await existing.save()
        return existing, secret, uri

    doc = Admin2FA(user_id=uid, secret=secret, enabled=False)
    await doc.insert()
    return doc, secret, uri


async def verify_and_enable(user_id: str, code: str):
    doc = await get_for_user(user_id)
    if not doc:
        return False, "2FA has not been set up", []
    if doc.enabled:
        return False, "2FA is already enabled", []

    totp = pyotp.TOTP(doc.secret)
    if not totp.verify(code, valid_window=1):
        return False, "Invalid or expired code", []

    codes = [secrets.token_hex(4).upper() for _ in range(8)]
    doc.enabled = True
    doc.verified_at = _now()
    doc.recovery_codes = codes
    doc.updated_at = _now()
    await doc.save()
    return True, "2FA enabled", codes


async def verify_code(user_id: str, code: str) -> bool:
    doc = await get_for_user(user_id)
    if not doc or not doc.enabled:
        return False

    if code.upper() in doc.recovery_codes:
        doc.recovery_codes.remove(code.upper())
        doc.last_used_at = _now()
        doc.updated_at = _now()
        await doc.save()
        return True

    totp = pyotp.TOTP(doc.secret)
    if totp.verify(code, valid_window=1):
        doc.last_used_at = _now()
        doc.updated_at = _now()
        await doc.save()
        return True
    return False


async def disable(user_id: str) -> bool:
    doc = await get_for_user(user_id)
    if not doc:
        return False
    await doc.delete()
    return True
