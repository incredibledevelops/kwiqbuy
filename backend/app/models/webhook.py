from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


class WebhookEvent(str, Enum):
    ORDER_CREATED = "order.created"
    ORDER_STATUS_CHANGED = "order.status_changed"
    ORDER_DELIVERED = "order.delivered"
    PAYOUT_PAID = "payout.paid"
    SUBSCRIPTION_ACTIVATED = "subscription.activated"
    REVIEW_POSTED = "review.posted"


class VendorWebhook(Document):
    vendor_id: Indexed(PydanticObjectId)  # type: ignore
    url: str
    description: Optional[str] = None
    secret: str
    events: List[str] = Field(default_factory=lambda: [e.value for e in WebhookEvent])
    is_active: bool = True
    last_success_at: Optional[datetime] = None
    last_failure_at: Optional[datetime] = None
    consecutive_failures: int = 0
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)

    class Settings:
        name = "vendor_webhooks"
        indexes = ["vendor_id", "is_active"]


class WebhookStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    DEAD = "dead"


class WebhookDelivery(Document):
    webhook_id: Indexed(PydanticObjectId)  # type: ignore
    vendor_id: Indexed(PydanticObjectId)  # type: ignore
    event: str
    payload: dict
    url: str

    status: WebhookStatus = WebhookStatus.PENDING
    attempts: int = 0
    last_attempt_at: Optional[datetime] = None
    next_attempt_at: Optional[datetime] = None

    response_status: Optional[int] = None
    response_body: Optional[str] = None
    error: Optional[str] = None

    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)

    class Settings:
        name = "webhook_deliveries"
        indexes = [
            "webhook_id",
            "vendor_id",
            "status",
            "next_attempt_at",
            "created_at",
        ]
