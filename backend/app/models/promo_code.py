from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


class DiscountType(str, Enum):
    PERCENT = "percent"
    FIXED = "fixed"
    FREE_DELIVERY = "free_delivery"


class PromoCode(Document):
    code: Indexed(str, unique=True)  # type: ignore
    description: Optional[str] = None
    vendor_id: Optional[PydanticObjectId] = None
    discount_type: DiscountType
    discount_value: float = Field(ge=0, default=0.0)
    min_order_total: float = Field(ge=0, default=0.0)
    max_discount: Optional[float] = None
    usage_limit: Optional[int] = None
    per_customer_limit: int = 1
    times_used: int = 0
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_active: bool = True
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)

    class Settings:
        name = "promo_codes"
        indexes = ["code", "vendor_id", "is_active"]
