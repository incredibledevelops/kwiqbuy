from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from beanie import Document, Indexed, PydanticObjectId
from pydantic import BaseModel, Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


class VendorStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"


class VendorCategory(str, Enum):
    """
    Determines the vendor's fulfillment workflow:

      FOOD   — kitchen workflow (accepted → preparing → ready → picked_up),
               geo-scoped to a delivery radius around pickup_location.

      RETAIL — shipping workflow (confirmed → processing → packed → shipped
               → delivered), not geo-scoped; ships nationally.
    """
    FOOD = "food"
    RETAIL = "retail"


class GeoPoint(BaseModel):
    """GeoJSON Point. MongoDB stores this under a 2dsphere index."""
    type: str = "Point"
    coordinates: list[float]  # [lng, lat]


class Vendor(Document):
    # Identity
    business_name: str
    slug: Indexed(str, unique=True)  # type: ignore
    description: Optional[str] = None
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None

    # Category — food vs. retail. Determines workflow.
    # NOTE: Beanie's Indexed() can't wrap an Enum directly, so we declare
    # the field as the enum but declare the index explicitly in Settings.
    business_category: VendorCategory = VendorCategory.FOOD
    business_subtype: Optional[str] = None

    # Owner user (role="vendor")
    owner_user_id: Indexed(PydanticObjectId)  # type: ignore

    # Contact
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None

    # Pickup / dispatch address
    pickup_address: str
    pickup_lat: Optional[float] = None
    pickup_lng: Optional[float] = None

    # GeoJSON Point for $geoNear. Must be kept in sync with pickup_lat/lng.
    # Populated automatically by crud.vendor.create_vendor / update_vendor
    # when lat/lng are provided.
    pickup_location: Optional[GeoPoint] = None

    # Food-only: how far this vendor will deliver from pickup_location.
    # Ignored for retail vendors.
    delivery_radius_km: float = Field(default=15.0, ge=0.1, le=100.0)

    # Food-only: prep time before rider pickup.
    # Retail-only: dispatch SLA (hours to hand off to courier).
    prep_minutes: int = Field(default=20, ge=1, le=1440)

    # Status
    status: VendorStatus = VendorStatus.PENDING

    # Commission override — None means use PlatformSettings.commission_pct
    commission_pct_override: Optional[float] = Field(default=None, ge=0, le=100)

    # Payout recipient details (Paystack)
    payout_recipient_code: Optional[str] = None
    payout_recipient_type: Optional[str] = None
    payout_account_name: Optional[str] = None
    payout_account_number: Optional[str] = None
    payout_bank_code: Optional[str] = None
    payout_mobile_provider: Optional[str] = None

    # Aggregates (denormalized)
    total_orders: int = 0
    total_gross_sales: float = 0.0
    lifetime_platform_fees: float = 0.0
    lifetime_paid_out: float = 0.0

    average_rating: float = 0.0
    total_reviews: int = 0

    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)
    approved_at: Optional[datetime] = None
    suspended_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

    @property
    def available_balance(self) -> float:
        raw = (
            self.total_gross_sales
            - self.lifetime_platform_fees
            - self.lifetime_paid_out
        )
        return round(max(0.0, raw), 2)

    class Settings:
        name = "vendors"
        indexes = [
            "slug",
            "owner_user_id",
            "status",
            # Index the enum field by its string value via a compound
            # expression index. Beanie accepts this form.
            [("business_category", 1)],
            # 2dsphere index on the GeoJSON point for $geoNear.
            [("pickup_location", "2dsphere")],
        ]