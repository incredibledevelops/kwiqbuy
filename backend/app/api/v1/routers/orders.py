from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.api.v1.routers.kitchen_helpers import to_vendor_order_public
from app.core.config import settings
from app.core.deps import (
    check_idempotency,
    get_current_staff_or_admin,
    get_idempotency_key,
    store_idempotency,
)
from app.core.limiter import limiter
from app.core.sms import (
    sms_order_cancelled,
    sms_order_delivered,
    sms_order_out_for_delivery,
    sms_order_received,
)
from app.crud import order as order_crud
from app.crud import product as product_crud
from app.crud import user as user_crud
from app.models.order import Order, OrderStatus
from app.models.user import User, UserRole
from fastapi.responses import Response
from app.services.pdf_invoice import render_invoice
from app.schemas.order import (
    OrderAdminListOut,
    OrderAssignRider,
    OrderCreate,
    OrderOut,
    OrderStatusUpdate,
    OrderTrackOut,
)

router = APIRouter(prefix="/orders", tags=["Orders"])


def _to_out(o: Order) -> OrderOut:
    return OrderOut(
        id=str(o.id),
        reference=o.reference,
        order_type=o.order_type,
        customer=o.customer.model_dump(),
        delivery_zone_id=str(o.delivery_zone_id) if o.delivery_zone_id else None,
        delivery_zone_name=o.delivery_zone_name,
        delivery_address=o.delivery_address,
        vendor_orders=[to_vendor_order_public(vo) for vo in o.vendor_orders],
        subtotal=o.subtotal,
        delivery_fee=o.delivery_fee,
        platform_delivery_cut=o.platform_delivery_cut,
        rider_earning=o.rider_earning,
        promo_code=o.promo_code,
        promo_discount=o.promo_discount,
        loyalty_points_redeemed=o.loyalty_points_redeemed,
        loyalty_discount=o.loyalty_discount,
        wallet_applied=o.wallet_applied,
        wallet_used=o.wallet_used,
        total=o.total,
        amount_due_external=o.amount_due_external,
        status=o.status,
        status_history=o.status_history,
        rider_id=str(o.rider_id) if o.rider_id else None,
        rider_name=o.rider_name,
        rider_phone=o.rider_phone,
        dispatched_at=o.dispatched_at,
        delivered_at=o.delivered_at,
        payment_reference=o.payment_reference,
        notes=o.notes,
        created_at=o.created_at,
        updated_at=o.updated_at,
    )


