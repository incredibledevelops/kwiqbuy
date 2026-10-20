from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from beanie import PydanticObjectId

from app.core.config import settings
from app.core.database import transactional
from app.crud import loyalty as loyalty_crud
from app.crud import platform_settings as platform_settings_crud
from app.crud import product as product_crud
from app.crud import promo_code as promo_crud
from app.crud import referral as referral_crud
from app.crud import rider_earning as rider_earning_crud
from app.crud import subscription as subscription_crud
from app.crud import vendor as vendor_crud
from app.models.order import (
    Order,
    OrderItem,
    OrderStatus,
    OrderStatusEvent,
    OrderType,
    VendorOrder,
    VendorOrderStatus,
)
from app.models.promo_code import PromoCode
from app.models.user import User
from app.models.vendor import VendorCategory
from app.utils.generators import generate_order_reference

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _r2(v: float) -> float:
    return round(float(v), 2)


def _effective_delivery_fee(subtotal: float, zone_fee: float, threshold: float) -> float:
    if threshold > 0 and subtotal >= threshold:
        return 0.0
    return _r2(zone_fee)


def _compute_delivery_split(
    delivery_fee: float,
    default_cut_pct: float,
    override_cut_pct: Optional[float] = None,
) -> tuple[float, float]:
    fee = _r2(delivery_fee)
    if fee <= 0:
        return 0.0, 0.0
    pct = (
        float(override_cut_pct)
        if override_cut_pct is not None
        else float(default_cut_pct)
    )
    cut = _r2(fee * (pct / 100.0))
    rider = _r2(fee - cut)
    return cut, rider


def _apply_promo_across_vendors(
    promo: PromoCode,
    vendor_orders: list[VendorOrder],
    delivery_fee: float,
) -> float:
    if promo.discount_type.value == "free_delivery":
        return _r2(delivery_fee)

    if promo.vendor_id is not None:
        eligible = [vo for vo in vendor_orders if vo.vendor_id == promo.vendor_id]
    else:
        eligible = list(vendor_orders)

    eligible_subtotal = sum(vo.subtotal for vo in eligible)
    if eligible_subtotal <= 0:
        return 0.0

    if promo.discount_type.value == "percent":
        raw = eligible_subtotal * (promo.discount_value / 100.0)
        if promo.max_discount is not None:
            raw = min(raw, promo.max_discount)
        total_discount = _r2(raw)
    elif promo.discount_type.value == "fixed":
        total_discount = _r2(min(promo.discount_value, eligible_subtotal))
    else:
        total_discount = 0.0

    total_discount = min(total_discount, _r2(eligible_subtotal))

    for vo in eligible:
        share = vo.subtotal / eligible_subtotal if eligible_subtotal else 0
        vo_discount = _r2(total_discount * share)
        vo.vendor_payout = _r2(max(0.0, vo.vendor_payout - vo_discount))

    return total_discount


def _apply_discount_cap(
    subtotal: float, promo_discount: float, loyalty_discount: float
) -> tuple[float, float]:
    cap_pct = float(settings.MAX_TOTAL_DISCOUNT_PCT or 0)
    if cap_pct <= 0:
        return promo_discount, loyalty_discount
    cap = _r2(subtotal * (cap_pct / 100.0))
    combined = _r2(promo_discount + loyalty_discount)
    if combined <= cap:
        return promo_discount, loyalty_discount
    excess = _r2(combined - cap)
    new_loyalty = _r2(max(0.0, loyalty_discount - excess))
    remaining_excess = _r2(excess - (loyalty_discount - new_loyalty))
    new_promo = _r2(max(0.0, promo_discount - remaining_excess))
    return new_promo, new_loyalty


