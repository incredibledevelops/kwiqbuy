import hashlib
import logging
from datetime import datetime, timezone

from app.crud import order as order_crud
from app.crud import wallet as wallet_crud
from app.models.customer import Customer

logger = logging.getLogger(__name__)


def _hash_phone(phone: str) -> str:
    return hashlib.sha256(phone.encode("utf-8")).hexdigest()[:24]


async def export_customer(customer: Customer) -> dict:
    orders = await order_crud.list_by_customer(customer.phone, limit=1000)
    wallet_txs = await wallet_crud.list_transactions(phone=customer.phone, limit=1000)

    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "profile": {
            "id": str(customer.id),
            "phone": customer.phone,
            "email": customer.email,
            "full_name": customer.full_name,
            "loyalty_points": customer.loyalty_points,
            "lifetime_points_earned": customer.lifetime_points_earned,
            "lifetime_points_redeemed": customer.lifetime_points_redeemed,
            "wallet_balance": customer.wallet_balance,
            "lifetime_wallet_credited": customer.lifetime_wallet_credited,
            "lifetime_wallet_spent": customer.lifetime_wallet_spent,
            "total_orders": customer.total_orders,
            "total_spent": customer.total_spent,
            "referral_code": customer.referral_code,
            "created_at": customer.created_at.isoformat() if customer.created_at else None,
            "saved_addresses": [
                {"label": a.label, "zone_name": a.zone_name, "address": a.address, "is_default": a.is_default}
                for a in (customer.saved_addresses or [])
            ],
        },
        "orders": [
            {
                "reference": o.reference,
                "status": o.status.value,
                "total": o.total,
                "subtotal": o.subtotal,
                "delivery_fee": o.delivery_fee,
                "wallet_applied": o.wallet_applied,
                "promo_code": o.promo_code,
                "delivery_address": o.delivery_address,
                "delivery_zone_name": o.delivery_zone_name,
                "created_at": o.created_at.isoformat(),
                "items": [
                    {"vendor": vo.vendor_name, "name": i.name, "quantity": i.quantity, "unit_price": i.unit_price}
                    for vo in o.vendor_orders for i in vo.items
                ],
            }
            for o in orders
        ],
        "wallet_transactions": [
            {
                "amount": t.amount,
                "balance_after": t.balance_after,
                "reason": t.reason.value,
                "order_reference": t.order_reference,
                "note": t.note,
                "created_at": t.created_at.isoformat(),
            }
            for t in wallet_txs
        ],
    }


async def soft_delete_customer(customer: Customer) -> dict:
    original_phone = customer.phone
    hashed = _hash_phone(original_phone)

    customer.phone = f"deleted_{hashed}"
    customer.full_name = "Deleted User"
    customer.email = None
    customer.saved_addresses = []
    customer.favorite_item_ids = []
    customer.referral_code = None
    customer.loyalty_points = 0
    customer.wallet_balance = 0.0
    customer.updated_at = datetime.now(timezone.utc)
    await customer.save()

    logger.info("Customer soft-deleted: %s -> %s", hashed, customer.id)
    return {
        "deleted": True,
        "hashed_reference": hashed,
        "message": "Your account has been deleted. Order history has been retained for legal and accounting purposes.",
    }
