from datetime import datetime, timezone
from typing import List, Optional

from beanie import Document, Indexed, PydanticObjectId
from pydantic import BaseModel, EmailStr, Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


class SavedAddress(BaseModel):
    label: str = "Home"
    zone_id: Optional[PydanticObjectId] = None
    zone_name: str
    address: str
    is_default: bool = False


class Customer(Document):
    phone: Indexed(str, unique=True)  # type: ignore
    email: Optional[EmailStr] = None
    full_name: str

    # Loyalty
    loyalty_points: int = 0
    lifetime_points_earned: int = 0
    lifetime_points_redeemed: int = 0

    # Wallet (Phase 2) — store credit in GHS
    wallet_balance: float = 0.0
    lifetime_wallet_credited: float = 0.0
    lifetime_wallet_spent: float = 0.0

    # Stats
    total_orders: int = 0
    total_spent: float = 0.0
    last_order_at: Optional[datetime] = None

    # Saved info
    saved_addresses: List[SavedAddress] = Field(default_factory=list)
    favorite_item_ids: List[PydanticObjectId] = Field(default_factory=list)

    # Referral
    referral_code: Optional[str] = None

    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)

    class Settings:
        name = "customers"
        indexes = ["phone"]
