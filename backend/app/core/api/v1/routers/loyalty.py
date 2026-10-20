from fastapi import APIRouter, Depends, HTTPException

from app.core.config import settings
from app.core.deps import get_current_admin
from app.crud import loyalty as loyalty_crud
from app.schemas.loyalty import (
    LoyaltyAdjustRequest,
    LoyaltyBalanceOut,
    LoyaltyHistoryOut,
    LoyaltyRedeemRequest,
    LoyaltyTransactionOut,
)

router = APIRouter(prefix="/loyalty", tags=["Loyalty"])


def _balance_out(customer) -> LoyaltyBalanceOut:
    return LoyaltyBalanceOut(
        phone=customer.phone,
        full_name=customer.full_name,
        points=customer.loyalty_points,
        lifetime_points_earned=customer.lifetime_points_earned,
        lifetime_points_redeemed=customer.lifetime_points_redeemed,
        cash_value=loyalty_crud.points_to_cash(customer.loyalty_points),
        min_redeem_points=settings.LOYALTY_MIN_REDEEM,
        # Rate the client can use to preview redemptions without drifting
        # from the server's real calculation.
        points_to_cash_rate=settings.LOYALTY_POINTS_TO_CEDI,
    )


@router.get("/balance/{phone}", response_model=LoyaltyBalanceOut)
async def get_balance(phone: str):
    customer = await loyalty_crud.get_customer_by_phone(phone)
    if not customer:
        # Return zeroed balance for unknown phone — do not 404, frontend
        # treats "no customer yet" as "0 points"
        return LoyaltyBalanceOut(
            phone=phone,
            full_name=None,
            points=0,
            lifetime_points_earned=0,
            lifetime_points_redeemed=0,
            cash_value=0.0,
            min_redeem_points=settings.LOYALTY_MIN_REDEEM,
            points_to_cash_rate=settings.LOYALTY_POINTS_TO_CEDI,
        )
    return _balance_out(customer)


@router.get("/history/{phone}", response_model=LoyaltyHistoryOut)
async def get_history(phone: str, limit: int = 50):
    customer = await loyalty_crud.get_customer_by_phone(phone)
    txs = await loyalty_crud.history(phone, limit=limit)

    balance = (
        _balance_out(customer)
        if customer
        else LoyaltyBalanceOut(
            phone=phone,
            full_name=None,
            points=0,
            lifetime_points_earned=0,
            lifetime_points_redeemed=0,
            cash_value=0.0,
            min_redeem_points=settings.LOYALTY_MIN_REDEEM,
            points_to_cash_rate=settings.LOYALTY_POINTS_TO_CEDI,
        )
    )

    return LoyaltyHistoryOut(
        balance=balance,
        transactions=[
            LoyaltyTransactionOut(
                id=str(t.id),
                points=t.points,
                reason=t.reason,
                order_reference=t.order_reference,
                note=t.note,
                created_at=t.created_at,
            )
            for t in txs
        ],
    )


# ---------- ADMIN ----------
@router.post(
    "/admin/adjust",
    response_model=LoyaltyBalanceOut,
    dependencies=[Depends(get_current_admin)],
)
async def admin_adjust(payload: LoyaltyAdjustRequest):
    customer, _ = await loyalty_crud.adjust_points(
        phone=payload.phone,
        points=payload.points,
        note=payload.note,
    )
    if not customer:
        raise HTTPException(404, "Customer with that phone not found")
    return _balance_out(customer)