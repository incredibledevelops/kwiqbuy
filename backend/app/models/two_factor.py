from datetime import datetime, timezone
from typing import List, Optional

from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Admin2FA(Document):
    user_id: Indexed(PydanticObjectId, unique=True)  # type: ignore
    secret: str
    enabled: bool = False
    verified_at: Optional[datetime] = None
    recovery_codes: List[str] = Field(default_factory=list)
    last_used_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)

    class Settings:
        name = "admin_2fa"
        indexes = ["user_id"]
