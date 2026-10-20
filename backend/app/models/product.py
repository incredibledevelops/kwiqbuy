from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from beanie import Document, Indexed, PydanticObjectId
from pydantic import BaseModel, Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ProductType(str, Enum):
    SIMPLE = "simple"
    VARIABLE = "variable"
    DIGITAL = "digital"


class VariantOption(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    values: List[str] = Field(min_length=1, max_length=30)


class ProductVariant(BaseModel):
    sku: Optional[str] = Field(default=None, max_length=64)
    selections: dict[str, str] = Field(default_factory=dict)
    price: float = Field(ge=0)
    stock_count: Optional[int] = Field(default=None, ge=0)  # aggregated across warehouses
    image_url: Optional[str] = None
    is_available: bool = True


class Product(Document):
    vendor_id: Indexed(PydanticObjectId)  # type: ignore

    name: str
    slug: Indexed(str, unique=True)  # type: ignore
    description: Optional[str] = None
    price: float = Field(ge=0)
    category_id: Indexed(PydanticObjectId)  # type: ignore

    product_type: ProductType = ProductType.SIMPLE

    image_url: Optional[str] = None
    image_urls: List[str] = Field(default_factory=list)

    tags: List[str] = Field(default_factory=list)
    brand: Optional[str] = None
    weight_grams: Optional[int] = Field(default=None, ge=0)

    is_available: bool = True

    # Simple products only
    stock_count: Optional[int] = Field(default=None, ge=0)
    low_stock_threshold: int = Field(default=5, ge=0)

    # Variable products
    variant_options: List[VariantOption] = Field(default_factory=list)
    variants: List[ProductVariant] = Field(default_factory=list)

    # Warehouses this product is stocked at. Empty = single default warehouse.
    warehouse_ids: List[PydanticObjectId] = Field(default_factory=list)

    display_order: int = 0
    average_rating: float = 0.0
    total_reviews: int = 0
    popularity_score: float = 0.0  # updated by search ranking cache

    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)

    class Settings:
        name = "products"
        indexes = [
            "slug",
            "vendor_id",
            "category_id",
            "is_available",
            "product_type",
        ]
