import secrets
from datetime import datetime, timezone


def generate_order_reference() -> str:
    """Human-readable KwiqBuy order ref, e.g. KB-20261007-A4F9K2."""
    now = datetime.now(timezone.utc)
    suffix = secrets.token_hex(3).upper()
    return f"KB-{now.strftime('%Y%m%d')}-{suffix}"


def generate_payment_reference(order_reference: str) -> str:
    nonce = secrets.token_hex(4).upper()
    return f"{order_reference}-PAY-{nonce}"