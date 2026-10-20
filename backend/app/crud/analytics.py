"""
Analytics for admin and vendor.

Money fields returned here are always in the platform currency (GHS).
Vendor analytics hide platform-wide numbers (only their own slice).
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from beanie import PydanticObjectId

from app.models.order import Order, OrderStatus, VendorOrderStatus


def _safe_float(v, default: float = 0.0) -> float:
    try:
        return float(v) if v is not None else default
    except (TypeError, ValueError):
        return default


def _safe_int(v, default: int = 0) -> int:
    try:
        return int(v) if v is not None else default
    except (TypeError, ValueError):
        return default


def _r2(v: float) -> float:
    return round(float(v), 2)


def _revenue_orders(orders: list[Order]) -> list[Order]:
    return [
        o for o in orders
        if o.status in (
            OrderStatus.PAID,
            OrderStatus.PREPARING,
            OrderStatus.READY,
            OrderStatus.OUT_FOR_DELIVERY,
            OrderStatus.DELIVERED,
        )
    ]


# ---------- Admin analytics ----------

async def summary(start: datetime, end: datetime) -> dict:
    orders = await Order.find(
        Order.created_at >= start, Order.created_at <= end
    ).to_list()

    paid = [o for o in orders if o.status == OrderStatus.PAID]
    delivered = [o for o in orders if o.status == OrderStatus.DELIVERED]
    cancelled = [o for o in orders if o.status == OrderStatus.CANCELLED]
    pending = [
        o for o in orders
        if o.status in (
            OrderStatus.PENDING,
            OrderStatus.PREPARING,
            OrderStatus.READY,
            OrderStatus.OUT_FOR_DELIVERY,
        )
    ]

    rev = _revenue_orders(orders)
    total_revenue = _r2(sum(_safe_float(o.total) for o in rev))
    platform_fees = _r2(
        sum(
            sum(_safe_float(vo.platform_fee) for vo in o.vendor_orders)
            for o in rev
        )
    )
    vendor_payouts = _r2(
        sum(
            sum(_safe_float(vo.vendor_payout) for vo in o.vendor_orders)
            for o in rev
        )
    )

    return {
        "total_revenue": total_revenue,
        "platform_fees_earned": platform_fees,
        "vendor_payouts_total": vendor_payouts,
        "total_orders": len(orders),
        "paid_orders": len(paid) + len(delivered),
        "pending_orders": len(pending),
        "delivered_orders": len(delivered),
        "cancelled_orders": len(cancelled),
        "average_order_value": (
            _r2(total_revenue / len(rev)) if rev else 0.0
        ),
        "total_promo_discount": _r2(sum(_safe_float(o.promo_discount) for o in rev)),
        "total_loyalty_discount": _r2(sum(_safe_float(o.loyalty_discount) for o in rev)),
        "total_points_redeemed": sum(_safe_int(o.loyalty_points_redeemed) for o in rev),
        "total_points_earned": sum(_safe_int(o.loyalty_points_earned) for o in rev),
        "range_start": start,
        "range_end": end,
    }


# ---------- Vendor analytics ----------

async def vendor_summary(
    vendor_id: str,
    start: datetime,
    end: datetime,
) -> dict:
    vid = PydanticObjectId(vendor_id)
    orders = await Order.find(
        Order.created_at >= start,
        Order.created_at <= end,
        {"vendor_orders.vendor_id": vid},
    ).to_list()

    total_sales = 0.0
    total_fees = 0.0
    total_payout = 0.0
    item_count = 0
    delivered_count = 0
    cancelled_count = 0

    for o in orders:
        for vo in o.vendor_orders:
            if vo.vendor_id != vid:
                continue
            if vo.status in (
                VendorOrderStatus.REJECTED,
                VendorOrderStatus.CANCELLED,
            ):
                cancelled_count += 1
                continue
            if vo.status == VendorOrderStatus.PICKED_UP:
                delivered_count += 1
            total_sales = _r2(total_sales + _safe_float(vo.subtotal))
            total_fees = _r2(total_fees + _safe_float(vo.platform_fee))
            total_payout = _r2(total_payout + _safe_float(vo.vendor_payout))
            item_count += sum(_safe_int(i.quantity) for i in vo.items)

    return {
        "gross_sales": total_sales,
        "platform_fees": total_fees,
        "net_earnings": total_payout,
        "orders_total": len(orders),
        "orders_delivered": delivered_count,
        "orders_cancelled": cancelled_count,
        "items_sold": item_count,
        "range_start": start,
        "range_end": end,
    }


# ---------- Series ----------

async def daily_series(
    start: datetime,
    end: datetime,
    vendor_id: Optional[str] = None,
) -> list[dict]:
    query = Order.find(Order.created_at >= start, Order.created_at <= end)
    if vendor_id:
        query = query.find({"vendor_orders.vendor_id": PydanticObjectId(vendor_id)})
    orders = await query.to_list()

    vid = PydanticObjectId(vendor_id) if vendor_id else None
    buckets: dict[str, dict] = {}
    cursor = start.date()
    end_date = end.date()
    while cursor <= end_date:
        key = cursor.isoformat()
        buckets[key] = {"date": key, "revenue": 0.0, "orders": 0}
        cursor = cursor + timedelta(days=1)

    for o in orders:
        key = o.created_at.date().isoformat()
        if key not in buckets:
            continue
        buckets[key]["orders"] += 1
        if vid is not None:
            slice_total = sum(
                _safe_float(vo.subtotal)
                for vo in o.vendor_orders
                if vo.vendor_id == vid
                and vo.status not in (
                    VendorOrderStatus.REJECTED,
                    VendorOrderStatus.CANCELLED,
                )
            )
            buckets[key]["revenue"] += slice_total
        else:
            if o.status in (
                OrderStatus.PAID,
                OrderStatus.PREPARING,
                OrderStatus.READY,
                OrderStatus.OUT_FOR_DELIVERY,
                OrderStatus.DELIVERED,
            ):
                buckets[key]["revenue"] += _safe_float(o.total)

    return [
        {"date": k, "revenue": _r2(v["revenue"]), "orders": v["orders"]}
        for k, v in sorted(buckets.items())
    ]


async def status_breakdown(
    start: datetime, end: datetime, vendor_id: Optional[str] = None
) -> list[dict]:
    query = Order.find(Order.created_at >= start, Order.created_at <= end)
    if vendor_id:
        query = query.find({"vendor_orders.vendor_id": PydanticObjectId(vendor_id)})
    orders = await query.to_list()

    counts: dict[str, int] = {}
    if vendor_id:
        vid = PydanticObjectId(vendor_id)
        for o in orders:
            for vo in o.vendor_orders:
                if vo.vendor_id != vid:
                    continue
                key = vo.status.value
                counts[key] = counts.get(key, 0) + 1
    else:
        for o in orders:
            key = o.status.value
            counts[key] = counts.get(key, 0) + 1

    labels = {
        "pending": "Pending",
        "accepted": "Accepted",
        "paid": "Paid",
        "preparing": "Preparing",
        "ready": "Ready",
        "picked_up": "Picked up",
        "out_for_delivery": "Out for delivery",
        "delivered": "Delivered",
        "cancelled": "Cancelled",
        "rejected": "Rejected",
        "failed": "Failed",
    }
    return [
        {
            "status": k,
            "label": labels.get(k, k.replace("_", " ").title()),
            "count": v,
        }
        for k, v in counts.items()
    ]


# ---------- Top sellers ----------

async def top_sellers(
    start: datetime,
    end: datetime,
    limit: int = 5,
    vendor_id: Optional[str] = None,
) -> list[dict]:
    query = Order.find(
        Order.created_at >= start,
        Order.created_at <= end,
        Order.status != OrderStatus.CANCELLED,
    )
    if vendor_id:
        query = query.find({"vendor_orders.vendor_id": PydanticObjectId(vendor_id)})
    orders = await query.to_list()

    vid = PydanticObjectId(vendor_id) if vendor_id else None
    tally: dict[str, dict] = {}

    for o in orders:
        for vo in o.vendor_orders:
            if vid is not None and vo.vendor_id != vid:
                continue
            for item in vo.items:
                key = item.name
                row = tally.setdefault(
                    key, {"name": key, "quantity": 0, "revenue": 0.0}
                )
                qty = _safe_int(item.quantity)
                price = _safe_float(item.unit_price)
                row["quantity"] += qty
                row["revenue"] += price * qty

    top = sorted(tally.values(), key=lambda r: r["quantity"], reverse=True)[:limit]
    for r in top:
        r["revenue"] = _r2(r["revenue"])
    return top


async def top_vendors(start: datetime, end: datetime, limit: int = 5) -> list[dict]:
    orders = await Order.find(
        Order.created_at >= start,
        Order.created_at <= end,
        Order.status != OrderStatus.CANCELLED,
    ).to_list()

    tally: dict[str, dict] = {}
    for o in orders:
        for vo in o.vendor_orders:
            key = str(vo.vendor_id)
            row = tally.setdefault(
                key,
                {"vendor_id": key, "vendor_name": vo.vendor_name,
                 "orders": 0, "revenue": 0.0, "platform_fees": 0.0},
            )
            row["orders"] += 1
            row["revenue"] += _safe_float(vo.subtotal)
            row["platform_fees"] += _safe_float(vo.platform_fee)

    top = sorted(tally.values(), key=lambda r: r["revenue"], reverse=True)[:limit]
    for r in top:
        r["revenue"] = _r2(r["revenue"])
        r["platform_fees"] = _r2(r["platform_fees"])
    return top


async def top_promos(
    start: datetime, end: datetime, limit: int = 5
) -> list[dict]:
    orders = await Order.find(
        {
            "created_at": {"$gte": start, "$lte": end},
            "promo_code": {"$exists": True, "$ne": None},
            "status": {"$ne": OrderStatus.CANCELLED.value},
        }
    ).to_list()

    tally: dict[str, dict] = {}
    for o in orders:
        code = o.promo_code or ""
        if not code:
            continue
        row = tally.setdefault(
            code, {"code": code, "times_used": 0, "discount_given": 0.0}
        )
        row["times_used"] += 1
        row["discount_given"] += _safe_float(o.promo_discount)

    top = sorted(tally.values(), key=lambda r: r["times_used"], reverse=True)[:limit]
    for r in top:
        r["discount_given"] = _r2(r["discount_given"])
    return top


async def top_zones(start: datetime, end: datetime, limit: int = 5) -> list[dict]:
    orders = await Order.find(
        Order.created_at >= start,
        Order.created_at <= end,
        Order.status != OrderStatus.CANCELLED,
    ).to_list()

    tally: dict[str, dict] = {}
    for o in orders:
        key = o.delivery_zone_name or "Unknown zone"
        row = tally.setdefault(key, {"zone": key, "orders": 0, "revenue": 0.0})
        row["orders"] += 1
        row["revenue"] += _safe_float(o.total)

    top = sorted(tally.values(), key=lambda r: r["orders"], reverse=True)[:limit]
    for r in top:
        r["revenue"] = _r2(r["revenue"])
    return top


def default_range(days: int = 30) -> tuple[datetime, datetime]:
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days - 1)
    start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    return start, end