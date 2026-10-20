import re
from typing import Optional

from beanie import PydanticObjectId

from app.models.category import Category


def slugify(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[-\s]+", "-", text).strip("-")


async def create_category(data: dict) -> Category:
    if not data.get("slug"):
        data["slug"] = slugify(data["name"])
    cat = Category(**data)
    await cat.insert()
    return cat


async def list_categories(active_only: bool = False) -> list[Category]:
    query = Category.find()
    if active_only:
        query = query.find(Category.is_active == True)  # noqa: E712
    return await query.sort(+Category.display_order).to_list()


async def get_category(cat_id: str) -> Optional[Category]:
    try:
        return await Category.get(PydanticObjectId(cat_id))
    except Exception:
        return None


async def get_by_slug(slug: str) -> Optional[Category]:
    return await Category.find_one(Category.slug == slug)


async def update_category(cat: Category, data: dict) -> Category:
    for k, v in data.items():
        if v is not None:
            setattr(cat, k, v)
    await cat.save()
    return cat


async def delete_category(cat: Category) -> None:
    await cat.delete()