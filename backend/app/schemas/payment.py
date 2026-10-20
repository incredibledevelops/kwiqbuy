from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, EmailStr


class PaymentInitialize(BaseModel):
    order_id: Optional[str] = None
    email: EmailStr


class PaymentInitializeOut(BaseModel):
    authorization_url: str
    access_code: str
    reference: str
    amount: float


class PaymentVerifyOut(BaseModel):
    reference: str
    status: str
    amount: float
    currency: str
    channel: Optional[str] = None
    paid_at: Optional[datetime] = None
    gateway_response: Optional[dict[str, Any]] = None


class PaymentOut(BaseModel):
    id: str
    order_id: str
    reference: str
    amount: float
    currency: str
    status: str
    channel: Optional[str] = None
    created_at: datetime
    paid_at: Optional[datetime] = None