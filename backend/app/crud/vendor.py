"""
Vendor CRUD, including geo-aware discovery for food vendors.
"""
import logging
import math
import re
from datetime import datetime, timezone
from typing import Optional

from beanie import PydanticObjectId
from fastapi import Request

from app.core.config import settings
from app.core.database import get_database
from app.crud import audit as audit_crud
from app.models.audit_log import ActorType
from app.models.vendor import GeoPoint, Vendor, VendorCategory, VendorStatus

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def slugify(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[-\s]+", "-", text).strip("-")


# ---------- Reads ----------

async def get_by_id(vendor_id: str) -> Optional[Vendor]:
    try:
        return await Vendor.get(PydanticObjectId(vendor_id))
    except Exception:
        return None


async def get_by_slug(slug: str) -> Optional[Vendor]:
    return await Vendor.find_one(Vendor.slug == slug)


async def get_by_owner(user_id: str) -> Optional[Vendor]:
    try:
        oid = PydanticObjectId(user_id)
    except Exception:
        return None
    return await Vendor.find_one(Vendor.owner_user_id == oid)


async def list_vendors(
    *,
    status: Optional[VendorStatus] = None,
    category: Optional[VendorCategory] = None,
    active_only: bool = False,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 200,
) -> list[Vendor]:
    query = Vendor.find()
    if active_only:
        query = query.find(Vendor.status == VendorStatus.ACTIVE)
    elif status:
        query = query.find(Vendor.status == status)
    if category:
        query = query.find(Vendor.business_category == category)
    if search:
        rx = re.escape(search.strip())
        query = query.find({
            "$or": [
                {"business_name": {"$regex": rx, "$options": "i"}},
                {"slug": {"$regex": rx, "$options": "i"}},
            ]
        })
    return (
        await query.sort(+Vendor.business_name).skip(skip).limit(limit).to_list()
    )


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Distance between two lat/lng points in km."""
    R = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lng / 2) ** 2
    )
    return 2 * R * math.asin(math.sqrt(a))


async def nearby_food_vendors(
    *,
    lat: float,
    lng: float,
    radius_km: Optional[float] = None,
    limit: int = 50,
) -> list[dict]:
    """
    Return food vendors within radius_km of (lat, lng).

    Primary path: MongoDB $geoNear on the 2dsphere index for pickup_location.
    Fallback path: Python-side Haversine over all active food vendors
    (used if the geo index is missing, which can happen if the collection
    existed before the 2dsphere index was added).
    """
    db = get_database()
    effective_radius = min(
        radius_km or settings.FOOD_DEFAULT_RADIUS_KM,
        settings.FOOD_MAX_RADIUS_KM,
    )
    max_distance_m = effective_radius * 1000

    pipeline = [
        {
            "$geoNear": {
                "near": {"type": "Point", "coordinates": [lng, lat]},
                "distanceField": "distance_meters",
                "maxDistance": max_distance_m,
                "spherical": True,
                "query": {
                    "status": VendorStatus.ACTIVE.value,
                    "business_category": VendorCategory.FOOD.value,
                },
            }
        },
        {
            "$addFields": {
                "distance_km": {"$divide": ["$distance_meters", 1000]},
            }
        },
        {
            "$match": {
                "$expr": {
                    "$lte": [
                        "$distance_km",
                        {"$ifNull": ["$delivery_radius_km", 15.0]},
                    ]
                }
            }
        },
        {"$limit": limit},
    ]

    try:
        results = await db["vendors"].aggregate(pipeline).to_list(length=limit)
        return results
    except Exception as exc:
        logger.warning(
            "$geoNear failed (%s) — falling back to in-process Haversine",
            exc,
        )

    # ---------- Fallback: fetch all active food vendors and filter in Python
    vendors = await Vendor.find(
        Vendor.status == VendorStatus.ACTIVE,
        Vendor.business_category == VendorCategory.FOOD,
    ).to_list()

    matches: list[dict] = []
    for v in vendors:
        # Prefer pickup_location; fall back to pickup_lat/lng
        vlat = v.pickup_lat
        vlng = v.pickup_lng
        if v.pickup_location and v.pickup_location.coordinates:
            vlng, vlat = v.pickup_location.coordinates[0], v.pickup_location.coordinates[1]
        if vlat is None or vlng is None:
            continue
        d_km = _haversine_km(lat, lng, vlat, vlng)
        if d_km > effective_radius:
            continue
        if d_km > (v.delivery_radius_km or 15.0):
            continue
        doc = v.model_dump()
        doc["_id"] = v.id
        doc["distance_km"] = d_km
        doc["distance_meters"] = d_km * 1000
        matches.append(doc)

    matches.sort(key=lambda d: d["distance_km"])
    return matches[:limit]


async def unique_slug(base: str) -> str:
    base_slug = slugify(base) or "vendor"
    slug = base_slug
    i = 2
    while await Vendor.find_one(Vendor.slug == slug):
        slug = f"{base_slug}-{i}"
        i += 1
        if i > 500:
            raise RuntimeError("could not allocate unique vendor slug")
    return slug


# ---------- Create / update ----------

def _build_location(lat: Optional[float], lng: Optional[float]) -> Optional[GeoPoint]:
    if lat is None or lng is None:
        return None
    return GeoPoint(coordinates=[float(lng), float(lat)])


async def create_vendor(
    *,
    business_name: str,
    business_category: VendorCategory,
    owner_user_id: str,
    pickup_address: str,
    description: Optional[str] = None,
    business_subtype: Optional[str] = None,
    contact_email: Optional[str] = None,
    contact_phone: Optional[str] = None,
    pickup_lat: Optional[float] = None,
    pickup_lng: Optional[float] = None,
    delivery_radius_km: float = 15.0,
    prep_minutes: int = 20,
    status: VendorStatus = VendorStatus.PENDING,
    commission_pct_override: Optional[float] = None,
    slug: Optional[str] = None,
) -> Vendor:
    vendor = Vendor(
        business_name=business_name.strip(),
        business_category=business_category,
        business_subtype=business_subtype,
        slug=slug or await unique_slug(business_name),
        description=description,
        owner_user_id=PydanticObjectId(owner_user_id),
        contact_email=contact_email,
        contact_phone=contact_phone,
        pickup_address=pickup_address,
        pickup_lat=pickup_lat,
        pickup_lng=pickup_lng,
        pickup_location=_build_location(pickup_lat, pickup_lng),
        delivery_radius_km=delivery_radius_km,
        prep_minutes=prep_minutes,
        status=status,
        commission_pct_override=commission_pct_override,
    )
    await vendor.insert()
    return vendor


async def update_vendor(
    vendor: Vendor,
    data: dict,
    *,
    actor_id: Optional[str] = None,
    actor_email: Optional[str] = None,
    actor_type: ActorType = ActorType.USER,
    request: Optional[Request] = None,
) -> Vendor:
    before = {}
    after = {}

    editable = {
        "business_name",
        "description",
        "logo_url",
        "banner_url",
        "contact_email",
        "contact_phone",
        "pickup_address",
        "pickup_lat",
        "pickup_lng",
        "delivery_radius_km",
        "prep_minutes",
        "business_subtype",
        "payout_recipient_code",
        "payout_recipient_type",
        "payout_account_name",
        "payout_account_number",
        "payout_bank_code",
        "payout_mobile_provider",
    }

    for k, v in data.items():
        if k not in editable:
            continue
        if v is None and k not in {"pickup_lat", "pickup_lng"}:
            continue
        old = getattr(vendor, k, None)
        if old != v:
            before[k] = old
            after[k] = v
            setattr(vendor, k, v)

    if "pickup_lat" in after or "pickup_lng" in after:
        vendor.pickup_location = _build_location(vendor.pickup_lat, vendor.pickup_lng)

    if not after:
        return vendor

    vendor.updated_at = _now()
    await vendor.save()

    await audit_crud.log(
        action="vendor.updated",
        actor_type=actor_type,
        actor_id=actor_id,
        actor_email=actor_email,
        target_type="Vendor",
        target_id=str(vendor.id),
        before=before,
        after=after,
        request=request,
    )
    return vendor


async def set_status(
    vendor: Vendor,
    status: VendorStatus,
    *,
    actor_id: Optional[str] = None,
    actor_email: Optional[str] = None,
    request: Optional[Request] = None,
    reason: Optional[str] = None,
) -> Vendor:
    if vendor.status == status:
        return vendor

    old = vendor.status
    vendor.status = status
    vendor.updated_at = _now()
    if status == VendorStatus.ACTIVE and vendor.approved_at is None:
        vendor.approved_at = _now()
    elif status == VendorStatus.SUSPENDED:
        vendor.suspended_at = _now()
    elif status == VendorStatus.CLOSED:
        vendor.closed_at = _now()

    await vendor.save()

    await audit_crud.log(
        action=f"vendor.status.{status.value}",
        actor_type=ActorType.USER if actor_id else ActorType.SYSTEM,
        actor_id=actor_id,
        actor_email=actor_email,
        target_type="Vendor",
        target_id=str(vendor.id),
        before={"status": old.value},
        after={"status": status.value},
        metadata={"reason": reason} if reason else None,
        request=request,
    )
    return vendor


async def set_commission_override(
    vendor: Vendor,
    pct: Optional[float],
    *,
    admin_id: Optional[str] = None,
    admin_email: Optional[str] = None,
    request: Optional[Request] = None,
) -> Vendor:
    old = vendor.commission_pct_override
    if old == pct:
        return vendor
    vendor.commission_pct_override = pct
    vendor.updated_at = _now()
    await vendor.save()

    await audit_crud.log(
        action="vendor.commission_override_updated",
        actor_type=ActorType.USER if admin_id else ActorType.SYSTEM,
        actor_id=admin_id,
        actor_email=admin_email,
        target_type="Vendor",
        target_id=str(vendor.id),
        before={"commission_pct_override": old},
        after={"commission_pct_override": pct},
        request=request,
    )
    return vendor


def resolve_commission_pct(vendor: Vendor, platform_default: float) -> float:
    if vendor.commission_pct_override is not None:
        return float(vendor.commission_pct_override)
    return float(platform_default)