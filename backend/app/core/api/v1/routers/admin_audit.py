from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_admin
from app.crud import audit as audit_crud
from app.schemas.audit_log import AuditLogListOut, AuditLogOut

router = APIRouter(prefix="/admin/audit", tags=["Admin Audit"])


def _to_out(a) -> AuditLogOut:
    return AuditLogOut(
        id=str(a.id),
        actor_type=a.actor_type,
        actor_id=a.actor_id,
        actor_email=a.actor_email,
        action=a.action,
        target_type=a.target_type,
        target_id=a.target_id,
        before=a.before,
        after=a.after,
        metadata=a.metadata,
        ip=a.ip,
        user_agent=a.user_agent,
        at=a.at,
    )


@router.get("", response_model=AuditLogListOut)
async def list_logs(
    action: str | None = None,
    actor_id: str | None = None,
    target_id: str | None = None,
    limit: int = Query(200, ge=1, le=1000),
    skip: int = Query(0, ge=0),
    _=Depends(get_current_admin),
):
    logs = await audit_crud.list_logs(
        action=action,
        actor_id=actor_id,
        target_id=target_id,
        limit=limit,
        skip=skip,
    )
    return AuditLogListOut(
        items=[_to_out(a) for a in logs],
        total=len(logs),
    )
