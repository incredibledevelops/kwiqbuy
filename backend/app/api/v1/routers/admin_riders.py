from fastapi import APIRouter, Depends, HTTPException, Request
from beanie import PydanticObjectId
from pydantic import BaseModel

from app.core.deps import get_current_admin
from app.models.user import User, UserRole
from app.models.audit_log import ActorType
from app.crud import audit as audit_crud

router = APIRouter(prefix="/admin/riders", tags=["Admin Riders"])


class RiderStatusUpdate(BaseModel):
    is_active: bool


@router.get("")
async def list_riders(_=Depends(get_current_admin)):
    riders = await User.find(User.role == UserRole.RIDER).to_list()
    return [
        {
            "id": str(r.id),
            "full_name": r.full_name,
            "email": r.email,
            "phone": r.phone,
            "vehicle": r.vehicle,
            "plate_number": r.plate_number,
            "is_active": r.is_active,
            "created_at": r.created_at,
        }
        for r in riders
    ]


@router.patch("/{rider_id}/status")
async def toggle_rider_status(
    rider_id: str,
    payload: RiderStatusUpdate,
    request: Request,
    current_user: User = Depends(get_current_admin),
):
    try:
        rider = await User.get(PydanticObjectId(rider_id))
    except Exception:
        raise HTTPException(400, "Invalid rider ID")

    if not rider or rider.role != UserRole.RIDER:
        raise HTTPException(404, "Rider not found")

    if rider.is_active == payload.is_active:
        return {"message": "No change needed", "is_active": rider.is_active}

    rider.is_active = payload.is_active
    await rider.save()

    await audit_crud.log(
        action=f"rider.{'activated' if payload.is_active else 'suspended'}",
        actor_type=ActorType.USER,
        actor_id=str(current_user.id),
        actor_email=current_user.email,
        target_type="User",
        target_id=str(rider.id),
        request=request,
    )

    return {"message": "Status updated", "is_active": rider.is_active}