@transactional()
async def create_order(
    *,
    customer: dict,
    grouped_items: dict[str, list[dict]],
    delivery_zone_id: Optional[str],
    delivery_zone_name: str,
    delivery_address: str,
    delivery_fee: float,
    zone_platform_cut_override: Optional[float] = None,
    notes: Optional[str] = None,
    promo_code: Optional[str] = None,
    redeem_points: Optional[int] = None,
    apply_wallet: bool = False,
    session=None,
):
    if not grouped_items:
        raise ValueError("Order must contain at least one item")

    plat = await platform_settings_crud.get_settings()
    free_delivery_threshold = plat.free_delivery_threshold
    delivery_cut_pct = plat.platform_delivery_cut_pct

    vendor_orders: list[VendorOrder] = []
    grand_subtotal = 0.0
    categories_present: set[str] = set()

    for vendor_id_str, items in grouped_items.items():
        vendor = await vendor_crud.get_by_id(vendor_id_str)
        if not vendor:
            raise ValueError(f"Vendor not found: {vendor_id_str}")
        if vendor.status.value != "active":
            raise ValueError(f"Vendor '{vendor.business_name}' is not accepting orders")

        categories_present.add(vendor.business_category.value)

        vo_items: list[OrderItem] = []
        vo_subtotal = 0.0
        for it in items:
            qty = int(it["quantity"])
            price = _r2(it["unit_price"])
            line_total = _r2(price * qty)
            vo_subtotal = _r2(vo_subtotal + line_total)
            vo_items.append(
                OrderItem(
                    product_id=PydanticObjectId(it["product_id"]) if it.get("product_id") else None,
                    variant_sku=it.get("variant_sku"),
                    variant_selections=it.get("variant_selections"),
                    name=it["name"],
                    unit_price=price,
                    quantity=qty,
                    is_custom_bowl=bool(it.get("is_custom_bowl")),
                    customizations=it.get("customizations"),
                )
            )

        # Base commission for category, then optionally discounted by tier
        base_pct = plat.commission_for(vendor.business_category.value)

        active_sub = None
        tier = None
        if settings.VENDOR_TIERS_ENABLED:
            active_sub = await subscription_crud.get_active_for_vendor(str(vendor.id))
            if active_sub:
                tier = await subscription_crud.get_tier_by_id(str(active_sub.tier_id))

        commission_pct = subscription_crud.effective_commission_pct(
            vendor, base_pct, active_sub, tier
        )

        platform_fee = _r2(vo_subtotal * (commission_pct / 100.0))
        vendor_payout = _r2(vo_subtotal - platform_fee)

        vendor_orders.append(
            VendorOrder(
                vendor_id=vendor.id,
                vendor_name=vendor.business_name,
                vendor_category=vendor.business_category.value,
                items=vo_items,
                subtotal=vo_subtotal,
                commission_pct=commission_pct,
                platform_fee=platform_fee,
                vendor_payout=vendor_payout,
                status=VendorOrderStatus.PENDING,
                status_history=[OrderStatusEvent(status=VendorOrderStatus.PENDING.value)],
            )
        )
        grand_subtotal = _r2(grand_subtotal + vo_subtotal)

    # Order type
    if len(categories_present) == 1:
        order_type = OrderType(categories_present.pop())
    else:
        if not settings.ALLOW_MIXED_CARTS:
            raise ValueError(
                "You can't mix food and retail items in one order. "
                "Please check out separately."
            )
        order_type = OrderType.MIXED

    # Delivery fee
    if order_type == OrderType.RETAIL:
        effective_delivery_fee = 0.0
    else:
        effective_delivery_fee = _effective_delivery_fee(
            grand_subtotal, delivery_fee, free_delivery_threshold
        )

    platform_delivery_cut, rider_earning = _compute_delivery_split(
        effective_delivery_fee, delivery_cut_pct, zone_platform_cut_override
    )

    # Promo
    promo_discount = 0.0
    promo_obj: Optional[PromoCode] = None
    if promo_code:
        valid, msg, _discount, promo_obj = await promo_crud.validate_promo(
            code=promo_code,
            subtotal=grand_subtotal,
            delivery_fee=effective_delivery_fee,
            phone=customer.get("phone"),
            vendor_ids=[vo.vendor_id for vo in vendor_orders],
        )
        if not valid or promo_obj is None:
            raise ValueError(f"Promo error: {msg}")
        promo_discount = _apply_promo_across_vendors(
            promo_obj, vendor_orders, effective_delivery_fee
        )

    # Loyalty
    loyalty_discount = 0.0
    loyalty_customer = None
    if redeem_points and redeem_points > 0:
        loyalty_customer = await loyalty_crud.get_customer_by_phone(customer["phone"])
        if not loyalty_customer:
            raise ValueError("No loyalty account found for this phone number")
        if redeem_points > loyalty_customer.loyalty_points:
            raise ValueError("Insufficient loyalty points")
        if redeem_points < settings.LOYALTY_MIN_REDEEM:
            raise ValueError(f"Minimum redemption is {settings.LOYALTY_MIN_REDEEM} points")
        loyalty_discount = _r2(redeem_points * settings.LOYALTY_POINTS_TO_CEDI)

    promo_discount, loyalty_discount = _apply_discount_cap(
        grand_subtotal, promo_discount, loyalty_discount
    )

    total_before_wallet = _r2(
        max(grand_subtotal + effective_delivery_fee - promo_discount - loyalty_discount, 0.0)
    )

    # Wallet
    wallet_applied = 0.0
    wallet_customer = None
    if apply_wallet and settings.WALLET_ENABLED:
        if total_before_wallet < settings.WALLET_MIN_ORDER_FOR_APPLY:
            raise ValueError(
                f"Order total must be at least GH₵ {settings.WALLET_MIN_ORDER_FOR_APPLY:.2f} "
                "to use wallet balance"
            )
        wallet_customer = await loyalty_crud.get_customer_by_phone(customer["phone"])
        if not wallet_customer:
            raise ValueError("No wallet account found for this phone number")
        from app.crud import wallet as wallet_crud
        wallet_applied = wallet_crud.compute_wallet_application(
            customer_balance=wallet_customer.wallet_balance,
            amount_due=total_before_wallet,
            max_coverage_pct=settings.WALLET_MAX_COVERAGE_PCT,
        )

    amount_due_external = _r2(total_before_wallet - wallet_applied)

    order = Order(
        reference=generate_order_reference(),
        order_type=order_type,
        customer=customer,
        delivery_zone_id=(PydanticObjectId(delivery_zone_id) if delivery_zone_id else None),
        delivery_zone_name=delivery_zone_name,
        delivery_address=delivery_address,
        delivery_fee=effective_delivery_fee,
        platform_delivery_cut=platform_delivery_cut,
        rider_earning=rider_earning,
        vendor_orders=vendor_orders,
        subtotal=grand_subtotal,
        promo_code=promo_obj.code if promo_obj else None,
        promo_discount=promo_discount,
        loyalty_points_redeemed=int(redeem_points or 0),
        loyalty_discount=loyalty_discount,
        wallet_applied=wallet_applied,
        wallet_used=wallet_applied > 0,
        total=total_before_wallet,
        amount_due_external=amount_due_external,
        notes=notes,
        status=OrderStatus.PENDING,
        status_history=[OrderStatusEvent(status=OrderStatus.PENDING.value)],
    )
    await order.insert(session=session)

    for vo in vendor_orders:
        for item in vo.items:
            if not item.product_id:
                continue
            ok = await product_crud.decrement_stock_atomic(
                item.product_id, item.quantity, variant_sku=item.variant_sku, session=session
            )
            if not ok:
                raise ValueError(
                    f"'{item.name}' just went out of stock. Please refresh and try again."
                )

    if promo_obj:
        await promo_crud.increment_usage(promo_obj, session=session)

    if loyalty_customer and redeem_points and redeem_points > 0:
        await loyalty_crud.redeem_points(
            customer=loyalty_customer,
            order_id=order.id,
            order_reference=order.reference,
            points=int(redeem_points),
            note=f"Redeemed on order {order.reference}",
            session=session,
        )

    if wallet_applied > 0 and wallet_customer:
        from app.crud import wallet as wallet_crud
        from app.models.wallet import WalletReason
        await wallet_crud.debit(
            wallet_customer,
            wallet_applied,
            reason=WalletReason.ORDER_PAYMENT,
            order_id=order.id,
            order_reference=order.reference,
            note=f"Applied to order {order.reference}",
            created_by="customer",
            session=session,
        )

    if amount_due_external <= 0:
        order.status = OrderStatus.PAID
        order.status_history.append(OrderStatusEvent(status=OrderStatus.PAID.value, by="wallet"))
        order.updated_at = _now()
        await order.save(session=session)
        await _post_payment_effects(order, session=session)

    return order, promo_discount, loyalty_discount, wallet_applied


