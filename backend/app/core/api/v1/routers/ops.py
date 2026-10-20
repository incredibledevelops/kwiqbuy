"""
Operational endpoints:
  GET /health   — overall health (Mongo + Redis)
  GET /ready    — readiness — fails if any dependency is down
  GET /live     — liveness — always 200 unless the process is dead
  GET /metrics  — basic counters (JSON; not Prometheus, but enough for MVP)
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Response, status

from app.core.cache import cache
from app.core.config import settings
from app.core.database import mongodb

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Ops"])


async def _mongo_ok() -> tuple[bool, str]:
    if mongodb.client is None:
        return False, "mongo client not initialized"
    try:
        await mongodb.client.admin.command("ping")
        return True, "ok"
    except Exception as exc:
        return False, str(exc)


async def _redis_ok() -> tuple[bool, str]:
    if not cache.enabled:
        return False, "cache disabled or not connected"
    try:
        await cache._client.ping()  # noqa: SLF001
        return True, "ok"
    except Exception as exc:
        return False, str(exc)


@router.get("/health")
async def health():
    mongo_ok, mongo_msg = await _mongo_ok()
    redis_ok, redis_msg = await _redis_ok()

    body = {
        "status": "ok" if mongo_ok else "degraded",
        "mongo": {"ok": mongo_ok, "message": mongo_msg},
        "redis": {"ok": redis_ok, "message": redis_msg},
        "cache_enabled": cache.enabled,
        "env": settings.APP_ENV,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    code = status.HTTP_200_OK if mongo_ok else status.HTTP_503_SERVICE_UNAVAILABLE
    return Response(
        content=__import__("json").dumps(body),
        media_type="application/json",
        status_code=code,
    )


@router.get("/ready")
async def ready():
    """Strict: all critical dependencies must be healthy."""
    mongo_ok, mongo_msg = await _mongo_ok()
    redis_ok, redis_msg = await _redis_ok()
    ok = mongo_ok  # Redis is a soft dependency — we don't fail readiness if it's down
    return Response(
        content=__import__("json").dumps({
            "ready": ok,
            "mongo": {"ok": mongo_ok, "message": mongo_msg},
            "redis": {"ok": redis_ok, "message": redis_msg},
        }),
        media_type="application/json",
        status_code=status.HTTP_200_OK if ok else status.HTTP_503_SERVICE_UNAVAILABLE,
    )


@router.get("/live")
async def live():
    return {"alive": True, "ts": datetime.now(timezone.utc).isoformat()}


# Very simple in-process counters. Good enough for MVP; swap for Prometheus
# client when we instrument properly.
_counters: dict[str, int] = {}


def increment_counter(name: str, by: int = 1) -> None:
    _counters[name] = _counters.get(name, 0) + by


@router.get("/metrics")
async def metrics():
    return {
        "uptime_info": {
            "env": settings.APP_ENV,
            "version": "1.0.0",
        },
        "counters": _counters,
        "cache_enabled": cache.enabled,
    }
