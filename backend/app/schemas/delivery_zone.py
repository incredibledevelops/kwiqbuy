from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DeliveryZoneBase(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    slug: Optional[str] = None
    description: Optional[str] = Field(default=None, max_length=500)
    delivery_fee: float = Field(default=15.0, ge=0)
    estimated_minutes: Optional[int] = Field(default=None, ge=1, le=300)
    center_lat: Optional[float] = None
    center_lng: Optional[float] = None
    radius_km: Optional[float] = Field(default=None, ge=0)
    platform_cut_pct_override: Optional[float] = Field(default=None, ge=0, le=100)
    is_active: bool = True
    display_order: int = 0


class DeliveryZoneCreate(DeliveryZoneBase):
    pass


class DeliveryZoneUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    slug: Optional[str] = None
    description: Optional[str] = Field(default=None, max_length=500)
    delivery_fee: Optional[float] = Field(default=None, ge=0)
    estimated_minutes: Optional[int] = Field(default=None, ge=1, le=300)
    center_lat: Optional[float] = None
    center_lng: Optional[float] = None
    radius_km: Optional[float] = Field(default=None, ge=0)
    platform_cut_pct_override: Optional[float] = Field(default=None, ge=0, le=100)
    is_active: Optional[bool] = None
    display_order: Optional[int] = None


class DeliveryZoneOut(DeliveryZoneBase):
    id: str
    created_at: datetime
    updated_at: datetime
