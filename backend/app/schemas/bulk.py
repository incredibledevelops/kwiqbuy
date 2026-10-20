from typing import List, Optional

from pydantic import BaseModel, Field


class BulkProductAvailabilityIn(BaseModel):
    product_ids: List[str] = Field(min_length=1, max_length=500)
    is_available: bool


class BulkProductDeleteIn(BaseModel):
    product_ids: List[str] = Field(min_length=1, max_length=500)


class BulkResultOut(BaseModel):
    updated: int = 0
    deleted: int = 0
    created: int = 0
    skipped: int = 0
    errors: List[str] = Field(default_factory=list)


class BulkOrderStatusIn(BaseModel):
    order_ids: List[str] = Field(min_length=1, max_length=200)
    status: str
    note: Optional[str] = None


class BulkVendorStatusIn(BaseModel):
    vendor_ids: List[str] = Field(min_length=1, max_length=200)
    status: str
    reason: Optional[str] = None
