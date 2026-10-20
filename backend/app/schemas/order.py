from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.order import (
    OrderStatus,
    OrderStatusEvent,
    OrderType,
    VendorOrderStatus,
)


class OrderItemIn(BaseModel):
    product_id: Optional[str] = None
    variant_sku: Optional[str] = None
    variant_selections: Optional[dict[str, str]] = None
    name: str
    unit_price: float = Field(ge=0)
    quantity: int = Field(ge=1)
    is_custom_bowl: bool = False
    customizations: Optional[dict] = None


class OrderCustomerIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(min_length=7, max_length=20)


class OrderCreate(BaseModel):
    customer: OrderCustomerIn
    delivery_zone_id: Optional[str] = None
    delivery_address: str = Field(min_length=4, max_length=300)
    items: List[OrderItemIn] = Field(min_length=1)
    notes: Optional[str] = Field(default=None, max_length=1000)
    promo_code: Optional[str] = None
    redeem_points: Optional[int] = Field(default=None, ge=0)
    apply_wallet: bool = False


class OrderItemOut(BaseModel):
    product_id: Optional[str] = None
    variant_sku: Optional[str] = None
    variant_selections: Optional[dict[str, str]] = None
    name: str
    unit_price: float
    quantity: int
    is_custom_bowl: bool
    customizations: Optional[dict] = None


class VendorOrderOut(BaseModel):
    vendor_id: str
    vendor_name: str
    vendor_category: str
    items: List[OrderItemOut]
    subtotal: float
    commission_pct: float
    platform_fee: float
    vendor_payout: float
    status: VendorOrderStatus
    status_history: List[OrderStatusEvent] = Field(default_factory=list)
    rejection_reason: Optional[str] = None
    accepted_at: Optional[datetime] = None
    ready_at: Optional[datetime] = None
    picked_up_at: Optional[datetime] = None
    packed_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None


class OrderOut(BaseModel):
    id: str
    reference: str
    order_type: OrderType
    customer: OrderCustomerIn
    delivery_zone_id: Optional[str] = None
    delivery_zone_name: str = ""
    delivery_address: str
    vendor_orders: List[VendorOrderOut]
    subtotal: float
    delivery_fee: float
    platform_delivery_cut: float = 0.0
    rider_earning: float = 0.0
    promo_code: Optional[str] = None
    promo_discount: float = 0.0
    loyalty_points_redeemed: int = 0
    loyalty_discount: float = 0.0
    wallet_applied: float = 0.0
    wallet_used: bool = False
    total: float
    amount_due_external: float = 0.0
    status: OrderStatus
    status_history: List[OrderStatusEvent] = Field(default_factory=list)
    rider_id: Optional[str] = None
    rider_name: Optional[str] = None
    rider_phone: Optional[str] = None
    dispatched_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    payment_reference: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class OrderAdminListOut(BaseModel):
    id: str
    reference: str
    order_type: OrderType
    customer_name: str
    customer_phone: str
    delivery_zone_name: str
    vendor_names: List[str] = Field(default_factory=list)
    vendor_count: int = 0
    total: float
    platform_fee_total: float = 0.0
    platform_delivery_cut: float = 0.0
    rider_earning: float = 0.0
    wallet_applied: float = 0.0
    status: OrderStatus
    promo_code: Optional[str] = None
    created_at: datetime


class OrderVendorListOut(BaseModel):
    order_id: str
    reference: str
    order_type: OrderType
    customer_name: str
    delivery_zone_name: str
    items_count: int
    subtotal: float
    platform_fee: float
    vendor_payout: float
    status: VendorOrderStatus
    created_at: datetime


class OrderTrackOut(BaseModel):
    reference: str
    order_type: OrderType
    status: OrderStatus
    subtotal: float
    delivery_fee: float
    promo_discount: float = 0.0
    loyalty_discount: float = 0.0
    wallet_applied: float = 0.0
    total: float
    amount_due_external: float = 0.0
    delivery_zone_name: str = ""
    delivery_address: str
    vendor_statuses: List[dict] = Field(default_factory=list)
    rider_name: Optional[str] = None
    rider_phone: Optional[str] = None
    dispatched_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    status_history: List[OrderStatusEvent] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class VendorOrderStatusUpdate(BaseModel):
    status: VendorOrderStatus
    note: Optional[str] = Field(default=None, max_length=500)
    reason: Optional[str] = Field(default=None, max_length=500)


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
    note: Optional[str] = Field(default=None, max_length=500)


class OrderAssignRider(BaseModel):
    rider_id: str


class RiderOrderOut(BaseModel):
    id: str
    reference: str
    order_type: OrderType
    customer_name: str
    customer_phone: str
    delivery_address: str
    delivery_zone_name: str
    vendor_pickups: List[dict] = Field(default_factory=list)
    items_count: int
    total: float
    rider_earning: float = 0.0
    status: OrderStatus
    dispatched_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    created_at: datetime


class RiderAssignableOut(BaseModel):
    id: str
    reference: str
    delivery_zone_name: str
    vendor_count: int
    items_count: int
    total: float
    rider_earning: float = 0.0
    status: OrderStatus
    created_at: datetime
