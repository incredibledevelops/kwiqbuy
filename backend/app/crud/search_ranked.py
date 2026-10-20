import logging
import math
from typing import Optional

from app.core.cache import cache
from app.core.config import settings
from app.crud import category as category_crud
from app.crud import product as product_crud
from app.crud import vendor as vendor_crud
from app.models.order import Order, OrderStatus

logger = logging.getLogger(__name__)


async def _popularity_map(product_ids: list[str]) -> dict[str, int]:
    if not product_ids:
        return {}

    cache_key = "search:popularity:v1"
    cached = await cache.get(cache_key)
    wanted = set(product_ids)
    if cached and isinstance(cached, dict):
        return {k: v for k, v in cached.items() if k in wanted}

    orders = await Order.find(
        {"status": {"$nin": [OrderStatus.CANCELLED.value, OrderStatus.FAILED.value]}}
    ).to_list()
    counts: dict[str, int] = {}
    for o in orders:
        for vo in o.vendor_orders:
            for item in vo.items:
                if item.product_id:
                    k = str(item.product_id)
                    counts[k] = counts.get(k, 0) + int(item.quantity or 1)

    await cache.set(cache_key, counts, ttl=settings.SEARCH_CACHE_TTL_SECONDS)
    return {k: v for k, v in counts.items() if k in wanted}


def _score_product(p, term: str, popularity: int) -> float:
    term_lower = term.lower().strip()
    if not term_lower:
        return 0.0

    name = (p.name or "").lower()
    desc = (p.description or "").lower()
    tags = [t.lower() for t in (p.tags or [])]
    brand = (p.brand or "").lower()

    score = 0.0
    if name == term_lower:
        score += 10
    if name.startswith(term_lower):
        score += 5
    if term_lower in name:
        score += 3
    if any(term_lower in t for t in tags):
        score += 2
    if term_lower in desc:
        score += 1
    if term_lower in brand:
        score += 1.5

    score += math.log1p(popularity) * 1.5
    score += float(p.average_rating or 0) * 0.5
    return score


async def search_products_ranked(
    *,
    term: str,
    vendor_category: Optional[str] = None,
    category_id: Optional[str] = None,
    available_only: bool = True,
    limit: int = 30,
) -> list[dict]:
    term = (term or "").strip()
    if not term:
        return []

    products = await product_crud.list_products(
        vendor_category=vendor_category,
        category_id=category_id,
        available_only=available_only,
        search=term,
        limit=max(limit * 5, 100),
    )
    if not products:
        return []

    pop_map = await _popularity_map([str(p.id) for p in products])

    vendor_names: dict[str, tuple[str, str]] = {}
    cat_names: dict[str, str] = {}

    scored = []
    for p in products:
        v_id = str(p.vendor_id)
        if v_id not in vendor_names:
            v = await vendor_crud.get_by_id(v_id)
            vendor_names[v_id] = (
                v.business_name if v else None,
                v.business_category.value if v else None,
            )
        c_id = str(p.category_id)
        if c_id not in cat_names:
            c = await category_crud.get_category(c_id)
            cat_names[c_id] = c.name if c else None

        pop = pop_map.get(str(p.id), 0)
        s = _score_product(p, term, pop)
        if s <= 0:
            continue

        scored.append({
            "product": p,
            "score": s,
            "vendor_name": vendor_names[v_id][0],
            "vendor_category": vendor_names[v_id][1],
            "category_name": cat_names[c_id],
            "popularity": pop,
        })

    scored.sort(key=lambda r: r["score"], reverse=True)
    return scored[:limit]
