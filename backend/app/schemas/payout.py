from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.payout import PayoutMethod, PayoutStatus


class VendorPayoutOut(BaseModel):
    id: str
    vendor_id: str
    vendor_name: str
    gross_sales: float
    platform_fees: float
    net_payout: float
    currency: str
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    order_count: int = 0
    status: PayoutStatus
    method: PayoutMethod
    paystack_transfer_code: Optional[str] = None
    paystack_transfer_reference: Optional[str] = None
    failure_reason: Optional[str] = None
    requested_by: Optional[str] = None
    processed_by: Optional[str] = None
    created_at: datetime
    processed_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None


class VendorPayoutRequestIn(BaseModel):
    """Vendor-initiated payout request."""
    # Currently no fields required, but reserves room for a note or a
    # specific period. Kept empty intentionally.
    note: Optional[str] = Field(default=None, max_length=500)


class AdminPayoutCreateIn(BaseModel):
    vendor_id: str
    method: PayoutMethod = PayoutMethod.PAYSTACK_TRANSFER
    note: Optional[str] = Field(default=None, max_length=500)


class VendorPayoutFailIn(BaseModel):
    reason: str = Field(min_length=4, max_length=500)


class VendorPayoutCancelIn(BaseModel):
    reason: Optional[str] = Field(default=None, max_length=500)


class VendorPayoutListOut(BaseModel):
    items: list[VendorPayoutOut]
    total: int
    # Convenience: sum of net_payout across all returned items
    total_net: float = 0.0