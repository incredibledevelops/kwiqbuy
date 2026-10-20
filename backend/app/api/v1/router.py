from fastapi import APIRouter

from app.api.v1.routers import (
    admin_2fa,
    admin_audit,
    admin_exports,
    admin_payouts,
    admin_riders,
    admin_settings,
    admin_wallet,
    analytics,
    auth,
    builder,
    cart,
    categories,
    customer_account,
    customer_auth, # <--- Imported here
    delivery_zones,
    loyalty,
    orders,
    payments,
    products,
    promo_codes,
    public_config,
    referrals,
    review_disputes,
    reviews,
    rider_locations,
    riders,
    search,
    seo,
    subscriptions,
    uploads,
    vendor_applications,
    vendor_bulk,
    vendor_portal,
    vendor_webhooks,
    vendors,
    wallet,
)

api_router = APIRouter()

# Auth
api_router.include_router(auth.router)
api_router.include_router(customer_auth.router, prefix="/customer-auth") # <--- Prefix added here

# Customers
api_router.include_router(customer_account.router)
api_router.include_router(wallet.router)

# Marketplace catalog
api_router.include_router(categories.router)
api_router.include_router(products.router)
api_router.include_router(builder.router)
api_router.include_router(vendors.router)
api_router.include_router(vendor_applications.router)
api_router.include_router(subscriptions.router)

# Cart
api_router.include_router(cart.router)

# Public
api_router.include_router(public_config.router)
api_router.include_router(search.router)
api_router.include_router(seo.router)

# Zones
api_router.include_router(delivery_zones.router)

# Growth
api_router.include_router(promo_codes.router)
api_router.include_router(referrals.router)
api_router.include_router(reviews.router)
api_router.include_router(review_disputes.router)

# Orders & fulfillment
api_router.include_router(orders.router)
api_router.include_router(riders.router)
api_router.include_router(rider_locations.router)
api_router.include_router(payments.router)

# Vendor portal + bulk + webhooks
api_router.include_router(vendor_portal.router)
api_router.include_router(vendor_bulk.router)
api_router.include_router(vendor_webhooks.router)

# Admin
api_router.include_router(admin_settings.router)
api_router.include_router(admin_payouts.router)
api_router.include_router(admin_audit.router)
api_router.include_router(admin_wallet.router)
api_router.include_router(admin_2fa.router)
api_router.include_router(admin_exports.router)
api_router.include_router(admin_riders.router)
api_router.include_router(analytics.router)

# Loyalty
api_router.include_router(loyalty.router)

# Infra
api_router.include_router(uploads.router)