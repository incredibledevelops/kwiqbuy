"""
Wallet transactions.

Each row is an immutable ledger entry. Customer.wallet_balance is the
running total; this collection is the audit trail. If they ever disagree,
this collection wins (recompute the balance from it).

Sign convention:
  - points > 0 → credit (money in)
  - points < 0 → debit (money out)
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


class WalletReason(str, Enum):
    TOPUP = "topup"                       # admin credit / promo credit
    ORDER_PAYMENT = "order_payment"       # debited at checkout
    ORDER_PARTIAL = "order_partial"       # partial wallet payment
    ADMIN_ADJUSTMENT = "admin_adjustment"
    REFERRAL_BONUS = "referral_bonus"     # future: cash bonus instead of points
    LOYALTY_CASHBACK = "loyalty_cashback" # future
    REVERSAL = "reversal"                 # admin reversal of an incorrect charge


class WalletTransaction(Document):
    customer_id: Indexed(PydanticObjectId)  # type: ignore
    phone: Indexed(str)  # type: ignore
    amount: float                            # signed; + credit, − debit
    balance_after: float                     # snapshot for quick audit
    reason: WalletReason
    order_id: Optional[PydanticObjectId] = None
    order_reference: Optional[str] = None
    note: Optional[str] = None
    created_by: Optional[str] = None         # "self" | "admin:<id>" | "system"
    created_at: datetime = Field(default_factory=_now)

    class Settings:
        name = "wallet_transactions"
        indexes = [
            "customer_id",
            "phone",
            "order_id",
            "created_at",
        ]
