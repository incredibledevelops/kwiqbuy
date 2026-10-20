"""
Vendor application CRUD.

Approval path is transactional (see crud/order.py pattern): creates the
Vendor + owner User + updates the application + writes AuditLog, all in
one session.

Self-signup flow:
    1. Applicant POSTs to /api/v1/vendor-applications
    2. Admin reviews via GET /api/v1/admin/vendor-applications
    3. Admin approves or rejects
       - approve → Vendor(ACTIVE) + User(role=vendor) created
       - reject  → status=rejected + reason stored
    4. Rejected applications cannot be re-approved — applicant must
       re-submit (avoids contested-approval griefing).
"""
from datetime import datetime, timezone
from typing import Optional

from beanie import PydanticObjectId
from fastapi import Request

from app.core.database import transactional
from app.core.security import hash_password
from app.crud import audit as audit_crud
from app.crud import vendor as vendor_crud
from app.models.audit_log import ActorType
from app.models.user import User, UserRole
from app.models.vendor import VendorStatus
from app.models.vendor_application import (
    VendorApplication,
    VendorApplicationStatus,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def get_by_id(app_id: str) -> Optional[VendorApplication]:
    try:
        return await VendorApplication.get(PydanticObjectId(app_id))
    except Exception:
        return None


async def has_pending_application(phone: str) -> bool:
    return bool(
        await VendorApplication.find_one(
            VendorApplication.contact_phone == phone,
            VendorApplication.status == VendorApplicationStatus.PENDING,
        )
    )


async def create_application(
    data: dict,
    *,
    ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    request: Optional[Request] = None,
) -> VendorApplication:
    app = VendorApplication(
        **data,
        applied_ip=ip,
        applied_user_agent=user_agent,
    )
    await app.insert()

    await audit_crud.log(
        action="vendor_application.submitted",
        actor_type=ActorType.SYSTEM,
        target_type="VendorApplication",
        target_id=str(app.id),
        after={"business_name": app.business_name, "contact_phone": app.contact_phone},
        request=request,
    )
    return app


async def list_applications(
    *,
    status: Optional[VendorApplicationStatus] = None,
    skip: int = 0,
    limit: int = 200,
) -> list[VendorApplication]:
    query = VendorApplication.find()
    if status:
        query = query.find(VendorApplication.status == status)
    return (
        await query.sort(-VendorApplication.created_at).skip(skip).limit(limit).to_list()
    )


async def withdraw(
    app: VendorApplication,
    *,
    request: Optional[Request] = None,
) -> VendorApplication:
    if app.status != VendorApplicationStatus.PENDING:
        raise ValueError("Only pending applications can be withdrawn")
    app.status = VendorApplicationStatus.WITHDRAWN
    app.updated_at = _now()
    await app.save()

    await audit_crud.log(
        action="vendor_application.withdrawn",
        actor_type=ActorType.SYSTEM,
        target_type="VendorApplication",
        target_id=str(app.id),
        request=request,
    )
    return app


@transactional()
async def approve_application(
    app: VendorApplication,
    *,
    admin_id: str,
    admin_email: str,
    generated_password: str,
    commission_pct_override: Optional[float] = None,
    request: Optional[Request] = None,
    session=None,
) -> tuple[VendorApplication, "User", "Vendor"]:
    """
    Approve an application. Creates:
      - Vendor with status=ACTIVE
      - User with role=vendor, linked to the vendor, with a generated password
      - Marks the application approved
    All inside one transaction (when available).
    """
    from app.models.vendor import Vendor  # avoid circular import at module load

    if app.status != VendorApplicationStatus.PENDING:
        raise ValueError(f"Cannot approve an application in status '{app.status.value}'")

    # 1. Create the owner User
    if await User.find_one(User.email == app.contact_email.lower()):
        raise ValueError("A user with that email already exists")

    user = User(
        full_name=app.contact_name,
        email=app.contact_email.lower(),
        phone=app.contact_phone,
        hashed_password=hash_password(generated_password),
        role=UserRole.VENDOR,
        is_active=True,
    )
    await user.insert(session=session)

    # 2. Create the Vendor
    vendor = Vendor(
        business_name=app.business_name,
        slug=await vendor_crud.unique_slug(app.business_name),
        description=app.description,
        owner_user_id=user.id,
        contact_email=app.contact_email,
        contact_phone=app.contact_phone,
        pickup_address=app.pickup_address,
        status=VendorStatus.ACTIVE,
        commission_pct_override=commission_pct_override,
        approved_at=_now(),
    )
    await vendor.insert(session=session)

    # Link user → vendor
    user.vendor_id = vendor.id
    user.updated_at = _now()
    await user.save(session=session)

    # 3. Update the application
    app.status = VendorApplicationStatus.APPROVED
    app.reviewed_by = admin_id
    app.reviewed_at = _now()
    app.created_vendor_id = str(vendor.id)
    app.created_user_id = str(user.id)
    app.updated_at = _now()
    await app.save(session=session)

    # 4. Audit
    await audit_crud.log(
        action="vendor_application.approved",
        actor_type=ActorType.USER,
        actor_id=admin_id,
        actor_email=admin_email,
        target_type="VendorApplication",
        target_id=str(app.id),
        after={
            "vendor_id": str(vendor.id),
            "user_id": str(user.id),
            "business_name": vendor.business_name,
        },
        request=request,
    )

    return app, user, vendor


async def reject_application(
    app: VendorApplication,
    *,
    admin_id: str,
    admin_email: str,
    reason: str,
    request: Optional[Request] = None,
) -> VendorApplication:
    if app.status != VendorApplicationStatus.PENDING:
        raise ValueError(f"Cannot reject an application in status '{app.status.value}'")

    app.status = VendorApplicationStatus.REJECTED
    app.reviewed_by = admin_id
    app.reviewed_at = _now()
    app.rejection_reason = reason
    app.updated_at = _now()
    await app.save()

    await audit_crud.log(
        action="vendor_application.rejected",
        actor_type=ActorType.USER,
        actor_id=admin_id,
        actor_email=admin_email,
        target_type="VendorApplication",
        target_id=str(app.id),
        metadata={"reason": reason},
        request=request,
    )
    return app


async def expire_stale_applications() -> int:
    """
    Called by a nightly job. Marks pending applications whose `expires_at`
    has passed as `expired` so the AuditLog preserves history before the
    TTL index deletes the raw document.
    """
    now = _now()
    stale = await VendorApplication.find(
        VendorApplication.status == VendorApplicationStatus.PENDING,
        VendorApplication.expires_at < now,
    ).to_list()

    for app in stale:
        app.status = VendorApplicationStatus.EXPIRED
        app.updated_at = now
        await app.save()
        await audit_crud.log(
            action="vendor_application.expired",
            actor_type=ActorType.SYSTEM,
            target_type="VendorApplication",
            target_id=str(app.id),
        )
    return len(stale)