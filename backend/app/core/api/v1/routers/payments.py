import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from app.core.config import settings
from app.core.deps import get_current_staff_or_admin
from app.core.email import send_order_receipt
from app.core.limiter import limiter
from app.core.paystack import PaystackError, paystack_client
from app.core.sms import sms_loyalty_earned, sms_order_paid
from app.crud import loyalty as loyalty_crud
from app.crud import order as order_crud
from app.crud import payment as payment_crud
from app.crud import payout as payout_crud
from app.crud import subscription as sub_crud
from app.models.order import OrderStatus
from app.models.payment import Payment, PaymentStatus
from app.schemas.payment import (
    PaymentInitialize,
    PaymentInitializeOut,
    PaymentOut,
    PaymentVerifyOut,
)
from app.utils.generators import generate_payment_reference

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["Payments"])


def _to_out(p: Payment) -> PaymentOut:
    return PaymentOut(
        id=str(p.id),
        order_id=str(p.order_id),
        reference=p.reference,
        amount=p.amount,
        currency=p.currency,
        status=p.status.value,
        channel=p.channel,
        created_at=p.created_at,
        paid_at=p.paid_at,
    )


async def _on_paid(order, was_already_success: bool) -> None:
    if not order:
        return
    earned = 0
    try:
        earned = await order_crud.on_order_paid(order)
    except Exception:
        logger.exception("Failed to process on_order_paid for %s", order.reference)

    if was_already_success:
        return

    try:
        await send_order_receipt(order)
    except Exception:
        logger.exception("Failed to send receipt for %s", order.reference)

    try:
        await sms_order_paid(order)
    except Exception:
        logger.exception("Failed to send paid SMS for %s", order.reference)

    if earned > 0:
        try:
            customer = await loyalty_crud.get_customer_by_phone(order.customer.phone)
            if customer:
                await sms_loyalty_earned(order, earned, customer.loyalty_points)
        except Exception:
            logger.exception("Failed to send loyalty SMS for %s", order.reference)