async def _post_payment_effects(order: Order, *, session=None) -> None:
    if order.delivery_fee > 0 and order.order_type != OrderType.RETAIL:
        await rider_earning_crud.create_pending(
            order_id=order.id,
            order_reference=order.reference,
            delivery_fee=order.delivery_fee,
            platform_cut=order.platform_delivery_cut,
            session=session,
        )


# ---------- Reads ----------

async def get_order(order_id: str) -> Optional[Order]:
    try:
        return await Order.get(PydanticObjectId(order_id))
    except Exception:
        return None


async def get_order_by_reference(reference: str) -> Optional[Order]:
    return await Order.find_one(Order.reference == reference)


async def list_orders(
    *, status: Optional[OrderStatus] = None, order_type: Optional[OrderType] = None,
    limit: int = 100, skip: int = 0,
) -> list[Order]:
    query = Order.find()
    if status:
        query = query.find(Order.status == status)
    if order_type:
        query = query.find(Order.order_type == order_type)
    return await query.sort(-Order.created_at).skip(skip).limit(limit).to_list()


async def list_by_statuses(statuses: list[OrderStatus], limit: int = 200) -> list[Order]:
    return (
        await Order.find({"status": {"$in": [s.value for s in statuses]}})
        .sort(-Order.created_at)
        .limit(limit)
        .to_list()
    )


