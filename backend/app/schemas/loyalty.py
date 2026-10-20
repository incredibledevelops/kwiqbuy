from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.models.loyalty import LoyaltyReason


class LoyaltyBalanceOut(BaseModel):
    phone: str
    full_name: Optional[str] = None
    points: int
    lifetime_points_earned: int
    lifetime_points_redeemed: int
    cash_value: float          # points × rate
    min_redeem_points: int
    # Rate (GH₵ per point) applied by the server. Clients MUST use this to
    # preview redemption amounts so their totals match the server's.
    points_to_cash_rate: float = 0.01


class LoyaltyTransactionOut(BaseModel):
    id: str
    points: int
    reason: LoyaltyReason
    order_reference: Optional[str] = None
    note: Optional[str] = None
    created_at: datetime


class LoyaltyHistoryOut(BaseModel):
    balance: LoyaltyBalanceOut
    transactions: List[LoyaltyTransactionOut]


class LoyaltyRedeemRequest(BaseModel):
    phone: str
    points: int


class LoyaltyAdjustRequest(BaseModel):
    """Admin-only manual adjustment."""
    phone: str
    points: int
    note: Optional[str] = None