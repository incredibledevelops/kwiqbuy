"""
Platform-wide settings, singleton.

Exactly one document with `key="global"` exists. Reads fall back to
config defaults if the doc hasn't been created yet.

Admin can update:
  - commission_pct           — default % the platform takes
  - min_payout_ghs           — vendor balance floor before payout
  - payout_schedule          — manual | weekly | monthly
  - free_delivery_threshold  — subtotal ≥ this ⇒ delivery free
  - support_phone/email
  - maintenance_mode         — kill-switch for customer-facing endpoints
"""
from datetime import datetime, timezone
from typing import Optional

from beanie import Document
from pydantic import EmailStr, Field

from app.core.config import settings


def _now() -> datetime:
    return datetime.now(timezone.utc)


class PlatformSettings(Document):
    key: str = "global"  # always "global"

    # Commission
    commission_pct: float = Field(
        default_factory=lambda: settings.DEFAULT_PLATFORM_COMMISSION_PCT,
        ge=0.0,
        le=100.0,
    )

    # Payouts
    min_payout_ghs: float = Field(
        default_factory=lambda: settings.MIN_VENDOR_PAYOUT_GHS,
        ge=0.0,
    )
    payout_schedule: str = Field(
        default_factory=lambda: settings.PAYOUT_SCHEDULE
    )  # manual | weekly | monthly

    # Delivery
    free_delivery_threshold: float = Field(
        default_factory=lambda: settings.FREE_DELIVERY_THRESHOLD,
        ge=0.0,
    )

    # Rider compensation
    rider_fee_model: str = Field(
        default_factory=lambda: settings.RIDER_FEE_MODEL
    )  # flat | pct_of_delivery_fee
    rider_flat_fee_ghs: float = Field(
        default_factory=lambda: settings.RIDER_FLAT_FEE_GHS, ge=0.0
    )
    rider_pct_of_delivery_fee: float = Field(
        default_factory=lambda: settings.RIDER_PCT_OF_DELIVERY_FEE, ge=0.0, le=100.0
    )

    # Support
    support_phone: str = Field(default_factory=lambda: settings.SUPPORT_PHONE)
    support_email: Optional[EmailStr] = None
    support_whatsapp: str = Field(
        default_factory=lambda: settings.SUPPORT_WHATSAPP
    )

    # Platform controls
    maintenance_mode: bool = False
    customer_ordering_enabled: bool = True
    vendor_signups_enabled: bool = True

    updated_by: Optional[str] = None  # admin user id
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)

    class Settings:
        name = "platform_settings"
        indexes = ["key"]