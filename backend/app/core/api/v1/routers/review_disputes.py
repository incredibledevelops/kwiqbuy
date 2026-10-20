from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.core.deps import get_current_admin, get_current_vendor
from app.crud import review as review_crud
from app.crud import review_dispute as dispute_crud
from app.models.review_dispute import DisputeStatus
from app.models.user import User
from app.schemas.review_dispute import (
    ReviewDisputeCreate,
    ReviewDisputeListOut,
    ReviewDisputeOut,
    ReviewDisputeResolveIn,
)

router = APIRouter(tags=["Review Disputes"])


def _out(d) -> ReviewDisputeOut:
    return ReviewDisputeOut(
        id=str(d.id),
        review_id=str(d.review_id),
        vendor_id=str(d.vendor_id),
        order_reference=d.order_reference,
        reason=d.reason,
        status=d.status,
        reviewed_by=d.reviewed_by,
        reviewed_at=d.reviewed_at,
        review_notes=d.review_notes,
        created_at=d.created_at,
        updated_at=d.updated_at,
    )


# ---------- Vendor ----------

@router.post(
    "/vendor/reviews/{review_id}/dispute",
    response_model=ReviewDisputeOut,
    status_code=status.HTTP_201_CREATED,
)
async def dispute_review(
    review_id: str,
    payload: ReviewDisputeCreate,
    user: User = Depends(get_current_vendor),
):
    review = await review_crud.get_by_id(review_id)
    if not review:
        raise HTTPException(404, "Review not found")
    if review.vendor_id != user.vendor_id:
        raise HTTPException(403, "This review is not about your business")

    existing = await dispute_crud.get_open_for_review(review_id)
    if existing:
        raise HTTPException(409, "A dispute is already open for this review")

    d = await dispute_crud.create_dispute(
        review_id=review.id,
        vendor_id=user.vendor_id,
        order_reference=review.order_reference,
        reason=payload.reason,
    )
    await review_crud.mark_dispute_flag(review, True)
    return _out(d)


@router.get("/vendor/review-disputes", response_model=list[ReviewDisputeOut])
async def my_disputes(user: User = Depends(get_current_vendor)):
    rows = await dispute_crud.list_disputes(vendor_id=str(user.vendor_id))
    return [_out(r) for r in rows]


@router.post(
    "/vendor/review-disputes/{dispute_id}/withdraw",
    response_model=ReviewDisputeOut,
)
async def withdraw(
    dispute_id: str,
    user: User = Depends(get_current_vendor),
):
    d = await dispute_crud.get_by_id(dispute_id)
    if not d or d.vendor_id != user.vendor_id:
        raise HTTPException(404, "Dispute not found")
    try:
        d = await dispute_crud.withdraw(d)
    except ValueError as e:
        raise HTTPException(400, str(e))

    review = await review_crud.get_by_id(str(d.review_id))
    if review:
        await review_crud.mark_dispute_flag(review, False)
    return _out(d)


# ---------- Admin ----------

@router.get(
    "/admin/review-disputes",
    response_model=ReviewDisputeListOut,
    dependencies=[Depends(get_current_admin)],
)
async def admin_list(
    status_filter: DisputeStatus | None = Query(None, alias="status"),
    vendor_id: str | None = None,
    limit: int = Query(200, ge=1, le=500),
    skip: int = Query(0, ge=0),
):
    rows = await dispute_crud.list_disputes(
        status=status_filter, vendor_id=vendor_id, limit=limit, skip=skip
    )
    return ReviewDisputeListOut(items=[_out(r) for r in rows], total=len(rows))


@router.post(
    "/admin/review-disputes/{dispute_id}/resolve",
    response_model=ReviewDisputeOut,
    dependencies=[Depends(get_current_admin)],
)
async def admin_resolve(
    dispute_id: str,
    payload: ReviewDisputeResolveIn,
    request: Request,
    current_user: User = Depends(get_current_admin),
):
    d = await dispute_crud.get_by_id(dispute_id)
    if not d:
        raise HTTPException(404, "Dispute not found")
    try:
        d = await dispute_crud.resolve(
            d,
            status=payload.status,
            admin_id=str(current_user.id),
            review_notes=payload.review_notes,
            request=request,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

    review = await review_crud.get_by_id(str(d.review_id))
    if review:
        # UPHOLD → hide the review.  REJECTED/WITHDRAWN → clear flag.
        if d.status == DisputeStatus.UPHELD:
            await review_crud.mark_dispute_flag(review, False)
            review.is_published = False
            await review.save()
        else:
            await review_crud.mark_dispute_flag(review, False)

    return _out(d)
