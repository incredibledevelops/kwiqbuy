import asyncio

from app.core.database import init_db, close_db
from app.models import (
    ALL_DOCUMENTS,
    User,
    Category,
    MenuItem,
    BuilderOption,
    DeliveryZone,
    Order,
    Payment,
)


async def main():
    await init_db(ALL_DOCUMENTS)
    print("users:          ", await User.find_all().count())
    print("categories:     ", await Category.find_all().count())
    print("menu_items:     ", await MenuItem.find_all().count())
    print("builder_options:", await BuilderOption.find_all().count())
    print("delivery_zones: ", await DeliveryZone.find_all().count())
    print("orders:         ", await Order.find_all().count())
    print("payments:       ", await Payment.find_all().count())
    await close_db()


if __name__ == "__main__":
    asyncio.run(main())