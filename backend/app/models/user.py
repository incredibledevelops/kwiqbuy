from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from beanie import Document, Indexed, PydanticObjectId
from pydantic import EmailStr, Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


class UserRole(str, Enum):
    ADMIN = "admin"
    STAFF = "staff"
    VENDOR = "vendor"
    RIDER = "rider"


class User(Document):
    full_name: str
    email: Indexed(EmailStr, unique=True)  # type: ignore
    phone: Optional[str] = None
    hashed_password: str
    role: UserRole = UserRole.STAFF
    is_active: bool = True
    vendor_id: Optional[PydanticObjectId] = None
    vehicle: Optional[str] = None
    plate_number: Optional[str] = None
    last_login_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)

    class Settings:
        name = "users"
        indexes = ["email", "role", "vendor_id"]
