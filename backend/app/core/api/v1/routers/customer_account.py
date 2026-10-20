from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.deps import get_current_customer
from app.crud import customer as customer_crud
from app.crud import product as product_crud
from app.crud import vendor as vendor_crud
from app.models.customer import Customer
from app.schemas.customer import (
    CustomerOrderItemOut,
    CustomerOrderOut,
    CustomerOrderStats,
    CustomerProfileOut,
    CustomerUpdateIn,
    CustomerVendorSliceOut,
    FavoriteItemOut,
    FavoriteToggleOut,
    SavedAddressIn,
    SavedAddressOut,
    SavedAddressUpdateIn,
)
from app.schemas.gdpr import GDPRDeleteOut
from app.services import gdpr as gdpr_service

router = APIRouter(prefix="/customer-account", tags=["Customer Account"])


def _safe_str(v, default="") -> str:
    return str(v) if v is not None else default


def _safe_int(v, default=0) -> int:
    try:
        return int(v) if v is not None else default
    except (TypeError, ValueError):
        return default


def _safe_float(v, default=0.0) -> float:
    try:
        return float(v) if v is not None else default
    except (TypeError, ValueError):
        return default


def _profile(c: Customer) -> CustomerProfileOut:
    return CustomerProfileOut(
        id=str(c.id),
        phone=_safe_str(c.phone),
        full_name=_safe_str(c.full_name, "Customer"),
        email=getattr(c, "email", None),
        loyalty_points=_safe_int(getattr(c, "loyalty_points", 0)),
        lifetime_points_earned=_safe_int(getattr(c, "lifetime_points_earned", 0)),
        lifetime_points_redeemed=_safe_int(getattr(c, "lifetime_points_redeemed", 0)),
        wallet_balance=_safe_float(getattr(c, "wallet_balance", 0.0)),
        total_orders=_safe_int(getattr(c, "total_orders", 0)),
        total_spent=_safe_float(getattr(c, "total_spent", 0.0)),
        referral_code=getattr(c, "referral_code", None),
        created_at=c.created_at,
    )


def _address_out(addr, index: int) -> SavedAddressOut:
    return SavedAddressOut(
        index=index,
        label=_safe_str(getattr(addr, "label", None), "Home"),
        zone_id=str(addr.zone_id) if getattr(addr, "zone_id", None) else None,
        zone_name=_safe_str(getattr(addr, "zone_name", None)),
        address=_safe_str(getattr(addr, "address", None)),
        is_default=bool(getattr(addr, "is_default", False)),
    )


@router.get("/me", response_model=CustomerProfileOut)
async def get_profile(current: Customer = Depends(get_current_customer)):
    return _profile(current)


@router.patch("/me", response_model=CustomerProfileOut)
async def update_profile(
    payload: CustomerUpdateIn,
    current: Customer = Depends(get_current_customer),
):
    if payload.full_name:
        current.full_name = payload.full_name.strip()
    if payload.email:
        current.email = payload.email
    await current.save()
    return _profile(current)


@router.get("/me/export")
async def export_my_data(current: Customer = Depends(get_current_customer)):
    return await gdpr_service.export_customer(current)


@router.delete("/me", response_model=GDPRDeleteOut)
async def delete_my_account(current: Customer = Depends(get_current_customer)):
    result = await gdpr_service.soft_delete_customer(current)
    return GDPRDeleteOut(**result)


@router.get("/addresses", response_model=list[SavedAddressOut])
async def list_addresses(current: Customer = Depends(get_current_customer)):
    addresses = getattr(current, "saved_addresses", None) or []
    return [_address_out(a, i) for i, a in enumerate(addresses)]


@router.post("/addresses", response_model=list[SavedAddressOut])
async def add_address(
    payload: SavedAddressIn,
    current: Customer = Depends(get_current_customer),
):
    current = await customer_crud.add_address(
        current,
        label=payload.label,
        zone_id=payload.zone_id,
        zone_name=payload.zone_name,
        address=payload.address,
        is_default=payload.is_default,
    )
    addresses = getattr(current, "saved_addresses", None) or []
    return [_address_out(a, i) for i, a in enumerate(addresses)]


