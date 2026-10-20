from datetime import datetime, timezone
from typing import Optional

from beanie import PydanticObjectId

from app.models.payment import Payment, PaymentStatus


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def create_payment(
    order_id: str,
    reference: str,
    amount: float,
    currency: str = "GHS",
    authorization_url: Optional[str] = None,
    access_code: Optional[str] = None,
) -> Payment:
    payment = Payment(
        order_id=PydanticObjectId(order_id),
        reference=reference,
        amount=amount,
        currency=currency,
        authorization_url=authorization_url,
        access_code=access_code,
        status=PaymentStatus.INITIALIZED,
    )
    await payment.insert()
    return payment


async def get_by_reference(reference: str) -> Optional[Payment]:
    return await Payment.find_one(Payment.reference == reference)


async def get_by_order(order_id: str) -> Optional[Payment]:
    return await Payment.find_one(
        Payment.order_id == PydanticObjectId(order_id)
    )


async def mark_paid(
    payment: Payment,
    channel: Optional[str] = None,
    gateway_response: Optional[dict] = None,
    paystack_reference: Optional[str] = None,
) -> Payment:
    payment.status = PaymentStatus.SUCCESS
    payment.channel = channel
    payment.gateway_response = gateway_response
    payment.paystack_reference = paystack_reference or payment.reference
    payment.paid_at = _now()
    payment.updated_at = _now()
    await payment.save()
    return payment


async def mark_failed(
    payment: Payment,
    gateway_response: Optional[dict] = None,
) -> Payment:
    payment.status = PaymentStatus.FAILED
    payment.gateway_response = gateway_response
    payment.updated_at = _now()
    await payment.save()
    return payment


async def list_payments(limit: int = 100, skip: int = 0) -> list[Payment]:
    return (
        await Payment.find_all()
        .sort(-Payment.created_at)
        .skip(skip)
        .limit(limit)
        .to_list()
    )