import secrets
from datetime import datetime, timezone

from beanie import PydanticObjectId

from app.models.webhook import VendorWebhook, WebhookDelivery, WebhookEvent


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _generate_secret() -> str:
    return secrets.token_urlsafe(32)


async def create_webhook(
    *,
    vendor_id: PydanticObjectId,
    url: str,
    description: str | None = None,
    events: list[str] | None = None,
):
    secret = _generate_secret()
    wh = VendorWebhook(
        vendor_id=vendor_id,
        url=url,
        description=description,
        secret=secret,
        events=events or [e.value for e in WebhookEvent],
    )
    await wh.insert()
    return wh, secret


async def list_for_vendor(vendor_id: str) -> list[VendorWebhook]:
    try:
        vid = PydanticObjectId(vendor_id)
    except Exception:
        return []
    return await VendorWebhook.find(VendorWebhook.vendor_id == vid).sort(-VendorWebhook.created_at).to_list()


async def get_by_id(webhook_id: str) -> VendorWebhook | None:
    try:
        return await VendorWebhook.get(PydanticObjectId(webhook_id))
    except Exception:
        return None


async def count_for_vendor(vendor_id: str) -> int:
    try:
        vid = PydanticObjectId(vendor_id)
    except Exception:
        return 0
    return await VendorWebhook.find(VendorWebhook.vendor_id == vid).count()


async def update_webhook(wh: VendorWebhook, data: dict) -> VendorWebhook:
    for k, v in data.items():
        if v is None:
            continue
        if hasattr(wh, k):
            setattr(wh, k, v)
    wh.updated_at = _now()
    await wh.save()
    return wh


async def delete_webhook(wh: VendorWebhook) -> None:
    await wh.delete()


async def list_deliveries(
    *,
    webhook_id: str | None = None,
    vendor_id: str | None = None,
    limit: int = 100,
    skip: int = 0,
) -> list[WebhookDelivery]:
    query = WebhookDelivery.find()
    if webhook_id:
        query = query.find(WebhookDelivery.webhook_id == PydanticObjectId(webhook_id))
    if vendor_id:
        query = query.find(WebhookDelivery.vendor_id == PydanticObjectId(vendor_id))
    return await query.sort(-WebhookDelivery.created_at).skip(skip).limit(limit).to_list()
