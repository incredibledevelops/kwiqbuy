from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional

from beanie import Document, Indexed
from pydantic import Field

from app.core.config import settings


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=settings.AUDIT_LOG_RETENTION_DAYS)


class ActorType(str, Enum):
    USER = "user"
    VENDOR = "vendor"
    CUSTOMER = "customer"
    RIDER = "rider"
    SYSTEM = "system"


class AuditLog(Document):
    actor_type: ActorType = ActorType.SYSTEM
    actor_id: Optional[str] = None
    actor_email: Optional[str] = None
    action: Indexed(str)  # type: ignore
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    before: Optional[dict[str, Any]] = None
    after: Optional[dict[str, Any]] = None
    metadata: Optional[dict[str, Any]] = None
    ip: Optional[str] = None
    user_agent: Optional[str] = None
    at: datetime = Field(default_factory=_now)
    expire_at: datetime = Field(default_factory=_expiry)

    class Settings:
        name = "audit_logs"
        indexes = ["action", "actor_id", "target_id", "expire_at"]
