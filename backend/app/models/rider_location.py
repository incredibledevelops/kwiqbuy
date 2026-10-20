"""
Rider location snapshots.

TTL'd — Mongo purges after RIDER_LOCATION_TTL_HOURS. Only the latest
position per rider matters; historical positions are for the map view.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from beanie import Document, Indexed, PydanticObjectId
from pydantic import BaseModel, Field

from app.core.config import settings


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=settings.RIDER_LOCATION_TTL_HOURS)


class GeoPoint(BaseModel):
    type: str = "Point"
    coordinates: list[float]  # [lng, lat]


class RiderLocation(Document):
    rider_id: Indexed(PydanticObjectId)  # type: ignore
    order_id: Optional[PydanticObjectId] = None
    location: GeoPoint

    accuracy_meters: Optional[float] = None
    heading: Optional[float] = None
    speed_mps: Optional[float] = None

    at: datetime = Field(default_factory=_now)
    expire_at: datetime = Field(default_factory=_expiry)

    class Settings:
        name = "rider_locations"
        indexes = [
            "rider_id",
            "order_id",
            [("location", "2dsphere")],
            "expire_at",  # TTL
        ]
