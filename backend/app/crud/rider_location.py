"""
Rider location CRUD.
"""
from datetime import datetime, timezone
from typing import Optional

from beanie import PydanticObjectId

from app.models.rider_location import GeoPoint, RiderLocation


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def record(
    *,
    rider_id: PydanticObjectId,
    lat: float,
    lng: float,
    order_id: Optional[PydanticObjectId] = None,
    accuracy_meters: Optional[float] = None,
    heading: Optional[float] = None,
    speed_mps: Optional[float] = None,
) -> RiderLocation:
    loc = RiderLocation(
        rider_id=rider_id,
        order_id=order_id,
        location=GeoPoint(coordinates=[float(lng), float(lat)]),
        accuracy_meters=accuracy_meters,
        heading=heading,
        speed_mps=speed_mps,
    )
    await loc.insert()
    return loc


async def latest_for_rider(rider_id: str) -> Optional[RiderLocation]:
    try:
        rid = PydanticObjectId(rider_id)
    except Exception:
        return None
    return (
        await RiderLocation.find(RiderLocation.rider_id == rid)
        .sort(-RiderLocation.at)
        .limit(1)
        .to_list()
    )[0] if await RiderLocation.find(RiderLocation.rider_id == rid).count() else None


async def latest_for_order(order_id: str) -> Optional[RiderLocation]:
    try:
        oid = PydanticObjectId(order_id)
    except Exception:
        return None
    rows = (
        await RiderLocation.find(RiderLocation.order_id == oid)
        .sort(-RiderLocation.at)
        .limit(1)
        .to_list()
    )
    return rows[0] if rows else None


async def history_for_order(order_id: str, limit: int = 200) -> list[RiderLocation]:
    try:
        oid = PydanticObjectId(order_id)
    except Exception:
        return []
    return (
        await RiderLocation.find(RiderLocation.order_id == oid)
        .sort(+RiderLocation.at)
        .limit(limit)
        .to_list()
    )
