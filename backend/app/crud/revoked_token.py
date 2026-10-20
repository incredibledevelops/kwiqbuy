from datetime import datetime, timezone

from app.models.revoked_token import RevokedToken


async def revoke(
    *,
    jti: str,
    subject: str,
    expire_at: datetime,
    reason: str = "logout",
    revoked_by: str = "self",
) -> RevokedToken:
    existing = await RevokedToken.find_one(RevokedToken.jti == jti)
    if existing:
        return existing
    doc = RevokedToken(
        jti=jti,
        subject=subject,
        expire_at=expire_at,
        reason=reason,
        revoked_by=revoked_by,
    )
    await doc.insert()
    return doc


async def is_revoked(jti: str) -> bool:
    return bool(await RevokedToken.find_one(RevokedToken.jti == jti))


async def revoke_all_for_subject(subject: str, reason: str = "security") -> int:
    """
    Not a real "revoke all sessions" — we don't track issued tokens.
    Instead, this revokes any *currently known* revoked tokens for the
    subject that are still within their lifetime. Real bulk revocation
    needs a `User.token_version` field that bumps and gets embedded in
    every token, which we'll add when the need arises.
    """
    now = datetime.now(timezone.utc)
    result = await RevokedToken.find(
        RevokedToken.subject == subject,
        RevokedToken.expire_at > now,
    ).update({"$set": {"reason": reason}})
    return int(getattr(result, "modified_count", 0) or 0)


async def purge_expired() -> int:
    now = datetime.now(timezone.utc)
    result = await RevokedToken.find(RevokedToken.expire_at < now).delete()
    return int(getattr(result, "deleted_count", 0) or 0)
