from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.promo_code import DiscountType


class PromoCodeBase(BaseModel):
    code: str = Field(min_length=3, max_length=30)
    description: Optional[str] = Field(default=None, max_length=500)
    discount_type: DiscountType
    discount_value: float = Field(default=0.0, ge=0)
    min_order_total: float = Field(default=0.0, ge=0)
    max_discount: Optional[float] = Field(default=None, gt=0)
    usage_limit: Optional[int] = Field(default=None, ge=1)
    per_customer_limit: int = Field(default=1, ge=1)
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_active: bool = True


class PromoCodeCreateAdmin(PromoCodeBase):
    """Admin can create platform-wide (vendor_id=None) or vendor-scoped codes."""
    vendor_id: Optional[str] = None


class PromoCodeCreateVendor(PromoCodeBase):
    """Vendors can only create codes for their own vendor (server injects vendor_id)."""


class PromoCodeUpdate(BaseModel):
    code: Optional[str] = Field(default=None, min_length=3, max_length=30)
    description: Optional[str] = Field(default=None, max_length=500)
    discount_type: Optional[DiscountType] = None
    discount_value: Optional[float] = Field(default=None, ge=0)
    min_order_total: Optional[float] = Field(default=None, ge=0)
    max_discount: Optional[float] = Field(default=None, gt=0)
    usage_limit: Optional[int] = Field(default=None, ge=1)
    per_customer_limit: Optional[int] = Field(default=None, ge=1)
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_active: Optional[bool] = None


class PromoCodeOut(PromoCodeBase):
    id: str
    vendor_id: Optional[str] = None
    times_used: int
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class PromoValidateRequest(BaseModel):
    code: str
    phone: Optional[str] = None
    subtotal: float = Field(ge=0)
    # Optional: the vendors currently in the cart, so vendor-scoped promos
    # can be validated client-side preview too.
    vendor_ids: Optional[list[str]] = None


class PromoValidateOut(BaseModel):
    valid: bool
    code: str
    discount_amount: float = 0.0
    message: str
    discount_type: Optional[DiscountType] = None
    vendor_id: Optional[str] = None