"""
Customer-facing wallet endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException

from app.core.config import settings
from app.core.deps import get_current_customer
from app.crud import wallet as wallet_crud
from app.models.customer import Customer
from app.models.wallet import WalletReason, WalletTransaction
from app.schemas.wallet import (
    WalletBalanceOut,
    WalletComputeIn,
    WalletComputeOut,
    WalletHistoryOut,
    WalletTransactionOut,
)

router = APIRouter(prefix="/wallet", tags=["Wallet"])


def _balance_out(c: Customer) -> WalletBalanceOut:
    return WalletBalanceOut(
        phone=c.phone,
        customer_name=c.full_name,
        balance=round(c.wallet_balance, 2),
        lifetime_credited=round(c.lifetime_wallet_credited, 2),
        lifetime_spent=round(c.lifetime_wallet_spent, 2),
        currency=settings.CURRENCY,
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


@router.get("/me", response_model=WalletBalanceOut)
async def my_wallet(current: Customer = Depends(get_current_customer)):
    return _balance_out(current)


@router.get("/me/history", response_model=WalletHistoryOut)
async def my_wallet_history(
    limit: int = 50,
    skip: int = 0,
    current: Customer = Depends(get_current_customer),
):
    txs = await wallet_crud.list_transactions(
        phone=current.phone, limit=limit, skip=skip
    )
    return WalletHistoryOut(
        balance=_balance_out(current),
        transactions=[_tx_out(t) for t in txs],
    )


@router.post("/me/compute", response_model=WalletComputeOut)
async def compute_wallet(
    payload: WalletComputeIn,
    current: Customer = Depends(get_current_customer),
):
    applied = wallet_crud.compute_wallet_application(
        customer_balance=current.wallet_balance,
        amount_due=payload.order_total,
        max_coverage_pct=settings.WALLET_MAX_COVERAGE_PCT,
    )
    return WalletComputeOut(
        customer_balance=round(current.wallet_balance, 2),
        order_total=payload.order_total,
        wallet_applied=applied,
        amount_due_external=round(payload.order_total - applied, 2),
        max_coverage_pct=settings.WALLET_MAX_COVERAGE_PCT,
    )
