from datetime import datetime, timezone
from typing import Optional

from beanie import PydanticObjectId

from app.core.config import settings
from app.models.customer import Customer
from app.models.loyalty import LoyaltyReason, LoyaltyTransaction


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def get_or_create_customer(
    phone: str,
    full_name: str,
    email: Optional[str] = None,
    *,
    session=None,
) -> Customer:
    existing = await Customer.find_one(Customer.phone == phone, session=session)
    if existing:
        changed = False
        if existing.full_name != full_name:
            existing.full_name = full_name
            changed = True
        if email and existing.email != email:
            existing.email = email
            changed = True
        if changed:
            existing.updated_at = _now()
            await existing.save(session=session)
        return existing

    customer = Customer(phone=phone, full_name=full_name, email=email)
    await customer.insert(session=session)
    return customer


async def get_customer_by_phone(phone: str) -> Optional[Customer]:
    return await Customer.find_one(Customer.phone == phone)


async def touch_customer_order_stats(
    customer: Customer,
    order_total: float,
    *,
    session=None,
) -> Customer:
    customer.total_orders += 1
    customer.total_spent = round(customer.total_spent + order_total, 2)
    customer.last_order_at = _now()
    customer.updated_at = _now()
    await customer.save(session=session)
    return customer


async def award_points(
    customer: Customer,
    order_id: Optional[PydanticObjectId],
    order_reference: Optional[str],
    points: int,
    reason: LoyaltyReason = LoyaltyReason.EARNED_ORDER,
    note: Optional[str] = None,
    *,
    session=None,
) -> tuple[int, LoyaltyTransaction]:
    if points <= 0:
        raise ValueError("Points must be positive when awarding")

    customer.loyalty_points += points
    customer.lifetime_points_earned += points
    customer.updated_at = _now()
    await customer.save(session=session)

    tx = LoyaltyTransaction(
        customer_id=customer.id,
        phone=customer.phone,
        points=points,
        reason=reason,
        order_id=order_id,
        order_reference=order_reference,
        note=note,
    )
    await tx.insert(session=session)
    return customer.loyalty_points, tx


async def redeem_points(
    customer: Customer,
    order_id: Optional[PydanticObjectId],
    order_reference: Optional[str],
    points: int,
    note: Optional[str] = None,
    *,
    session=None,
) -> tuple[int, float, LoyaltyTransaction]:
    if points <= 0:
        raise ValueError("Points must be positive when redeeming")
    if points > customer.loyalty_points:
        raise ValueError("Insufficient loyalty points")
    if points < settings.LOYALTY_MIN_REDEEM:
        raise ValueError(
            f"Minimum redemption is {settings.LOYALTY_MIN_REDEEM} points"
        )

    cash_value = round(points * settings.LOYALTY_POINTS_TO_CEDI, 2)

    customer.loyalty_points -= points
    customer.lifetime_points_redeemed += points
    customer.updated_at = _now()
    await customer.save(session=session)

    tx = LoyaltyTransaction(
        customer_id=customer.id,
        phone=customer.phone,
        points=-points,
        reason=LoyaltyReason.REDEEMED_ORDER,
        order_id=order_id,
        order_reference=order_reference,
        note=note or f"Redeemed for GH₵ {cash_value:.2f}",
    )
    await tx.insert(session=session)
    return customer.loyalty_points, cash_value, tx


async def adjust_points(
    phone: str,
    points: int,
    note: Optional[str] = None,
) -> tuple[Optional[Customer], Optional[LoyaltyTransaction]]:
    customer = await get_customer_by_phone(phone)
    if not customer:
        return None, None
    customer.loyalty_points += points
    if points > 0:
        customer.lifetime_points_earned += points
    else:
        customer.lifetime_points_redeemed += -points
    customer.updated_at = _now()
    await customer.save()
    tx = LoyaltyTransaction(
        customer_id=customer.id,
        phone=customer.phone,
        points=points,
        reason=LoyaltyReason.ADMIN_ADJUSTMENT,
        note=note or "Manual admin adjustment",
    )
    await tx.insert()
    return customer, tx


async def history(phone: str, limit: int = 50) -> list[LoyaltyTransaction]:
    return (
        await LoyaltyTransaction.find(LoyaltyTransaction.phone == phone)
        .sort(-LoyaltyTransaction.created_at)
        .limit(limit)
        .to_list()
    )


def points_to_cash(points: int) -> float:
    return round(points * settings.LOYALTY_POINTS_TO_CEDI, 2)


def cash_to_points(amount: float) -> int:
    return int(amount * settings.LOYALTY_POINTS_PER_CEDI)