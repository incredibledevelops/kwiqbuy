"""
Admin wallet adjustments + lookup.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.core.deps import get_current_admin
from app.crud import audit as audit_crud
from app.crud import loyalty as loyalty_crud
from app.crud import wallet as wallet_crud
from app.models.audit_log import ActorType
from app.models.user import User
from app.models.wallet import WalletReason, WalletTransaction
from app.schemas.wallet import (
    WalletAdminAdjustIn,
    WalletBalanceOut,
    WalletHistoryOut,
    WalletTransactionOut,
)

router = APIRouter(prefix="/admin/wallet", tags=["Admin Wallet"])


def _balance_out(c) -> WalletBalanceOut:
    return WalletBalanceOut(
        phone=c.phone,
        customer_name=c.full_name,
        balance=round(c.wallet_balance, 2),
        lifetime_credited=round(c.lifetime_wallet_credited, 2),
        lifetime_spent=round(c.lifetime_wallet_spent, 2),
    )


def _tx_out(t: WalletTransaction) -> WalletTransactionOut:
    return WalletTransactionOut(
        id=str(t.id),
        amount=t.amount,
        balance_after=t.balance_after,
        reason=t.reason,
        order_reference=t.order_reference,
        note=t.note,
        created_by=t.created_by,
        created_at=t.created_at,
    )


@router.post("/adjust", response_model=WalletBalanceOut)
async def admin_adjust(
    payload: WalletAdminAdjustIn,
    request: Request,
    current_user: User = Depends(get_current_admin),
):
    customer = await loyalty_crud.get_customer_by_phone(payload.phone)
    if not customer:
        raise HTTPException(404, "No customer with that phone number")

    if payload.amount == 0:
        raise HTTPException(400, "Amount cannot be zero")

    try:
        if payload.amount > 0:
            await wallet_crud.credit(
                customer,
                payload.amount,
                reason=WalletReason.ADMIN_ADJUSTMENT,
                note=payload.note or f"Credit by {current_user.email}",
                created_by=f"admin:{current_user.id}",
            )
        else:
            await wallet_crud.debit(
                customer,
                abs(payload.amount),
                reason=WalletReason.ADMIN_ADJUSTMENT,
                note=payload.note or f"Debit by {current_user.email}",
                created_by=f"admin:{current_user.id}",
            )
    except ValueError as e:
        raise HTTPException(400, str(e))

    await audit_crud.log(
        action="wallet.adjusted",
        actor_type=ActorType.USER,
        actor_id=str(current_user.id),
        actor_email=current_user.email,
        target_type="Customer",
        target_id=str(customer.id),
        after={"amount": payload.amount, "new_balance": customer.wallet_balance},
        metadata={"note": payload.note} if payload.note else None,
        request=request,
    )
    return _balance_out(customer)


@router.get("/history/{phone}", response_model=WalletHistoryOut)
async def admin_history(
    phone: str,
    limit: int = Query(100, ge=1, le=500),
    skip: int = Query(0, ge=0),
    _=Depends(get_current_admin),
):
    """
    Return the customer's current balance + history.

    Unlike a normal "find-or-404" endpoint, this returns a zeroed balance
    when the customer doesn't exist yet — the admin "lookup" UI can then
    show a "no wallet yet" state instead of an error.
    """
    customer = await loyalty_crud.get_customer_by_phone(phone)
    if not customer:
        return WalletHistoryOut(
            balance=WalletBalanceOut(
                phone=phone,
                customer_name=None,
                balance=0.0,
                lifetime_credited=0.0,
                lifetime_spent=0.0,
            ),
            transactions=[],
        )

    txs = await wallet_crud.list_transactions(phone=phone, limit=limit, skip=skip)
    return WalletHistoryOut(
        balance=_balance_out(customer),
        transactions=[_tx_out(t) for t in txs],
    )