from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.vendor_application import VendorApplicationStatus


# ---------- Public submission ----------

class VendorApplicationIn(BaseModel):
    business_name: str = Field(min_length=2, max_length=120)
    business_category: Optional[str] = Field(default="food", description="food | retail")
    business_type: Optional[str] = Field(default=None, max_length=60)
    description: str = Field(min_length=10, max_length=2000)
    contact_name: str = Field(min_length=2, max_length=100)
    contact_email: EmailStr
    contact_phone: str = Field(min_length=7, max_length=20)

    pickup_address: str = Field(min_length=4, max_length=300)
    city: Optional[str] = None
    region: Optional[str] = None

    requested_payout_method: Optional[str] = None
    requested_payout_account_name: Optional[str] = None
    requested_payout_account_number: Optional[str] = None

    id_document_url: Optional[str] = None
    business_registration_url: Optional[str] = None


class VendorApplicationOut(BaseModel):
    id: str
    business_name: str
    business_type: Optional[str] = None
    business_category: Optional[str] = None
    description: str
    contact_name: str
    contact_email: str
    contact_phone: str
    pickup_address: str
    city: Optional[str] = None
    region: Optional[str] = None
    requested_payout_method: Optional[str] = None
    id_document_url: Optional[str] = None
    business_registration_url: Optional[str] = None
    status: VendorApplicationStatus
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_vendor_id: Optional[str] = None
    created_user_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    expires_at: datetime


class VendorApplicationSubmitOut(BaseModel):
    """Response returned right after the applicant submits."""
    id: str
    message: str = (
        "Thanks — we've received your application and will review it "
        "within 2 business days."
    )


# ---------- Admin decisions ----------

class VendorApplicationApproveIn(BaseModel):
    """
    Admin approves. Server generates a temporary password and returns it
    exactly once. The vendor must change it on first login.
    """
    commission_pct_override: Optional[float] = Field(default=None, ge=0, le=100)


class VendorApplicationApproveOut(BaseModel):
    application: VendorApplicationOut
    vendor_id: str
    owner_user_id: str
    owner_email: str
    temporary_password: str


class VendorApplicationRejectIn(BaseModel):
    reason: str = Field(min_length=4, max_length=500)