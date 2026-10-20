from app.models.audit_log import ActorType, AuditLog
from app.models.category import Category
from app.models.customer import Customer, SavedAddress
from app.models.delivery_zone import DeliveryZone
from app.models.idempotency import IdempotencyRecord
from app.models.loyalty import LoyaltyReason, LoyaltyTransaction
from app.models.order import (
    Order, OrderCustomer, OrderItem, OrderStatus, OrderStatusEvent,
    OrderType, VendorOrder, VendorOrderStatus,
)
from app.models.otp import OTPPurpose, OTPToken
from app.models.payment import Payment, PaymentStatus
from app.models.payout import PayoutMethod, PayoutStatus, VendorPayout
from app.models.platform_settings import PlatformSettings
from app.models.product import Product, ProductType, ProductVariant, VariantOption
from app.models.promo_code import DiscountType, PromoCode
from app.models.referral import Referral, ReferralStatus
from app.models.review import Review
from app.models.review_dispute import DisputeStatus, ReviewDispute
from app.models.revoked_token import RevokedToken
from app.models.rider_earning import RiderEarning, RiderEarningStatus
from app.models.rider_location import RiderLocation
from app.models.subscription_tier import (
    SubscriptionStatus, SubscriptionTier, VendorSubscription,
)
from app.models.two_factor import Admin2FA
from app.models.user import User, UserRole
from app.models.variant_stock import VariantStock
from app.models.vendor import GeoPoint, Vendor, VendorCategory, VendorStatus
from app.models.vendor_application import (
    VendorApplication, VendorApplicationStatus,
)
from app.models.wallet import WalletReason, WalletTransaction
from app.models.webhook import (
    VendorWebhook, WebhookDelivery, WebhookEvent, WebhookStatus,
)

ALL_DOCUMENTS = [
    User, Customer,
    Vendor, VendorApplication, PlatformSettings, VendorPayout,
    Category, Product,
    DeliveryZone, Order, Payment,
    PromoCode, Referral, LoyaltyTransaction, Review,
    OTPToken,
    IdempotencyRecord,
    AuditLog,
    RevokedToken,
    WalletTransaction,
    RiderEarning,
    RiderLocation,
    ReviewDispute,
    SubscriptionTier, VendorSubscription,
    VariantStock,
    VendorWebhook, WebhookDelivery,
    Admin2FA,
]

__all__ = [
    "User", "UserRole",
    "Customer", "SavedAddress",
    "Vendor", "VendorStatus", "VendorCategory", "GeoPoint",
    "VendorApplication", "VendorApplicationStatus",
    "PlatformSettings", "VendorPayout", "PayoutMethod", "PayoutStatus",
    "Category",
    "Product", "ProductType", "ProductVariant", "VariantOption",
    "DeliveryZone",
    "Order", "OrderItem", "OrderCustomer",
    "OrderStatus", "OrderStatusEvent", "OrderType",
    "VendorOrder", "VendorOrderStatus",
    "Payment", "PaymentStatus",
    "PromoCode", "DiscountType",
    "Referral", "ReferralStatus",
    "LoyaltyTransaction", "LoyaltyReason",
    "Review",
    "ReviewDispute", "DisputeStatus",
    "RevokedToken",
    "WalletTransaction", "WalletReason",
    "RiderEarning", "RiderEarningStatus",
    "RiderLocation",
    "SubscriptionTier", "VendorSubscription", "SubscriptionStatus",
    "VariantStock",
    "VendorWebhook", "WebhookDelivery", "WebhookEvent", "WebhookStatus",
    "Admin2FA",
    "OTPToken", "OTPPurpose",
    "IdempotencyRecord",
    "AuditLog", "ActorType",
    "ALL_DOCUMENTS",
]
