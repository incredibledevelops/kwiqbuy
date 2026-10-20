import json
import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.config import settings
from app.core.deps import get_current_vendor
from app.core.webhooks import _sign
from app.crud import webhook as wh_crud
from app.models.user import User
from app.models.webhook import (
    VendorWebhook, WebhookDelivery, WebhookEvent,
)
from app.schemas.webhook import (
    WebhookCreate, WebhookDeliveryOut, WebhookOut, WebhookTestOut,
    WebhookUpdate, WebhookWithSecretOut,
)

router = APIRouter(prefix="/vendor/webhooks", tags=["Vendor Webhooks"])


def _out(w: VendorWebhook) -> WebhookOut:
    return WebhookOut(
        id=str(w.id),
        url=w.url,
        description=w.description,
        events=w.events,
        is_active=w.is_active,
        last_success_at=w.last_success_at,
        last_failure_at=w.last_failure_at,
        consecutive_failures=w.consecutive_failures,
        created_at=w.created_at,
        updated_at=w.updated_at,
    )


def _out_with_secret(w: VendorWebhook, secret: str) -> WebhookWithSecretOut:
    return WebhookWithSecretOut(
        id=str(w.id), url=w.url, description=w.description,
        events=w.events, is_active=w.is_active,
        last_success_at=w.last_success_at, last_failure_at=w.last_failure_at,
        consecutive_failures=w.consecutive_failures,
        created_at=w.created_at, updated_at=w.updated_at, secret=secret,
    )


def _delivery_out(d: WebhookDelivery) -> WebhookDeliveryOut:
    return WebhookDeliveryOut(
        id=str(d.id), event=d.event, url=d.url, status=d.status,
        attempts=d.attempts, response_status=d.response_status,
        response_body=d.response_body, error=d.error,
        next_attempt_at=d.next_attempt_at, created_at=d.created_at,
    )


@router.get("/events")
async def available_events():
    return {"events": [e.value for e in WebhookEvent]}


@router.get("", response_model=list[WebhookOut])
async def list_webhooks(user: User = Depends(get_current_vendor)):
    rows = await wh_crud.list_for_vendor(str(user.vendor_id))
    return [_out(r) for r in rows]


@router.post("", response_model=WebhookWithSecretOut, status_code=status.HTTP_201_CREATED)
async def create_webhook(payload: WebhookCreate, user: User = Depends(get_current_vendor)):
    count = await wh_crud.count_for_vendor(str(user.vendor_id))
    if count >= settings.WEBHOOK_MAX_PER_VENDOR:
        raise HTTPException(400, f"Maximum {settings.WEBHOOK_MAX_PER_VENDOR} webhooks per vendor")

    events = [e.value for e in payload.events] if payload.events else None
    wh, secret = await wh_crud.create_webhook(
        vendor_id=user.vendor_id,
        url=payload.url,
        description=payload.description,
        events=events,
    )
    return _out_with_secret(wh, secret)


@router.get("/{webhook_id}", response_model=WebhookOut)
async def get_webhook(webhook_id: str, user: User = Depends(get_current_vendor)):
    wh = await wh_crud.get_by_id(webhook_id)
    if not wh or wh.vendor_id != user.vendor_id:
        raise HTTPException(404, "Webhook not found")
    return _out(wh)


@router.patch("/{webhook_id}", response_model=WebhookOut)
async def update_webhook(
    webhook_id: str, payload: WebhookUpdate, user: User = Depends(get_current_vendor),
):
    wh = await wh_crud.get_by_id(webhook_id)
    if not wh or wh.vendor_id != user.vendor_id:
        raise HTTPException(404, "Webhook not found")
    data = payload.model_dump(exclude_unset=True)
    if "events" in data and data["events"] is not None:
        data["events"] = [e.value if hasattr(e, "value") else e for e in data["events"]]
    wh = await wh_crud.update_webhook(wh, data)
    return _out(wh)


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(webhook_id: str, user: User = Depends(get_current_vendor)):
    wh = await wh_crud.get_by_id(webhook_id)
    if not wh or wh.vendor_id != user.vendor_id:
        raise HTTPException(404, "Webhook not found")
    await wh_crud.delete_webhook(wh)


@router.get("/{webhook_id}/deliveries", response_model=list[WebhookDeliveryOut])
async def list_deliveries(
    webhook_id: str,
    limit: int = Query(100, ge=1, le=500),
    skip: int = Query(0, ge=0),
    user: User = Depends(get_current_vendor),
):
    wh = await wh_crud.get_by_id(webhook_id)
    if not wh or wh.vendor_id != user.vendor_id:
        raise HTTPException(404, "Webhook not found")
    rows = await wh_crud.list_deliveries(webhook_id=webhook_id, limit=limit, skip=skip)
    return [_delivery_out(r) for r in rows]


@router.post("/{webhook_id}/test", response_model=WebhookTestOut)
async def test_webhook(webhook_id: str, user: User = Depends(get_current_vendor)):
    wh = await wh_crud.get_by_id(webhook_id)
    if not wh or wh.vendor_id != user.vendor_id:
        raise HTTPException(404, "Webhook not found")

    payload = {"test": True, "event": "test.ping", "webhook_id": str(wh.id)}
    body = json.dumps(payload).encode("utf-8")
    sig = _sign(wh.secret, body)

    try:
        async with httpx.AsyncClient(timeout=settings.WEBHOOK_TIMEOUT_SECONDS) as client:
            resp = await client.post(
                wh.url, content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-KwiqBuy-Event": "test.ping",
                    "X-KwiqBuy-Signature": sig,
                },
            )
        return WebhookTestOut(
            delivered=200 <= resp.status_code < 300,
            status_code=resp.status_code,
            response_body=resp.text[:500],
        )
    except Exception as e:
        return WebhookTestOut(delivered=False, error=f"{type(e).__name__}: {e}")
