import pytest


@pytest.mark.asyncio
async def test_list_menu_empty(client):
    resp = await client.get("/api/v1/menu")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_create_category_requires_auth(client):
    resp = await client.post(
        "/api/v1/categories",
        json={"name": "Test Category", "description": "desc"},
    )
    assert resp.status_code == 401