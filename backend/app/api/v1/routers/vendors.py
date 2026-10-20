from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.core.config import settings
from app.core.limiter import limiter
from app.crud import audit as audit_crud
from app.crud import user as user_crud
from app.crud import vendor as vendor_crud
from app.core.deps import get_current_admin
from app.models.audit_log import ActorType
from app.models.user import User, UserRole
from app.models.vendor import VendorCategory, VendorStatus
from app.schemas.vendor import (
    NearbyVendorOut,
    NearbyVendorsOut,
    VendorAdminUpdate,
    VendorCreateByAdmin,
    VendorOut,
    VendorPublicOut,
    VendorStatusUpdate,
)

router = APIRouter(prefix="/vendors", tags=["Vendors"])


def _to_out(v) -> VendorOut:
    return VendorOut(
        id=str(v.id),
        business_name=v.business_name,
        slug=v.slug,
        business_category=v.business_category,
        business_subtype=v.business_subtype,
        description=v.description,
        logo_url=v.logo_url,
        banner_url=v.banner_url,
        contact_email=v.contact_email,
        contact_phone=v.contact_phone,
        pickup_address=v.pickup_address,
        pickup_lat=v.pickup_lat,
        pickup_lng=v.pickup_lng,
        delivery_radius_km=v.delivery_radius_km,
        prep_minutes=v.prep_minutes,
        status=v.status,
        commission_pct_override=v.commission_pct_override,
        average_rating=v.average_rating,
        total_reviews=v.total_reviews,
        total_orders=v.total_orders,
        created_at=v.created_at,
        updated_at=v.updated_at,
        approved_at=v.approved_at,
    )


def _to_public(v) -> VendorPublicOut:
    return VendorPublicOut(
        id=str(v.id),
        business_name=v.business_name,
        slug=v.slug,
        business_category=v.business_category,
        business_subtype=v.business_subtype,
        description=v.description,
        logo_url=v.logo_url,
        banner_url=v.banner_url,
        pickup_lat=v.pickup_lat,
        pickup_lng=v.pickup_lng,
        delivery_radius_km=v.delivery_radius_km,
        prep_minutes=v.prep_minutes,
        average_rating=v.average_rating,
        total_reviews=v.total_reviews,
    )


# ---------- Public storefront ----------

@router.get("/public", response_model=list[VendorPublicOut])
async def list_active_vendors(
    category: VendorCategory | None = Query(None),
    search: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
):
    vendors = await vendor_crud.list_vendors(
        active_only=True,
        category=category,
        search=search,
        skip=skip,
        limit=limit,
    )
    return [_to_public(v) for v in vendors]


@router.get("/nearby", response_model=NearbyVendorsOut)
@limiter.limit(settings.RATE_LIMIT_NEARBY)
async def nearby_food_vendors(
    request: Request,
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius_km: float | None = Query(None, ge=0.1, le=100),
    limit: int = Query(50, ge=1, le=200),
):
    """
    Return food vendors near the given coordinates.

    Uses $geoNear on the vendor pickup_location 2dsphere index.
    A vendor is included when:
        distance_km <= min(search_radius, vendor.delivery_radius_km)
    """
    radius = radius_km or settings.FOOD_DEFAULT_RADIUS_KM
    raw = await vendor_crud.nearby_food_vendors(
        lat=lat, lng=lng, radius_km=radius, limit=limit
    )

    vendors: list[NearbyVendorOut] = []
    for row in raw:
        vendors.append(
            NearbyVendorOut(
                id=str(row["_id"]),
                business_name=row["business_name"],
                slug=row["slug"],
                business_category=row["business_category"],
                business_subtype=row.get("business_subtype"),
                description=row.get("description"),
                logo_url=row.get("logo_url"),
                banner_url=row.get("banner_url"),
                pickup_lat=row.get("pickup_lat"),
                pickup_lng=row.get("pickup_lng"),
                delivery_radius_km=row.get("delivery_radius_km", 15.0),
                prep_minutes=row.get("prep_minutes", 20),
                average_rating=row.get("average_rating", 0.0),
                total_reviews=row.get("total_reviews", 0),
                distance_km=round(row["distance_km"], 2),
                distance_meters=round(row["distance_meters"], 0),
            )
        )

    return NearbyVendorsOut(
        center_lat=lat,
        center_lng=lng,
        radius_km=min(radius, settings.FOOD_MAX_RADIUS_KM),
        vendors=vendors,
    )


