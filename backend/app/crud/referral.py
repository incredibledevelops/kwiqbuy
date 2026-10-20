import secrets
from datetime import datetime, timezone
from typing import Optional

from beanie import PydanticObjectId

from app.models.referral import Referral, ReferralStatus


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _generate_code() -> str:
    return "KB-" + secrets.token_hex(3)[:5].upper()


async def create_referral(
    referrer_phone: str,
    referrer_name: str,
    referrer_reward: float = 10.0,
    referee_reward: float = 10.0,
    *,
    session=None,
) -> Referral:
    for _ in range(5):
        code = _generate_code()
        existing = await Referral.find_one(Referral.code == code)
        if not existing:
            break
    else:
        raise RuntimeError("Could not generate unique referral code")

    ref = Referral(
        code=code,
        referrer_phone=referrer_phone,
        referrer_name=referrer_name,
        referrer_reward=referrer_reward,
        referee_reward=referee_reward,
    )
    await ref.insert(session=session)
    return ref


async def get_by_code(code: str) -> Optional[Referral]:
    return await Referral.find_one(Referral.code == code.strip().upper())


async def list_for_referrer(phone: str) -> list[Referral]:
    return (
        await Referral.find(Referral.referrer_phone == phone)
        .sort(-Referral.created_at)
        .to_list()
    )


async def list_all(
    status: Optional[ReferralStatus] = None,
    limit: int = 200,
    skip: int = 0,
) -> list[Referral]:
    query = Referral.find()
    if status:
        query = query.find(Referral.status == status)
    return await query.sort(-Referral.created_at).skip(skip).limit(limit).to_list()


async def attach_referee(
    referral: Referral,
    referee_phone: str,
    referee_name: str,
    *,
    session=None,
) -> Referral:
    referral.referee_phone = referee_phone
    referral.referee_name = referee_name
    referral.updated_at = _now()
    await referral.save(session=session)
    return referral


async def complete_referral(
    referral: Referral,
    triggering_order_reference: str,
    *,
    session=None,
) -> Referral:
    if referral.status == ReferralStatus.COMPLETED:
        return referral
    referral.status = ReferralStatus.COMPLETED
    referral.completed_at = _now()
    referral.triggering_order_reference = triggering_order_reference
    referral.updated_at = _now()
    await referral.save(session=session)
    return referral


async def find_pending_by_referee(referee_phone: str) -> Optional[Referral]:
    return await Referral.find_one(
        Referral.referee_phone == referee_phone,
        Referral.status == ReferralStatus.PENDING,
    )


async def summary_for_referrer(phone: str) -> dict:
    refs = await list_for_referrer(phone)
    completed = [r for r in refs if r.status == ReferralStatus.COMPLETED]
    pending = [r for r in refs if r.status == ReferralStatus.PENDING]
    total_earned = sum(r.referrer_reward for r in completed)
    return {
        "total_referrals": len(refs),
        "completed_referrals": len(completed),
        "pending_referrals": len(pending),
        "total_earned": round(total_earned, 2),
        "currency": "GHS",
    }


async def get_by_id(referral_id: str) -> Optional[Referral]:
    try:
        return await Referral.get(PydanticObjectId(referral_id))
    except Exception:
        return None


async def expire_referral(referral: Referral, *, session=None) -> Referral:
    referral.status = ReferralStatus.EXPIRED
    referral.updated_at = _now()
    await referral.save(session=session)
    return referral
