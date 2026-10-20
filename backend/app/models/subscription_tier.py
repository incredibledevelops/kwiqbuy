"""
Vendor subscription tiers.

A vendor is on at most one active subscription. Subscriptions bill monthly
via Paystack (see crud/subscription.py). When active, the tier's commission
discount applies — the vendor's effective commission is
    base_commission − tier.commission_discount_pct
clamped to [0, base_commission].

The `SubscriptionTier` collection holds the catalogue; `VendorSubscription`
holds one row per vendor with start/end dates.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


class SubscriptionStatus(str, Enum):
    PENDING = "pending"        # created, awaiting first payment
    ACTIVE = "active"
    CANCELLED = "cancelled"    # won't renew
    EXPIRED = "expired"        # ran out of days


class SubscriptionTier(Document):
    """
    Catalogue entry. Admin manages these.
    `slug` is a stable identifier used in code:
      "free"       — default, no billing
      "growth"     — mid tier
      "enterprise" — top tier
    """
    slug: Indexed(str, unique=True)  # type: ignore
    name: str
    description: Optional[str] = None

    monthly_price: float = Field(ge=0)          # 0 for free
    commission_discount_pct: float = Field(ge=0, le=100, default=0.0)

    features: List[str] = Field(default_factory=list)

    is_active: bool = True
    display_order: int = 0

    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)

    class Settings:
        name = "subscription_tiers"
        indexes = ["slug", "is_active"]


class VendorSubscription(Document):
    vendor_id: Indexed(PydanticObjectId)  # type: ignore
    tier_id: Indexed(PydanticObjectId)  # type: ignore
    tier_slug: str

    status: SubscriptionStatus = SubscriptionStatus.PENDING

    started_at: Optional[datetime] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    expired_at: Optional[datetime] = None

    # Paystack subscription ref
    paystack_reference: Optional[str] = None
    last_payment_at: Optional[datetime] = None
    last_payment_amount: float = 0.0

    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)

    class Settings:
        name = "vendor_subscriptions"
        indexes = [
            "vendor_id",
            "tier_id",
            "status",
            "current_period_end",
        ]
