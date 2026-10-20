"""
Vendor bulk endpoints: CSV product import + bulk product ops.
"""
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from app.core.config import settings
from app.core.deps import get_current_vendor
from app.core.limiter import limiter
from app.crud import bulk as bulk_crud
from app.crud import vendor as vendor_crud
from app.models.user import User
from app.schemas.bulk import (
    BulkProductAvailabilityIn,
    BulkProductDeleteIn,
    BulkResultOut,
)

router = APIRouter(prefix="/vendor/bulk", tags=["Vendor Bulk Ops"])


async def _load_vendor(user: User):
    v = await vendor_crud.get_by_id(str(user.vendor_id))
    if not v:
        raise HTTPException(404, "Vendor not found")
    return v


@router.post("/products/import-csv", response_model=BulkResultOut)
@limiter.limit(settings.RATE_LIMIT_BULK)
async def import_csv(
    request: Request,
    file: UploadFile = File(...),
    user: User = Depends(get_current_vendor),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "File must be a .csv")

    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(400, "CSV too large (max 5MB)")

    vendor = await _load_vendor(user)
    try:
        result = await bulk_crud.import_products_csv(
            vendor, contents, max_rows=settings.MAX_CSV_IMPORT_ROWS
        )
    except bulk_crud.BulkError as e:
        raise HTTPException(400, str(e))

    return BulkResultOut(
        created=result["created"],
        skipped=result["skipped"],
        errors=result["errors"],
    )


@router.post("/products/set-availability", response_model=BulkResultOut)
async def bulk_set_availability(
    payload: BulkProductAvailabilityIn,
    user: User = Depends(get_current_vendor),
):
    result = await bulk_crud.bulk_set_product_availability(
        str(user.vendor_id), payload.product_ids, payload.is_available
    )
    return BulkResultOut(updated=result["updated"], errors=result["errors"])


@router.post("/products/delete", response_model=BulkResultOut)
async def bulk_delete(
    payload: BulkProductDeleteIn,
    user: User = Depends(get_current_vendor),
):
    result = await bulk_crud.bulk_delete_products(
        str(user.vendor_id), payload.product_ids
    )
    return BulkResultOut(deleted=result["deleted"], errors=result["errors"])
