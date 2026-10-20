from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.core.config import settings
from app.core.deps import get_current_admin
from app.core.paystack import PaystackError, paystack_client
from app.crud import payout as payout_crud
from app.crud import vendor as vendor_crud
from app.models.payout import PayoutMethod, PayoutStatus
from app.models.user import User
from app.schemas.payout import (
    AdminPayoutCreateIn,
    VendorPayoutCancelIn,
    VendorPayoutFailIn,
    VendorPayoutOut,
)

router = APIRouter(prefix="/admin/payouts", tags=["Admin Payouts"])


def _to_out(p) -> VendorPayoutOut:
    return VendorPayoutOut(
        id=str(p.id),
        vendor_id=str(p.vendor_id),
        vendor_name=p.vendor_name,
        gross_sales=p.gross_sales,
        platform_fees=p.platform_fees,
        net_payout=p.net_payout,
        currency=p.currency,
        period_start=p.period_start,
        period_end=p.period_end,
        order_count=len(p.vendor_order_ids),
        status=p.status,
        method=p.method,
        paystack_transfer_code=p.paystack_transfer_code,
        paystack_transfer_reference=p.paystack_transfer_reference,
        failure_reason=p.failure_reason,
        requested_by=p.requested_by,
        processed_by=p.processed_by,
        created_at=p.created_at,
        processed_at=p.processed_at,
        paid_at=p.paid_at,
    )


@router.get("", response_model=list[VendorPayoutOut])
async def list_payouts(
    vendor_id: str | None = None,
    status_filter: PayoutStatus | None = Query(None, alias="status"),
    limit: int = Query(200, ge=1, le=500),
    skip: int = Query(0, ge=0),
    _=Depends(get_current_admin),
):
    payouts = await payout_crud.list_payouts(
        vendor_id=vendor_id, status=status_filter, limit=limit, skip=skip
    )
    return [_to_out(p) for p in payouts]


@router.post(
    "",
    response_model=VendorPayoutOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_payout(
    payload: AdminPayoutCreateIn,
    request: Request,
    current_user: User = Depends(get_current_admin),
):
    vendor = await vendor_crud.get_by_id(payload.vendor_id)
    if not vendor:
        raise HTTPException(404, "Vendor not found")

    try:
        p = await payout_crud.request_payout(
            vendor,
            requested_by=f"admin:{current_user.id}",
            method=payload.method,
            request=request,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

    # If Paystack is enabled AND method is Paystack, immediately attempt the transfer.
    if (
        settings.PAYSTACK_TRANSFER_ENABLED
        and payload.method == PayoutMethod.PAYSTACK_TRANSFER
        and vendor.payout_recipient_code
    ):
        try:
            resp = await paystack_client.initiate_transfer(
                amount_ghs=p.net_payout,
                recipient_code=vendor.payout_recipient_code,
                reason=f"KwiqBuy payout {p.id}",
                reference=f"PAYOUT-{p.id}",
            )
            data = resp.get("data", {})
            p = await payout_crud.mark_processing(
                p,
                paystack_transfer_code=data.get("transfer_code"),
                paystack_transfer_reference=data.get("reference"),
            )
        except PaystackError as e:
            # Leave the payout in REQUESTED so admin can retry
            raise HTTPException(
                502, f"Paystack transfer failed: {e.message}"
            )

    return _to_out(p)


@router.post("/{payout_id}/mark-paid", response_model=VendorPayoutOut)
async def mark_paid(
    payout_id: str,
    current_user: User = Depends(get_current_admin),
):
    p = await payout_crud.get_payout(payout_id)
    if not p:
        raise HTTPException(404, "Payout not found")
    p = await payout_crud.mark_paid(p)
    p.processed_by = str(current_user.id)
    await p.save()
    return _to_out(p)


@router.post("/{payout_id}/mark-failed", response_model=VendorPayoutOut)
async def mark_failed(
    payout_id: str,
    payload: VendorPayoutFailIn,
    _=Depends(get_current_admin),
):
    p = await payout_crud.get_payout(payout_id)
    if not p:
        raise HTTPException(404, "Payout not found")
    try:
        p = await payout_crud.mark_failed(p, payload.reason)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return _to_out(p)


@router.post("/{payout_id}/cancel", response_model=VendorPayoutOut)
async def cancel(
    payout_id: str,
    payload: VendorPayoutCancelIn,
    request: Request,
    current_user: User = Depends(get_current_admin),
):
    p = await payout_crud.get_payout(payout_id)
    if not p:
        raise HTTPException(404, "Payout not found")
    try:
        p = await payout_crud.cancel_payout(
            p,
            actor_id=str(current_user.id),
            reason=payload.reason,
            request=request,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    return _to_out(p)