async def list_by_customer(phone: str, limit: int = 50, skip: int = 0) -> list[Order]:
    return (
        await Order.find(Order.customer.phone == phone)
        .sort(-Order.created_at)
        .skip(skip)
        .limit(limit)
        .to_list()
    )


async def list_orders_for_vendor(
    vendor_id: str, *, statuses: Optional[list[VendorOrderStatus]] = None,
    limit: int = 200, skip: int = 0,
) -> list[Order]:
    try:
        vid = PydanticObjectId(vendor_id)
    except Exception:
        return []
    query = Order.find({"vendor_orders.vendor_id": vid})
    if statuses:
        query = query.find({
            "vendor_orders": {
                "$elemMatch": {
                    "vendor_id": vid,
                    "status": {"$in": [s.value for s in statuses]},
                }
            }
        })
    return await query.sort(-Order.created_at).skip(skip).limit(limit).to_list()


async def list_assignable(limit: int = 200) -> list[Order]:
    return (
        await Order.find(Order.status == OrderStatus.READY, Order.rider_id == None)  # noqa: E711
        .sort(+Order.created_at)
        .limit(limit)
        .to_list()
    )


async def list_for_rider(rider_id: str, include_delivered: bool = False, limit: int = 200) -> list[Order]:
    query = Order.find(Order.rider_id == PydanticObjectId(rider_id))
    if not include_delivered:
        query = query.find({
            "status": {"$in": [OrderStatus.READY.value, OrderStatus.OUT_FOR_DELIVERY.value]}
        })
    return await query.sort(+Order.dispatched_at).limit(limit).to_list()


