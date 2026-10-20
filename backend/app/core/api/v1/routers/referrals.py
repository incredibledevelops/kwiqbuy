from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import get_current_admin, get_current_customer
from app.crud import referral as referral_crud
from app.models.customer import Customer
from app.models.referral import Referral, ReferralStatus
from app.schemas.referral import (
    ReferralApplyIn,
    ReferralApplyOut,
    ReferralCreate,
    ReferralOut,
    ReferralSummary,
)

router = APIRouter(prefix="/referrals", tags=["Referrals"])


def _to_out(r: Referral) -> ReferralOut:
    return ReferralOut(
        id=str(r.id),
        code=r.code,
        referrer_phone=r.referrer_phone,
        referrer_name=r.referrer_name,
        referee_phone=r.referee_phone,
        referee_name=r.referee_name,
        status=r.status,
        referrer_reward=r.referrer_reward,
        referee_reward=r.referee_reward,
        reward_currency=r.reward_currency,
        completed_at=r.completed_at,
        triggering_order_reference=r.triggering_order_reference,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


@router.get("/code/{code}/validate", response_model=ReferralApplyOut)
async def validate_code(code: str):
    ref = await referral_crud.get_by_code(code)
    if not ref:
        return ReferralApplyOut(success=False, message="Referral code not found")
    if ref.status == ReferralStatus.COMPLETED:
        return ReferralApplyOut(
            success=False, message="This referral code has already been used"
        )
    if ref.status == ReferralStatus.EXPIRED:
        return ReferralApplyOut(
            success=False, message="This referral code has expired"
        )
    return ReferralApplyOut(
        success=True,
        message=f"Valid! You'll get GH₵ {ref.referee_reward:.2f} off your first order.",
        referral_code=ref.code,
        discount_amount=ref.referee_reward,
    )


@router.post("/apply", response_model=ReferralApplyOut)
async def apply_code(payload: ReferralApplyIn):
    ref = await referral_crud.get_by_code(payload.code)
    if not ref:
        raise HTTPException(404, "Referral code not found")
    if ref.status != ReferralStatus.PENDING:
        raise HTTPException(400, "This referral code is no longer usable")
    if ref.referrer_phone == payload.referee_phone:
        raise HTTPException(400, "You cannot use your own referral code")
    if ref.referee_phone and ref.referee_phone != payload.referee_phone:
        raise HTTPException(400, "This referral code was already claimed")

    ref = await referral_crud.attach_referee(
        ref, payload.referee_phone, payload.referee_name
    )
    return ReferralApplyOut(
        success=True,
        message=(
            f"Referral applied! You'll get GH₵ {ref.referee_reward:.2f} off "
            "after your first order."
        ),
        referral_code=ref.code,
        discount_amount=ref.referee_reward,
    )


@router.get("/me", response_model=list[ReferralOut])
async def my_referrals(current: Customer = Depends(get_current_customer)):
    refs = await referral_crud.list_for_referrer(current.phone)
    return [_to_out(r) for r in refs]


@router.get("/me/summary", response_model=ReferralSummary)
async def my_summary(current: Customer = Depends(get_current_customer)):
    data = await referral_crud.summary_for_referrer(current.phone)
    return ReferralSummary(**data)


@router.post("/me/generate", response_model=ReferralOut)
async def generate_my_referral(current: Customer = Depends(get_current_customer)):
    existing = await referral_crud.list_for_referrer(current.phone)
    pending = [r for r in existing if r.status == ReferralStatus.PENDING]
    if pending:
        return _to_out(pending[0])
    ref = await referral_crud.create_referral(
        referrer_phone=current.phone,
        referrer_name=current.full_name,
        referrer_reward=10.0,
        referee_reward=10.0,
    )
    return _to_out(ref)


@router.get("", response_model=list[ReferralOut], dependencies=[Depends(get_current_admin)])
async def list_all(
    status_filter: ReferralStatus | None = Query(None, alias="status"),
    limit: int = Query(200, ge=1, le=500),
    skip: int = Query(0, ge=0),
):
    refs = await referral_crud.list_all(status=status_filter, limit=limit, skip=skip)
    return [_to_out(r) for r in refs]


@router.post(
    "",
    response_model=ReferralOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_admin)],
)
async def admin_create(payload: ReferralCreate):
    ref = await referral_crud.create_referral(
        referrer_phone=payload.referrer_phone,
        referrer_name=payload.referrer_name,
    )
    return _to_out(ref)