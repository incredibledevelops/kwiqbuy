from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import get_current_admin
from app.crud import promo_code as promo_crud
from app.models.promo_code import PromoCode
from app.schemas.promo_code import (
    PromoCodeCreateAdmin,
    PromoCodeOut,
    PromoCodeUpdate,
    PromoValidateOut,
    PromoValidateRequest,
)

router = APIRouter(prefix="/promo-codes", tags=["Promo Codes"])


def _to_out(p: PromoCode) -> PromoCodeOut:
    return PromoCodeOut(
        id=str(p.id),
        vendor_id=str(p.vendor_id) if p.vendor_id else None,
        code=p.code,
        description=p.description,
        discount_type=p.discount_type,
        discount_value=p.discount_value,
        min_order_total=p.min_order_total,
        max_discount=p.max_discount,
        usage_limit=p.usage_limit,
        per_customer_limit=p.per_customer_limit,
        times_used=p.times_used,
        valid_from=p.valid_from,
        valid_until=p.valid_until,
        is_active=p.is_active,
        created_by=p.created_by,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


# ---------- Public: validate ----------

@router.post("/validate", response_model=PromoValidateOut)
async def validate_promo(payload: PromoValidateRequest):
    from beanie import PydanticObjectId
    vendor_ids = None
    if payload.vendor_ids:
        try:
            vendor_ids = [PydanticObjectId(v) for v in payload.vendor_ids]
        except Exception:
            vendor_ids = None

    valid, message, discount, promo = await promo_crud.validate_promo(
        code=payload.code,
        subtotal=payload.subtotal,
        delivery_fee=0.0,
        phone=payload.phone,
        vendor_ids=vendor_ids,
    )
    return PromoValidateOut(
        valid=valid,
        code=payload.code.strip().upper(),
        discount_amount=round(discount, 2),
        message=message,
        discount_type=promo.discount_type if promo else None,
        vendor_id=str(promo.vendor_id) if promo and promo.vendor_id else None,
    )


# ---------- Admin CRUD ----------

@router.get("", response_model=list[PromoCodeOut], dependencies=[Depends(get_current_admin)])
async def list_promos(
    platform_only: bool = False,
    active_only: bool = False,
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=500),
):
    promos = await promo_crud.list_promos(
        platform_only=platform_only, active_only=active_only, skip=skip, limit=limit
    )
    return [_to_out(p) for p in promos]


@router.get("/{promo_id}", response_model=PromoCodeOut, dependencies=[Depends(get_current_admin)])
async def get_promo(promo_id: str):
    promo = await promo_crud.get_by_id(promo_id)
    if not promo:
        raise HTTPException(404, "Promo code not found")
    return _to_out(promo)


@router.post(
    "",
    response_model=PromoCodeOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_admin)],
)
async def create_promo(payload: PromoCodeCreateAdmin):
    if await promo_crud.get_by_code(payload.code):
        raise HTTPException(409, "A promo with that code already exists")
    promo = await promo_crud.create_promo(
        payload.model_dump(), created_by="admin"
    )
    return _to_out(promo)


@router.patch("/{promo_id}", response_model=PromoCodeOut, dependencies=[Depends(get_current_admin)])
async def update_promo(promo_id: str, payload: PromoCodeUpdate):
    promo = await promo_crud.get_by_id(promo_id)
    if not promo:
        raise HTTPException(404, "Promo code not found")
    promo = await promo_crud.update_promo(promo, payload.model_dump(exclude_unset=True))
    return _to_out(promo)


@router.delete(
    "/{promo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_current_admin)],
)
async def delete_promo(promo_id: str):
    promo = await promo_crud.get_by_id(promo_id)
    if not promo:
        raise HTTPException(404, "Promo code not found")
    await promo_crud.delete_promo(promo)