import pytest


@pytest.mark.asyncio
async def test_grouped_builder(client):
    resp = await client.get("/api/v1/builder/grouped")
    assert resp.status_code == 200
    data = resp.json()
    assert set(data.keys()) == {"bases", "proteins", "sauces", "toppings"}