"""
Seed KwiqBuy: platform settings, food vendors, retail vendors,
categories, zones, promos.
"""
import asyncio

from app.core.database import close_db, init_db
from app.crud import category as category_crud
from app.crud import delivery_zone as zone_crud
from app.crud import platform_settings as ps_crud
from app.crud import product as product_crud
from app.crud import promo_code as promo_crud
from app.crud import user as user_crud
from app.crud import vendor as vendor_crud
from app.models import ALL_DOCUMENTS
from app.models.product import ProductType
from app.models.promo_code import DiscountType
from app.models.user import UserRole
from app.models.vendor import VendorCategory, VendorStatus

# Accra coords for demo
ACCRA_LEGON_LAT = 5.6355
ACCRA_LEGON_LNG = -0.1766
ACCRA_OSU_LAT = 5.5540
ACCRA_OSU_LNG = -0.1810

# Kumasi
KUMASI_LAT = 6.6885
KUMASI_LNG = -1.6244

FOOD_VENDORS = [
    {
        "business_name": "Ali's Kitchen",
        "slug": "alis-kitchen",
        "business_subtype": "restaurant",
        "description": "Loaded fries & wings since 2020.",
        "pickup_address": "Boundary Road, East Legon, Accra",
        "pickup_lat": ACCRA_LEGON_LAT,
        "pickup_lng": ACCRA_LEGON_LNG,
        "delivery_radius_km": 10.0,
        "prep_minutes": 20,
        "contact_phone": "0534634845",
        "owner_name": "Ali Mensah",
        "owner_email": "ali@kwiqbuy.com",
        "owner_password": "Vendor@1234",
        "products": [
            ("The Ali Special Bowl", 75.0, "Loaded fries with chicken and cheese", "loaded, signature"),
            ("Gourmet Loaded Bacon & Beef Fries", 85.0, "Beef strips, bacon, house mayo", "loaded, beef"),
            ("Sticky Wings (6pcs)", 60.0, "Sweet chili BBQ glaze", "wings"),
        ],
    },
    {
        "business_name": "Kumasi Bowl Co.",
        "slug": "kumasi-bowl-co",
        "business_subtype": "restaurant",
        "description": "Authentic Kumasi flavors.",
        "pickup_address": "Bomso Road, near KNUST, Kumasi",
        "pickup_lat": KUMASI_LAT,
        "pickup_lng": KUMASI_LNG,
        "delivery_radius_km": 8.0,
        "prep_minutes": 25,
        "contact_phone": "0534634846",
        "owner_name": "Ama Osei",
        "owner_email": "ama@kwiqbuy.com",
        "owner_password": "Vendor@1234",
        "products": [
            ("Fried Yam & Pepper Chicken", 55.0, "Golden yam with grilled chicken", "yam"),
            ("Peppered Gizzard Combo", 60.0, "Spicy gizzard over fries", "gizzard"),
        ],
    },
]

