from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from app.core.config import settings
from app.core.deps import get_current_admin, get_current_vendor
from app.core.paystack import PaystackError, paystack_client
from app.crud import platform_settings as ps_crud
from app.crud import subscription as sub_crud
from app.crud import vendor as vendor_crud
from app.models.subscription_tier import (
    SubscriptionStatus,
    SubscriptionTier,
    VendorSubscription,
)
from app.models.user import User
from app.schemas.subscription import (
    SubscriptionTierCreate,
    SubscriptionTierOut,
    SubscriptionTierUpdate,
    VendorSubscribeIn,
    VendorSubscriptionOut,
    VendorSubscriptionStatusOut,
)
from app.utils.generators import generate_payment_reference

router = APIRouter(tags=["Vendor Subscriptions"])


def _tier_out(t: SubscriptionTier) -> SubscriptionTierOut:
    return SubscriptionTierOut(
        id=str(t.id),
        slug=t.slug,
        name=t.name,
        description=t.description,
        monthly_price=t.monthly_price,
        commission_discount_pct=t.commission_discount_pct,
        features=t.features,
        is_active=t.is_active,
        display_order=t.display_order,
    )


def _sub_out(s: VendorSubscription) -> VendorSubscriptionOut:
    return VendorSubscriptionOut(
        id=str(s.id),
        vendor_id=str(s.vendor_id),
        tier_id=str(s.tier_id),
        tier_slug=s.tier_slug,
        status=s.status,
        started_at=s.started_at,
        current_period_start=s.current_period_start,
        current_period_end=s.current_period_end,
        cancelled_at=s.cancelled_at,
        expired_at=s.expired_at,
        last_payment_at=s.last_payment_at,
        last_payment_amount=s.last_payment_amount,
        created_at=s.created_at,
    )


# ---------- Public catalogue ----------

@router.get("/subscription-tiers", response_model=list[SubscriptionTierOut])
async def list_tiers_public():
    tiers = await sub_crud.list_tiers(active_only=True)
    return [_tier_out(t) for t in tiers]


# ---------- Admin ----------

@router.get(
    "/admin/subscription-tiers",
    response_model=list[SubscriptionTierOut],
    dependencies=[Depends(get_current_admin)],
)
async def admin_list_tiers():
    tiers = await sub_crud.list_tiers(active_only=False)
    return [_tier_out(t) for t in tiers]


@router.post(
    "/admin/subscription-tiers",
    response_model=SubscriptionTierOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_admin)],
)
async def admin_create_tier(payload: SubscriptionTierCreate):
    if payload.slug and await sub_crud.get_tier_by_slug(payload.slug):
        raise HTTPException(409, "Tier slug already exists")
    tier = await sub_crud.create_tier(payload.model_dump())
    return _tier_out(tier)


@router.patch(
    "/admin/subscription-tiers/{tier_id}",
    response_model=SubscriptionTierOut,
    dependencies=[Depends(get_current_admin)],
)
async def admin_update_tier(tier_id: str, payload: SubscriptionTierUpdate):
    tier = await sub_crud.get_tier_by_id(tier_id)
    if not tier:
        raise HTTPException(404, "Tier not found")
    tier = await sub_crud.update_tier(tier, payload.model_dump(exclude_unset=True))
    return _tier_out(tier)


@router.delete(
    "/admin/subscription-tiers/{tier_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_current_admin)],
)
async def admin_delete_tier(tier_id: str):
    tier = await sub_crud.get_tier_by_id(tier_id)
    if not tier:
        raise HTTPException(404, "Tier not found")
    await sub_crud.delete_tier(tier)


@router.get(
    "/admin/vendor-subscriptions",
    response_model=list[VendorSubscriptionOut],
    dependencies=[Depends(get_current_admin)],
)
async def admin_list_subscriptions(
    status_filter: SubscriptionStatus | None = None,
    vendor_id: str | None = None,
):
    subs = await sub_crud.list_subscriptions(status=status_filter, vendor_id=vendor_id)
    return [_sub_out(s) for s in subs]


