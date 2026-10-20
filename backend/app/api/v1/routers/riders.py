from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import get_current_rider, get_current_rider_or_admin
from app.crud import order as order_crud
from app.crud import rider_earning as rider_earning_crud
from app.models.order import Order, OrderStatus
from app.models.user import User
from app.schemas.order import (
    OrderStatusUpdate,
    RiderAssignableOut,
    RiderOrderOut,
)
from app.schemas.rider_earning import (
    RiderEarningOut,
    RiderEarningsSummaryOut,
)

router = APIRouter(prefix="/riders", tags=["Riders"])


def _items_count(order: Order) -> int:
    return sum(
        sum(i.quantity for i in vo.items)
        for vo in order.vendor_orders
    )


def _vendor_pickups(order: Order) -> list[dict]:
    return [
        {
            "vendor_id": str(vo.vendor_id),
            "vendor_name": vo.vendor_name,
            "items_count": sum(i.quantity for i in vo.items),
            "status": vo.status.value,
        }
        for vo in order.vendor_orders
        if vo.status.value not in ("rejected", "cancelled")
    ]


def _to_rider(o: Order) -> RiderOrderOut:
    return RiderOrderOut(
        id=str(o.id),
        reference=o.reference,
        order_type=o.order_type,
        customer_name=o.customer.full_name,
        customer_phone=o.customer.phone,
        delivery_address=o.delivery_address,
        delivery_zone_name=o.delivery_zone_name,
        vendor_pickups=_vendor_pickups(o),
        items_count=_items_count(o),
        total=o.total,
        rider_earning=o.rider_earning,
        status=o.status,
        dispatched_at=o.dispatched_at,
        delivered_at=o.delivered_at,
        created_at=o.created_at,
    )


def _to_assignable(o: Order) -> RiderAssignableOut:
    return RiderAssignableOut(
        id=str(o.id),
        reference=o.reference,
        delivery_zone_name=o.delivery_zone_name,
        vendor_count=len(o.vendor_orders),
        items_count=_items_count(o),
        total=o.total,
        rider_earning=o.rider_earning,
        status=o.status,
        created_at=o.created_at,
    )


def _earning_out(row) -> RiderEarningOut:
    return RiderEarningOut(
        id=str(row.id),
        order_id=str(row.order_id),
        order_reference=row.order_reference,
        delivery_fee=row.delivery_fee,
        platform_cut=row.platform_cut,
        rider_amount=row.rider_amount,
        status=row.status,
        earned_at=row.earned_at,
        paid_out_at=row.paid_out_at,
        created_at=row.created_at,
    )


@router.get("/assignable", response_model=list[RiderAssignableOut])
async def assignable(_: User = Depends(get_current_rider_or_admin)):
    orders = await order_crud.list_assignable()
    return [_to_assignable(o) for o in orders]


@router.get("/mine", response_model=list[RiderOrderOut])
async def my_orders(
    include_delivered: bool = False,
    current_user: User = Depends(get_current_rider),
):
    orders = await order_crud.list_for_rider(
        str(current_user.id), include_delivered=include_delivered
    )
    return [_to_rider(o) for o in orders]


@router.post("/claim/{order_id}", response_model=RiderOrderOut)
async def claim_order(
    order_id: str,
    current_user: User = Depends(get_current_rider),
):
    order = await order_crud.get_order(order_id)
    if not order:
        raise HTTPException(404, "Order not found")

    if order.rider_id is not None and str(order.rider_id) != str(current_user.id):
        raise HTTPException(409, "This order is already assigned to another rider")

    if order.status not in (OrderStatus.READY,):
        raise HTTPException(400, f"Cannot claim an order in '{order.status.value}'")

    order = await order_crud.mark_out_for_delivery(order, current_user)
    return _to_rider(order)


@router.patch("/orders/{order_id}/status", response_model=RiderOrderOut)
async def rider_update_status(
    order_id: str,
    payload: OrderStatusUpdate,
    current_user: User = Depends(get_current_rider),
):
    order = await order_crud.get_order(order_id)
    if not order:
        raise HTTPException(404, "Order not found")

    if order.rider_id is None or str(order.rider_id) != str(current_user.id):
        raise HTTPException(403, "This order is not assigned to you")

    if payload.status == OrderStatus.DELIVERED:
        order = await order_crud.mark_delivered(order, by=current_user.email)
    elif payload.status == OrderStatus.OUT_FOR_DELIVERY:
        order = await order_crud.mark_out_for_delivery(
            order, current_user, by=current_user.email
        )
    else:
        raise HTTPException(400, f"Rider cannot set status '{payload.status.value}'")

    return _to_rider(order)


# ---------- Earnings ----------

@router.get("/me/earnings", response_model=RiderEarningsSummaryOut)
async def my_earnings(current_user: User = Depends(get_current_rider)):
    data = await rider_earning_crud.summary_for_rider(str(current_user.id))
    return RiderEarningsSummaryOut(
        total_earned=data["total_earned"],
        total_paid_out=data["total_paid_out"],
        pending=data["pending"],
        available=data["available"],
        rows=[_earning_out(r).model_dump() for r in data["rows"]],
    )


@router.get("/me/earnings/rows", response_model=list[RiderEarningOut])
async def my_earnings_rows(
    limit: int = 200,
    skip: int = 0,
    current_user: User = Depends(get_current_rider),
):
    rows = await rider_earning_crud.list_for_rider(
        str(current_user.id), limit=limit, skip=skip
    )
    return [_earning_out(r) for r in rows]
