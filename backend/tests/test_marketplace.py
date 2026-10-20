"""
Integration tests for the KwiqBuy marketplace.

Runs against the test DB created by conftest.py. Uses FastAPI's
httpx ASGITransport — no real server needed.

Skip if Mongo isn't running.
"""
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.security import hash_password
from app.models.category import Category
from app.models.platform_settings import PlatformSettings
from app.models.product import ProductType
from app.models.user import User, UserRole
from app.models.vendor import Vendor, VendorCategory, VendorStatus


async def _seed_minimal():
    """Create one food vendor, one retail vendor, one of each product."""
    cat = await Category(
        name="Test Cat", slug="test-cat", description=None, display_order=0
    ).insert()

    plat = PlatformSettings(key="global")
    await plat.insert()

    food_user = await User(
        full_name="Food Vendor",
        email="foodtest@kwiqbuy.com",
        hashed_password=hash_password("Vendor@1234"),
        role=UserRole.VENDOR,
        is_active=True,
    ).insert()
    food_vendor = await Vendor(
        business_name="Food Test",
        slug="food-test",
        business_category=VendorCategory.FOOD,
        owner_user_id=food_user.id,
        pickup_address="Test address 1",
        pickup_lat=5.6355,
        pickup_lng=-0.1766,
        status=VendorStatus.ACTIVE,
        pickup_location={"type": "Point", "coordinates": [-0.1766, 5.6355]},
    ).insert()
    food_user.vendor_id = food_vendor.id
    await food_user.save()

    retail_user = await User(
        full_name="Retail Vendor",
        email="retailtest@kwiqbuy.com",
        hashed_password=hash_password("Vendor@1234"),
        role=UserRole.VENDOR,
        is_active=True,
    ).insert()
    retail_vendor = await Vendor(
        business_name="Retail Test",
        slug="retail-test",
        business_category=VendorCategory.RETAIL,
        owner_user_id=retail_user.id,
        pickup_address="Test address 2",
        status=VendorStatus.ACTIVE,
    ).insert()
    retail_user.vendor_id = retail_vendor.id
    await retail_user.save()

    food_product = await Product(
        vendor_id=food_vendor.id,
        name="Test Burger",
        slug="test-burger",
        price=50.0,
        category_id=cat.id,
        product_type=ProductType.SIMPLE,
        stock_count=10,
        is_available=True,
    ).insert()

    retail_product = await Product(
        vendor_id=retail_vendor.id,
        name="Test Earbuds",
        slug="test-earbuds",
        price=200.0,
        category_id=cat.id,
        product_type=ProductType.SIMPLE,
        stock_count=5,
        is_available=True,
    ).insert()

    return {
        "category": cat,
        "food_vendor": food_vendor,
        "retail_vendor": retail_vendor,
        "food_product": food_product,
        "retail_product": retail_product,
        "food_user": food_user,
        "retail_user": retail_user,
    }


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_public_config(client):
    await PlatformSettings(key="global").insert()
    resp = await client.get("/api/v1/config/public")
    assert resp.status_code == 200
    data = resp.json()
    assert "commission_pct" in data
    assert data["currency"] == "GHS"


@pytest.mark.asyncio
async def test_vendors_public_list(client):
    await _seed_minimal()
    resp = await client.get("/api/v1/vendors/public")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    names = {v["business_name"] for v in data}
    assert names == {"Food Test", "Retail Test"}


