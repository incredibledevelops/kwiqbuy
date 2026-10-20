from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional

from beanie import Document, Indexed
from pydantic import EmailStr, Field

from app.core.config import settings


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _default_expiry() -> datetime:
    return _now() + timedelta(days=settings.VENDOR_APPLICATION_TTL_DAYS)


class VendorApplicationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    WITHDRAWN = "withdrawn"


class VendorApplication(Document):
    # What kind of business
    business_name: str
    # Changed to have a default value to prevent Pydantic crashes if missing
    business_category: str = Field(default="food", description="food | retail")
    business_type: Optional[str] = None

    description: str
    contact_name: str
    contact_email: Indexed(EmailStr)  # type: ignore
    contact_phone: Indexed(str)  # type: ignore

    # Location
    pickup_address: str
    pickup_lat: Optional[float] = None
    pickup_lng: Optional[float] = None
    city: Optional[str] = None
    region: Optional[str] = None

    # Food-only: requested delivery radius
    delivery_radius_km: Optional[float] = Field(default=15.0, ge=0.1, le=100.0)

    # Requested payout method
    requested_payout_method: Optional[str] = None
    requested_payout_account_name: Optional[str] = None
    requested_payout_account_number: Optional[str] = None

    # Documents
    id_document_url: Optional[str] = None
    business_registration_url: Optional[str] = None

    # Status
    status: VendorApplicationStatus = VendorApplicationStatus.PENDING
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None

    created_vendor_id: Optional[str] = None
    created_user_id: Optional[str] = None

    applied_ip: Optional[str] = None
    applied_user_agent: Optional[str] = None

    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)
    expires_at: datetime = Field(default_factory=_default_expiry)

    class Settings:
        name = "vendor_applications"
        indexes = ["contact_email", "contact_phone", "status", "expires_at"]