@router.get("/public/{slug}", response_model=VendorPublicOut)
async def get_public_vendor(slug: str):
    v = await vendor_crud.get_by_slug(slug)
    if not v or v.status != VendorStatus.ACTIVE:
        raise HTTPException(404, "Vendor not found")
    return _to_public(v)


# ---------- Admin ----------

@router.get(
    "",
    response_model=list[VendorOut],
    dependencies=[Depends(get_current_admin)],
)
async def admin_list_vendors(
    status_filter: VendorStatus | None = Query(None, alias="status"),
    category: VendorCategory | None = Query(None),
    search: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=500),
):
    vendors = await vendor_crud.list_vendors(
        status=status_filter,
        category=category,
        search=search,
        skip=skip,
        limit=limit,
    )
    return [_to_out(v) for v in vendors]


@router.post(
    "",
    response_model=VendorOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_admin)],
)
async def admin_create_vendor(
    payload: VendorCreateByAdmin,
    request: Request,
    current_user: User = Depends(get_current_admin),
):
    if await user_crud.get_by_email(payload.owner_email):
        raise HTTPException(409, "A user with that email already exists")

    user = await user_crud.create_user(
        full_name=payload.owner_full_name,
        email=payload.owner_email,
        password=payload.owner_password,
        phone=payload.owner_phone,
        role=UserRole.VENDOR,
    )

    vendor = await vendor_crud.create_vendor(
        business_name=payload.business_name,
        business_category=payload.business_category,
        business_subtype=payload.business_subtype,
        owner_user_id=str(user.id),
        pickup_address=payload.pickup_address,
        description=payload.description,
        contact_email=str(payload.contact_email) if payload.contact_email else None,
        contact_phone=payload.contact_phone,
        pickup_lat=payload.pickup_lat,
        pickup_lng=payload.pickup_lng,
        delivery_radius_km=payload.delivery_radius_km,
        prep_minutes=payload.prep_minutes,
        status=payload.status,
        commission_pct_override=payload.commission_pct_override,
    )
    user.vendor_id = vendor.id
    await user.save()

    await audit_crud.log(
        action="vendor.created",
        actor_type=ActorType.USER,
        actor_id=str(current_user.id),
        actor_email=current_user.email,
        target_type="Vendor",
        target_id=str(vendor.id),
        after={
            "business_name": vendor.business_name,
            "business_category": vendor.business_category.value,
            "owner_user_id": str(user.id),
        },
        request=request,
    )
    return _to_out(vendor)


@router.get(
    "/{vendor_id}",
    response_model=VendorOut,
    dependencies=[Depends(get_current_admin)],
)
async def admin_get_vendor(vendor_id: str):
    v = await vendor_crud.get_by_id(vendor_id)
    if not v:
        raise HTTPException(404, "Vendor not found")
    return _to_out(v)


@router.patch(
    "/{vendor_id}",
    response_model=VendorOut,
    dependencies=[Depends(get_current_admin)],
)
async def admin_update_vendor(
    vendor_id: str,
    payload: VendorAdminUpdate,
    request: Request,
    current_user: User = Depends(get_current_admin),
):
    v = await vendor_crud.get_by_id(vendor_id)
    if not v:
        raise HTTPException(404, "Vendor not found")

    data = payload.model_dump(exclude_unset=True)
    status_val = data.pop("status", None)
    override = data.pop("commission_pct_override", None)

    v = await vendor_crud.update_vendor(
        v,
        data,
        actor_id=str(current_user.id),
        actor_email=current_user.email,
        request=request,
    )

    if override is not None:
        v = await vendor_crud.set_commission_override(
            v,
            override,
            admin_id=str(current_user.id),
            admin_email=current_user.email,
            request=request,
        )

    if status_val is not None and status_val != v.status:
        v = await vendor_crud.set_status(
            v,
            status_val,
            actor_id=str(current_user.id),
            actor_email=current_user.email,
            request=request,
        )

    return _to_out(v)


@router.post(
    "/{vendor_id}/status",
    response_model=VendorOut,
    dependencies=[Depends(get_current_admin)],
)
async def admin_set_status(
    vendor_id: str,
    payload: VendorStatusUpdate,
    request: Request,
    current_user: User = Depends(get_current_admin),
):
    v = await vendor_crud.get_by_id(vendor_id)
    if not v:
        raise HTTPException(404, "Vendor not found")
    v = await vendor_crud.set_status(
        v,
        payload.status,
        actor_id=str(current_user.id),
        actor_email=current_user.email,
        request=request,
        reason=payload.reason,
    )
    return _to_out(v)