def _to_admin_list(o: Order) -> OrderAdminListOut:
    return OrderAdminListOut(
        id=str(o.id),
        reference=o.reference,
        order_type=o.order_type,
        customer_name=o.customer.full_name,
        customer_phone=o.customer.phone,
        delivery_zone_name=o.delivery_zone_name,
        vendor_names=[vo.vendor_name for vo in o.vendor_orders],
        vendor_count=len(o.vendor_orders),
        total=o.total,
        platform_fee_total=round(sum(vo.platform_fee for vo in o.vendor_orders), 2),
        platform_delivery_cut=o.platform_delivery_cut,
        rider_earning=o.rider_earning,
        wallet_applied=o.wallet_applied,
        status=o.status,
        promo_code=o.promo_code,
        created_at=o.created_at,
    )


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_ORDER)
async def create_order(
    request: Request,
    payload: OrderCreate,
    idem_key: str | None = Depends(get_idempotency_key),
):
    endpoint = "POST /api/v1/orders"
    cached = await check_idempotency(idem_key, endpoint)
    if cached:
        return OrderOut(**cached)

    grouped: dict[str, list[dict]] = defaultdict(list)
    for item in payload.items:
        if item.is_custom_bowl:
            raise HTTPException(400, "Custom bowls must specify a vendor_id")
        if not item.product_id:
            raise HTTPException(400, f"product_id missing for '{item.name}'")
        db_product = await product_crud.get_product(item.product_id)
        if not db_product:
            raise HTTPException(400, f"Product not found: {item.name}")
        if not db_product.is_available:
            raise HTTPException(400, f"'{db_product.name}' is out of stock")
        grouped[str(db_product.vendor_id)].append({
            "product_id": str(db_product.id),
            "name": db_product.name,
            "unit_price": db_product.price,
            "quantity": item.quantity,
            "is_custom_bowl": False,
            "customizations": None,
            "variant_sku": item.variant_sku,
            "variant_selections": item.variant_selections,
        })

    from app.crud import delivery_zone as zone_crud
    zone = None
    if payload.delivery_zone_id:
        zone = await zone_crud.get_zone(payload.delivery_zone_id)
        if not zone or not zone.is_active:
            raise HTTPException(400, "Invalid or inactive delivery_zone_id")

    try:
        order, _, _, _ = await order_crud.create_order(
            customer=payload.customer.model_dump(),
            grouped_items=grouped,
            delivery_zone_id=str(zone.id) if zone else None,
            delivery_zone_name=zone.name if zone else "",
            delivery_address=payload.delivery_address,
            delivery_fee=zone.delivery_fee if zone else 0.0,
            zone_platform_cut_override=(
                zone.platform_cut_pct_override if zone else None
            ),
            notes=payload.notes,
            promo_code=payload.promo_code,
            redeem_points=payload.redeem_points,
            apply_wallet=payload.apply_wallet,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

    try:
        await sms_order_received(order)
    except Exception:
        import logging
        logging.getLogger(__name__).exception("SMS received failed")

    result = _to_out(order)
    await store_idempotency(idem_key, endpoint, result.model_dump(), 201)
    return result


@router.get("/track/{reference}", response_model=OrderTrackOut)
async def track_order(reference: str):
    order = await order_crud.get_order_by_reference(reference)
    if not order:
        raise HTTPException(404, "Order not found")
    return OrderTrackOut(
        reference=order.reference,
        order_type=order.order_type,
        status=order.status,
        subtotal=order.subtotal,
        delivery_fee=order.delivery_fee,
        promo_discount=order.promo_discount,
        loyalty_discount=order.loyalty_discount,
        wallet_applied=order.wallet_applied,
        total=order.total,
        amount_due_external=order.amount_due_external,
        delivery_zone_name=order.delivery_zone_name,
        delivery_address=order.delivery_address,
        vendor_statuses=[
            {
                "vendor_id": str(vo.vendor_id),
                "vendor_name": vo.vendor_name,
                "status": vo.status.value,
                "items_count": sum(i.quantity for i in vo.items),
            }
            for vo in order.vendor_orders
        ],
        rider_name=order.rider_name,
        rider_phone=order.rider_phone,
        dispatched_at=order.dispatched_at,
        delivered_at=order.delivered_at,
        status_history=order.status_history,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )



@router.get("/{order_id}/invoice.pdf")
async def order_invoice(
    order_id: str,
    _=Depends(get_current_staff_or_admin),
):
    order = await order_crud.get_order(order_id)
    if not order:
        order = await order_crud.get_order_by_reference(order_id)
    if not order:
        raise HTTPException(404, "Order not found")

    try:
        pdf_bytes = render_invoice(order)
    except Exception as e:
        import logging
        logging.getLogger(__name__).exception("PDF render failed")
        raise HTTPException(500, f"Invoice render failed: {type(e).__name__}")

    filename = f"kwiqbuy-{order.reference}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@router.get("", response_model=list[OrderAdminListOut])
async def list_orders(
    status_filter: OrderStatus | None = Query(None, alias="status"),
    limit: int = Query(100, ge=1, le=500),
    skip: int = Query(0, ge=0),
    _=Depends(get_current_staff_or_admin),
):
    orders = await order_crud.list_orders(status=status_filter, limit=limit, skip=skip)
    return [_to_admin_list(o) for o in orders]


@router.get("/misc/riders", dependencies=[Depends(get_current_staff_or_admin)])
async def list_riders():
    riders = await User.find(User.role == UserRole.RIDER).to_list()
    return [
        {
            "id": str(r.id),
            "full_name": r.full_name,
            "phone": r.phone,
            "vehicle": r.vehicle,
            "plate_number": r.plate_number,
            "is_active": r.is_active,
        }
        for r in riders
    ]


@router.get("/{order_id}", response_model=OrderOut)
async def get_order(order_id: str, _=Depends(get_current_staff_or_admin)):
    order = await order_crud.get_order(order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    return _to_out(order)


@router.patch(
    "/{order_id}/status",
    response_model=OrderOut,
    dependencies=[Depends(get_current_staff_or_admin)],
)
async def update_status(order_id: str, payload: OrderStatusUpdate):
    order = await order_crud.get_order(order_id)
    if not order:
        raise HTTPException(404, "Order not found")

    if (
        order.status in (OrderStatus.DELIVERED, OrderStatus.CANCELLED)
        and payload.status != order.status
    ):
        raise HTTPException(
            400, f"Cannot change status once order is '{order.status.value}'"
        )

    if payload.status == OrderStatus.CANCELLED:
        try:
            order = await order_crud.cancel_order(order, note=payload.note)
        except ValueError as e:
            raise HTTPException(400, str(e))
    elif payload.status == OrderStatus.DELIVERED:
        order = await order_crud.mark_delivered(order, by="admin", session=None)
    else:
        from app.models.order import OrderStatusEvent
        order.status = payload.status
        order.status_history.append(
            OrderStatusEvent(status=payload.status.value, note=payload.note)
        )
        await order.save()

    try:
        if payload.status == OrderStatus.OUT_FOR_DELIVERY:
            await sms_order_out_for_delivery(order)
        elif payload.status == OrderStatus.DELIVERED:
            await sms_order_delivered(order)
        elif payload.status == OrderStatus.CANCELLED:
            await sms_order_cancelled(order)
    except Exception:
        import logging
        logging.getLogger(__name__).exception("Status SMS failed")

    return _to_out(order)


@router.patch(
    "/{order_id}/assign-rider",
    response_model=OrderOut,
    dependencies=[Depends(get_current_staff_or_admin)],
)
async def assign_rider(order_id: str, payload: OrderAssignRider):
    order = await order_crud.get_order(order_id)
    if not order:
        raise HTTPException(404, "Order not found")

    rider = await user_crud.get_by_id(payload.rider_id)
    if not rider:
        raise HTTPException(400, "Rider not found")
    if rider.role != UserRole.RIDER:
        raise HTTPException(400, "User is not a rider")
    if not rider.is_active:
        raise HTTPException(400, "Rider is inactive")

    order = await order_crud.assign_rider(order, rider)
    return _to_out(order)
