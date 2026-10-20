"""
Review disputes.

Vendors can flag a review as unfair/false. Admin reviews the dispute
and either upholds it (hides the review) or rejects it (review stays).
Vendors cannot delete reviews themselves.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


class DisputeStatus(str, Enum):
    OPEN = "open"
    UPHELD = "upheld"        # admin agreed with vendor → review hidden
    REJECTED = "rejected"    # admin sided with review → review stays
    WITHDRAWN = "withdrawn"  # vendor withdrew


class ReviewDispute(Document):
    review_id: Indexed(PydanticObjectId)  # type: ignore
    vendor_id: Indexed(PydanticObjectId)  # type: ignore
    order_reference: str

    reason: str                                  # vendor's argument
    status: DisputeStatus = DisputeStatus.OPEN

    reviewed_by: Optional[str] = None            # admin user id
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None           # admin's explanation

    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)

    class Settings:
        name = "review_disputes"
        indexes = [
            "review_id",
            "vendor_id",
            "status",
            "created_at",
        ]