@pytest.mark.asyncio
async def test_vendors_nearby_geo(client):
    """Only the food vendor near Accra should appear for Accra coords."""
    await _seed_minimal()
    # Accra coords, 10km radius — should hit the food vendor only
    resp = await client.get(
        "/api/v1/vendors/nearby?lat=5.6355&lng=-0.1766&radius_km=10"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["radius_km"] == 10
    vendor_names = [v["business_name"] for v in data["vendors"]]
    assert "Food Test" in vendor_names
    assert "Retail Test" not in vendor_names  # retail isn't in /nearby


@pytest.mark.asyncio
async def test_products_category_filter(client):
    await _seed_minimal()
    resp = await client.get("/api/v1/products?vendor_category=food")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test Burger"

    resp = await client.get("/api/v1/products?vendor_category=retail")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test Earbuds"


@pytest.mark.asyncio
async def test_cart_validate_single_category(client):
    s = await _seed_minimal()
    resp = await client.post(
        "/api/v1/cart/validate",
        json={"product_ids": [str(s["food_product"].id)]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is True
    assert data["order_type"] == "food"


@pytest.mark.asyncio
async def test_cart_validate_mixed_rejected(client):
    s = await _seed_minimal()
    resp = await client.post(
        "/api/v1/cart/validate",
        json={
            "product_ids": [
                str(s["food_product"].id),
                str(s["retail_product"].id),
            ]
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is False
    assert data["order_type"] == "mixed"


@pytest.mark.asyncio
async def test_order_create_single_vendor(client):
    s = await _seed_minimal()
    resp = await client.post(
        "/api/v1/orders",
        json={
            "customer": {
                "full_name": "Test User",
                "email": "test@example.com",
                "phone": "0240000000",
            },
            "delivery_zone_id": None,
            "delivery_address": "Some test address",
            "items": [
                {
                    "product_id": str(s["food_product"].id),
                    "name": "Test Burger",
                    "unit_price": 50.0,
                    "quantity": 2,
                    "is_custom_bowl": False,
                }
            ],
        },
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["order_type"] == "food"
    assert data["subtotal"] == 100.0
    assert len(data["vendor_orders"]) == 1


@pytest.mark.asyncio
async def test_order_create_mixed_rejected(client):
    s = await _seed_minimal()
    resp = await client.post(
        "/api/v1/orders",
        json={
            "customer": {
                "full_name": "Test User",
                "email": "test@example.com",
                "phone": "0240000001",
            },
            "delivery_zone_id": None,
            "delivery_address": "Some test address",
            "items": [
                {
                    "product_id": str(s["food_product"].id),
                    "name": "Test Burger",
                    "unit_price": 50.0,
                    "quantity": 1,
                    "is_custom_bowl": False,
                },
                {
                    "product_id": str(s["retail_product"].id),
                    "name": "Test Earbuds",
                    "unit_price": 200.0,
                    "quantity": 1,
                    "is_custom_bowl": False,
                },
            ],
        },
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_stock_decremented_on_order(client):
    s = await _seed_minimal()
    before = await Product.get(s["food_product"].id)
    assert before.stock_count == 10

    resp = await client.post(
        "/api/v1/orders",
        json={
            "customer": {
                "full_name": "Test User",
                "email": "test@example.com",
                "phone": "0240000002",
            },
            "delivery_zone_id": None,
            "delivery_address": "Some test address",
            "items": [
                {
                    "product_id": str(s["food_product"].id),
                    "name": "Test Burger",
                    "unit_price": 50.0,
                    "quantity": 3,
                    "is_custom_bowl": False,
                }
            ],
        },
    )
    assert resp.status_code == 201

    after = await Product.get(s["food_product"].id)
    assert after.stock_count == 7


@pytest.mark.asyncio
async def test_order_insufficient_stock(client):
    s = await _seed_minimal()
    # Only 5 in stock for retail
    resp = await client.post(
        "/api/v1/orders",
        json={
            "customer": {
                "full_name": "Test User",
                "email": "test@example.com",
                "phone": "0240000003",
            },
            "delivery_zone_id": None,
            "delivery_address": "Test address",
            "items": [
                {
                    "product_id": str(s["retail_product"].id),
                    "name": "Test Earbuds",
                    "unit_price": 200.0,
                    "quantity": 10,
                    "is_custom_bowl": False,
                }
            ],
        },
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_auth_login_admin(client):
    user = await User(
        full_name="Admin",
        email="admin@test.com",
        hashed_password=hash_password("Admin@1234"),
        role=UserRole.ADMIN,
        is_active=True,
    ).insert()
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.com", "password": "Admin@1234"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
