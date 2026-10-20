import base64
import io

import qrcode
from fastapi import APIRouter, Depends, HTTPException

from app.core.config import settings
from app.core.deps import get_current_admin
from app.core.security import verify_password
from app.crud import two_factor as tf_crud
from app.models.user import User
from app.schemas.two_factor import (
    TwoFADisableIn, TwoFASetupOut, TwoFAStatusOut,
    TwoFAVerifyIn, TwoFAVerifyOut,
)

router = APIRouter(prefix="/admin/2fa", tags=["Admin 2FA"])


def _qr_data_url(uri: str) -> str:
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


@router.get("/status", response_model=TwoFAStatusOut)
async def status(current: User = Depends(get_current_admin)):
    doc = await tf_crud.get_for_user(str(current.id))
    if not doc:
        return TwoFAStatusOut(enabled=False)
    return TwoFAStatusOut(
        enabled=doc.enabled,
        verified_at=doc.verified_at.isoformat() if doc.verified_at else None,
        recovery_codes_remaining=len(doc.recovery_codes or []),
    )


@router.post("/setup", response_model=TwoFASetupOut)
async def setup(current: User = Depends(get_current_admin)):
    if not settings.TWO_FA_ENABLED:
        raise HTTPException(400, "2FA is disabled on this server")
    doc, secret, uri = await tf_crud.start_setup(
        str(current.id), current.email, settings.TWO_FA_ISSUER,
    )
    return TwoFASetupOut(secret=secret, provisioning_uri=uri, qr_data_url=_qr_data_url(uri))


@router.post("/verify", response_model=TwoFAVerifyOut)
async def verify(payload: TwoFAVerifyIn, current: User = Depends(get_current_admin)):
    ok, msg, codes = await tf_crud.verify_and_enable(str(current.id), payload.code)
    if not ok:
        raise HTTPException(400, msg)
    return TwoFAVerifyOut(enabled=True, message=msg, recovery_codes=codes)


@router.post("/disable")
async def disable(payload: TwoFADisableIn, current: User = Depends(get_current_admin)):
    if not verify_password(payload.password, current.hashed_password):
        raise HTTPException(400, "Password is incorrect")
    if await tf_crud.is_enabled(str(current.id)):
        if not payload.code or not await tf_crud.verify_code(str(current.id), payload.code):
            raise HTTPException(400, "Valid 2FA code required to disable")
    await tf_crud.disable(str(current.id))
    return {"message": "2FA disabled"}