RETAIL_VENDORS = [
    {
        "business_name": "TechPoint Electronics",
        "slug": "techpoint-electronics",
        "business_subtype": "electronics",
        "description": "Phones, accessories and gadgets delivered nationwide.",
        "pickup_address": "Oxford Street, Osu, Accra",
        "pickup_lat": ACCRA_OSU_LAT,
        "pickup_lng": ACCRA_OSU_LNG,
        "prep_minutes": 120,  # 2 hours to pack
        "contact_phone": "0534634847",
        "owner_name": "Kofi Adjei",
        "owner_email": "kofi@kwiqbuy.com",
        "owner_password": "Vendor@1234",
        "products": [
            # Variable product — has variants
            {
                "name": "Wireless Earbuds Pro",
                "description": "Noise-cancelling, 30h battery",
                "price": 450.0,
                "product_type": ProductType.VARIABLE,
                "variant_options": [
                    {"name": "Color", "values": ["Black", "White", "Blue"]},
                ],
                "variants": [
                    {"sku": "EAR-BLK", "selections": {"Color": "Black"}, "price": 450.0, "stock_count": 12},
                    {"sku": "EAR-WHT", "selections": {"Color": "White"}, "price": 450.0, "stock_count": 8},
                    {"sku": "EAR-BLU", "selections": {"Color": "Blue"}, "price": 470.0, "stock_count": 5},
                ],
            },
            {
                "name": "USB-C Fast Charger",
                "description": "65W GaN, travel size",
                "price": 180.0,
                "product_type": ProductType.SIMPLE,
                "stock_count": 50,
            },
        ],
    },
    {
        "business_name": "Green Fork Grocery",
        "slug": "green-fork-grocery",
        "business_subtype": "grocery",
        "description": "Fresh produce and pantry staples.",
        "pickup_address": "Boundary Road, East Legon, Accra",
        "pickup_lat": ACCRA_LEGON_LAT,
        "pickup_lng": ACCRA_LEGON_LNG,
        "prep_minutes": 60,
        "contact_phone": "0534634848",
        "owner_name": "Yaa Asantewaa",
        "owner_email": "yaa@kwiqbuy.com",
        "owner_password": "Vendor@1234",
        "products": [
            {
                "name": "Organic Tomatoes (1kg)",
                "description": "Locally sourced, no pesticides",
                "price": 25.0,
                "product_type": ProductType.SIMPLE,
                "stock_count": 100,
            },
        ],
    },
]

CATEGORIES = [
    {"name": "Food & Drinks", "display_order": 1},
    {"name": "Electronics", "display_order": 2},
    {"name": "Groceries", "display_order": 3},
    {"name": "Fashion", "display_order": 4},
]

ZONES = [
    ("East Legon / Adjiringanor", 20.0, 40),
    ("UG Legon Campus", 15.0, 30),
    ("UPSA / Madina", 20.0, 40),
    ("Osu / Labone", 20.0, 40),
    ("KNUST Bomso", 15.0, 30),
]


async def seed_platform_settings():
    doc = await ps_crud.get_settings()
    print(f"OK Platform settings (commission {doc.commission_pct}%)")


async def seed_users():
    users = [
        ("KwiqBuy Admin", "admin@kwiqbuy.com", "Admin@1234", "0534634845", UserRole.ADMIN, None, None),
        ("Support Staff", "support@kwiqbuy.com", "Staff@1234", "0534634846", UserRole.STAFF, None, None),
        ("Kwame Rider", "rider@kwiqbuy.com", "Rider@1234", "0534634847", UserRole.RIDER, "Motorbike", "GT-1234-22"),
    ]
    for name, email, password, phone, role, vehicle, plate in users:
        if await user_crud.get_by_email(email):
            print(f"   skip {email}")
            continue
        await user_crud.create_user(
            full_name=name, email=email, password=password,
            phone=phone, role=role, vehicle=vehicle, plate_number=plate,
        )
        print(f"   OK {role.value}: {email}")


async def seed_categories():
    cat_map = {}
    for c in CATEGORIES:
        existing = await category_crud.get_by_slug(category_crud.slugify(c["name"]))
        cat_map[c["name"]] = existing or await category_crud.create_category(c)
    print(f"OK Categories ready: {len(cat_map)}")
    return cat_map


async def _create_owner(v):
    existing = await user_crud.get_by_email(v["owner_email"])
    if existing:
        print(f"   skip owner {v['owner_email']}")
        return existing
    owner = await user_crud.create_user(
        full_name=v["owner_name"],
        email=v["owner_email"],
        password=v["owner_password"],
        phone=v["contact_phone"],
        role=UserRole.VENDOR,
    )
    print(f"   OK vendor user: {v['owner_email']}")
    return owner


