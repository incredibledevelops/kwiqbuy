from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.vendor import VendorCategory, VendorStatus


class VendorBase(BaseModel):
    business_name: str = Field(min_length=2, max_length=120)
    business_category: VendorCategory
    business_subtype: Optional[str] = Field(default=None, max_length=60)
    description: Optional[str] = Field(default=None, max_length=2000)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    pickup_address: str = Field(min_length=4, max_length=300)
    pickup_lat: Optional[float] = None
    pickup_lng: Optional[float] = None
    delivery_radius_km: float = Field(default=15.0, ge=0.1, le=100.0)
    prep_minutes: int = Field(default=20, ge=1, le=1440)


class VendorCreateByAdmin(VendorBase):
    owner_full_name: str = Field(min_length=2, max_length=100)
    owner_email: EmailStr
    owner_phone: Optional[str] = None
    owner_password: str = Field(min_length=8, max_length=128)
    commission_pct_override: Optional[float] = Field(default=None, ge=0, le=100)
    status: VendorStatus = VendorStatus.ACTIVE


class VendorUpdate(BaseModel):
    business_name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    business_subtype: Optional[str] = Field(default=None, max_length=60)
    description: Optional[str] = Field(default=None, max_length=2000)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    pickup_address: Optional[str] = Field(default=None, min_length=4, max_length=300)
    pickup_lat: Optional[float] = None
    pickup_lng: Optional[float] = None
    delivery_radius_km: Optional[float] = Field(default=None, ge=0.1, le=100.0)
    prep_minutes: Optional[int] = Field(default=None, ge=1, le=1440)
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    
    # --- ADDED PAYOUT FIELDS ---
    payout_recipient_type: Optional[str] = None
    payout_account_name: Optional[str] = None
    payout_account_number: Optional[str] = None
    payout_bank_code: Optional[str] = None
    payout_mobile_provider: Optional[str] = None
    payout_recipient_code: Optional[str] = None


class VendorAdminUpdate(VendorUpdate):
    commission_pct_override: Optional[float] = Field(default=None, ge=0, le=100)
    status: Optional[VendorStatus] = None


class VendorStatusUpdate(BaseModel):
    status: VendorStatus
    reason: Optional[str] = None


class VendorPayoutDetailsIn(BaseModel):
    payout_recipient_type: Optional[str] = None
    payout_account_name: Optional[str] = None
    payout_account_number: Optional[str] = None
    payout_bank_code: Optional[str] = None
    payout_mobile_provider: Optional[str] = None


# ---------- Out ----------

class VendorOut(BaseModel):
    id: str
    business_name: str
    slug: str
    business_category: VendorCategory
    business_subtype: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    pickup_address: str
    pickup_lat: Optional[float] = None
    pickup_lng: Optional[float] = None
    delivery_radius_km: float = 15.0
    prep_minutes: int
    status: VendorStatus
    commission_pct_override: Optional[float] = None
    average_rating: float = 0.0
    total_reviews: int = 0
    total_orders: int = 0
    created_at: datetime
    updated_at: datetime
    approved_at: Optional[datetime] = None


class VendorPublicOut(BaseModel):
    """Storefront view — customer-facing."""
    id: str
    business_name: str
    slug: str
    business_category: VendorCategory
    business_subtype: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    pickup_lat: Optional[float] = None
    pickup_lng: Optional[float] = None
    delivery_radius_km: float = 15.0
    prep_minutes: int
    average_rating: float = 0.0
    total_reviews: int = 0
    # Only present for /nearby results
    distance_km: Optional[float] = None
    distance_meters: Optional[float] = None


class NearbyVendorOut(VendorPublicOut):
    distance_km: float
    distance_meters: float


class NearbyVendorsOut(BaseModel):
    center_lat: float
    center_lng: float
    radius_km: float
    vendors: List[NearbyVendorOut]


class VendorSelfOut(VendorOut):
    available_balance: float = 0.0
    total_gross_sales: float = 0.0
    lifetime_platform_fees: float = 0.0
    lifetime_paid_out: float = 0.0
    payout_recipient_type: Optional[str] = None
    payout_account_name: Optional[str] = None
    payout_account_number: Optional[str] = None
    payout_bank_code: Optional[str] = None
    payout_mobile_provider: Optional[str] = None
    payout_recipient_code: Optional[str] = None


class VendorListOut(BaseModel):
    items: list[VendorOut]
    total: int