from datetime import datetime, timezone
from typing import Optional

from fastapi import Request

from app.crud import audit as audit_crud
from app.models.audit_log import ActorType
from app.models.platform_settings import PlatformSettings


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def get_settings() -> PlatformSettings:
    doc = await PlatformSettings.find_one(PlatformSettings.key == "global")
    if doc:
        return doc
    doc = PlatformSettings(key="global")
    await doc.insert()
    return doc


async def update_settings(
    data: dict,
    *,
    admin_id: Optional[str] = None,
    admin_email: Optional[str] = None,
    request: Optional[Request] = None,
) -> PlatformSettings:
    doc = await get_settings()

    before = {}
    after = {}
    for k, v in data.items():
        if v is None:
            continue
        if not hasattr(doc, k):
            continue
        old = getattr(doc, k)
        if old != v:
            before[k] = old
            after[k] = v
            setattr(doc, k, v)

    if not after:
        return doc

    doc.updated_at = _now()
    doc.updated_by = admin_id
    await doc.save()

    await audit_crud.log(
        action="platform_settings.updated",
        actor_type=ActorType.USER if admin_id else ActorType.SYSTEM,
        actor_id=admin_id,
        actor_email=admin_email,
        target_type="PlatformSettings",
        target_id=str(doc.id),
        before=before,
        after=after,
        request=request,
    )
    return doc
