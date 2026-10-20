from datetime import datetime, timezone
from typing import List, Optional

from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Review(Document):
    order_id: Indexed(PydanticObjectId)  # type: ignore
    order_reference: Indexed(str)  # type: ignore
    customer_phone: Indexed(str)  # type: ignore
    customer_name: Optional[str] = None

    vendor_id: Optional[PydanticObjectId] = None
    vendor_name: Optional[str] = None

    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None
    item_ids: List[PydanticObjectId] = Field(default_factory=list)
    photo_urls: List[str] = Field(default_factory=list)

    is_published: bool = True
    is_featured: bool = False
    has_open_dispute: bool = False

    created_at: datetime = Field(default_factory=_now)

    class Settings:
        name = "reviews"
        indexes = [
            "order_reference",
            "customer_phone",
            "vendor_id",
            "has_open_dispute",
        ]
