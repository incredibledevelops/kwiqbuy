from datetime import datetime, timezone
from typing import List, Optional

from beanie import Document
from pydantic import EmailStr, Field

from app.core.config import settings


def _now() -> datetime:
    return datetime.now(timezone.utc)


class PlatformSettings(Document):
    key: str = "global"

    # Commission
    commission_pct: float = Field(
        default_factory=lambda: settings.DEFAULT_PLATFORM_COMMISSION_PCT,
        ge=0.0, le=100.0,
    )
    food_commission_pct: float = Field(
        default_factory=lambda: settings.FOOD_COMMISSION_PCT, ge=0.0, le=100.0
    )
    retail_commission_pct: float = Field(
        default_factory=lambda: settings.RETAIL_COMMISSION_PCT, ge=0.0, le=100.0
    )

    # Delivery fee cut
    platform_delivery_cut_pct: float = Field(
        default_factory=lambda: settings.PLATFORM_DELIVERY_CUT_PCT,
        ge=0.0, le=100.0,
    )

    # Payouts
    min_payout_ghs: float = Field(
        default_factory=lambda: settings.MIN_VENDOR_PAYOUT_GHS, ge=0.0
    )
    payout_schedule: str = Field(default_factory=lambda: settings.PAYOUT_SCHEDULE)

    # Delivery
    free_delivery_threshold: float = Field(
        default_factory=lambda: settings.FREE_DELIVERY_THRESHOLD, ge=0.0
    )

    # Rider compensation
    rider_fee_model: str = Field(default_factory=lambda: settings.RIDER_FEE_MODEL)
    rider_flat_fee_ghs: float = Field(
        default_factory=lambda: settings.RIDER_FLAT_FEE_GHS, ge=0.0
    )
    rider_pct_of_delivery_fee: float = Field(
        default_factory=lambda: settings.RIDER_PCT_OF_DELIVERY_FEE, ge=0.0, le=100.0
    )

    # Support
    support_phone: str = Field(default_factory=lambda: settings.SUPPORT_PHONE)
    support_email: Optional[EmailStr] = None
    support_whatsapp: str = Field(default_factory=lambda: settings.SUPPORT_WHATSAPP)

    # Platform controls
    maintenance_mode: bool = False
    customer_ordering_enabled: bool = True
    vendor_signups_enabled: bool = True

    # Security
    admin_ip_allowlist: List[str] = Field(default_factory=list)
    admin_2fa_required: bool = False

    updated_by: Optional[str] = None
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)

    def commission_for(self, category: str) -> float:
        if category == "food":
            return float(self.food_commission_pct)
        if category == "retail":
            return float(self.retail_commission_pct)
        return float(self.commission_pct)

    class Settings:
        name = "platform_settings"
        indexes = ["key"]