def _derive_order_status(order: Order) -> OrderStatus:
    vos = order.vendor_orders
    if not vos:
        return order.status
    if order.status in (OrderStatus.DELIVERED, OrderStatus.CANCELLED, OrderStatus.REFUNDED):
        return order.status
    statuses = [vo.status for vo in vos]
    dead = {VendorOrderStatus.REJECTED, VendorOrderStatus.CANCELLED}
    if all(s in dead for s in statuses):
        return OrderStatus.CANCELLED
    if all(s == VendorOrderStatus.DELIVERED for s in statuses):
        return OrderStatus.DELIVERED
    if all(s == VendorOrderStatus.IN_TRANSIT for s in statuses):
        return OrderStatus.IN_TRANSIT
    if all(
        s in {VendorOrderStatus.SHIPPED, VendorOrderStatus.IN_TRANSIT, VendorOrderStatus.DELIVERED}
        for s in statuses
    ):
        return OrderStatus.SHIPPED
    if all(s in {VendorOrderStatus.PICKED_UP, VendorOrderStatus.DELIVERED} for s in statuses):
        if any(s == VendorOrderStatus.PICKED_UP for s in statuses):
            return OrderStatus.OUT_FOR_DELIVERY
        return OrderStatus.READY
    preparing_states = {VendorOrderStatus.PREPARING, VendorOrderStatus.READY, VendorOrderStatus.PACKED}
    if any(s in preparing_states for s in statuses):
        return OrderStatus.PREPARING
    if any(s in {VendorOrderStatus.ACCEPTED, VendorOrderStatus.CONFIRMED} for s in statuses):
        return OrderStatus.PREPARING
    return OrderStatus.PAID


def _rederive_and_stamp(order: Order, *, by: Optional[str] = None, note: Optional[str] = None) -> None:
    new_status = _derive_order_status(order)
    if new_status != order.status:
        order.status = new_status
        order.status_history.append(OrderStatusEvent(status=new_status.value, by=by, note=note))
    order.updated_at = _now()


_FOOD_ALLOWED_TRANSITIONS: dict[VendorOrderStatus, set[VendorOrderStatus]] = {
    VendorOrderStatus.PENDING: {VendorOrderStatus.ACCEPTED, VendorOrderStatus.REJECTED},
    VendorOrderStatus.ACCEPTED: {VendorOrderStatus.PREPARING, VendorOrderStatus.CANCELLED},
    VendorOrderStatus.PREPARING: {VendorOrderStatus.READY, VendorOrderStatus.CANCELLED},
    VendorOrderStatus.READY: {VendorOrderStatus.PICKED_UP, VendorOrderStatus.CANCELLED},
    VendorOrderStatus.PICKED_UP: {VendorOrderStatus.DELIVERED},
    VendorOrderStatus.DELIVERED: set(),
    VendorOrderStatus.REJECTED: set(),
    VendorOrderStatus.CANCELLED: set(),
}

_RETAIL_ALLOWED_TRANSITIONS: dict[VendorOrderStatus, set[VendorOrderStatus]] = {
    VendorOrderStatus.PENDING: {VendorOrderStatus.CONFIRMED, VendorOrderStatus.REJECTED},
    VendorOrderStatus.CONFIRMED: {VendorOrderStatus.PREPARING, VendorOrderStatus.CANCELLED},
    VendorOrderStatus.PREPARING: {VendorOrderStatus.PACKED, VendorOrderStatus.CANCELLED},
    VendorOrderStatus.PACKED: {VendorOrderStatus.SHIPPED, VendorOrderStatus.CANCELLED},
    VendorOrderStatus.SHIPPED: {VendorOrderStatus.IN_TRANSIT, VendorOrderStatus.DELIVERED},
    VendorOrderStatus.IN_TRANSIT: {VendorOrderStatus.DELIVERED},
    VendorOrderStatus.DELIVERED: set(),
    VendorOrderStatus.REJECTED: set(),
    VendorOrderStatus.CANCELLED: set(),
}


def allowed_transitions_for(category: str) -> dict[VendorOrderStatus, set[VendorOrderStatus]]:
    if category == VendorCategory.RETAIL.value:
        return _RETAIL_ALLOWED_TRANSITIONS
    return _FOOD_ALLOWED_TRANSITIONS


