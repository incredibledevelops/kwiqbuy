from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_admin
from app.crud import builder as builder_crud
from app.models.builder_option import BuilderOption, BuilderOptionType
from app.schemas.builder import (
    BuilderGroupedOut,
    BuilderOptionCreate,
    BuilderOptionOut,
    BuilderOptionUpdate,
)

router = APIRouter(prefix="/builder", tags=["Builder"])


def _to_out(opt: BuilderOption) -> BuilderOptionOut:
    return BuilderOptionOut(
        id=str(opt.id),
        type=opt.type,
        name=opt.name,
        description=opt.description,
        price=opt.price,
        image_url=opt.image_url,
        is_default=opt.is_default,
        is_available=opt.is_available,
        display_order=opt.display_order,
        created_at=opt.created_at,
        updated_at=opt.updated_at,
    )


@router.get("/options", response_model=list[BuilderOptionOut])
async def list_options(
    type: BuilderOptionType | None = None, available_only: bool = False
):
    opts = await builder_crud.list_options(option_type=type, available_only=available_only)
    return [_to_out(o) for o in opts]


@router.get("/grouped", response_model=BuilderGroupedOut)
async def get_grouped():
    grouped = await builder_crud.get_grouped()
    return BuilderGroupedOut(
        bases=[_to_out(o) for o in grouped["bases"]],
        proteins=[_to_out(o) for o in grouped["proteins"]],
        sauces=[_to_out(o) for o in grouped["sauces"]],
        toppings=[_to_out(o) for o in grouped["toppings"]],
    )


@router.get("/options/{option_id}", response_model=BuilderOptionOut)
async def get_option(option_id: str):
    opt = await builder_crud.get_option(option_id)
    if not opt:
        raise HTTPException(404, "Builder option not found")
    return _to_out(opt)


@router.post(
    "/options",
    response_model=BuilderOptionOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_admin)],
)
async def create_option(payload: BuilderOptionCreate):
    opt = await builder_crud.create_option(payload.model_dump())
    return _to_out(opt)


@router.patch(
    "/options/{option_id}",
    response_model=BuilderOptionOut,
    dependencies=[Depends(get_current_admin)],
)
async def update_option(option_id: str, payload: BuilderOptionUpdate):
    opt = await builder_crud.get_option(option_id)
    if not opt:
        raise HTTPException(404, "Builder option not found")
    opt = await builder_crud.update_option(opt, payload.model_dump(exclude_unset=True))
    return _to_out(opt)


@router.delete(
    "/options/{option_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_current_admin)],
)
async def delete_option(option_id: str):
    opt = await builder_crud.get_option(option_id)
    if not opt:
        raise HTTPException(404, "Builder option not found")
    await builder_crud.delete_option(opt)