from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field


class PaymentStatus(str, Enum):
    INITIALIZED = "initialized"
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    ABANDONED = "abandoned"


class Payment(Document):
    order_id: PydanticObjectId
    reference: Indexed(str, unique=True)  # type: ignore
    paystack_reference: Optional[str] = None
    authorization_url: Optional[str] = None
    access_code: Optional[str] = None
    amount: float
    currency: str = "GHS"
    channel: Optional[str] = None
    status: PaymentStatus = PaymentStatus.INITIALIZED
    gateway_response: Optional[dict[str, Any]] = None
    paid_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "payments"