from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel

from app.models.audit_log import ActorType


class AuditLogOut(BaseModel):
    id: str
    actor_type: ActorType
    actor_id: Optional[str] = None
    actor_email: Optional[str] = None
    action: str
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    before: Optional[dict[str, Any]] = None
    after: Optional[dict[str, Any]] = None
    metadata: Optional[dict[str, Any]] = None
    ip: Optional[str] = None
    user_agent: Optional[str] = None
    at: datetime


class AuditLogListOut(BaseModel):
    items: list[AuditLogOut]
    total: int