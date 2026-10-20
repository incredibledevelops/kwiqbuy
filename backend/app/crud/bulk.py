"""
Bulk operations: CSV product import, bulk status changes.
"""
import csv
import io
import logging
from typing import Optional

from beanie import PydanticObjectId

from app.crud import category as category_crud
from app.crud import product as product_crud
from app.models.product import Product, ProductType, ProductVariant, VariantOption
from app.models.vendor import Vendor

logger = logging.getLogger(__name__)


class BulkError(Exception):
    pass


async def import_products_csv(
    vendor: Vendor,
    csv_bytes: bytes,
    *,
    max_rows: int = 1000,
) -> dict:
    """
    Import products from a CSV.

    Required columns: name, price, category_slug
    Optional: description, tags (comma-separated), image_url, stock_count,
              variant_option_1, variant_value_1_1,variant_value_1_2 (etc.)

    Returns:
        {"created": int, "skipped": int, "errors": [str]}
    """
    text = csv_bytes.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))

    if reader.fieldnames is None:
        raise BulkError("CSV has no header row")

    required = {"name", "price", "category_slug"}
    missing = required - set(reader.fieldnames)
    if missing:
        raise BulkError(f"CSV missing required columns: {sorted(missing)}")

    created = 0
    skipped = 0
    errors: list[str] = []

    for row_num, row in enumerate(reader, start=2):
        if row_num - 1 > max_rows:
            errors.append(f"Row {row_num}: exceeds MAX_CSV_IMPORT_ROWS")
            break

        try:
            name = (row.get("name") or "").strip()
            price_raw = (row.get("price") or "").strip()
            cat_slug = (row.get("category_slug") or "").strip()

            if not name or not price_raw or not cat_slug:
                errors.append(f"Row {row_num}: missing name/price/category_slug")
                skipped += 1
                continue

            price = float(price_raw)
            cat = await category_crud.get_by_slug(cat_slug)
            if not cat:
                errors.append(f"Row {row_num}: unknown category '{cat_slug}'")
                skipped += 1
                continue

            slug = product_crud.slugify(name)
            if await product_crud.get_by_slug(slug):
                skipped += 1
                continue

            tags = [
                t.strip() for t in (row.get("tags") or "").split(",") if t.strip()
            ]

            doc = {
                "name": name,
                "slug": slug,
                "description": (row.get("description") or "").strip() or None,
                "price": price,
                "category_id": str(cat.id),
                "image_url": (row.get("image_url") or "").strip() or None,
                "tags": tags,
                "is_available": True,
                "product_type": ProductType.SIMPLE,
                "stock_count": None,
                "display_order": 0,
            }
            sc_raw = (row.get("stock_count") or "").strip()
            if sc_raw:
                doc["stock_count"] = int(sc_raw)

            await product_crud.create_product(str(vendor.id), doc)
            created += 1
        except Exception as e:
            errors.append(f"Row {row_num}: {type(e).__name__}: {e}")
            skipped += 1

    return {"created": created, "skipped": skipped, "errors": errors}


async def bulk_set_product_availability(
    vendor_id: str,
    product_ids: list[str],
    is_available: bool,
) -> dict:
    updated = 0
    errors: list[str] = []
    try:
        vid = PydanticObjectId(vendor_id)
    except Exception:
        raise BulkError("Invalid vendor id")

    for pid in product_ids:
        try:
            p = await Product.get(PydanticObjectId(pid))
            if not p or p.vendor_id != vid:
                errors.append(f"{pid}: not found or not yours")
                continue
            p.is_available = is_available
            await p.save()
            updated += 1
        except Exception as e:
            errors.append(f"{pid}: {e}")
    return {"updated": updated, "errors": errors}


async def bulk_delete_products(
    vendor_id: str, product_ids: list[str]
) -> dict:
    deleted = 0
    errors: list[str] = []
    try:
        vid = PydanticObjectId(vendor_id)
    except Exception:
        raise BulkError("Invalid vendor id")

    for pid in product_ids:
        try:
            p = await Product.get(PydanticObjectId(pid))
            if not p or p.vendor_id != vid:
                errors.append(f"{pid}: not found or not yours")
                continue
            await p.delete()
            deleted += 1
        except Exception as e:
            errors.append(f"{pid}: {e}")
    return {"deleted": deleted, "errors": errors}