async def _create_vendor(v, category: VendorCategory):
    existing = await vendor_crud.get_by_slug(v["slug"])
    if existing:
        print(f"   skip vendor {v['business_name']}")
        return existing

    owner = await _create_owner(v)
    vendor = await vendor_crud.create_vendor(
        business_name=v["business_name"],
        business_category=category,
        business_subtype=v.get("business_subtype"),
        owner_user_id=str(owner.id),
        pickup_address=v["pickup_address"],
        description=v["description"],
        contact_phone=v["contact_phone"],
        pickup_lat=v.get("pickup_lat"),
        pickup_lng=v.get("pickup_lng"),
        delivery_radius_km=v.get("delivery_radius_km", 15.0),
        prep_minutes=v.get("prep_minutes", 20),
        status=VendorStatus.ACTIVE,
    )
    owner.vendor_id = vendor.id
    await owner.save()
    print(f"   OK vendor {v['business_name']} [{category.value}]")
    return vendor


async def _seed_products(vendor, products, cat_map):
    added = 0
    for p in products:
        if isinstance(p, tuple):
            # Legacy food tuple format
            name, price, desc, tags = p
            p = {
                "name": name,
                "description": desc,
                "price": price,
                "product_type": ProductType.SIMPLE,
                "tags": tags.split(", "),
                "stock_count": 50,
            }
        slug = product_crud.slugify(p["name"])
        if await product_crud.get_by_slug(slug):
            continue
        # Pick a sensible category
        if vendor.business_category == VendorCategory.FOOD:
            cat = cat_map.get("Food & Drinks")
        elif vendor.business_subtype == "electronics":
            cat = cat_map.get("Electronics")
        elif vendor.business_subtype == "grocery":
            cat = cat_map.get("Groceries")
        else:
            cat = next(iter(cat_map.values()))

        await product_crud.create_product(str(vendor.id), {
            **p,
            "slug": slug,
            "category_id": str(cat.id),
            "is_available": True,
        })
        added += 1
    print(f"      {added} products added")


async def seed_vendors(cat_map):
    for v in FOOD_VENDORS:
        vendor = await _create_vendor(v, VendorCategory.FOOD)
        await _seed_products(vendor, v["products"], cat_map)
    for v in RETAIL_VENDORS:
        vendor = await _create_vendor(v, VendorCategory.RETAIL)
        await _seed_products(vendor, v["products"], cat_map)


async def seed_zones():
    added = 0
    for name, fee, mins in ZONES:
        if await zone_crud.get_by_slug(zone_crud.slugify(name)):
            continue
        await zone_crud.create_zone({
            "name": name, "delivery_fee": fee,
            "estimated_minutes": mins, "is_active": True,
        })
        added += 1
    print(f"OK Zones added: {added}")


async def seed_promos():
    promos = [
        {"code": "WELCOME10", "description": "10% off your first order",
         "discount_type": DiscountType.PERCENT, "discount_value": 10.0,
         "min_order_total": 30.0, "max_discount": 20.0, "per_customer_limit": 1},
    ]
    added = 0
    for p in promos:
        if await promo_crud.get_by_code(p["code"]):
            continue
        await promo_crud.create_promo(p, created_by="seed")
        added += 1
    print(f"OK Promos added: {added}")


async def seed():
    await init_db(ALL_DOCUMENTS)
    print("Seeding KwiqBuy marketplace...")
    await seed_platform_settings()
    await seed_users()
    cat_map = await seed_categories()
    await seed_vendors(cat_map)
    await seed_zones()
    await seed_promos()
    await close_db()
    print("")
    print("Done!")
    print("")
    print("Login credentials:")
    print("  Admin:          admin@kwiqbuy.com / Admin@1234")
    print("  Food vendor:    ali@kwiqbuy.com / Vendor@1234")
    print("  Food vendor:    ama@kwiqbuy.com / Vendor@1234")
    print("  Retail vendor:  kofi@kwiqbuy.com / Vendor@1234")
    print("  Retail vendor:  yaa@kwiqbuy.com / Vendor@1234")
    print("  Rider:          rider@kwiqbuy.com / Rider@1234")


if __name__ == "__main__":
    asyncio.run(seed())
