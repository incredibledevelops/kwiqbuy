import pytest


@pytest.mark.asyncio
async def test_order_creation_invalid_zone(client):
    payload = {
        "customer": {
            "full_name": "Test User",
            "email": "test@example.com",
            "phone": "0240000000",
        },
        "delivery_zone_id": "000000000000000000000000",
        "delivery_address": "Some address",
        "items": [
            {
                "item_id": "000000000000000000000000",
                "name": "Fake",
                "unit_price": 10,
                "quantity": 1,
                "is_custom_bowl": False,
            }
        ],
    }
    resp = await client.post("/api/v1/orders", json=payload)
    assert resp.status_code == 400