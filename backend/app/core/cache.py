"""
Thin async cache wrapper around Redis.

Usage:
    from app.core.cache import cache, cached, invalidate

    await cache.set("key", {...}, ttl=60)
    value = await cache.get("key")

    # Simple helper for cache-or-compute
    data = await cache.get_or_set(
        "menu:all",
        lambda: _fetch_menu(),
        ttl=60,
    )
"""
import json
import logging
from typing import Any, Awaitable, Callable, Optional

import redis.asyncio as redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class Cache:
    def __init__(self):
        self._client: Optional[redis.Redis] = None
        self._enabled = False

    async def init(self) -> None:
        """Connect to Redis. If it fails, caching is disabled but the app runs."""
        if not settings.REDIS_URL:
            logger.info("Cache disabled — no REDIS_URL configured")
            return
        try:
            self._client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=3,
            )
            await self._client.ping()
            self._enabled = True
            logger.info("Cache connected: %s", settings.REDIS_URL)
        except Exception as exc:
            logger.warning("Cache unavailable (%s) — running without cache", exc)
            self._client = None
            self._enabled = False

    async def close(self) -> None:
        if self._client:
            try:
                await self._client.close()
            except Exception:
                pass

    @property
    def enabled(self) -> bool:
        return self._enabled and self._client is not None

    async def get(self, key: str) -> Optional[Any]:
        if not self.enabled:
            return None
        try:
            raw = await self._client.get(key)
            if raw is None:
                return None
            return json.loads(raw)
        except Exception as exc:
            logger.debug("cache get failed for %s: %s", key, exc)
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        if not self.enabled:
            return
        try:
            payload = json.dumps(value, default=str)
            await self._client.set(
                key, payload, ex=ttl or settings.CACHE_TTL_SECONDS
            )
        except Exception as exc:
            logger.debug("cache set failed for %s: %s", key, exc)

    async def delete(self, key: str) -> None:
        if not self.enabled:
            return
        try:
            await self._client.delete(key)
        except Exception:
            pass

    async def delete_prefix(self, prefix: str) -> int:
        if not self.enabled:
            return 0
        try:
            count = 0
            async for key in self._client.scan_iter(match=f"{prefix}*"):
                await self._client.delete(key)
                count += 1
            return count
        except Exception:
            return 0

    async def get_or_set(
        self,
        key: str,
        factory: Callable[[], Awaitable[Any]],
        ttl: Optional[int] = None,
    ) -> Any:
        """Return cached value, or compute + cache it."""
        cached = await self.get(key)
        if cached is not None:
            return cached
        fresh = await factory()
        await self.set(key, fresh, ttl=ttl)
        return fresh


cache = Cache()


# Convenience helpers

async def invalidate_menu() -> None:
    await cache.delete_prefix("menu:")
    await cache.delete_prefix("categories:")
    await cache.delete_prefix("search:")


async def invalidate_zones() -> None:
    await cache.delete_prefix("zones:")


async def invalidate_branches() -> None:
    await cache.delete_prefix("branches:")