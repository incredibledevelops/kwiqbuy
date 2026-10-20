from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import get_current_admin
from app.crud import order as order_crud
from app.crud import product as product_crud
from app.crud import review as review_crud
from app.crud import vendor as vendor_crud
from app.models.review import Review
from app.schemas.review import (
    ReviewCreate,
    ReviewModerateIn,
    ReviewOut,
    ReviewSummary,
)

router = APIRouter(prefix="/reviews", tags=["Reviews"])


def _to_out(r: Review) -> ReviewOut:
    return ReviewOut(
        id=str(r.id),
        order_reference=r.order_reference,
        vendor_id=str(r.vendor_id) if getattr(r, "vendor_id", None) else None,
        vendor_name=getattr(r, "vendor_name", None),
        rating=r.rating,
        comment=r.comment,
        photo_urls=r.photo_urls,
        is_published=r.is_published,
        is_featured=r.is_featured,
        customer_name=getattr(r, "customer_name", None),
        created_at=r.created_at,
    )


# ---------- Public ----------

@router.post("", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
async def submit_review(payload: ReviewCreate):
    order = await order_crud.get_order_by_reference(payload.order_reference)
    if not order:
        raise HTTPException(404, "Order not found")
    if order.customer.phone != payload.phone:
        raise HTTPException(403, "Phone does not match this order")

    eligible, msg = await review_crud.order_is_eligible_for_review(order)
    if not eligible:
        raise HTTPException(400, msg)

    product_ids = []
    vendor_name = None
    for vo in order.vendor_orders:
        if payload.vendor_id and str(vo.vendor_id) != payload.vendor_id:
            continue
        for item in vo.items:
            if item.product_id:
                product_ids.append(item.product_id)
        if payload.vendor_id:
            vendor_name = vo.vendor_name

    from beanie import PydanticObjectId
    vendor_oid = None
    if payload.vendor_id:
        try:
            vendor_oid = PydanticObjectId(payload.vendor_id)
        except Exception:
            raise HTTPException(400, "Invalid vendor_id")

    review = await review_crud.create_review({
        "order_id": order.id,
        "order_reference": order.reference,
        "customer_phone": payload.phone,
        "customer_name": order.customer.full_name,
        "vendor_id": vendor_oid,
        "vendor_name": vendor_name,
        "rating": payload.rating,
        "comment": payload.comment,
        "photo_urls": payload.photo_urls or [],
        "item_ids": product_ids,
    })
    return _to_out(review)


@router.get("/item-by-slug/{slug}", response_model=list[ReviewOut])
async def reviews_for_slug(
    slug: str, limit: int = Query(20, ge=1, le=100)
):
    item = await product_crud.get_by_slug(slug)
    if not item:
        raise HTTPException(404, "Product not found")
    reviews = await review_crud.reviews_for_item(item.id, limit=limit)
    return [_to_out(r) for r in reviews]


@router.get("/recent", response_model=list[ReviewOut])
async def recent_reviews(
    featured_only: bool = False,
    vendor_id: str | None = None,
    limit: int = Query(20, ge=1, le=100),
):
    reviews = await review_crud.list_reviews(
        published_only=True, vendor_id=vendor_id, limit=limit
    )
    if featured_only:
        reviews = [r for r in reviews if r.is_featured]
    return [_to_out(r) for r in reviews]


@router.get("/summary", response_model=ReviewSummary)
async def review_summary(vendor_id: str | None = None):
    return ReviewSummary(**await review_crud.summary(vendor_id=vendor_id))


# ---------- Admin ----------

@router.get("", response_model=list[ReviewOut], dependencies=[Depends(get_current_admin)])
async def list_all(
    published_only: bool = False,
    limit: int = Query(200, ge=1, le=500),
    skip: int = Query(0, ge=0),
):
    reviews = await review_crud.list_reviews(
        published_only=published_only, limit=limit, skip=skip
    )
    return [_to_out(r) for r in reviews]


@router.patch(
    "/{review_id}",
    response_model=ReviewOut,
    dependencies=[Depends(get_current_admin)],
)
async def moderate_review(review_id: str, payload: ReviewModerateIn):
    from beanie import PydanticObjectId
    try:
        oid = PydanticObjectId(review_id)
    except Exception:
        raise HTTPException(400, "Invalid review id")
    review = await Review.get(oid)
    if not review:
        raise HTTPException(404, "Review not found")
    review = await review_crud.update_review(
        review,
        is_published=payload.is_published,
        is_featured=payload.is_featured,
    )
    return _to_out(review)


@router.delete(
    "/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_current_admin)],
)
async def delete_review(review_id: str):
    from beanie import PydanticObjectId
    try:
        oid = PydanticObjectId(review_id)
    except Exception:
        raise HTTPException(400, "Invalid review id")
    review = await Review.get(oid)
    if not review:
        raise HTTPException(404, "Review not found")
    await review_crud.delete_review(review)