from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, Request, Response

from app.core.config import settings
from app.core.deps import get_current_admin
from app.core.limiter import limiter
from app.services import exports as exports_service

router = APIRouter(prefix="/admin/analytics/export", tags=["Admin Exports"])


@router.get("")
@limiter.limit(settings.RATE_LIMIT_EXPORT)
async def export_analytics(
    request: Request,
    format: str = Query("csv", pattern="^(csv|xlsx)$"),
    days: int = Query(30, ge=1, le=365),
    _=Depends(get_current_admin),
):
    if format == "csv":
        content = await exports_service.build_summary_csv(days=days)
        media = "text/csv"
        ext = "csv"
    else:
        content = await exports_service.build_summary_xlsx(days=days)
        media = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ext = "xlsx"

    filename = f"kwiqbuy-analytics-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.{ext}"
    return Response(
        content=content, media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
