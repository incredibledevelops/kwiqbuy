from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.core.config import settings
from app.core.deps import get_current_admin
from app.core.limiter import limiter
from app.core.security import generate_password
from app.crud import vendor_application as va_crud
from app.models.user import User
from app.models.vendor_application import VendorApplicationStatus
from app.schemas.vendor_application import (
    VendorApplicationApproveIn,
    VendorApplicationApproveOut,
    VendorApplicationIn,
    VendorApplicationOut,
    VendorApplicationRejectIn,
    VendorApplicationSubmitOut,
)

router = APIRouter(tags=["Vendor Applications"])


def _to_out(a) -> VendorApplicationOut:
    return VendorApplicationOut(
        id=str(a.id),
        business_name=a.business_name,
        business_type=a.business_type,
        business_category=getattr(a, "business_category", "food"),
        description=a.description,
        contact_name=a.contact_name,
        contact_email=a.contact_email,
        contact_phone=a.contact_phone,
        pickup_address=a.pickup_address,
        city=a.city,
        region=a.region,
        requested_payout_method=a.requested_payout_method,
        id_document_url=a.id_document_url,
        business_registration_url=a.business_registration_url,
        status=a.status,
        reviewed_by=a.reviewed_by,
        reviewed_at=a.reviewed_at,
        rejection_reason=a.rejection_reason,
        created_vendor_id=a.created_vendor_id,
        created_user_id=a.created_user_id,
        created_at=a.created_at,
        updated_at=a.updated_at,
        expires_at=a.expires_at,
    )


@router.post(
    "/vendor-applications",
    response_model=VendorApplicationSubmitOut,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(settings.RATE_LIMIT_VENDOR_APPLICATION)
async def submit_application(request: Request, payload: VendorApplicationIn):
    if await va_crud.has_pending_application(payload.contact_phone):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "You already have a pending application. We'll be in touch "
                "within 2 business days."
            ),
        )

    ip = None
    ua = None
    try:
        xff = request.headers.get("x-forwarded-for")
        ip = xff.split(",")[0].strip() if xff else (request.client.host if request.client else None)
        ua = request.headers.get("user-agent")
    except Exception:
        pass

    application = await va_crud.create_application(
        payload.model_dump(),
        ip=ip,
        user_agent=ua,
        request=request,
    )
    return VendorApplicationSubmitOut(id=str(application.id))


@router.get("/vendor-applications/status/{application_id}")
async def check_status(application_id: str):
    app = await va_crud.get_by_id(application_id)
    if not app:
        raise HTTPException(404, "Application not found")
    return {
        "id": str(app.id),
        "status": app.status.value,
        "reviewed_at": app.reviewed_at,
        "rejection_reason": app.rejection_reason,
    }


@router.get(
    "/admin/vendor-applications",
    response_model=list[VendorApplicationOut],
    dependencies=[Depends(get_current_admin)],
)
async def list_applications(
    status_filter: VendorApplicationStatus | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=500),
):
    apps = await va_crud.list_applications(
        status=status_filter, skip=skip, limit=limit
    )
    return [_to_out(a) for a in apps]


@router.get(
    "/admin/vendor-applications/{application_id}",
    response_model=VendorApplicationOut,
    dependencies=[Depends(get_current_admin)],
)
async def get_application(application_id: str):
    app = await va_crud.get_by_id(application_id)
    if not app:
        raise HTTPException(404, "Application not found")
    return _to_out(app)


@router.post(
    "/admin/vendor-applications/{application_id}/approve",
    response_model=VendorApplicationApproveOut,
    dependencies=[Depends(get_current_admin)],
)
async def approve_application(
    application_id: str,
    payload: VendorApplicationApproveIn,
    request: Request,
    current_user: User = Depends(get_current_admin),
):
    app = await va_crud.get_by_id(application_id)
    if not app:
        raise HTTPException(404, "Application not found")

    temporary_password = generate_password(12)

    try:
        app, user, vendor = await va_crud.approve_application(
            app,
            admin_id=str(current_user.id),
            admin_email=current_user.email,
            generated_password=temporary_password,
            commission_pct_override=payload.commission_pct_override,
            request=request,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

    return VendorApplicationApproveOut(
        application=_to_out(app),
        vendor_id=str(vendor.id),
        owner_user_id=str(user.id),
        owner_email=user.email,
        temporary_password=temporary_password,
    )


@router.post(
    "/admin/vendor-applications/{application_id}/reject",
    response_model=VendorApplicationOut,
    dependencies=[Depends(get_current_admin)],
)
async def reject_application(
    application_id: str,
    payload: VendorApplicationRejectIn,
    request: Request,
    current_user: User = Depends(get_current_admin),
):
    app = await va_crud.get_by_id(application_id)
    if not app:
        raise HTTPException(404, "Application not found")
    try:
        app = await va_crud.reject_application(
            app,
            admin_id=str(current_user.id),
            admin_email=current_user.email,
            reason=payload.reason,
            request=request,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    return _to_out(app)
