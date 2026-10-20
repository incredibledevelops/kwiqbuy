from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from beanie import Document, Indexed
from pydantic import Field

from app.core.config import settings


class IdempotencyRecord(Document):
    """Records a request + response for a client-provided idempotency key."""

    key: Indexed(str)  # type: ignore
    endpoint: Indexed(str)  # type: ignore
    response_status: int = 200
    response_body: Optional[dict[str, Any]] = None

    # `expire_at` is a TTL anchor. Mongo removes the document once the
    # server clock passes this value. We use a dedicated field rather than
    # `created_at` because Mongo's TTL monitor only honors one index per
    # field, and we want the TTL independent from the audit trail.
    expire_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
        + timedelta(hours=settings.IDEMPOTENCY_TTL_HOURS)
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    class Settings:
        name = "idempotency_records"
        # Compound unique index — same key + endpoint = one record
        indexes = [
            [("key", 1), ("endpoint", 1)],
            # TTL index — Mongo deletes the doc once `expire_at` passes.
            # Single-field index required for TTL semantics.
            "expire_at",
        ]