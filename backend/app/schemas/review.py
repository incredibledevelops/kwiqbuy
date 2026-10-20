from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    order_reference: str
    phone: str
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=2000)
    photo_urls: List[str] = Field(default_factory=list)
    # If omitted, the review applies to the whole order (all vendors).
    # If set, it's a per-vendor review.
    vendor_id: Optional[str] = None


class ReviewModerateIn(BaseModel):
    is_published: Optional[bool] = None
    is_featured: Optional[bool] = None


class ReviewOut(BaseModel):
    id: str
    order_reference: str
    vendor_id: Optional[str] = None
    vendor_name: Optional[str] = None
    rating: int
    comment: Optional[str] = None
    photo_urls: List[str] = Field(default_factory=list)
    is_published: bool
    is_featured: bool
    customer_name: Optional[str] = None
    created_at: datetime


class ReviewSummary(BaseModel):
    average_rating: float
    total_reviews: int
    rating_breakdown: dict


class MenuItemRatingOut(BaseModel):
    menu_item_id: str
    average_rating: float
    total_reviews: int