async def update_vendor_order_status(
    order: Order, vendor_id: str, status: VendorOrderStatus,
    *, by: Optional[str] = None, note: Optional[str] = None, reason: Optional[str] = None,
    session=None,
) -> Order:
    try:
        vid = PydanticObjectId(vendor_id)
    except Exception:
        raise ValueError("Invalid vendor_id")
    target = None
    for vo in order.vendor_orders:
        if vo.vendor_id == vid:
            target = vo
            break
    if target is None:
        raise ValueError("This order has no slice for that vendor")
    if target.status == status:
        return order
    transitions = allowed_transitions_for(target.vendor_category)
    if status not in transitions.get(target.status, set()):
        raise ValueError(f"Vendor cannot move from '{target.status.value}' to '{status.value}'")
    target.status = status
    target.status_history.append(OrderStatusEvent(status=status.value, by=by, note=note))
    now = _now()
    if status in (VendorOrderStatus.ACCEPTED, VendorOrderStatus.CONFIRMED):
        target.accepted_at = now
    elif status == VendorOrderStatus.READY:
        target.ready_at = now
    elif status == VendorOrderStatus.PACKED:
        target.packed_at = now
    elif status == VendorOrderStatus.PICKED_UP:
        target.picked_up_at = now
    elif status == VendorOrderStatus.SHIPPED:
        target.shipped_at = now
    elif status == VendorOrderStatus.DELIVERED:
        target.delivered_at = now
    elif status == VendorOrderStatus.REJECTED:
        target.rejection_reason = reason
    _rederive_and_stamp(order, by=by, note=note)
    await order.save(session=session)
    return order


async def mark_out_for_delivery(order: Order, rider: User, *, by: Optional[str] = None, session=None) -> Order:
    order.rider_id = rider.id
    order.rider_name = rider.full_name
    order.rider_phone = rider.phone
    order.dispatched_at = _now()
    for vo in order.vendor_orders:
        if vo.vendor_category == "food" and vo.status == VendorOrderStatus.READY:
            vo.status = VendorOrderStatus.PICKED_UP
            vo.picked_up_at = order.dispatched_at
            vo.status_history.append(OrderStatusEvent(status=VendorOrderStatus.PICKED_UP.value, by=by))
    _rederive_and_stamp(order, by=by)
    await order.save(session=session)
    await rider_earning_crud.attach_rider(order_id=order.id, rider_id=rider.id, session=session)
    return order


async def mark_delivered(order: Order, *, by: Optional[str] = None, session=None) -> Order:
    order.status = OrderStatus.DELIVERED
    order.delivered_at = _now()
    order.status_history.append(OrderStatusEvent(status=OrderStatus.DELIVERED.value, by=by))
    order.updated_at = _now()
    await order.save(session=session)
    await rider_earning_crud.mark_earned(order_id=order.id, session=session)
    return order


async def assign_rider(order: Order, rider: User) -> Order:
    order.rider_id = rider.id
    order.rider_name = rider.full_name
    order.rider_phone = rider.phone
    order.updated_at = _now()
    await order.save()
    await rider_earning_crud.attach_rider(order_id=order.id, rider_id=rider.id)
    return order


async def attach_payment_reference(order: Order, payment_reference: str, *, session=None) -> Order:
    order.payment_reference = payment_reference
    order.updated_at = _now()
    await order.save(session=session)
    return order


