"""
Vendor subscription tiers + assignments.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from beanie import PydanticObjectId
from fastapi import Request

from app.core.config import settings
from app.crud import audit as audit_crud
from app.models.audit_log import ActorType
from app.models.subscription_tier import (
    SubscriptionStatus,
    SubscriptionTier,
    VendorSubscription,
)
from app.models.vendor import Vendor


def _now() -> datetime:
    return datetime.now(timezone.utc)


def slugify(text: str) -> str:
    import re
    text = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[-\s]+", "-", text).strip("-")


# ---------- Tiers ----------

async def list_tiers(active_only: bool = True) -> list[SubscriptionTier]:
    query = SubscriptionTier.find()
    if active_only:
        query = query.find(SubscriptionTier.is_active == True)  # noqa: E712
    return await query.sort(+SubscriptionTier.display_order).to_list()


async def get_tier_by_id(tier_id: str) -> Optional[SubscriptionTier]:
    try:
        return await SubscriptionTier.get(PydanticObjectId(tier_id))
    except Exception:
        return None


async def get_tier_by_slug(slug: str) -> Optional[SubscriptionTier]:
    return await SubscriptionTier.find_one(SubscriptionTier.slug == slug)


async def create_tier(data: dict) -> SubscriptionTier:
    if not data.get("slug"):
        data["slug"] = slugify(data["name"])
    tier = SubscriptionTier(**data)
    await tier.insert()
    return tier


async def update_tier(tier: SubscriptionTier, data: dict) -> SubscriptionTier:
    for k, v in data.items():
        if v is None:
            continue
        if hasattr(tier, k):
            setattr(tier, k, v)
    tier.updated_at = _now()
    await tier.save()
    return tier


async def delete_tier(tier: SubscriptionTier) -> None:
    tier.is_active = False
    tier.updated_at = _now()
    await tier.save()


# ---------- Subscriptions ----------

async def get_subscription_by_id(sub_id: str) -> Optional[VendorSubscription]:
    """Fetch a subscription by its ID (needed for Paystack webhooks)."""
    try:
        return await VendorSubscription.get(PydanticObjectId(sub_id))
    except Exception:
        return None

async def get_active_for_vendor(vendor_id: str) -> Optional[VendorSubscription]:
    try:
        vid = PydanticObjectId(vendor_id)
    except Exception:
        return None
    return await VendorSubscription.find_one(
        VendorSubscription.vendor_id == vid,
        VendorSubscription.status == SubscriptionStatus.ACTIVE,
    )


async def list_subscriptions(
    status: Optional[SubscriptionStatus] = None,
    vendor_id: Optional[str] = None,
    limit: int = 200,
    skip: int = 0,
) -> list[VendorSubscription]:
    query = VendorSubscription.find()
    if status:
        query = query.find(VendorSubscription.status == status)
    if vendor_id:
        query = query.find(VendorSubscription.vendor_id == PydanticObjectId(vendor_id))
    return (
        await query.sort(-VendorSubscription.created_at).skip(skip).limit(limit).to_list()
    )


async def subscribe_vendor(
    vendor: Vendor,
    tier: SubscriptionTier,
    *,
    paystack_reference: Optional[str] = None,
    session=None,
) -> VendorSubscription:
    """
    Create or replace the vendor's active subscription.
    Cancels any existing active subscription first.
    """
    now = _now()

    # Cancel any existing
    existing = await VendorSubscription.find_one(
        VendorSubscription.vendor_id == vendor.id,
        VendorSubscription.status == SubscriptionStatus.ACTIVE,
    )
    if existing:
        existing.status = SubscriptionStatus.CANCELLED
        existing.cancelled_at = now
        existing.updated_at = now
        await existing.save(session=session)

    # 30 day billing cycle
    period_end = now + timedelta(days=30)

    sub = VendorSubscription(
        vendor_id=vendor.id,
        tier_id=tier.id,
        tier_slug=tier.slug,
        status=(
            SubscriptionStatus.ACTIVE
            if tier.monthly_price == 0
            else SubscriptionStatus.PENDING
        ),
        started_at=now,
        current_period_start=now,
        current_period_end=period_end,
        paystack_reference=paystack_reference,
        last_payment_at=now if tier.monthly_price == 0 else None,
        last_payment_amount=0.0 if tier.monthly_price == 0 else tier.monthly_price,
    )
    await sub.insert(session=session)
    return sub


async def activate_subscription(
    sub: VendorSubscription,
    *,
    paystack_reference: Optional[str] = None,
    session=None,
) -> VendorSubscription:
    """Mark a pending subscription as paid + active."""
    now = _now()
    sub.status = SubscriptionStatus.ACTIVE
    sub.last_payment_at = now
    sub.current_period_start = now
    sub.current_period_end = now + timedelta(days=30)
    if paystack_reference:
        sub.paystack_reference = paystack_reference
    sub.updated_at = now
    await sub.save(session=session)
    return sub


async def cancel_subscription(
    sub: VendorSubscription,
    *,
    actor_id: Optional[str] = None,
    request: Optional[Request] = None,
    session=None,
) -> VendorSubscription:
    now = _now()
    sub.status = SubscriptionStatus.CANCELLED
    sub.cancelled_at = now
    sub.updated_at = now
    await sub.save(session=session)

    await audit_crud.log(
        action="vendor_subscription.cancelled",
        actor_type=ActorType.USER if actor_id else ActorType.SYSTEM,
        actor_id=actor_id,
        target_type="VendorSubscription",
        target_id=str(sub.id),
        request=request,
    )
    return sub


def effective_commission_pct(
    vendor: Vendor,
    base_pct: float,
    subscription: Optional[VendorSubscription],
    tier: Optional[SubscriptionTier],
) -> float:
    """
    Apply the vendor's overrides in priority order:
      1. explicit vendor.commission_pct_override wins
      2. else if an active subscription → base − tier.commission_discount_pct
      3. else base
    Clamped to [0, 100].
    """
    if vendor.commission_pct_override is not None:
        return float(vendor.commission_pct_override)

    if (
        settings.VENDOR_TIERS_ENABLED
        and subscription is not None
        and subscription.status == SubscriptionStatus.ACTIVE
        and tier is not None
    ):
        discounted = base_pct - float(tier.commission_discount_pct or 0)
        return max(0.0, min(100.0, discounted))

    return float(base_pct)