@router.post(
    "/initialize",
    response_model=PaymentInitializeOut,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("20/minute")
async def initialize_payment(request: Request, payload: PaymentInitialize):
    if not payload.order_id:
        raise HTTPException(400, "order_id is required")

    order = await order_crud.get_order(payload.order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    if order.status not in (OrderStatus.PENDING, OrderStatus.FAILED):
        raise HTTPException(400, f"Order already in status '{order.status.value}'")

    amount = float(order.amount_due_external or 0)
    if amount <= 0:
        raise HTTPException(400, "This order is fully covered by wallet — no payment required.")

    reference = generate_payment_reference(order.reference)
    amount_pesewas = int(round(amount * 100))

    try:
        resp = await paystack_client.initialize_transaction(
            email=payload.email,
            amount_pesewas=amount_pesewas,
            reference=reference,
            currency=settings.CURRENCY,
            metadata={
                "order_reference": order.reference,
                "order_id": str(order.id),
                "customer_name": order.customer.full_name,
                "customer_phone": order.customer.phone,
                "wallet_applied": order.wallet_applied,
                "vendor_count": len(order.vendor_orders),
            },
            channels=["mobile_money", "card", "bank_transfer"],
        )
    except PaystackError as e:
        raise HTTPException(502, f"Paystack error: {e.message}")

    data = resp["data"]

    await payment_crud.create_payment(
        order_id=str(order.id),
        reference=reference,
        amount=amount,
        currency=settings.CURRENCY,
        authorization_url=data.get("authorization_url"),
        access_code=data.get("access_code"),
    )
    await order_crud.attach_payment_reference(order, reference)

    return PaymentInitializeOut(
        authorization_url=data["authorization_url"],
        access_code=data["access_code"],
        reference=reference,
        amount=amount,
    )


@router.get("/verify/{reference}", response_model=PaymentVerifyOut)
async def verify_payment(reference: str):
    payment = await payment_crud.get_by_reference(reference)
    if not payment:
        raise HTTPException(404, "Payment record not found")

    try:
        resp = await paystack_client.verify_transaction(reference)
    except PaystackError as e:
        raise HTTPException(502, f"Paystack error: {e.message}")

    data = resp["data"]
    ps_status = data.get("status")
    
    # Handle subscriptions verify
    metadata = data.get("metadata") or {}
    if metadata.get("type") == "vendor_subscription":
        if ps_status == "success":
            sub_id = metadata.get("subscription_id")
            sub = await sub_crud.get_subscription_by_id(sub_id)
            if sub and sub.status != sub.status.ACTIVE:
                await sub_crud.activate_subscription(sub, paystack_reference=reference)
        return PaymentVerifyOut(
            reference=reference, 
            status=ps_status or "success", 
            amount=data.get("amount", 0) / 100,
            currency=data.get("currency", "GHS"), 
            channel=data.get("channel"), 
            gateway_response=data,
        )

    # Handle standard orders verify
    order = await order_crud.get_order_by_reference(metadata.get("order_reference", ""))
    expected = int(round(payment.amount * 100))
    received = int(data.get("amount", 0))
    
    if ps_status == "success" and received != expected:
        logger.error("Amount mismatch for %s: expected %d, got %d", reference, expected, received)
        raise HTTPException(400, "Payment amount does not match order total")

    if ps_status == "success":
        was_success = payment.status == PaymentStatus.SUCCESS
        await payment_crud.mark_paid(payment, channel=data.get("channel"), gateway_response=data, paystack_reference=data.get("reference"))
        await _on_paid(order, was_success)
    elif ps_status in ("failed", "abandoned"):
        await payment_crud.mark_failed(payment, gateway_response=data)
        if order:
            order.status = OrderStatus.FAILED
            await order.save()

    return PaymentVerifyOut(
        reference=reference, 
        status=ps_status or payment.status.value, 
        amount=data.get("amount", 0) / 100,
        currency=data.get("currency", settings.CURRENCY), 
        channel=data.get("channel"), 
        gateway_response=data,
    )


@router.post("/webhook", include_in_schema=False)
async def paystack_webhook(
    request: Request,
    x_paystack_signature: str | None = Header(None, alias="x-paystack-signature"),
):
    raw = await request.body()
    if not x_paystack_signature or not paystack_client.verify_webhook_signature(raw, x_paystack_signature):
        raise HTTPException(401, "Invalid signature")

    try:
        event = await request.json()
    except Exception:
        raise HTTPException(400, "Invalid JSON")

    event_type = event.get("event")
    data = event.get("data", {})

    # ---------- Transfer events (payouts) ----------
    if event_type in ("transfer.success", "transfer.failed", "transfer.reversed"):
        reference = data.get("reference")
        if not reference or not str(reference).startswith("PAYOUT-"):
            return {"status": "ignored"}
        payout_id = str(reference).replace("PAYOUT-", "", 1)
        payout = await payout_crud.get_payout(payout_id)
        if not payout:
            return {"status": "not_found"}
        if event_type == "transfer.success":
            await payout_crud.mark_paid(payout)
        else:
            reason = data.get("reason") or event_type
            try:
                await payout_crud.mark_failed(payout, reason)
            except ValueError:
                pass
        return {"status": "ok"}

    # ---------- Charge events (customer payments & subscriptions) ----------
    reference = data.get("reference")
    if not reference:
        return {"status": "ignored"}

    metadata = data.get("metadata") or {}

    # Subscription payment
    if metadata.get("type") == "vendor_subscription" and event_type == "charge.success":
        sub_id = metadata.get("subscription_id")
        sub = await sub_crud.get_subscription_by_id(sub_id)
        if sub and sub.status != sub.status.ACTIVE:
            await sub_crud.activate_subscription(sub, paystack_reference=reference)
        return {"status": "ok"}

    # Standard order payment
    payment = await payment_crud.get_by_reference(reference)
    order_ref = metadata.get("order_reference", "")
    order = await order_crud.get_order_by_reference(order_ref) if order_ref else None

    if event_type == "charge.success" and payment:
        expected = int(round(payment.amount * 100))
        received = int(data.get("amount", 0))
        if expected != received:
            logger.error("webhook amount mismatch for %s: expected %d got %d", reference, expected, received)
            return {"status": "amount_mismatch"}

    if event_type == "charge.success":
        was_success = payment and payment.status == PaymentStatus.SUCCESS
        if payment:
            await payment_crud.mark_paid(payment, channel=data.get("channel"), gateway_response=data, paystack_reference=data.get("reference"))
        await _on_paid(order, bool(was_success))
    elif event_type in ("charge.failed", "transfer.failed"):
        if payment:
            await payment_crud.mark_failed(payment, gateway_response=data)
        if order:
            order.status = OrderStatus.FAILED
            await order.save()

    return {"status": "ok"}


@router.get("", response_model=list[PaymentOut])
async def list_payments(
    limit: int = 100,
    skip: int = 0,
    _=Depends(get_current_staff_or_admin),
):
    payments = await payment_crud.list_payments(limit=limit, skip=skip)
    return [_to_out(p) for p in payments]