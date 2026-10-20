from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class PlatformSettingsOut(BaseModel):
    commission_pct: float
    food_commission_pct: float
    retail_commission_pct: float
    platform_delivery_cut_pct: float
    min_payout_ghs: float
    payout_schedule: str
    free_delivery_threshold: float
    rider_fee_model: str
    rider_flat_fee_ghs: float
    rider_pct_of_delivery_fee: float
    support_phone: str
    support_email: Optional[EmailStr] = None
    support_whatsapp: str
    maintenance_mode: bool
    customer_ordering_enabled: bool
    vendor_signups_enabled: bool
    admin_ip_allowlist: List[str] = Field(default_factory=list)
    admin_2fa_required: bool = False
    updated_by: Optional[str] = None
    updated_at: datetime


class PlatformSettingsUpdate(BaseModel):
    commission_pct: Optional[float] = Field(default=None, ge=0, le=100)
    food_commission_pct: Optional[float] = Field(default=None, ge=0, le=100)
    retail_commission_pct: Optional[float] = Field(default=None, ge=0, le=100)
    platform_delivery_cut_pct: Optional[float] = Field(default=None, ge=0, le=100)
    min_payout_ghs: Optional[float] = Field(default=None, ge=0)
    payout_schedule: Optional[str] = None
    free_delivery_threshold: Optional[float] = Field(default=None, ge=0)
    rider_fee_model: Optional[str] = None
    rider_flat_fee_ghs: Optional[float] = Field(default=None, ge=0)
    rider_pct_of_delivery_fee: Optional[float] = Field(default=None, ge=0, le=100)
    support_phone: Optional[str] = None
    support_email: Optional[EmailStr] = None
    support_whatsapp: Optional[str] = None
    maintenance_mode: Optional[bool] = None
    customer_ordering_enabled: Optional[bool] = None
    vendor_signups_enabled: Optional[bool] = None
    admin_ip_allowlist: Optional[List[str]] = None
    admin_2fa_required: Optional[bool] = None


class PlatformPublicSettingsOut(BaseModel):
    commission_pct: float
    free_delivery_threshold: float
    support_phone: str
    support_whatsapp: str
    maintenance_mode: bool
    customer_ordering_enabled: bool
    vendor_signups_enabled: bool
    currency: str = "GHS"
