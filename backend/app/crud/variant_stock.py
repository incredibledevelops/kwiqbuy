"""
Variant × warehouse stock CRUD.
"""
from datetime import datetime, timezone

from beanie import PydanticObjectId

from app.models.variant_stock import VariantStock


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def upsert(
    *,
    product_id: PydanticObjectId,
    vendor_id: PydanticObjectId,
    variant_sku: str,
    warehouse_id: PydanticObjectId,
    stock_count: int,
    low_stock_threshold: int = 5,
    session=None,
) -> VariantStock:
    existing = await VariantStock.find_one(
        VariantStock.product_id == product_id,
        VariantStock.variant_sku == variant_sku,
        VariantStock.warehouse_id == warehouse_id,
        session=session,
    )
    if existing:
        existing.stock_count = max(0, stock_count)
        existing.is_available = existing.stock_count > 0
        existing.low_stock_threshold = low_stock_threshold
        existing.updated_at = _now()
        await existing.save(session=session)
        return existing

    row = VariantStock(
        product_id=product_id,
        vendor_id=vendor_id,
        variant_sku=variant_sku,
        warehouse_id=warehouse_id,
        stock_count=max(0, stock_count),
        is_available=stock_count > 0,
        low_stock_threshold=low_stock_threshold,
    )
    await row.insert(session=session)
    return row


async def list_for_product(product_id: str) -> list[VariantStock]:
    try:
        pid = PydanticObjectId(product_id)
    except Exception:
        return []
    return await VariantStock.find(VariantStock.product_id == pid).to_list()


async def list_for_warehouse(warehouse_id: str) -> list[VariantStock]:
    try:
        wid = PydanticObjectId(warehouse_id)
    except Exception:
        return []
    return await VariantStock.find(VariantStock.warehouse_id == wid).to_list()


async def decrement_atomic(
    *,
    product_id: PydanticObjectId,
    variant_sku: str,
    warehouse_id: PydanticObjectId,
    quantity: int,
    session=None,
) -> bool:
    row = await VariantStock.find_one(
        VariantStock.product_id == product_id,
        VariantStock.variant_sku == variant_sku,
        VariantStock.warehouse_id == warehouse_id,
        session=session,
    )
    if not row:
        return False
    if row.stock_count < quantity:
        return False
    row.stock_count -= quantity
    if row.stock_count == 0:
        row.is_available = False
    row.updated_at = _now()
    await row.save(session=session)
    return True


async def increment(
    *,
    product_id: PydanticObjectId,
    variant_sku: str,
    warehouse_id: PydanticObjectId,
    quantity: int,
    session=None,
) -> None:
    row = await VariantStock.find_one(
        VariantStock.product_id == product_id,
        VariantStock.variant_sku == variant_sku,
        VariantStock.warehouse_id == warehouse_id,
        session=session,
    )
    if not row:
        return
    row.stock_count += quantity
    row.is_available = True
    row.updated_at = _now()
    await row.save(session=session)
