import logging
from typing import Optional

from fastapi import APIRouter, Query

from app.crud import category as category_crud
from app.crud import product as product_crud
from app.crud import search_ranked as ranked_crud
from app.crud import vendor as vendor_crud
from app.schemas.search import (
    SearchCategoryOut,
    SearchMenuItemOut,
    SearchResultsOut,
    SearchSuggestOut,
    SearchSuggestionItem,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("", response_model=SearchResultsOut)
async def search(
    q: str = Query("", min_length=0, max_length=120),
    vendor_id: Optional[str] = Query(None),
    limit: int = Query(30, ge=1, le=100),
):
    term = q.strip()
    if not term:
        return SearchResultsOut(query=q, items=[], categories=[], suggestions=[], total=0)

    # Products (ranked)
    ranked = await ranked_crud.search_products_ranked(
        term=term,
        available_only=False,
        limit=limit,
    )
    products = [r["product"] for r in ranked]

    vendor_names = {}
    for p in products:
        if p.vendor_id not in vendor_names:
            v = await vendor_crud.get_by_id(str(p.vendor_id))
            vendor_names[p.vendor_id] = v.business_name if v else None

    cat_ids = {p.category_id for p in products}
    cat_map = {}
    for cid in cat_ids:
        c = await category_crud.get_category(str(cid))
        if c:
            cat_map[cid] = c

    items = [
        SearchMenuItemOut(
            id=str(p.id),
            name=p.name,
            slug=p.slug,
            description=p.description,
            price=p.price,
            image_url=p.image_url,
            is_available=p.is_available,
            average_rating=p.average_rating,
            total_reviews=p.total_reviews,
            category_name=(cat_map.get(p.category_id).name if cat_map.get(p.category_id) else None),
            category_slug=(cat_map.get(p.category_id).slug if cat_map.get(p.category_id) else None),
            vendor_id=str(p.vendor_id),
            vendor_name=vendor_names.get(p.vendor_id),
        )
        for p in products
    ]

    # Categories
    rx = term.lower()
    all_cats = await category_crud.list_categories(active_only=True)
    matched_cats = [
        c for c in all_cats
        if rx in c.name.lower() or rx in c.slug.lower()
    ][:5]

    categories = [
        SearchCategoryOut(id=str(c.id), name=c.name, slug=c.slug, image_url=c.image_url)
        for c in matched_cats
    ]

    suggestions = []
    for item in items[:5]:
        suggestions.append(
            SearchSuggestionItem(text=item.name, kind="item", slug=item.slug)
        )
    for c in categories[:3]:
        suggestions.append(
            SearchSuggestionItem(text=c.name, kind="category", slug=c.slug)
        )

    return SearchResultsOut(
        query=q,
        items=items,
        categories=categories,
        suggestions=suggestions,
        total=len(items),
    )


@router.get("/suggest", response_model=SearchSuggestOut)
async def suggest(
    q: str = Query(..., min_length=1, max_length=120),
    vendor_id: Optional[str] = Query(None),
):
    result = await search(q=q, vendor_id=vendor_id, limit=5)
    return SearchSuggestOut(query=q, suggestions=result.suggestions)