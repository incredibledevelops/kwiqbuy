from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.referral import ReferralStatus


class ReferralCreate(BaseModel):
    referrer_phone: str
    referrer_name: str


class ReferralOut(BaseModel):
    id: str
    code: str
    referrer_phone: str
    referrer_name: str
    referee_phone: Optional[str] = None
    referee_name: Optional[str] = None
    status: ReferralStatus
    referrer_reward: float
    referee_reward: float
    reward_currency: str
    completed_at: Optional[datetime] = None
    triggering_order_reference: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ReferralApplyIn(BaseModel):
    code: str
    referee_phone: str
    referee_name: str


class ReferralApplyOut(BaseModel):
    success: bool
    message: str
    referral_code: Optional[str] = None
    discount_amount: float = 0.0


class ReferralSummary(BaseModel):
    total_referrals: int
    completed_referrals: int
    pending_referrals: int
    total_earned: float
    currency: str