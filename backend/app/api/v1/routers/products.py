from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.core.cache import cache
from app.crud import category as category_crud
from app.crud import product as product_crud
from app.crud import vendor as vendor_crud
from app.models.product import Product
from app.schemas.product import ProductPublicOut

router = APIRouter(prefix="/products", tags=["Products"])


def _to_public(
    p: Product,
    vendor_name: Optional[str] = None,
    vendor_category: Optional[str] = None,
    category_name: Optional[str] = None,
) -> ProductPublicOut:
    return ProductPublicOut(
        id=str(p.id),
        vendor_id=str(p.vendor_id),
        vendor_name=vendor_name,
        vendor_category=vendor_category,
        name=p.name,
        slug=p.slug,
        description=p.description,
        price=p.price,
        category_id=str(p.category_id),
        category_name=category_name,
        product_type=p.product_type,
        image_url=p.image_url,
        tags=p.tags,
        brand=p.brand,
        is_available=p.is_available,
        variant_options=[
            {"name": o.name, "values": o.values} for o in p.variant_options
        ],
        variants=[
            {
                "sku": v.sku,
                "selections": v.selections,
                "price": v.price,
                "stock_count": v.stock_count,
                "image_url": v.image_url,
                "is_available": v.is_available,
            }
            for v in p.variants
        ],
        average_rating=p.average_rating,
        total_reviews=p.total_reviews,
    )


@router.get("", response_model=list[ProductPublicOut])
async def list_products(
    vendor_id: Optional[str] = Query(None),
    vendor_category: Optional[str] = Query(
        None, description="Filter by vendor category: food | retail"
    ),
    category_id: Optional[str] = Query(None),
    available_only: bool = False,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=500),
):
    if vendor_category and vendor_category not in ("food", "retail"):
        raise HTTPException(400, "vendor_category must be 'food' or 'retail'")

    products = await product_crud.list_products(
        vendor_id=vendor_id,
        vendor_category=vendor_category,
        category_id=category_id,
        available_only=available_only,
        search=search,
        skip=skip,
        limit=limit,
    )

    vendor_ids = {p.vendor_id for p in products}
    cat_ids = {p.category_id for p in products}
    vendors_by_id = {}
    cats_by_id = {}
    for vid in vendor_ids:
        v = await vendor_crud.get_by_id(str(vid))
        if v:
            vendors_by_id[vid] = (v.business_name, v.business_category.value)
    for cid in cat_ids:
        c = await category_crud.get_category(str(cid))
        if c:
            cats_by_id[cid] = c.name

    return [
        _to_public(
            p,
            vendor_name=(vendors_by_id.get(p.vendor_id) or (None, None))[0],
            vendor_category=(vendors_by_id.get(p.vendor_id) or (None, None))[1],
            category_name=cats_by_id.get(p.category_id),
        )
        for p in products
    ]


@router.get("/slug/{slug}", response_model=ProductPublicOut)
async def get_by_slug(slug: str):
    cache_key = f"products:slug:{slug}"

    async def build():
        p = await product_crud.get_by_slug(slug)
        if not p:
            return None
        v = await vendor_crud.get_by_id(str(p.vendor_id))
        c = await category_crud.get_category(str(p.category_id))
        return _to_public(
            p,
            vendor_name=v.business_name if v else None,
            vendor_category=v.business_category.value if v else None,
            category_name=c.name if c else None,
        ).model_dump()

    data = await cache.get_or_set(cache_key, build, ttl=60)
    if not data:
        raise HTTPException(404, "Product not found")
    return ProductPublicOut(**data)


@router.get("/{product_id}/related", response_model=list[ProductPublicOut])
async def get_related(
    product_id: str,
    limit: int = Query(4, ge=1, le=12),
):
    p = await product_crud.get_product(product_id)
    if not p:
        raise HTTPException(404, "Product not found")

    related = await product_crud.list_products(
        vendor_id=str(p.vendor_id),
        category_id=str(p.category_id),
        available_only=True,
        limit=limit + 1,
    )
    related = [r for r in related if r.id != p.id][:limit]

    v = await vendor_crud.get_by_id(str(p.vendor_id))
    return [
        _to_public(
            r,
            vendor_name=v.business_name if v else None,
            vendor_category=v.business_category.value if v else None,
        )
        for r in related
    ]


@router.get("/{product_id}", response_model=ProductPublicOut)
async def get_product(product_id: str):
    p = await product_crud.get_product(product_id)
    if not p:
        raise HTTPException(404, "Product not found")
    v = await vendor_crud.get_by_id(str(p.vendor_id))
    c = await category_crud.get_category(str(p.category_id))
    return _to_public(
        p,
        vendor_name=v.business_name if v else None,
        vendor_category=v.business_category.value if v else None,
        category_name=c.name if c else None,
    )
