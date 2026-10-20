from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.config import settings
from app.core.deps import get_current_admin, get_current_user
from app.core.limiter import limiter
from app.core.security import (
    create_access_token_with_meta,
    create_refresh_token_with_meta,
    decode_token,
    token_expiry_from_payload,
    verify_password,
)
from app.crud import audit as audit_crud
from app.crud import revoked_token as revoked_crud
from app.crud import user as user_crud
from app.crud import two_factor as tf_crud
from app.models.audit_log import ActorType
from app.models.user import User, UserRole
from app.schemas.two_factor import LoginTwoFARequired, TwoFALoginIn
from app.schemas.auth import (
    ChangePasswordIn,
    LoginRequest,
    LogoutRequest,
    PasswordReset,
    ProfileUpdateIn,
    RefreshRequest,
    TokenResponse,
    UserCreate,
    UserOut,
    UserUpdate,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


def _to_out(u: User) -> UserOut:
    return UserOut(
        id=str(u.id),
        full_name=u.full_name,
        email=u.email,
        phone=u.phone,
        role=u.role,
        is_active=u.is_active,
        vendor_id=str(u.vendor_id) if getattr(u, "vendor_id", None) else None,
        vehicle=getattr(u, "vehicle", None),
        plate_number=getattr(u, "plate_number", None),
        last_login_at=(
            u.last_login_at.isoformat() if getattr(u, "last_login_at", None) else None
        ),
        created_at=u.created_at.isoformat() if getattr(u, "created_at", None) else None,
    )


def _to_token_response(user: User) -> TokenResponse:
    access, _a_jti, _a_exp = create_access_token_with_meta(
        str(user.id),
        extra={
            "role": user.role.value,
            "email": user.email,
            "vendor_id": str(user.vendor_id) if user.vendor_id else None,
        },
    )
    refresh, _r_jti, _r_exp = create_refresh_token_with_meta(str(user.id))
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def login(request: Request, payload: LoginRequest):
    user = await user_crud.get_by_email(payload.email)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(401, "Invalid email or password")
    if not user.is_active:
        raise HTTPException(403, "Account disabled")

    # 2FA gate for admins who have it enabled
    if settings.TWO_FA_ENABLED and user.role == UserRole.ADMIN:
        if await tf_crud.is_enabled(str(user.id)):
            import jwt as _jwt
            from datetime import datetime as _dt, timezone as _tz
            now = _dt.now(_tz.utc)
            payload_2fa = {
                "sub": str(user.id),
                "type": "2fa_pending",
                "iat": int(now.timestamp()),
                "exp": int((now + timedelta(minutes=settings.TWO_FA_TEMP_TOKEN_EXPIRE_MINUTES)).timestamp()),
            }
            temp = _jwt.encode(payload_2fa, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
            return LoginTwoFARequired(needs_2fa=True, temp_token=temp).model_dump()

    user.last_login_at = datetime.now(timezone.utc)
    await user.save()

    return _to_token_response(user)




@router.post("/login/2fa", response_model=TokenResponse)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def login_2fa(request: Request, payload: TwoFALoginIn):
    try:
        decoded = decode_token(payload.temp_token)
    except ValueError:
        raise HTTPException(401, "Invalid or expired temp token")
    if decoded.get("type") != "2fa_pending":
        raise HTTPException(401, "Invalid token type")

    user = await user_crud.get_by_id(decoded.get("sub"))
    if not user or not user.is_active:
        raise HTTPException(401, "User not found")

    if not await tf_crud.verify_code(str(user.id), payload.code):
        raise HTTPException(401, "Invalid or expired 2FA code")

    user.last_login_at = datetime.now(timezone.utc)
    await user.save()
    return _to_token_response(user)

@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest):
    try:
        decoded = decode_token(payload.refresh_token)
    except ValueError:
        raise HTTPException(401, "Invalid refresh token")
    if decoded.get("type") != "refresh":
        raise HTTPException(401, "Invalid token type")

    jti = decoded.get("jti")
    if jti and await revoked_crud.is_revoked(jti):
        raise HTTPException(401, "Refresh token has been revoked")

    user = await user_crud.get_by_id(decoded.get("sub"))
    if not user or not user.is_active:
        raise HTTPException(401, "User not found")
    return _to_token_response(user)


@router.post("/logout")
async def logout(payload: LogoutRequest, current_user: User = Depends(get_current_user)):
    """
    Revoke the access token (and optionally the refresh token).
    Both are added to the revoked_tokens collection with their own expiry.
    """
    revoked_count = 0

    try:
        access_payload = decode_token(payload.access_token)
        access_jti = access_payload.get("jti")
        if access_jti:
            await revoked_crud.revoke(
                jti=access_jti,
                subject=str(current_user.id),
                expire_at=token_expiry_from_payload(access_payload),
                reason="logout",
                revoked_by="self",
            )
            revoked_count += 1
    except ValueError:
        pass

    if payload.refresh_token:
        try:
            refresh_payload = decode_token(payload.refresh_token)
            refresh_jti = refresh_payload.get("jti")
            if refresh_jti:
                await revoked_crud.revoke(
                    jti=refresh_jti,
                    subject=str(current_user.id),
                    expire_at=token_expiry_from_payload(refresh_payload),
                    reason="logout",
                    revoked_by="self",
                )
                revoked_count += 1
        except ValueError:
            pass

    return {"revoked": revoked_count, "message": "Logged out."}


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return _to_out(current_user)


@router.patch("/me", response_model=UserOut)
async def update_my_profile(
    payload: ProfileUpdateIn,
    current_user: User = Depends(get_current_user),
):
    user = await user_crud.update_profile(
        current_user, payload.full_name, payload.phone
    )
    return _to_out(user)


@router.post("/me/change-password")
async def change_my_password(
    payload: ChangePasswordIn,
    current_user: User = Depends(get_current_user),
):
    ok, msg = await user_crud.change_password(
        current_user, payload.current_password, payload.new_password
    )
    if not ok:
        raise HTTPException(400, msg)
    return {"message": "Password changed successfully"}


# ---------- Admin: user management ----------

@router.get(
    "/users",
    response_model=list[UserOut],
    dependencies=[Depends(get_current_admin)],
)
async def list_users(
    role: UserRole | None = None,
    vendor_id: str | None = None,
    search: str | None = None,
):
    users = await user_crud.list_users(role=role, vendor_id=vendor_id, search=search)
    return [_to_out(u) for u in users]


@router.post(
    "/users",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_admin)],
)
async def create_user(
    payload: UserCreate,
    request: Request,
    current_user: User = Depends(get_current_admin),
):
    existing = await user_crud.get_by_email(payload.email)
    if existing:
        raise HTTPException(409, "Email already registered")
    user = await user_crud.create_user(
        full_name=payload.full_name,
        email=payload.email,
        password=payload.password,
        phone=payload.phone,
        role=payload.role,
        vendor_id=payload.vendor_id,
        vehicle=payload.vehicle,
        plate_number=payload.plate_number,
    )
    await audit_crud.log(
        action="user.created",
        actor_type=ActorType.USER,
        actor_id=str(current_user.id),
        actor_email=current_user.email,
        target_type="User",
        target_id=str(user.id),
        after={"email": user.email, "role": user.role.value},
        request=request,
    )
    return _to_out(user)


