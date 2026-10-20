"""
MongoDB client + Beanie init.

Adds:
- Replica-set detection so we know whether transactions are usable.
- A `@transactional` decorator that gracefully degrades to non-transactional
  operation in dev when the DB is a standalone `mongod`.

The decorator is designed for functions that accept a `session` kwarg
(optional). When transactions are unavailable it simply passes `None`.
"""
from __future__ import annotations

import functools
import inspect
import logging
from typing import Any, Awaitable, Callable, Optional, TypeVar

from beanie import init_beanie
from pymongo import AsyncMongoClient
from pymongo.asynchronous.client_session import AsyncClientSession
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import ConfigurationError, OperationFailure

from app.core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T")


class MongoDB:
    client: Optional[AsyncMongoClient] = None
    db: Optional[AsyncDatabase] = None
    supports_transactions: bool = False


mongodb = MongoDB()


async def _detect_transactions_support(client: AsyncMongoClient) -> bool:
    """
    A Mongo deployment supports transactions only if it's a replica set
    (or sharded cluster with a replica-set shard). We detect by asking the
    primary for `hello`/`isMaster` and checking for `setName`.
    """
    try:
        hello = await client.admin.command("hello")
    except (OperationFailure, ConfigurationError) as exc:
        logger.warning("Could not query Mongo hello: %s", exc)
        return False
    except Exception as exc:  # network etc.
        logger.warning("Mongo hello failed: %s", exc)
        return False

    has_set = bool(hello.get("setName"))
    # Atlas serverless / shared tiers sometimes hide setName but still
    # support transactions. We trust the flag if explicitly set.
    if has_set:
        logger.info("Mongo replica set detected: %s", hello.get("setName"))
    else:
        logger.info("Mongo standalone detected — transactions unavailable")
    return has_set


async def init_db(document_models: list) -> None:
    """Initialize MongoDB client and Beanie ODM."""
    mongodb.client = AsyncMongoClient(
        settings.MONGODB_URL,
        # Ensure writes propagate before returning when we're in a transaction
        # heavy workload. `majority` is safe for both standalone and RS.
        w="majority",
    )
    mongodb.db = mongodb.client[settings.MONGODB_DB_NAME]

    supports = await _detect_transactions_support(mongodb.client)
    mongodb.supports_transactions = supports

    if settings.MONGODB_TRANSACTIONS_ENABLED and not supports:
        if settings.APP_ENV == "production":
            raise RuntimeError(
                "MONGODB_TRANSACTIONS_ENABLED=True but the connected MongoDB "
                "is not a replica set. Refusing to start in production without "
                "transactional guarantees. Either enable a replica set or set "
                "MONGODB_TRANSACTIONS_ENABLED=False to acknowledge the risk."
            )
        logger.warning(
            "MONGODB_TRANSACTIONS_ENABLED=True but replica set not detected. "
            "Falling back to non-transactional operation. This is fine in dev "
            "but MUST NOT happen in production."
        )

    allow_drop = settings.APP_ENV != "production"

    await init_beanie(
        database=mongodb.db,
        document_models=document_models,
        allow_index_dropping=allow_drop,
    )


async def close_db() -> None:
    if mongodb.client:
        await mongodb.client.close()
        mongodb.client = None
        mongodb.db = None
        mongodb.supports_transactions = False


def get_database() -> AsyncDatabase:
    if mongodb.db is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return mongodb.db


def transactions_available() -> bool:
    return mongodb.supports_transactions and settings.MONGODB_TRANSACTIONS_ENABLED


def transactional(
    *,
    require: bool = False,
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """
    Wrap an async function so it runs inside a Mongo session / transaction.

    The wrapped function MUST accept a `session: AsyncClientSession | None`
    keyword argument (default None). The decorator will supply it.

    Usage:
        @transactional()
        async def create_order(payload, *, session=None):
            await SomeDoc(...).insert(session=session)
            ...

    If transactions are unavailable:
      - `require=False` (default): runs the function with `session=None`.
      - `require=True`: raises RuntimeError.
    """

    def decorator(fn: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        if not _accepts_session(fn):
            raise TypeError(
                f"{fn.__qualname__} must accept a keyword argument `session` "
                "to be wrapped with @transactional()"
            )

        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            available = transactions_available()

            if not available:
                if require:
                    raise RuntimeError(
                        f"{fn.__qualname__} requires transactions but they are "
                        "not available on this MongoDB deployment."
                    )
                # Graceful degrade — pass through with session=None.
                kwargs.setdefault("session", None)
                return await fn(*args, **kwargs)

            client = mongodb.client
            if client is None:
                raise RuntimeError("MongoDB client not initialized")

            async with await client.start_session() as session:
                async with session.start_transaction():
                    kwargs["session"] = session
                    return await fn(*args, **kwargs)

        return wrapper

    return decorator


def _accepts_session(fn: Callable) -> bool:
    try:
        sig = inspect.signature(fn)
    except (TypeError, ValueError):
        return False
    return "session" in sig.parameters