"""
Vendor payout CRUD.

Flow:
  1. Admin (or a scheduler) requests a payout for a vendor.
     - Collect every VendorOrder with payout_id=None whose vendor_order
       status is settled (i.e. parent order DELIVERED, or at least PICKED_UP).
     - Sum gross/fee/net across those slices.
     - Create VendorPayout(status=REQUESTED) with the coverage list.
     - Stamp each VendorOrder.payout_id with the new payout id.
       (All inside a transaction.)
  2. Admin triggers processing.
     - If PAYSTACK_TRANSFER_ENABLED: call Paystack Transfer.
     - Else: mark method=MANUAL and wait for admin to mark paid.
  3. Result:
     - SUCCESS: status=PAID, paid_at=now, vendor.lifetime_paid_out += net.
     - FAILURE: status=FAILED, clear VendorOrder.payout_id so the balance
       returns to the vendor's available balance.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from beanie import PydanticObjectId
from fastapi import Request

from app.core.config import settings
from app.core.database import transactional
from app.crud import audit as audit_crud
from app.models.audit_log import ActorType
from app.models.order import Order, OrderStatus, VendorOrderStatus
from app.models.payout import PayoutMethod, PayoutStatus, VendorPayout
from app.models.vendor import Vendor

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _r2(v: float) -> float:
    return round(float(v), 2)


# ---------- Read ----------

async def get_payout(payout_id: str) -> Optional[VendorPayout]:
    try:
        return await VendorPayout.get(PydanticObjectId(payout_id))
    except Exception:
        return None


async def list_payouts(
    *,
    vendor_id: Optional[str] = None,
    status: Optional[PayoutStatus] = None,
    limit: int = 200,
    skip: int = 0,
) -> list[VendorPayout]:
    query = VendorPayout.find()
    if vendor_id:
        query = query.find(VendorPayout.vendor_id == PydanticObjectId(vendor_id))
    if status:
        query = query.find(VendorPayout.status == status)
    return (
        await query.sort(-VendorPayout.created_at).skip(skip).limit(limit).to_list()
    )


async def list_for_vendor(
    vendor_id: str, limit: int = 100, skip: int = 0
) -> list[VendorPayout]:
    return await list_payouts(vendor_id=vendor_id, limit=limit, skip=skip)


# ---------- Request payout ----------

@transactional()
async def request_payout(
    vendor: Vendor,
    *,
    requested_by: str,
    method: PayoutMethod = PayoutMethod.PAYSTACK_TRANSFER,
    request: Optional[Request] = None,
    session=None,
) -> VendorPayout:
    """
    Create a payout covering every eligible (delivered or picked_up)
    vendor_order slice for this vendor that hasn't been paid out yet.
    """
    if vendor.status.value == "closed":
        raise ValueError("Cannot pay out a closed vendor")

    # Find orders that contain this vendor's slices.
    # We only care about orders that are DELIVERED (or out for delivery for food).
    orders = await Order.find(
        {"vendor_orders.vendor_id": vendor.id},
        {"status": {"$in": [OrderStatus.DELIVERED.value, OrderStatus.OUT_FOR_DELIVERY.value]}},
    ).to_list()

    eligible_slices: list[tuple[PydanticObjectId, float, float, float]] = []
    vendor_order_ids: list[PydanticObjectId] = []
    gross = 0.0
    fees = 0.0
    net = 0.0
    earliest: Optional[datetime] = None
    latest: Optional[datetime] = None

    for order in orders:
        for vo in order.vendor_orders:
            if vo.vendor_id != vendor.id:
                continue
            if vo.payout_id is not None:
                continue
            if vo.status not in (VendorOrderStatus.PICKED_UP, VendorOrderStatus.DELIVERED):
                continue

            gross = _r2(gross + vo.subtotal)
            fees = _r2(fees + vo.platform_fee)
            net = _r2(net + vo.vendor_payout)
            eligible_slices.append((order.id, vo.subtotal, vo.platform_fee, vo.vendor_payout))
            vendor_order_ids.append(order.id)  # parent order id, for reference

            # Period bounds
            ts = vo.picked_up_at or vo.delivered_at or order.updated_at
            if ts:
                earliest = ts if earliest is None or ts < earliest else earliest
                latest = ts if latest is None or ts > latest else latest

    if net <= 0 or not eligible_slices:
        raise ValueError("No settled earnings available for payout. Have the orders been marked as 'Delivered'?")

    # Create the payout
    payout = VendorPayout(
        vendor_id=vendor.id,
        vendor_name=vendor.business_name,
        gross_sales=gross,
        platform_fees=fees,
        net_payout=net,
        currency=settings.CURRENCY,
        period_start=earliest,
        period_end=latest,
        vendor_order_ids=vendor_order_ids,
        status=PayoutStatus.REQUESTED,
        method=method,
        recipient_code=vendor.payout_recipient_code,
        requested_by=requested_by,
    )
    await payout.insert(session=session)

    # Stamp each VendorOrder so it can't be picked up by another payout
    for order in orders:
        modified = False
        for vo in order.vendor_orders:
            if vo.vendor_id != vendor.id:
                continue
            if vo.payout_id is not None:
                continue
            if vo.status not in (VendorOrderStatus.PICKED_UP, VendorOrderStatus.DELIVERED):
                continue
            vo.payout_id = payout.id
            modified = True
        if modified:
            order.updated_at = _now()
            await order.save(session=session)

    await audit_crud.log(
        action="payout.requested",
        actor_type=ActorType.USER if not requested_by.startswith("system") else ActorType.SYSTEM,
        actor_id=requested_by,
        target_type="VendorPayout",
        target_id=str(payout.id),
        after={
            "vendor_id": str(vendor.id),
            "net_payout": net,
            "gross_sales": gross,
            "platform_fees": fees,
        },
        request=request,
    )
    return payout


# ---------- Process payout ----------

@transactional()
async def mark_processing(
    payout: VendorPayout,
    *,
    paystack_transfer_code: Optional[str] = None,
    paystack_transfer_reference: Optional[str] = None,
    session=None,
) -> VendorPayout:
    if payout.status != PayoutStatus.REQUESTED:
        raise ValueError(f"Cannot process a payout in status '{payout.status.value}'")
    payout.status = PayoutStatus.PROCESSING
    payout.paystack_transfer_code = paystack_transfer_code
    payout.paystack_transfer_reference = paystack_transfer_reference
    payout.processed_at = _now()
    await payout.save(session=session)
    return payout


@transactional()
async def mark_paid(
    payout: VendorPayout,
    *,
    session=None,
) -> VendorPayout:
    if payout.status == PayoutStatus.PAID:
        return payout  # idempotent

    payout.status = PayoutStatus.PAID
    payout.paid_at = _now()
    await payout.save(session=session)

    # Update vendor lifetime paid-out total
    vendor = await Vendor.get(payout.vendor_id, session=session)
    if vendor:
        vendor.lifetime_paid_out = _r2(vendor.lifetime_paid_out + payout.net_payout)
        vendor.updated_at = _now()
        await vendor.save(session=session)

    await audit_crud.log(
        action="payout.paid",
        actor_type=ActorType.SYSTEM,
        target_type="VendorPayout",
        target_id=str(payout.id),
        after={"net_payout": payout.net_payout},
    )
    return payout


@transactional()
async def mark_failed(
    payout: VendorPayout,
    reason: str,
    *,
    session=None,
) -> VendorPayout:
    if payout.status == PayoutStatus.PAID:
        raise ValueError("Cannot fail a payout that has already been paid")

    payout.status = PayoutStatus.FAILED
    payout.failure_reason = reason
    payout.processed_at = _now()
    await payout.save(session=session)

    # Unstamp the vendor_orders so the balance returns to available
    orders = await Order.find({"vendor_orders.payout_id": payout.id}).to_list()
    for order in orders:
        changed = False
        for vo in order.vendor_orders:
            if vo.payout_id == payout.id:
                vo.payout_id = None
                changed = True
        if changed:
            order.updated_at = _now()
            await order.save(session=session)

    await audit_crud.log(
        action="payout.failed",
        actor_type=ActorType.SYSTEM,
        target_type="VendorPayout",
        target_id=str(payout.id),
        metadata={"reason": reason},
    )
    return payout


@transactional()
async def cancel_payout(
    payout: VendorPayout,
    *,
    actor_id: str,
    reason: Optional[str] = None,
    request: Optional[Request] = None,
    session=None,
) -> VendorPayout:
    if payout.status not in (PayoutStatus.REQUESTED, PayoutStatus.FAILED):
        raise ValueError(
            f"Cannot cancel a payout in status '{payout.status.value}'"
        )

    payout.status = PayoutStatus.CANCELLED
    payout.failure_reason = reason
    payout.processed_at = _now()
    await payout.save(session=session)

    # Unstamp vendor orders
    orders = await Order.find({"vendor_orders.payout_id": payout.id}).to_list()
    for order in orders:
        changed = False
        for vo in order.vendor_orders:
            if vo.payout_id == payout.id:
                vo.payout_id = None
                changed = True
        if changed:
            order.updated_at = _now()
            await order.save(session=session)

    await audit_crud.log(
        action="payout.cancelled",
        actor_type=ActorType.USER,
        actor_id=actor_id,
        target_type="VendorPayout",
        target_id=str(payout.id),
        metadata={"reason": reason} if reason else None,
        request=request,
    )
    return payout