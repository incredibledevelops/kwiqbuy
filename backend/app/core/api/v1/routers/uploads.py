from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from app.core.deps import (
    get_current_admin,
    get_current_customer,
    get_current_vendor,
)
from app.models.customer import Customer
from app.models.user import User
from app.schemas.upload import UploadOut
from app.utils.file_storage import save_upload

router = APIRouter(prefix="/uploads", tags=["Uploads"])


@router.post(
    "",
    response_model=UploadOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_admin)],
)
async def upload_image(
    file: UploadFile = File(...),
    subdir: str = Form("products"),
):
    result = await save_upload(file, subdir=subdir)
    return UploadOut(**result)


@router.post(
    "/vendor",
    response_model=UploadOut,
    status_code=status.HTTP_201_CREATED,
)
async def upload_vendor_image(
    file: UploadFile = File(...),
    subdir: str = Form("products"),
    current: User = Depends(get_current_vendor),
):
    # Vendors may only write to product images or their own branding.
    if subdir not in ("products", "vendors"):
        subdir = "products"
    result = await save_upload(file, subdir=subdir)
    return UploadOut(**result)


@router.post(
    "/customer",
    response_model=UploadOut,
    status_code=status.HTTP_201_CREATED,
)
async def upload_customer_image(
    file: UploadFile = File(...),
    current: Customer = Depends(get_current_customer),
):
    result = await save_upload(file, subdir="reviews")
    return UploadOut(**result)


@router.post(
    "/vendor-application",
    response_model=UploadOut,
    status_code=status.HTTP_201_CREATED,
)
async def upload_vendor_application_document(
    file: UploadFile = File(...),
    current: None = None,
):
    result = await save_upload(file, subdir="vendor_applications")
    return UploadOut(**result)