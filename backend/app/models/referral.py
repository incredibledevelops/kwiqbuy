from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from beanie import Document, Indexed
from pydantic import Field


class ReferralStatus(str, Enum):
    PENDING = "pending"       # invited, referee hasn't ordered yet
    COMPLETED = "completed"   # referee placed first paid order
    EXPIRED = "expired"


class Referral(Document):
    """One referrer, one referee, one code."""

    code: Indexed(str, unique=True)  # type: ignore
    referrer_phone: Indexed(str)  # type: ignore
    referrer_name: str
    referee_phone: Optional[str] = None
    referee_name: Optional[str] = None

    status: ReferralStatus = ReferralStatus.PENDING

    # Discounts given
    referrer_reward: float = 10.0
    referee_reward: float = 10.0
    reward_currency: str = "GHS"

    # When completed
    completed_at: Optional[datetime] = None
    triggering_order_reference: Optional[str] = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "referrals"
        indexes = ["code", "referrer_phone"]