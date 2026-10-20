from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_admin
from app.crud import category as category_crud
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryOut, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["Categories"])


def _to_out(c: Category) -> CategoryOut:
    return CategoryOut(
        id=str(c.id),
        name=c.name,
        slug=c.slug,
        description=c.description,
        image_url=c.image_url,
        display_order=c.display_order,
        is_active=c.is_active,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


@router.get("", response_model=list[CategoryOut])
async def list_categories(active_only: bool = False):
    cats = await category_crud.list_categories(active_only=active_only)
    return [_to_out(c) for c in cats]


@router.get("/{category_id}", response_model=CategoryOut)
async def get_category(category_id: str):
    cat = await category_crud.get_category(category_id)
    if not cat:
        raise HTTPException(404, "Category not found")
    return _to_out(cat)


@router.post(
    "",
    response_model=CategoryOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_admin)],
)
async def create_category(payload: CategoryCreate):
    if await category_crud.get_by_slug(
        payload.slug or category_crud.slugify(payload.name)
    ):
        raise HTTPException(409, "Category slug already exists")
    cat = await category_crud.create_category(payload.model_dump())
    return _to_out(cat)


@router.patch(
    "/{category_id}",
    response_model=CategoryOut,
    dependencies=[Depends(get_current_admin)],
)
async def update_category(category_id: str, payload: CategoryUpdate):
    cat = await category_crud.get_category(category_id)
    if not cat:
        raise HTTPException(404, "Category not found")
    cat = await category_crud.update_category(cat, payload.model_dump(exclude_unset=True))
    return _to_out(cat)


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_current_admin)],
)
async def delete_category(category_id: str):
    cat = await category_crud.get_category(category_id)
    if not cat:
        raise HTTPException(404, "Category not found")
    await category_crud.delete_category(cat)