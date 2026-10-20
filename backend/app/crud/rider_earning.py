"""
Rider earnings ledger CRUD.
"""
from datetime import datetime, timezone
from typing import Optional

from beanie import PydanticObjectId

from app.models.rider_earning import RiderEarning, RiderEarningStatus


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _r2(v: float) -> float:
    return round(float(v), 2)


async def create_pending(
    *,
    order_id: PydanticObjectId,
    order_reference: str,
    delivery_fee: float,
    platform_cut: float,
    session=None,
) -> Optional[RiderEarning]:
    """
    Create the earning row when an order is paid but has no rider yet.
    rider_id is filled in later when a rider claims the order.
    """
    delivery_fee = _r2(delivery_fee)
    platform_cut = _r2(platform_cut)
    rider_amount = _r2(max(0.0, delivery_fee - platform_cut))

    # If the delivery is free, there's no earning to record.
    if delivery_fee <= 0:
        return None

    existing = await RiderEarning.find_one(
        RiderEarning.order_id == order_id
    )
    if existing:
        return existing

    row = RiderEarning(
        rider_id=PydanticObjectId("000000000000000000000000"),  # placeholder until claimed
        order_id=order_id,
        order_reference=order_reference,
        delivery_fee=delivery_fee,
        platform_cut=platform_cut,
        rider_amount=rider_amount,
        status=RiderEarningStatus.PENDING,
    )
    await row.insert(session=session)
    return row


async def attach_rider(
    *,
    order_id: PydanticObjectId,
    rider_id: PydanticObjectId,
    session=None,
) -> Optional[RiderEarning]:
    row = await RiderEarning.find_one(
        RiderEarning.order_id == order_id, session=session
    )
    if not row:
        return None
    row.rider_id = rider_id
    row.updated_at = _now()
    await row.save(session=session)
    return row


async def mark_earned(
    *,
    order_id: PydanticObjectId,
    session=None,
) -> Optional[RiderEarning]:
    row = await RiderEarning.find_one(
        RiderEarning.order_id == order_id, session=session
    )
    if not row:
        return None
    if row.status == RiderEarningStatus.EARNED:
        return row
    row.status = RiderEarningStatus.EARNED
    row.earned_at = _now()
    row.updated_at = _now()
    await row.save(session=session)
    return row


async def void_for_order(
    *,
    order_id: PydanticObjectId,
    session=None,
) -> Optional[RiderEarning]:
    row = await RiderEarning.find_one(
        RiderEarning.order_id == order_id, session=session
    )
    if not row:
        return None
    row.status = RiderEarningStatus.VOIDED
    row.updated_at = _now()
    await row.save(session=session)
    return row


async def summary_for_rider(
    rider_id: str, *, limit: int = 100
) -> dict:
    try:
        rid = PydanticObjectId(rider_id)
    except Exception:
        return {"total_earned": 0.0, "total_paid_out": 0.0, "pending": 0.0, "rows": []}

    rows = await (
        RiderEarning.find(RiderEarning.rider_id == rid)
        .sort(-RiderEarning.created_at)
        .limit(limit)
        .to_list()
    )

    total_earned = _r2(
        sum(r.rider_amount for r in rows if r.status == RiderEarningStatus.EARNED)
    )
    total_paid = _r2(
        sum(r.rider_amount for r in rows if r.status == RiderEarningStatus.PAID_OUT)
    )
    pending = _r2(
        sum(r.rider_amount for r in rows if r.status == RiderEarningStatus.PENDING)
    )

    return {
        "total_earned": total_earned,
        "total_paid_out": total_paid,
        "pending": pending,
        "available": _r2(total_earned),  # nothing paid out yet in v1
        "rows": rows,
    }


async def list_for_rider(
    rider_id: str, *, limit: int = 200, skip: int = 0
) -> list[RiderEarning]:
    try:
        rid = PydanticObjectId(rider_id)
    except Exception:
        return []
    return (
        await RiderEarning.find(RiderEarning.rider_id == rid)
        .sort(-RiderEarning.created_at)
        .skip(skip)
        .limit(limit)
        .to_list()
    )