# ---------- Vendor ----------

@router.get("/vendor/subscription", response_model=VendorSubscriptionStatusOut)
async def my_subscription(user: User = Depends(get_current_vendor)):
    v = await vendor_crud.get_by_id(str(user.vendor_id))
    if not v:
        raise HTTPException(404, "Vendor not found")

    active_sub = await sub_crud.get_active_for_vendor(str(v.id))

    # --- On-the-fly expiry check ---
    # If the active sub has passed its end date, downgrade immediately
    if active_sub and active_sub.current_period_end:
        now = datetime.now(timezone.utc)
        end_date = active_sub.current_period_end
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)
        if end_date < now:
            free_tier = await sub_crud.get_tier_by_slug("free")
            if free_tier:
                await sub_crud.subscribe_vendor(v, free_tier)
            active_sub = await sub_crud.get_active_for_vendor(str(v.id))
    # --------------------------------

    plat = await ps_crud.get_settings()
    base_pct = plat.commission_for(v.business_category.value)

    tier = None
    if active_sub:
        tier = await sub_crud.get_tier_by_id(str(active_sub.tier_id))

    effective = sub_crud.effective_commission_pct(v, base_pct, active_sub, tier)

    return VendorSubscriptionStatusOut(
        has_active_subscription=active_sub is not None,
        current=_sub_out(active_sub) if active_sub else None,
        tier=_tier_out(tier) if tier else None,
        base_commission_pct=base_pct,
        effective_commission_pct=effective,
        is_override=v.commission_pct_override is not None,
    )


class SubscribeResponse(BaseModel):
    requires_payment: bool
    authorization_url: str | None = None
    subscription: VendorSubscriptionOut | None = None


@router.post("/vendor/subscription/subscribe", response_model=SubscribeResponse)
async def subscribe(
    payload: VendorSubscribeIn,
    user: User = Depends(get_current_vendor),
):
    v = await vendor_crud.get_by_id(str(user.vendor_id))
    if not v:
        raise HTTPException(404, "Vendor not found")

    tier = await sub_crud.get_tier_by_slug(payload.tier_slug)
    if not tier or not tier.is_active:
        raise HTTPException(404, "Tier not found or inactive")

    # Free tier - activate instantly
    if tier.monthly_price == 0:
        sub = await sub_crud.subscribe_vendor(v, tier)
        return SubscribeResponse(
            requires_payment=False,
            subscription=_sub_out(sub),
        )

    # Paid tier - create a pending subscription and init Paystack
    reference = generate_payment_reference(f"SUB-{v.id}")
    sub = await sub_crud.subscribe_vendor(v, tier, paystack_reference=reference)

    try:
        resp = await paystack_client.initialize_transaction(
            email=user.email,
            amount_pesewas=int(tier.monthly_price * 100),
            reference=reference,
            currency=settings.CURRENCY,
            # Redirect directly back to the dashboard — the page polls for
            # status until the webhook marks the subscription active.
            callback_url=f"{settings.FRONTEND_URL}/vendor/subscription",
            metadata={
                "type": "vendor_subscription",
                "vendor_id": str(v.id),
                "tier_slug": tier.slug,
                "subscription_id": str(sub.id),
            },
            channels=["mobile_money", "card"],
        )
    except PaystackError as e:
        raise HTTPException(502, f"Paystack error: {e.message}")

    return SubscribeResponse(
        requires_payment=True,
        authorization_url=resp["data"]["authorization_url"],
        subscription=_sub_out(sub),
    )


@router.post("/vendor/subscription/cancel", response_model=VendorSubscriptionOut)
async def cancel(
    request: Request,
    user: User = Depends(get_current_vendor),
):
    v = await vendor_crud.get_by_id(str(user.vendor_id))
    if not v:
        raise HTTPException(404, "Vendor not found")
    active = await sub_crud.get_active_for_vendor(str(v.id))
    if not active:
        raise HTTPException(404, "No active subscription")
    active = await sub_crud.cancel_subscription(
        active, actor_id=str(user.id), request=request
    )
    return _sub_out(active)