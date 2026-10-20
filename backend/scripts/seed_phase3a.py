"""
Seed Phase 3a default data (subscription tiers).

Run after `python -m scripts.seed_data`:
    python -m scripts.seed_phase3a
"""
import asyncio

from app.core.database import close_db, init_db
from app.crud import subscription as sub_crud
from app.models import ALL_DOCUMENTS


DEFAULT_TIERS = [
    {
        "slug": "free",
        "name": "Free",
        "description": "Standard listing with default commission.",
        "monthly_price": 0.0,
        "commission_discount_pct": 0.0,
        "features": ["Standard listing", "Basic analytics"],
        "is_active": True,
        "display_order": 1,
    },
    {
        "slug": "growth",
        "name": "Growth",
        "description": "Priority listing and reduced commission.",
        "monthly_price": 99.0,
        "commission_discount_pct": 3.0,
        "features": [
            "Priority in search",
            "Reduced commission (−3%)",
            "Bulk product import",
            "Advanced analytics",
        ],
        "is_active": True,
        "display_order": 2,
    },
    {
        "slug": "enterprise",
        "name": "Enterprise",
        "description": "Highest visibility and lowest commission.",
        "monthly_price": 299.0,
        "commission_discount_pct": 8.0,
        "features": [
            "Everything in Growth",
            "Lowest commission (−8%)",
            "Dedicated account manager",
            "Custom branding",
            "API access",
        ],
        "is_active": True,
        "display_order": 3,
    },
]


async def seed():
    await init_db(ALL_DOCUMENTS)
    print("Seeding subscription tiers...")
    for t in DEFAULT_TIERS:
        existing = await sub_crud.get_tier_by_slug(t["slug"])
        if existing:
            print(f"  skip {t['slug']}")
            continue
        await sub_crud.create_tier(t)
        print(f"  OK {t['slug']} ({t['monthly_price']} GHS/mo, -{t['commission_discount_pct']}%)")
    await close_db()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(seed())