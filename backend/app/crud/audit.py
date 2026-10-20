"""
Audit log writer.

Never raises — audit failures must not break the main operation. If the
write fails, we log the failure and move on.

Usage:
    from app.crud import audit as audit_crud

    await audit_crud.log(
        action="vendor.approved",
        actor_type=ActorType.USER,
        actor_id=str(admin.id),
        actor_email=admin.email,
        target_type="Vendor",
        target_id=str(vendor.id),
        before={"status": "pending"},
        after={"status": "active"},
        request=request,          # optional FastAPI Request for IP/UA
        metadata={"note": "…"},
    )
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import Request

from app.models.audit_log import ActorType, AuditLog

logger = logging.getLogger(__name__)


def _extract_ip_ua(request: Optional[Request]) -> tuple[Optional[str], Optional[str]]:
    if request is None:
        return None, None
    ip: Optional[str] = None
    try:
        # Trust X-Forwarded-For only if you run behind a proxy you control.
        # We read it best-effort; fall back to client.host.
        xff = request.headers.get("x-forwarded-for")
        if xff:
            ip = xff.split(",")[0].strip()
        elif request.client:
            ip = request.client.host
    except Exception:
        ip = None
    ua = None
    try:
        ua = request.headers.get("user-agent")
    except Exception:
        ua = None
    return ip, ua


async def log(
    *,
    action: str,
    actor_type: ActorType = ActorType.SYSTEM,
    actor_id: Optional[str] = None,
    actor_email: Optional[str] = None,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    before: Optional[dict[str, Any]] = None,
    after: Optional[dict[str, Any]] = None,
    metadata: Optional[dict[str, Any]] = None,
    request: Optional[Request] = None,
) -> None:
    try:
        ip, ua = _extract_ip_ua(request)
        doc = AuditLog(
            actor_type=actor_type,
            actor_id=actor_id,
            actor_email=actor_email,
            action=action,
            target_type=target_type,
            target_id=target_id,
            before=before,
            after=after,
            metadata=metadata,
            ip=ip,
            user_agent=ua,
        )
        await doc.insert()
    except Exception:
        logger.exception("audit log write failed (action=%s)", action)


async def list_logs(
    *,
    action: Optional[str] = None,
    actor_id: Optional[str] = None,
    target_id: Optional[str] = None,
    limit: int = 100,
    skip: int = 0,
) -> list[AuditLog]:
    query = AuditLog.find()
    if action:
        query = query.find(AuditLog.action == action)
    if actor_id:
        query = query.find(AuditLog.actor_id == actor_id)
    if target_id:
        query = query.find(AuditLog.target_id == target_id)
    return (
        await query.sort(-AuditLog.at).skip(skip).limit(limit).to_list()
    )