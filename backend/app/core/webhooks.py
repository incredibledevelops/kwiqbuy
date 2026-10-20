import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from beanie import PydanticObjectId

from app.core.config import settings
from app.models.webhook import VendorWebhook, WebhookDelivery, WebhookStatus

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _sign(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


def _backoff_seconds(attempt: int) -> int:
    return {1: 60, 2: 300, 3: 900}.get(attempt, 900)


async def emit(
    vendor_id: PydanticObjectId,
    event: str,
    payload: dict[str, Any],
) -> int:
    if not settings.WEBHOOKS_ENABLED:
        return 0

    webhooks = await VendorWebhook.find(
        VendorWebhook.vendor_id == vendor_id,
        VendorWebhook.is_active == True,  # noqa: E712
    ).to_list()

    target_hooks = [w for w in webhooks if event in (w.events or [])]
    if not target_hooks:
        return 0

    created = 0
    for wh in target_hooks:
        delivery = WebhookDelivery(
            webhook_id=wh.id,
            vendor_id=vendor_id,
            event=event,
            payload=payload,
            url=wh.url,
            status=WebhookStatus.PENDING,
        )
        await delivery.insert()
        created += 1
        await dispatch(delivery, secret=wh.secret)

    return created


async def dispatch(delivery: WebhookDelivery, *, secret: str) -> bool:
    body_bytes = json.dumps(delivery.payload, default=str).encode("utf-8")
    signature = _sign(secret, body_bytes)

    headers = {
        "Content-Type": "application/json",
        "X-KwiqBuy-Event": delivery.event,
        "X-KwiqBuy-Signature": signature,
        "X-KwiqBuy-Delivery-Id": str(delivery.id),
    }

    delivery.attempts += 1
    delivery.last_attempt_at = _now()
    delivery.updated_at = _now()

    try:
        async with httpx.AsyncClient(timeout=settings.WEBHOOK_TIMEOUT_SECONDS) as client:
            resp = await client.post(delivery.url, content=body_bytes, headers=headers)
        delivery.response_status = resp.status_code
        delivery.response_body = resp.text[:2000]

        if 200 <= resp.status_code < 300:
            delivery.status = WebhookStatus.SUCCESS
            delivery.next_attempt_at = None
            await delivery.save()
            await _mark_webhook_result(delivery.webhook_id, success=True)
            return True

        delivery.error = f"HTTP {resp.status_code}"
        return await _schedule_retry(delivery)
    except Exception as e:
        delivery.error = f"{type(e).__name__}: {e}"
        logger.warning("Webhook delivery %s failed: %s", delivery.id, delivery.error)
        return await _schedule_retry(delivery)


async def _schedule_retry(delivery: WebhookDelivery) -> bool:
    if delivery.attempts >= settings.WEBHOOK_MAX_ATTEMPTS:
        delivery.status = WebhookStatus.DEAD
        delivery.next_attempt_at = None
        await delivery.save()
        await _mark_webhook_result(delivery.webhook_id, success=False)
        return False

    delivery.status = WebhookStatus.FAILED
    delivery.next_attempt_at = _now() + timedelta(seconds=_backoff_seconds(delivery.attempts))
    await delivery.save()
    return False


async def _mark_webhook_result(webhook_id: PydanticObjectId, *, success: bool) -> None:
    wh = await VendorWebhook.get(webhook_id)
    if not wh:
        return
    now = _now()
    if success:
        wh.last_success_at = now
        wh.consecutive_failures = 0
    else:
        wh.last_failure_at = now
        wh.consecutive_failures += 1
    wh.updated_at = now
    await wh.save()


async def retry_pending() -> int:
    now = _now()
    rows = await WebhookDelivery.find(
        WebhookDelivery.status == WebhookStatus.FAILED,
        WebhookDelivery.next_attempt_at != None,  # noqa: E711
        WebhookDelivery.next_attempt_at <= now,
    ).limit(100).to_list()

    dispatched = 0
    for d in rows:
        wh = await VendorWebhook.get(d.webhook_id)
        if not wh or not wh.is_active:
            d.status = WebhookStatus.DEAD
            d.error = "webhook inactive or missing"
            await d.save()
            continue
        await dispatch(d, secret=wh.secret)
        dispatched += 1

    return dispatched
