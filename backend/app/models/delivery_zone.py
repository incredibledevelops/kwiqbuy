from datetime import datetime, timezone
from typing import Optional

from beanie import Document, Indexed
from pydantic import Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


class DeliveryZone(Document):
    name: str
    slug: Indexed(str, unique=True)  # type: ignore
    description: Optional[str] = None

    delivery_fee: float = Field(ge=0, default=15.0)
    estimated_minutes: Optional[int] = None

    center_lat: Optional[float] = None
    center_lng: Optional[float] = None
    radius_km: Optional[float] = None

    # Optional per-zone override of the global platform_delivery_cut_pct.
    # None = use the platform default.
    platform_cut_pct_override: Optional[float] = Field(
        default=None, ge=0, le=100
    )

    is_active: bool = True
    display_order: int = 0

    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)

    class Settings:
        name = "delivery_zones"
        indexes = ["slug", "is_active"]
