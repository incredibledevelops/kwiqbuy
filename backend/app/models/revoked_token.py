"""
Revoked JWT registry.

Every issued access/refresh token carries a `jti` (unique JWT ID). When a
user logs out (or an admin force-revokes), we insert the `jti` here with
an `expire_at` matching the token's own expiry. The `get_current_user`
dependency checks this collection before accepting any token.

TTL index on `expire_at` — Mongo deletes docs automatically once the
underlying token would have expired anyway.
"""
from datetime import datetime, timezone

from beanie import Document, Indexed
from pydantic import Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


class RevokedToken(Document):
    jti: Indexed(str, unique=True)  # type: ignore
    reason: str = "logout"        # logout | admin_revoke | password_change | security
    subject: str                   # token subject (user id or phone)
    revoked_by: str = "self"       # "self" | admin user id
    revoked_at: datetime = Field(default_factory=_now)
    expire_at: datetime            # matches token's own exp claim

    class Settings:
        name = "revoked_tokens"
        indexes = [
            "jti",
            "expire_at",  # TTL — Mongo purges after token would have expired
        ]
