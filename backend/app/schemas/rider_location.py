from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class RiderLocationIn(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    order_id: Optional[str] = None
    accuracy_meters: Optional[float] = Field(default=None, ge=0)
    heading: Optional[float] = None
    speed_mps: Optional[float] = Field(default=None, ge=0)


class RiderLocationOut(BaseModel):
    rider_id: str
    order_id: Optional[str] = None
    lat: float
    lng: float
    accuracy_meters: Optional[float] = None
    heading: Optional[float] = None
    speed_mps: Optional[float] = None
    at: datetime


class RiderTrackOut(BaseModel):
    order_reference: str
    rider_name: Optional[str] = None
    rider_phone: Optional[str] = None
    latest: Optional[RiderLocationOut] = None
    history: list[RiderLocationOut] = []
