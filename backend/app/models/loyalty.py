from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field


class LoyaltyReason(str, Enum):
    EARNED_ORDER = "earned_order"
    REDEEMED_ORDER = "redeemed_order"
    ADMIN_ADJUSTMENT = "admin_adjustment"
    REFUND_REVERSAL = "refund_reversal"


class LoyaltyTransaction(Document):
    customer_id: Indexed(PydanticObjectId)  # type: ignore
    phone: Indexed(str)  # type: ignore
    points: int  # positive = earned, negative = redeemed
    reason: LoyaltyReason
    order_id: Optional[PydanticObjectId] = None
    order_reference: Optional[str] = None
    note: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "loyalty_transactions"