from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from beanie import Document, Indexed, PydanticObjectId
from pydantic import BaseModel, Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


class OrderType(str, Enum):
    FOOD = "food"
    RETAIL = "retail"
    MIXED = "mixed"


class OrderStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    PREPARING = "preparing"
    READY = "ready"
    OUT_FOR_DELIVERY = "out_for_delivery"
    SHIPPED = "shipped"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    FAILED = "failed"
    REFUNDED = "refunded"


class VendorOrderStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    PACKED = "packed"
    PICKED_UP = "picked_up"
    SHIPPED = "shipped"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class OrderItem(BaseModel):
    product_id: Optional[PydanticObjectId] = None
    variant_sku: Optional[str] = None
    variant_selections: Optional[dict[str, str]] = None
    name: str
    unit_price: float
    quantity: int = Field(ge=1)
    is_custom_bowl: bool = False
    customizations: Optional[dict] = None


class OrderCustomer(BaseModel):
    full_name: str
    email: str
    phone: str


class OrderStatusEvent(BaseModel):
    status: str
    at: datetime = Field(default_factory=_now)
    by: Optional[str] = None
    note: Optional[str] = None


class VendorOrder(BaseModel):
    vendor_id: PydanticObjectId
    vendor_name: str
    vendor_category: str = "food"

    items: List[OrderItem] = Field(default_factory=list)
    subtotal: float = Field(ge=0)

    commission_pct: float = Field(ge=0, le=100)
    platform_fee: float = Field(ge=0)
    vendor_payout: float = Field(ge=0)

    status: VendorOrderStatus = VendorOrderStatus.PENDING
    status_history: List[OrderStatusEvent] = Field(default_factory=list)
    rejection_reason: Optional[str] = None

    accepted_at: Optional[datetime] = None
    ready_at: Optional[datetime] = None
    picked_up_at: Optional[datetime] = None
    packed_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None

    payout_id: Optional[PydanticObjectId] = None


class Order(Document):
    reference: Indexed(str, unique=True)  # type: ignore
    order_type: OrderType = OrderType.FOOD

    customer: OrderCustomer

    delivery_zone_id: Optional[PydanticObjectId] = None
    delivery_zone_name: str = ""
    delivery_address: str
    delivery_fee: float = 0.0
    delivery_distance_km: Optional[float] = None

    # NEW (Phase 2) — money split for the delivery fee
    platform_delivery_cut: float = 0.0   # what KwiqBuy keeps from delivery_fee
    rider_earning: float = 0.0           # what the rider gets

    vendor_orders: List[VendorOrder] = Field(default_factory=list)

    subtotal: float = 0.0
    promo_code: Optional[str] = None
    promo_discount: float = 0.0
    loyalty_points_redeemed: int = 0
    loyalty_discount: float = 0.0
    loyalty_points_earned: int = 0

    # NEW (Phase 2) — wallet usage snapshot
    wallet_applied: float = 0.0          # how much wallet was used on this order
    wallet_used: bool = False

    total: float = 0.0
    amount_due_external: float = 0.0     # what still needs Paystack (total − wallet)

    referral_code: Optional[str] = None
    referral_discount: float = 0.0

    status: OrderStatus = OrderStatus.PENDING
    status_history: List[OrderStatusEvent] = Field(default_factory=list)

    rider_id: Optional[PydanticObjectId] = None
    rider_name: Optional[str] = None
    rider_phone: Optional[str] = None
    dispatched_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None

    payment_reference: Optional[str] = None
    notes: Optional[str] = None

    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)

    class Settings:
        name = "orders"
        indexes = [
            "reference",
            "status",
            "order_type",
            "customer.phone",
            "vendor_orders.vendor_id",
            "promo_code",
            "rider_id",
            "created_at",
        ]