@transactional()
async def on_order_paid(order: Order, *, session=None) -> int:
    if order.loyalty_points_earned > 0:
        return order.loyalty_points_earned
    if order.status == OrderStatus.PENDING:
        order.status = OrderStatus.PAID
        order.status_history.append(OrderStatusEvent(status=OrderStatus.PAID.value))
        order.updated_at = _now()
        await order.save(session=session)
    points = int(order.total * settings.LOYALTY_POINTS_PER_CEDI)
    if points > 0:
        customer = await loyalty_crud.get_or_create_customer(
            phone=order.customer.phone, full_name=order.customer.full_name,
            email=order.customer.email, session=session,
        )
        await loyalty_crud.award_points(
            customer=customer, order_id=order.id, order_reference=order.reference,
            points=points, session=session,
        )
        await loyalty_crud.touch_customer_order_stats(customer, order.total, session=session)

    from app.models.vendor import Vendor
    for vo in order.vendor_orders:
        vendor = await Vendor.get(vo.vendor_id, session=session)
        if not vendor:
            continue
        vendor.total_orders += 1
        vendor.total_gross_sales = _r2(vendor.total_gross_sales + vo.subtotal)
        vendor.lifetime_platform_fees = _r2(vendor.lifetime_platform_fees + vo.platform_fee)
        vendor.updated_at = _now()
        await vendor.save(session=session)

    try:
        ref = await referral_crud.find_pending_by_referee(order.customer.phone)
        if ref:
            await referral_crud.complete_referral(ref, order.reference, session=session)
            points_per_cedi = settings.LOYALTY_POINTS_PER_CEDI
            referee_bonus = int(ref.referee_reward * points_per_cedi)
            if referee_bonus > 0:
                await loyalty_crud.award_points(
                    customer=customer, order_id=order.id, order_reference=order.reference,
                    points=referee_bonus, note=f"Referral bonus for using {ref.code}", session=session,
                )
            referrer = await loyalty_crud.get_customer_by_phone(ref.referrer_phone)
            if referrer:
                referrer_bonus = int(ref.referrer_reward * points_per_cedi)
                if referrer_bonus > 0:
                    await loyalty_crud.award_points(
                        customer=referrer, order_id=order.id, order_reference=order.reference,
                        points=referrer_bonus, note=f"Referral bonus — {ref.referee_name or 'friend'} ordered",
                        session=session,
                    )
    except Exception:
        logger.exception("Referral completion failed for %s", order.reference)

    order.loyalty_points_earned = points
    order.updated_at = _now()
    await order.save(session=session)
    await _post_payment_effects(order, session=session)
    return points


@transactional()
async def cancel_order(order: Order, *, by: Optional[str] = None, reason: Optional[str] = None, session=None) -> Order:
    if order.status in (OrderStatus.CANCELLED, OrderStatus.DELIVERED, OrderStatus.REFUNDED):
        raise ValueError(f"Order is already '{order.status.value}'")
    terminal = {
        VendorOrderStatus.READY, VendorOrderStatus.PICKED_UP, VendorOrderStatus.PACKED,
        VendorOrderStatus.SHIPPED, VendorOrderStatus.IN_TRANSIT,
    }
    for vo in order.vendor_orders:
        if vo.status in terminal:
            raise ValueError(
                f"Cannot cancel: vendor '{vo.vendor_name}' has already prepared or dispatched their slice"
            )
    for vo in order.vendor_orders:
        vo.status = VendorOrderStatus.CANCELLED
        vo.status_history.append(
            OrderStatusEvent(status=VendorOrderStatus.CANCELLED.value, by=by, note=reason)
        )
        for item in vo.items:
            if item.product_id:
                await product_crud.increment_stock(
                    item.product_id, item.quantity, variant_sku=item.variant_sku, session=session
                )
    order.status = OrderStatus.CANCELLED
    order.status_history.append(
        OrderStatusEvent(status=OrderStatus.CANCELLED.value, by=by, note=reason)
    )
    order.updated_at = _now()
    await order.save(session=session)
    await rider_earning_crud.void_for_order(order_id=order.id, session=session)

    if order.wallet_applied > 0:
        customer = await loyalty_crud.get_customer_by_phone(order.customer.phone)
        if customer:
            from app.crud import wallet as wallet_crud
            from app.models.wallet import WalletReason
            await wallet_crud.credit(
                customer, order.wallet_applied, reason=WalletReason.REVERSAL,
                note=f"Cancelled order {order.reference}", created_by="system", session=session,
            )
    return order
