from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.review_dispute import DisputeStatus


class ReviewDisputeCreate(BaseModel):
    reason: str = Field(min_length=10, max_length=2000)


class ReviewDisputeResolveIn(BaseModel):
    status: DisputeStatus
    review_notes: Optional[str] = Field(default=None, max_length=1000)


class ReviewDisputeOut(BaseModel):
    id: str
    review_id: str
    vendor_id: str
    order_reference: str
    reason: str
    status: DisputeStatus
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ReviewDisputeListOut(BaseModel):
    items: list[ReviewDisputeOut]
    total: int
