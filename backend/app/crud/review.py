from datetime import datetime, timezone
from typing import Optional

from beanie import PydanticObjectId

from app.models.order import Order, OrderStatus
from app.models.review import Review


async def create_review(data: dict, *, session=None) -> Review:
    review = Review(**data)
    await review.insert(session=session)
    return review


async def get_by_order_reference(reference: str) -> Optional[Review]:
    return await Review.find_one(Review.order_reference == reference)


async def get_by_id(review_id: str) -> Optional[Review]:
    try:
        return await Review.get(PydanticObjectId(review_id))
    except Exception:
        return None


async def list_reviews(
    published_only: bool = True,
    vendor_id: Optional[str] = None,
    limit: int = 100,
    skip: int = 0,
) -> list[Review]:
    query = Review.find()
    if published_only:
        query = query.find(Review.is_published == True)  # noqa: E712
    if vendor_id:
        query = query.find(Review.vendor_id == PydanticObjectId(vendor_id))
    return await query.sort(-Review.created_at).skip(skip).limit(limit).to_list()


async def list_featured(limit: int = 10) -> list[Review]:
    return (
        await Review.find(Review.is_featured == True)  # noqa: E712
        .sort(-Review.created_at)
        .limit(limit)
        .to_list()
    )


async def reviews_for_item(menu_item_id: PydanticObjectId, limit: int = 20) -> list[Review]:
    return (
        await Review.find(
            Review.is_published == True,  # noqa: E712
            {"item_ids": {"$in": [menu_item_id]}},
        )
        .sort(-Review.created_at)
        .limit(limit)
        .to_list()
    )


async def update_review(
    review: Review, is_published: Optional[bool] = None, is_featured: Optional[bool] = None,
) -> Review:
    if is_published is not None:
        review.is_published = is_published
    if is_featured is not None:
        review.is_featured = is_featured
    await review.save()
    return review


async def mark_dispute_flag(review: Review, has_open: bool) -> Review:
    review.has_open_dispute = has_open
    await review.save()
    return review


async def delete_review(review: Review) -> None:
    await review.delete()


async def summary(vendor_id: Optional[str] = None) -> dict:
    query = Review.find(Review.is_published == True)  # noqa: E712
    if vendor_id:
        query = query.find(Review.vendor_id == PydanticObjectId(vendor_id))
    reviews = await query.to_list()
    if not reviews:
        return {
            "average_rating": 0.0,
            "total_reviews": 0,
            "rating_breakdown": {str(i): 0 for i in range(1, 6)},
        }
    total = len(reviews)
    avg = round(sum(r.rating for r in reviews) / total, 2)
    breakdown = {str(i): 0 for i in range(1, 6)}
    for r in reviews:
        breakdown[str(r.rating)] += 1
    return {"average_rating": avg, "total_reviews": total, "rating_breakdown": breakdown}


async def ratings_for_items(item_ids: list[PydanticObjectId]) -> dict[str, dict]:
    if not item_ids:
        return {}
    id_strs = {str(i) for i in item_ids}
    reviews = await Review.find(
        Review.is_published == True,  # noqa: E712
        {"item_ids": {"$in": list(item_ids)}},
    ).to_list()
    tally: dict[str, dict] = {s: {"sum": 0, "count": 0} for s in id_strs}
    for r in reviews:
        for iid in r.item_ids:
            key = str(iid)
            if key in tally:
                tally[key]["sum"] += r.rating
                tally[key]["count"] += 1
    result: dict[str, dict] = {}
    for k, v in tally.items():
        if v["count"] > 0:
            result[k] = {"average": round(v["sum"] / v["count"], 2), "count": v["count"]}
    return result


async def ratings_for_products(product_ids: list[PydanticObjectId]) -> dict[str, dict]:
    return await ratings_for_items(product_ids)


async def order_is_eligible_for_review(order: Order) -> tuple[bool, str]:
    if order.status != OrderStatus.DELIVERED:
        return False, "You can only review delivered orders"
    existing = await get_by_order_reference(order.reference)
    if existing:
        return False, "You already reviewed this order"
    return True, ""
