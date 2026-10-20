from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.models.rider_earning import RiderEarningStatus


class RiderEarningOut(BaseModel):
    id: str
    order_id: str
    order_reference: str
    delivery_fee: float
    platform_cut: float
    rider_amount: float
    status: RiderEarningStatus
    earned_at: Optional[datetime] = None
    paid_out_at: Optional[datetime] = None
    created_at: datetime


class RiderEarningsSummaryOut(BaseModel):
    total_earned: float
    total_paid_out: float
    pending: float
    available: float
    rows: List[dict] = []