@router.patch("/addresses/{index}", response_model=list[SavedAddressOut])
async def update_address(
    index: int,
    payload: SavedAddressUpdateIn,
    current: Customer = Depends(get_current_customer),
):
    try:
        current = await customer_crud.update_address(
            current, index, payload.model_dump(exclude_unset=True)
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    addresses = getattr(current, "saved_addresses", None) or []
    return [_address_out(a, i) for i, a in enumerate(addresses)]


@router.delete("/addresses/{index}", response_model=list[SavedAddressOut])
async def delete_address(
    index: int,
    current: Customer = Depends(get_current_customer),
):
    try:
        current = await customer_crud.delete_address(current, index)
    except ValueError as e:
        raise HTTPException(400, str(e))
    addresses = getattr(current, "saved_addresses", None) or []
    return [_address_out(a, i) for i, a in enumerate(addresses)]


@router.get("/orders", response_model=list[CustomerOrderOut])
async def my_orders(
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
    current: Customer = Depends(get_current_customer),
):
    from app.crud import order as order_crud
    orders = await order_crud.list_by_customer(current.phone, limit=limit, skip=skip)
    out = []
    for o in orders:
        slices = []
        items_flat = []
        for vo in o.vendor_orders:
            slices.append(
                CustomerVendorSliceOut(
                    vendor_id=str(vo.vendor_id),
                    vendor_name=vo.vendor_name,
                    items_count=sum(i.quantity for i in vo.items),
                    subtotal=vo.subtotal,
                    status=vo.status.value,
                )
            )
            for i in vo.items:
                items_flat.append(
                    CustomerOrderItemOut(
                        name=i.name, quantity=i.quantity, unit_price=i.unit_price
                    )
                )
        out.append(
            CustomerOrderOut(
                id=str(o.id),
                reference=o.reference,
                status=o.status.value,
                subtotal=o.subtotal,
                delivery_fee=o.delivery_fee,
                wallet_applied=o.wallet_applied,
                total=o.total,
                amount_due_external=o.amount_due_external,
                delivery_zone_name=o.delivery_zone_name,
                delivery_address=o.delivery_address,
                vendor_slices=slices,
                items=items_flat,
                created_at=o.created_at,
            )
        )
    return out


@router.get("/orders/stats", response_model=CustomerOrderStats)
async def my_order_stats(current: Customer = Depends(get_current_customer)):
    stats = await customer_crud.order_stats(current.phone)
    return CustomerOrderStats(
        total_orders=_safe_int(stats.get("total_orders", 0)),
        completed_orders=_safe_int(stats.get("completed_orders", 0)),
        total_spent=_safe_float(stats.get("total_spent", 0.0)),
    )


@router.get("/favorites", response_model=list[FavoriteItemOut])
async def list_favorites(current: Customer = Depends(get_current_customer)):
    fav_ids = getattr(current, "favorite_item_ids", None) or []
    if not fav_ids:
        return []

    items = []
    for oid in fav_ids:
        p = await product_crud.get_product(str(oid))
        if p:
            items.append(p)

    if not items:
        return []

    vendor_names = {}
    for p in items:
        if p.vendor_id not in vendor_names:
            v = await vendor_crud.get_by_id(str(p.vendor_id))
            vendor_names[p.vendor_id] = v.business_name if v else None

    return [
        FavoriteItemOut(
            id=str(p.id),
            name=p.name,
            slug=p.slug,
            price=p.price,
            image_url=p.image_url,
            is_available=p.is_available,
            vendor_id=str(p.vendor_id),
            vendor_name=vendor_names.get(p.vendor_id),
            average_rating=p.average_rating,
            total_reviews=p.total_reviews,
        )
        for p in items
    ]


@router.post("/favorites/{product_id}", response_model=FavoriteToggleOut)
async def toggle_favorite(
    product_id: str,
    current: Customer = Depends(get_current_customer),
):
    p = await product_crud.get_product(product_id)
    if not p:
        raise HTTPException(404, "Product not found")
    try:
        current, is_fav = await customer_crud.toggle_favorite(current, product_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return FavoriteToggleOut(
        is_favorite=is_fav,
        message="Added to favorites" if is_fav else "Removed from favorites",
    )


@router.delete("/favorites/{product_id}", response_model=FavoriteToggleOut)
async def remove_favorite(
    product_id: str,
    current: Customer = Depends(get_current_customer),
):
    try:
        current, _ = await customer_crud.remove_favorite(current, product_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return FavoriteToggleOut(is_favorite=False, message="Removed from favorites")
