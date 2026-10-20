"""Arkesel SMS helper. Falls back to console logging when API key missing."""
import logging
import re
from typing import List

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class InvalidPhone(ValueError):
    pass


def _normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", str(phone or ""))
    if not digits:
        raise InvalidPhone("empty phone number")
    if digits.startswith("233") and len(digits) == 12:
        return digits
    if digits.startswith("0") and len(digits) == 10:
        return "233" + digits[1:]
    if len(digits) == 9:
        return "233" + digits
    raise InvalidPhone(f"unrecognized phone number format: {phone!r}")


async def send_sms(to: str, message: str) -> bool:
    try:
        recipient = _normalize_phone(to)
    except InvalidPhone as e:
        logger.warning("Skipping SMS — bad phone %r (%s)", to, e)
        return False

    if not settings.ARKESEL_API_KEY:
        logger.info("[SMS SKIPPED] to=%s msg=%s", recipient, message)
        return False

    url = f"{settings.ARKESEL_BASE_URL.rstrip('/')}/sms/send"
    payload = {
        "sender": settings.ARKESEL_SENDER_ID,
        "message": message,
        "recipients": [recipient],
    }
    headers = {"api-key": settings.ARKESEL_API_KEY, "Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.post(url, json=payload, headers=headers)
        if res.status_code >= 400:
            logger.error("Arkesel SMS failed (%s): %s", res.status_code, res.text)
            return False
        logger.info("[SMS SENT] to=%s", recipient)
        return True
    except Exception as exc:
        logger.exception("Arkesel SMS request error: %s", exc)
        return False


async def send_sms_bulk(recipients: List[str], message: str) -> bool:
    if not recipients:
        return True
    normalized = []
    for r in recipients:
        try:
            normalized.append(_normalize_phone(r))
        except InvalidPhone:
            pass
    if not normalized:
        return False
    if not settings.ARKESEL_API_KEY:
        logger.info("[SMS BULK SKIPPED] to=%s", normalized)
        return False
    url = f"{settings.ARKESEL_BASE_URL.rstrip('/')}/sms/send"
    payload = {
        "sender": settings.ARKESEL_SENDER_ID,
        "message": message,
        "recipients": normalized,
    }
    headers = {"api-key": settings.ARKESEL_API_KEY, "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.post(url, json=payload, headers=headers)
        return res.status_code < 400
    except Exception:
        logger.exception("Arkesel bulk SMS error")
        return False


# ---------- Templates ----------

def _support_line() -> str:
    return f"Questions? Call {settings.SUPPORT_PHONE}"


async def sms_order_received(order) -> bool:
    first = order.customer.full_name.split()[0]
    msg = (
        f"Hi {first}! Your KwiqBuy order {order.reference} has been received. "
        f"Total: GH₵ {order.total:.2f}. We'll notify you when it's on the way. "
        f"{_support_line()}"
    )
    return await send_sms(order.customer.phone, msg)


async def sms_order_paid(order) -> bool:
    first = order.customer.full_name.split()[0]
    msg = (
        f"Medaase {first}! Payment for {order.reference} "
        f"(GH₵ {order.total:.2f}) confirmed. The vendors are preparing your order."
    )
    return await send_sms(order.customer.phone, msg)


async def sms_order_out_for_delivery(order) -> bool:
    first = order.customer.full_name.split()[0]
    msg = (
        f"Good news, {first}! Order {order.reference} is on the way to "
        f"{order.delivery_zone_name}. 🛵"
    )
    return await send_sms(order.customer.phone, msg)


async def sms_order_delivered(order) -> bool:
    first = order.customer.full_name.split()[0]
    msg = (
        f"Delivered! Enjoy your order, {first} 🎉 Thanks for shopping with KwiqBuy."
    )
    return await send_sms(order.customer.phone, msg)


async def sms_order_cancelled(order) -> bool:
    first = order.customer.full_name.split()[0]
    msg = (
        f"Hi {first}, order {order.reference} has been cancelled. "
        f"If you were charged, a refund will arrive within 3 business days. "
        f"{_support_line()}"
    )
    return await send_sms(order.customer.phone, msg)


async def sms_loyalty_earned(order, points_earned: int, new_balance: int) -> bool:
    msg = (
        f"🎁 You earned {points_earned} loyalty points on order {order.reference}! "
        f"Your balance is now {new_balance} points. "
        f"Redeem at checkout: 100 points = GH₵ 1 off."
    )
    return await send_sms(order.customer.phone, msg)


async def sms_otp(phone: str, code: str) -> bool:
    msg = (
        f"Your KwiqBuy login code is: {code}\n"
        f"Valid for {settings.CUSTOMER_OTP_EXPIRE_MINUTES} minutes. "
        f"Do not share this code with anyone."
    )
    return await send_sms(phone, msg)