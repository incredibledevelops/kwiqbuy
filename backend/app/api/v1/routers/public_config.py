from fastapi import APIRouter

from app.core.config import settings as app_settings
from app.crud import platform_settings as ps_crud
from app.schemas.platform_settings import PlatformPublicSettingsOut

router = APIRouter(tags=["Public Config"])


@router.get("/config/public", response_model=PlatformPublicSettingsOut)
async def public_config():
    doc = await ps_crud.get_settings()
    return PlatformPublicSettingsOut(
        commission_pct=doc.commission_pct,
        free_delivery_threshold=doc.free_delivery_threshold,
        support_phone=doc.support_phone,
        support_whatsapp=doc.support_whatsapp,
        maintenance_mode=doc.maintenance_mode,
        customer_ordering_enabled=doc.customer_ordering_enabled,
        vendor_signups_enabled=doc.vendor_signups_enabled,
        currency=app_settings.CURRENCY,
    )
