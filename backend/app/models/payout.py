from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


class PayoutStatus(str, Enum):
    REQUESTED = "requested"
    PROCESSING = "processing"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PayoutMethod(str, Enum):
    PAYSTACK_TRANSFER = "paystack_transfer"
    MANUAL = "manual"


class VendorPayout(Document):
    vendor_id: Indexed(PydanticObjectId)  # type: ignore
    vendor_name: str
    gross_sales: float = Field(ge=0)
    platform_fees: float = Field(ge=0)
    net_payout: float = Field(ge=0)
    currency: str = "GHS"
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    vendor_order_ids: list[PydanticObjectId] = Field(default_factory=list)
    status: PayoutStatus = PayoutStatus.REQUESTED
    method: PayoutMethod = PayoutMethod.PAYSTACK_TRANSFER
    paystack_transfer_code: Optional[str] = None
    paystack_transfer_reference: Optional[str] = None
    recipient_code: Optional[str] = None
    failure_reason: Optional[str] = None
    requested_by: Optional[str] = None
    processed_by: Optional[str] = None
    created_at: datetime = Field(default_factory=_now)
    processed_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None

    class Settings:
        name = "vendor_payouts"
        indexes = ["vendor_id", "status", "created_at"]
