import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.core.config import settings
from app.models.otp import OTPPurpose, OTPToken


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _generate_code() -> str:
    """6-digit numeric code, avoiding leading zeros (nicer to read)."""
    return str(secrets.randbelow(900000) + 100000)


async def create_otp(
    phone: str,
    purpose: OTPPurpose = OTPPurpose.LOGIN,
) -> OTPToken:
    # Invalidate any outstanding codes for the same phone+purpose
    await OTPToken.find(
        OTPToken.phone == phone,
        OTPToken.purpose == purpose,
        OTPToken.used == False,  # noqa: E712
    ).update({"$set": {"used": True}})

    code = _generate_code()
    expires = _now() + timedelta(minutes=settings.CUSTOMER_OTP_EXPIRE_MINUTES)

    otp = OTPToken(
        phone=phone,
        code=code,
        purpose=purpose,
        expires_at=expires,
    )
    await otp.insert()
    return otp


async def verify_otp(
    phone: str,
    code: str,
    purpose: OTPPurpose = OTPPurpose.LOGIN,
) -> tuple[bool, str]:
    otp = await OTPToken.find_one(
        OTPToken.phone == phone,
        OTPToken.purpose == purpose,
        OTPToken.used == False,  # noqa: E712
    )
    if not otp:
        return False, "No active code — please request a new one"

    if otp.expires_at.replace(tzinfo=timezone.utc) < _now():
        otp.used = True
        await otp.save()
        return False, "Code has expired — please request a new one"

    if otp.attempts >= otp.max_attempts:
        otp.used = True
        await otp.save()
        return False, "Too many attempts — please request a new code"

    if otp.code != code.strip():
        otp.attempts += 1
        await otp.save()
        remaining = otp.max_attempts - otp.attempts
        return False, f"Incorrect code ({remaining} attempts left)"

    otp.used = True
    await otp.save()
    return True, ""