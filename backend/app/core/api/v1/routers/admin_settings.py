from fastapi import APIRouter, Depends, Request

from app.core.deps import get_current_admin
from app.crud import platform_settings as ps_crud
from app.models.user import User
from app.schemas.platform_settings import (
    PlatformSettingsOut,
    PlatformSettingsUpdate,
)

router = APIRouter(prefix="/admin/settings", tags=["Admin Settings"])


def _to_out(doc) -> PlatformSettingsOut:
    return PlatformSettingsOut(
        commission_pct=doc.commission_pct,
        food_commission_pct=doc.food_commission_pct,
        retail_commission_pct=doc.retail_commission_pct,
        platform_delivery_cut_pct=doc.platform_delivery_cut_pct,
        min_payout_ghs=doc.min_payout_ghs,
        payout_schedule=doc.payout_schedule,
        free_delivery_threshold=doc.free_delivery_threshold,
        rider_fee_model=doc.rider_fee_model,
        rider_flat_fee_ghs=doc.rider_flat_fee_ghs,
        rider_pct_of_delivery_fee=doc.rider_pct_of_delivery_fee,
        support_phone=doc.support_phone,
        support_email=doc.support_email,
        support_whatsapp=doc.support_whatsapp,
        maintenance_mode=doc.maintenance_mode,
        customer_ordering_enabled=doc.customer_ordering_enabled,
        vendor_signups_enabled=doc.vendor_signups_enabled,
        admin_ip_allowlist=doc.admin_ip_allowlist,
        admin_2fa_required=doc.admin_2fa_required,
        updated_by=doc.updated_by,
        updated_at=doc.updated_at,
    )


@router.get("", response_model=PlatformSettingsOut)
async def get_settings(_=Depends(get_current_admin)):
    doc = await ps_crud.get_settings()
    return _to_out(doc)


@router.patch("", response_model=PlatformSettingsOut)
async def update_settings(
    payload: PlatformSettingsUpdate,
    request: Request,
    current_user: User = Depends(get_current_admin),
):
    doc = await ps_crud.update_settings(
        payload.model_dump(exclude_unset=True),
        admin_id=str(current_user.id),
        admin_email=current_user.email,
        request=request,
    )
    return _to_out(doc)
