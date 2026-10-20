"""
Wallet CRUD.

Every mutation writes a WalletTransaction row AND updates
Customer.wallet_balance atomically. Both happen in one call so callers
never have to remember to do them separately.
"""
from datetime import datetime, timezone
from typing import Optional

from beanie import PydanticObjectId

from app.models.customer import Customer
from app.models.wallet import WalletReason, WalletTransaction


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _r2(v: float) -> float:
    return round(float(v), 2)


async def list_transactions(
    *,
    phone: Optional[str] = None,
    customer_id: Optional[PydanticObjectId] = None,
    limit: int = 100,
    skip: int = 0,
) -> list[WalletTransaction]:
    query = WalletTransaction.find()
    if phone:
        query = query.find(WalletTransaction.phone == phone)
    elif customer_id:
        query = query.find(WalletTransaction.customer_id == customer_id)
    return (
        await query.sort(-WalletTransaction.created_at).skip(skip).limit(limit).to_list()
    )


async def _apply(
    customer: Customer,
    *,
    amount: float,
    reason: WalletReason,
    order_id: Optional[PydanticObjectId] = None,
    order_reference: Optional[str] = None,
    note: Optional[str] = None,
    created_by: str = "system",
    session=None,
) -> WalletTransaction:
    """
    Apply a signed amount to the wallet. Both the Customer doc and the
    WalletTransaction are written.
    """
    amount = _r2(amount)
    if amount == 0:
        raise ValueError("Wallet amount cannot be zero")

    new_balance = _r2(customer.wallet_balance + amount)
    if new_balance < 0:
        raise ValueError("Insufficient wallet balance")

    customer.wallet_balance = new_balance
    if amount > 0:
        customer.lifetime_wallet_credited = _r2(
            customer.lifetime_wallet_credited + amount
        )
    else:
        customer.lifetime_wallet_spent = _r2(
            customer.lifetime_wallet_spent + abs(amount)
        )
    customer.updated_at = _now()
    await customer.save(session=session)

    tx = WalletTransaction(
        customer_id=customer.id,
        phone=customer.phone,
        amount=amount,
        balance_after=new_balance,
        reason=reason,
        order_id=order_id,
        order_reference=order_reference,
        note=note,
        created_by=created_by,
    )
    await tx.insert(session=session)
    return tx


async def credit(
    customer: Customer,
    amount: float,
    *,
    reason: WalletReason = WalletReason.TOPUP,
    note: Optional[str] = None,
    created_by: str = "system",
    session=None,
) -> WalletTransaction:
    if amount <= 0:
        raise ValueError("Credit amount must be positive")
    return await _apply(
        customer,
        amount=amount,
        reason=reason,
        note=note,
        created_by=created_by,
        session=session,
    )


async def debit(
    customer: Customer,
    amount: float,
    *,
    reason: WalletReason = WalletReason.ORDER_PAYMENT,
    order_id: Optional[PydanticObjectId] = None,
    order_reference: Optional[str] = None,
    note: Optional[str] = None,
    created_by: str = "customer",
    session=None,
) -> WalletTransaction:
    if amount <= 0:
        raise ValueError("Debit amount must be positive")
    if amount > customer.wallet_balance:
        raise ValueError("Insufficient wallet balance")
    return await _apply(
        customer,
        amount=-amount,
        reason=reason,
        order_id=order_id,
        order_reference=order_reference,
        note=note,
        created_by=created_by,
        session=session,
    )


def compute_wallet_application(
    *,
    customer_balance: float,
    amount_due: float,
    max_coverage_pct: float,
) -> float:
    """
    How much of `amount_due` can be covered by wallet.
    Capped by (a) the balance, (b) amount_due, (c) max_coverage_pct of amount_due.
    """
    amount_due = _r2(amount_due)
    if amount_due <= 0 or customer_balance <= 0:
        return 0.0
    coverage_cap = _r2(amount_due * (max_coverage_pct / 100.0))
    return _r2(min(customer_balance, amount_due, coverage_cap))
