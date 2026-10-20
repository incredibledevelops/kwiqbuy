from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.config import settings
from app.core.deps import get_current_rider, get_current_staff_or_admin
from app.core.limiter import limiter
from app.crud import order as order_crud
from app.crud import rider_location as loc_crud
from app.models.order import Order
from app.models.user import User
from app.schemas.rider_location import (
    RiderLocationIn,
    RiderLocationOut,
    RiderTrackOut,
)

router = APIRouter(tags=["Rider Locations"])


def _to_out(row) -> RiderLocationOut:
    coords = row.location.coordinates if row.location else [0, 0]
    return RiderLocationOut(
        rider_id=str(row.rider_id),
        order_id=str(row.order_id) if row.order_id else None,
        lat=coords[1],
        lng=coords[0],
        accuracy_meters=row.accuracy_meters,
        heading=row.heading,
        speed_mps=row.speed_mps,
        at=row.at,
    )


# ---------- Rider posts updates ----------

@router.post("/rider/location", response_model=RiderLocationOut)
@limiter.limit(settings.RATE_LIMIT_RIDER_LOCATION)
async def update_location(
    request: Request,
    payload: RiderLocationIn,
    current_user: User = Depends(get_current_rider),
):
    from beanie import PydanticObjectId
    order_oid = None
    if payload.order_id:
        try:
            order_oid = PydanticObjectId(payload.order_id)
        except Exception:
            raise HTTPException(400, "Invalid order_id")

    row = await loc_crud.record(
        rider_id=current_user.id,
        lat=payload.lat,
        lng=payload.lng,
        order_id=order_oid,
        accuracy_meters=payload.accuracy_meters,
        heading=payload.heading,
        speed_mps=payload.speed_mps,
    )
    return _to_out(row)


# ---------- Admin: any rider's latest ----------

@router.get(
    "/admin/riders/{rider_id}/location",
    response_model=RiderLocationOut,
    dependencies=[Depends(get_current_staff_or_admin)],
)
async def admin_get_rider_location(rider_id: str):
    row = await loc_crud.latest_for_rider(rider_id)
    if not row:
        raise HTTPException(404, "No location for that rider")
    return _to_out(row)


# ---------- Public: track order rider ----------

@router.get("/orders/track/{reference}/rider-position", response_model=RiderTrackOut)
async def track_rider_position(reference: str):
    order = await order_crud.get_order_by_reference(reference)
    if not order:
        raise HTTPException(404, "Order not found")

    history: list[RiderLocationOut] = []
    latest: RiderLocationOut | None = None
    if order.rider_id:
        rows = await loc_crud.history_for_order(str(order.id), limit=200)
        history = [_to_out(r) for r in rows]
        if history:
            latest = history[-1]

    return RiderTrackOut(
        order_reference=order.reference,
        rider_name=order.rider_name,
        rider_phone=order.rider_phone,
        latest=latest,
        history=history,
    )
