import pytest


@pytest.mark.asyncio
async def test_payment_initialize_no_order(client):
    resp = await client.post(
        "/api/v1/payments/initialize",
        json={"order_id": "000000000000000000000000", "email": "a@b.com"},
    )
    assert resp.status_code == 404