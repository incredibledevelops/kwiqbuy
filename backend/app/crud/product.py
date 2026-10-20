import logging
import re
from typing import Optional

from beanie import PydanticObjectId

from app.models.product import Product, ProductType

logger = logging.getLogger(__name__)


def slugify(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[-\s]+", "-", text).strip("-")


def _escape_regex(s: str) -> str:
    return re.escape(s)


async def unique_slug(base: str, exclude_id: Optional[PydanticObjectId] = None) -> str:
    base_slug = slugify(base) or "product"
    slug = base_slug
    i = 2
    while True:
        existing = await Product.find_one(Product.slug == slug)
        if not existing or (exclude_id and existing.id == exclude_id):
            return slug
        slug = f"{base_slug}-{i}"
        i += 1
        if i > 1000:
            raise RuntimeError("could not allocate unique product slug")


async def create_product(vendor_id: str, data: dict) -> Product:
    if isinstance(data.get("category_id"), str):
        data["category_id"] = PydanticObjectId(data["category_id"])
    data["vendor_id"] = PydanticObjectId(vendor_id)
    if not data.get("slug"):
        data["slug"] = await unique_slug(data["name"])

    # Normalize variant_options and variants to model instances
    from app.models.product import VariantOption, ProductVariant
    if data.get("variant_options"):
        data["variant_options"] = [
            o if isinstance(o, VariantOption) else VariantOption(**o)
            for o in data["variant_options"]
        ]
    if data.get("variants"):
        data["variants"] = [
            v if isinstance(v, ProductVariant) else ProductVariant(**v)
            for v in data["variants"]
        ]

    item = Product(**data)
    await item.insert()
    return item


async def get_product(product_id: str) -> Optional[Product]:
    try:
        return await Product.get(PydanticObjectId(product_id))
    except Exception:
        return None


async def get_by_slug(slug: str) -> Optional[Product]:
    return await Product.find_one(Product.slug == slug)


async def list_products(
    *,
    vendor_id: Optional[str] = None,
    category_id: Optional[str] = None,
    vendor_category: Optional[str] = None,
    available_only: bool = False,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 500,
) -> list[Product]:
    query = Product.find()
    if vendor_id:
        query = query.find(Product.vendor_id == PydanticObjectId(vendor_id))
    if category_id:
        query = query.find(Product.category_id == PydanticObjectId(category_id))
    if available_only:
        query = query.find(Product.is_available == True)  # noqa: E712

    # When filtering by vendor category, look up vendor IDs first
    if vendor_category:
        from app.models.vendor import Vendor, VendorCategory
        vendors = await Vendor.find(
            Vendor.business_category == VendorCategory(vendor_category)
        ).to_list()
        vendor_ids = [v.id for v in vendors]
        if not vendor_ids:
            return []
        query = query.find({"vendor_id": {"$in": vendor_ids}})

    if search:
        rx = _escape_regex(search.strip())
        query = query.find({
            "$or": [
                {"name": {"$regex": rx, "$options": "i"}},
                {"description": {"$regex": rx, "$options": "i"}},
                {"tags": {"$regex": rx, "$options": "i"}},
                {"brand": {"$regex": rx, "$options": "i"}},
            ]
        })

    return (
        await query.sort(+Product.display_order).skip(skip).limit(limit).to_list()
    )


async def update_product(product: Product, data: dict) -> Product:
    from app.models.product import VariantOption, ProductVariant
    for k, v in data.items():
        if v is None and k not in {"stock_count"}:
            continue
        if k == "category_id" and v is not None:
            product.category_id = PydanticObjectId(v)
        elif k == "slug" and v:
            product.slug = await unique_slug(v, exclude_id=product.id)
        elif k == "variant_options":
            product.variant_options = [
                o if isinstance(o, VariantOption) else VariantOption(**o)
                for o in v
            ]
        elif k == "variants":
            product.variants = [
                vi if isinstance(vi, ProductVariant) else ProductVariant(**vi)
                for vi in v
            ]
        elif hasattr(product, k):
            setattr(product, k, v)
    await product.save()
    return product


async def delete_product(product: Product) -> None:
    await product.delete()


async def toggle_stock(product: Product, is_available: bool) -> Product:
    product.is_available = is_available
    await product.save()
    return product


async def low_stock_items(
    *,
    vendor_id: Optional[str] = None,
    threshold: int = 5,
) -> list[dict]:
    query = Product.find()
    if vendor_id:
        query = query.find(Product.vendor_id == PydanticObjectId(vendor_id))
    items = await query.to_list()
    low = []
    for i in items:
        if i.product_type == ProductType.SIMPLE and i.stock_count is not None:
            if i.stock_count <= threshold:
                low.append({
                    "id": str(i.id),
                    "vendor_id": str(i.vendor_id),
                    "name": i.name,
                    "stock_count": i.stock_count,
                    "low_stock_threshold": i.low_stock_threshold,
                    "is_available": i.is_available,
                })
        elif i.product_type == ProductType.VARIABLE:
            for v in i.variants:
                if v.stock_count is not None and v.stock_count <= threshold:
                    low.append({
                        "id": str(i.id),
                        "vendor_id": str(i.vendor_id),
                        "name": f"{i.name} — {v.sku or 'variant'}",
                        "stock_count": v.stock_count,
                        "low_stock_threshold": i.low_stock_threshold,
                        "is_available": i.is_available,
                    })
    low.sort(key=lambda x: x["stock_count"])
    return low


# ---------- Variant-aware stock ----------

async def decrement_stock_atomic(
    product_id: PydanticObjectId,
    quantity: int,
    *,
    variant_sku: Optional[str] = None,
    session=None,
) -> bool:
    """
    Atomic-enough decrement for both simple and variable products.

    If variant_sku is provided, decrement that variant's stock.
    Otherwise, decrement the base product's stock.
    """
    doc = await Product.get(product_id, session=session)
    if not doc:
        return False

    # Variable product with a specific SKU
    if variant_sku:
        target = next(
            (v for v in doc.variants if v.sku == variant_sku), None
        )
        if target is None:
            return False
        if target.stock_count is None:
            return True  # unlimited
        if target.stock_count < quantity:
            return False
        target.stock_count -= quantity
        if target.stock_count == 0:
            target.is_available = False

        # If all variants are exhausted, mark the whole product unavailable
        all_out = all(
            (v.stock_count == 0) for v in doc.variants if v.stock_count is not None
        ) and all(v.stock_count is not None for v in doc.variants)
        if all_out:
            doc.is_available = False

        await doc.save(session=session)
        return True

    # Simple product
    if doc.stock_count is None:
        return True
    if doc.stock_count < quantity:
        return False
    doc.stock_count -= quantity
    if doc.stock_count == 0:
        doc.is_available = False
    await doc.save(session=session)
    return True


async def increment_stock(
    product_id: PydanticObjectId,
    quantity: int,
    *,
    variant_sku: Optional[str] = None,
    session=None,
) -> None:
    doc = await Product.get(product_id, session=session)
    if not doc:
        return

    if variant_sku:
        target = next((v for v in doc.variants if v.sku == variant_sku), None)
        if target and target.stock_count is not None:
            target.stock_count += quantity
            target.is_available = True
            doc.is_available = True
            await doc.save(session=session)
        return

    if doc.stock_count is None:
        return
    doc.stock_count += quantity
    if doc.stock_count > 0:
        doc.is_available = True
    await doc.save(session=session)


async def ratings_map_for(products: list[Product]) -> dict[str, dict]:
    from app.crud import review as review_crud
    return await review_crud.ratings_for_products([p.id for p in products])
