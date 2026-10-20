import asyncio
import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from beanie import init_beanie
from httpx import ASGITransport, AsyncClient
from pymongo import AsyncMongoClient

from app.core.config import settings
from app.models import ALL_DOCUMENTS

TEST_DB_NAME = "kwiqbuy_test"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _init_test_db():
    url = os.getenv("TEST_MONGODB_URL", settings.MONGODB_URL)
    client = AsyncMongoClient(url)
    db = client[TEST_DB_NAME]
    await init_beanie(database=db, document_models=ALL_DOCUMENTS)

    from app.core import database as db_module
    db_module.mongodb.client = client
    db_module.mongodb.db = db
    db_module.mongodb.supports_transactions = False

    yield

    await client.drop_database(TEST_DB_NAME)
    await client.close()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(autouse=True)
async def _clean_db():
    """Wipe collections between tests so they don't bleed into each other."""
    yield
    for doc in ALL_DOCUMENTS:
        try:
            await doc.find_all().delete()
        except Exception:
            pass
