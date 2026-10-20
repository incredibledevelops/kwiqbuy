"""
Idempotency CRUD.

The primary expiration mechanism is the Mongo TTL index on
`IdempotencyRecord.expire_at` (see models/idempotency.py). This module
also exposes a `purge_expired()` helper for scheduled cleanup jobs, so
we don't depend exclusively on the TTL monitor (which is best-effort and
only fires every ~60s).
"""
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from app.core.config import settings
from app.models.idempotency import IdempotencyRecord

logger = logging.getLogger(__name__)


async def get(key: str, endpoint: str) -> Optional[IdempotencyRecord]:
    return await IdempotencyRecord.find_one(
        IdempotencyRecord.key == key,
        IdempotencyRecord.endpoint == endpoint,
    )


async def save(
    key: str,
    endpoint: str,
    body: dict[str, Any],
    status_code: int = 200,
) -> IdempotencyRecord:
    """Insert a fresh record, ignoring an existing identical one."""
    existing = await get(key, endpoint)
    if existing:
        return existing

    record = IdempotencyRecord(
        key=key,
        endpoint=endpoint,
        response_status=status_code,
        response_body=body,
    )
    await record.insert()
    return record


async def purge_expired() -> int:
    """
    Delete all records whose `expire_at` is in the past.
    Safe to call from a periodic scheduler (cron / APScheduler).
    Returns the number of records removed.
    """
    now = datetime.now(timezone.utc)
    result = await IdempotencyRecord.find(
        IdempotencyRecord.expire_at < now
    ).delete()
    deleted = getattr(result, "deleted_count", None)
    if deleted is None:
        # Older Beanie returns None; treat as best-effort success.
        logger.info("[idempotency] purge ran (count unknown)")
        return 0
    if deleted:
        logger.info("[idempotency] purged %d expired records", deleted)
    return int(deleted)