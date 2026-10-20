"""
Rider earnings ledger.

Each delivered order produces exactly one RiderEarning row.
Amounts:
    delivery_fee          — what the customer paid for delivery
    platform_cut          — what KwiqBuy keeps
    rider_amount          — what the rider gets (delivery_fee − platform_cut)
    rider_amount_paid_out — set when a payout job runs; else 0

Sign convention is positive; refunds are out of scope for v1.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


class RiderEarningStatus(str, Enum):
    PENDING = "pending"      # order created, not yet delivered
    EARNED = "earned"        # delivered — rider is owed this
    PAID_OUT = "paid_out"    # included in a payout
    VOIDED = "voided"        # order cancelled before delivery


class RiderEarning(Document):
    rider_id: Indexed(PydanticObjectId)  # type: ignore
    order_id: Indexed(PydanticObjectId)  # type: ignore
    order_reference: str

    delivery_fee: float
    platform_cut: float
    rider_amount: float

    status: RiderEarningStatus = RiderEarningStatus.PENDING
    payout_id: Optional[PydanticObjectId] = None

    earned_at: Optional[datetime] = None
    paid_out_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)

    class Settings:
        name = "rider_earnings"
        indexes = [
            "rider_id",
            "order_id",
            "status",
            "created_at",
        ]