@router.get(
    "/users/{user_id}",
    response_model=UserOut,
    dependencies=[Depends(get_current_admin)],
)
async def get_user(user_id: str):
    user = await user_crud.get_by_id(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return _to_out(user)


@router.patch(
    "/users/{user_id}",
    response_model=UserOut,
    dependencies=[Depends(get_current_admin)],
)
async def update_user(
    user_id: str,
    payload: UserUpdate,
    request: Request,
    current_user: User = Depends(get_current_admin),
):
    user = await user_crud.get_by_id(user_id)
    if not user:
        raise HTTPException(404, "User not found")

    if user.id == current_user.id and payload.role and payload.role != user.role:
        raise HTTPException(400, "You cannot change your own role")
    if user.id == current_user.id and payload.is_active is False:
        raise HTTPException(400, "You cannot deactivate yourself")

    before = {"role": user.role.value, "is_active": user.is_active}
    user = await user_crud.update_user(user, payload.model_dump(exclude_unset=True))
    await audit_crud.log(
        action="user.updated",
        actor_type=ActorType.USER,
        actor_id=str(current_user.id),
        actor_email=current_user.email,
        target_type="User",
        target_id=str(user.id),
        before=before,
        after={"role": user.role.value, "is_active": user.is_active},
        request=request,
    )
    return _to_out(user)


@router.post(
    "/users/{user_id}/reset-password",
    dependencies=[Depends(get_current_admin)],
)
async def reset_password(
    user_id: str,
    payload: PasswordReset,
    request: Request,
    current_user: User = Depends(get_current_admin),
):
    user = await user_crud.get_by_id(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    await user_crud.reset_password(user, payload.new_password)
    await audit_crud.log(
        action="user.password_reset",
        actor_type=ActorType.USER,
        actor_id=str(current_user.id),
        actor_email=current_user.email,
        target_type="User",
        target_id=str(user.id),
        request=request,
    )
    return {"message": "Password reset successfully"}


@router.post(
    "/users/{user_id}/revoke-sessions",
    dependencies=[Depends(get_current_admin)],
)
async def admin_revoke_sessions(
    user_id: str,
    request: Request,
    current_user: User = Depends(get_current_admin),
):
    """
    Admin force-revoke: we can't retroactively revoke tokens we haven't
    seen, but we can reject any token presented after this call by using
    a per-user `tokens_valid_after` cutoff (added in Phase 2). For now we
    just audit the action so there's a paper trail.
    """
    user = await user_crud.get_by_id(user_id)
    if not user:
        raise HTTPException(404, "User not found")

    await audit_crud.log(
        action="user.sessions_revoked",
        actor_type=ActorType.USER,
        actor_id=str(current_user.id),
        actor_email=current_user.email,
        target_type="User",
        target_id=user_id,
        request=request,
    )
    return {"message": "Session revocation recorded."}


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user(
    user_id: str,
    request: Request,
    current_user: User = Depends(get_current_admin),
):
    if user_id == str(current_user.id):
        raise HTTPException(400, "You cannot delete yourself")
    user = await user_crud.get_by_id(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    await user_crud.delete_user(user)
    await audit_crud.log(
        action="user.deleted",
        actor_type=ActorType.USER,
        actor_id=str(current_user.id),
        actor_email=current_user.email,
        target_type="User",
        target_id=user_id,
        request=request,
    )
