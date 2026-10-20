"""
Per-warehouse stock for variants.

A "warehouse" is a lightweight representation of a vendor's pickup
location (or a sub-location). For v1 each vendor has one warehouse by
default, but the schema supports many.

Stock rule:
  - If a product has variants, stock is tracked per (product, variant_sku,
    warehouse_id).
  - If a product is simple (no variants), it uses Product.stock_count as
    before; this collection isn't consulted.
"""
from datetime import datetime, timezone
from typing import Optional

from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


class VariantStock(Document):
    product_id: Indexed(PydanticObjectId)  # type: ignore
    vendor_id: Indexed(PydanticObjectId)  # type: ignore
    variant_sku: Indexed(str)  # type: ignore
    warehouse_id: Indexed(PydanticObjectId)  # type: ignore

    stock_count: int = Field(ge=0)
    is_available: bool = True
    low_stock_threshold: int = Field(default=5, ge=0)

    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)

    class Settings:
        name = "variant_stocks"
        indexes = [
            "product_id",
            "variant_sku",
            "warehouse_id",
            # Compound unique: one row per (product, sku, warehouse)
            [("product_id", 1), ("variant_sku", 1), ("warehouse_id", 1)],
        ]
