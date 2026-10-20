from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.wallet import WalletReason


class WalletBalanceOut(BaseModel):
    phone: str
    customer_name: Optional[str] = None
    balance: float = 0.0
    lifetime_credited: float = 0.0
    lifetime_spent: float = 0.0
    currency: str = "GHS"


class WalletTransactionOut(BaseModel):
    id: str
    amount: float
    balance_after: float
    reason: WalletReason
    order_reference: Optional[str] = None
    note: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime


class WalletHistoryOut(BaseModel):
    balance: WalletBalanceOut
    transactions: List[WalletTransactionOut] = Field(default_factory=list)


class WalletAdminAdjustIn(BaseModel):
    phone: str
    amount: float = Field(description="Positive to credit, negative to debit")
    note: Optional[str] = Field(default=None, max_length=500)


class WalletComputeIn(BaseModel):
    """Preview how much wallet would apply to an order of a given size."""
    order_total: float = Field(ge=0)


class WalletComputeOut(BaseModel):
    customer_balance: float
    order_total: float
    wallet_applied: float
    amount_due_external: float
    max_coverage_pct: float
