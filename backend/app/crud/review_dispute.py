from datetime import datetime, timezone
from typing import Optional

from beanie import PydanticObjectId
from fastapi import Request

from app.crud import audit as audit_crud
from app.models.audit_log import ActorType
from app.models.review_dispute import DisputeStatus, ReviewDispute


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def get_by_id(dispute_id: str) -> Optional[ReviewDispute]:
    try:
        return await ReviewDispute.get(PydanticObjectId(dispute_id))
    except Exception:
        return None


async def get_open_for_review(review_id: str) -> Optional[ReviewDispute]:
    try:
        rid = PydanticObjectId(review_id)
    except Exception:
        return None
    return await ReviewDispute.find_one(
        ReviewDispute.review_id == rid,
        ReviewDispute.status == DisputeStatus.OPEN,
    )


async def create_dispute(
    *,
    review_id: PydanticObjectId,
    vendor_id: PydanticObjectId,
    order_reference: str,
    reason: str,
    session=None,
) -> ReviewDispute:
    d = ReviewDispute(
        review_id=review_id,
        vendor_id=vendor_id,
        order_reference=order_reference,
        reason=reason,
    )
    await d.insert(session=session)
    return d


async def list_disputes(
    status: Optional[DisputeStatus] = None,
    vendor_id: Optional[str] = None,
    limit: int = 200,
    skip: int = 0,
) -> list[ReviewDispute]:
    query = ReviewDispute.find()
    if status:
        query = query.find(ReviewDispute.status == status)
    if vendor_id:
        query = query.find(ReviewDispute.vendor_id == PydanticObjectId(vendor_id))
    return await query.sort(-ReviewDispute.created_at).skip(skip).limit(limit).to_list()


async def resolve(
    dispute: ReviewDispute,
    *,
    status: DisputeStatus,
    admin_id: str,
    review_notes: Optional[str] = None,
    request: Optional[Request] = None,
    session=None,
) -> ReviewDispute:
    if dispute.status != DisputeStatus.OPEN:
        raise ValueError(f"Dispute is already '{dispute.status.value}'")

    dispute.status = status
    dispute.reviewed_by = admin_id
    dispute.reviewed_at = _now()
    dispute.review_notes = review_notes
    dispute.updated_at = _now()
    await dispute.save(session=session)

    await audit_crud.log(
        action=f"review_dispute.{status.value}",
        actor_type=ActorType.USER,
        actor_id=admin_id,
        target_type="ReviewDispute",
        target_id=str(dispute.id),
        metadata={"review_id": str(dispute.review_id)},
        request=request,
    )
    return dispute


async def withdraw(
    dispute: ReviewDispute,
    *,
    request: Optional[Request] = None,
) -> ReviewDispute:
    if dispute.status != DisputeStatus.OPEN:
        raise ValueError("Only open disputes can be withdrawn")
    dispute.status = DisputeStatus.WITHDRAWN
    dispute.updated_at = _now()
    await dispute.save()

    await audit_crud.log(
        action="review_dispute.withdrawn",
        actor_type=ActorType.VENDOR,
        target_type="ReviewDispute",
        target_id=str(dispute.id),
        request=request,
    )
    return dispute
