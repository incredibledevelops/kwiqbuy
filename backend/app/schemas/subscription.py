from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.subscription_tier import SubscriptionStatus


class SubscriptionTierOut(BaseModel):
    id: str
    slug: str
    name: str
    description: Optional[str] = None
    monthly_price: float
    commission_discount_pct: float
    features: List[str] = []
    is_active: bool
    display_order: int


class SubscriptionTierCreate(BaseModel):
    slug: Optional[str] = None
    name: str = Field(min_length=2, max_length=60)
    description: Optional[str] = Field(default=None, max_length=500)
    monthly_price: float = Field(ge=0)
    commission_discount_pct: float = Field(ge=0, le=100, default=0.0)
    features: List[str] = []
    is_active: bool = True
    display_order: int = 0


class SubscriptionTierUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    monthly_price: Optional[float] = Field(default=None, ge=0)
    commission_discount_pct: Optional[float] = Field(default=None, ge=0, le=100)
    features: Optional[List[str]] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None


class VendorSubscriptionOut(BaseModel):
    id: str
    vendor_id: str
    tier_id: str
    tier_slug: str
    status: SubscriptionStatus
    started_at: Optional[datetime] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    expired_at: Optional[datetime] = None
    last_payment_at: Optional[datetime] = None
    last_payment_amount: float = 0.0
    created_at: datetime


class VendorSubscriptionStatusOut(BaseModel):
    """What a vendor sees on their dashboard."""
    has_active_subscription: bool
    current: Optional[VendorSubscriptionOut] = None
    tier: Optional[SubscriptionTierOut] = None
    base_commission_pct: float
    effective_commission_pct: float
    is_override: bool = False


class VendorSubscribeIn(BaseModel):
    tier_slug: str
