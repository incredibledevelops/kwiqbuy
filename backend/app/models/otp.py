from datetime import datetime, timezone
from enum import Enum

from beanie import Document, Indexed
from pydantic import Field


class OTPPurpose(str, Enum):
    LOGIN = "login"
    VERIFY_PHONE = "verify_phone"


class OTPToken(Document):
    phone: Indexed(str)  # type: ignore
    code: str                          # 6 digits
    purpose: OTPPurpose = OTPPurpose.LOGIN
    attempts: int = 0
    max_attempts: int = 5
    expires_at: datetime
    used: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "otp_tokens"
        indexes = ["phone"]