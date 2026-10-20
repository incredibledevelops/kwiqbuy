"""Email helper using Resend."""
import logging
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config import settings

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)


def _resend_client():
    try:
        import resend  # type: ignore
        resend.api_key = settings.RESEND_API_KEY
        return resend
    except ImportError:
        logger.warning("resend not installed — emails logged only")
        return None


def render_template(name: str, context: dict) -> str:
    template = _env.get_template(name)
    return template.render(**context)


async def send_email(
    to: str,
    subject: str,
    html: str,
    from_override: Optional[str] = None,
) -> bool:
    if not settings.RESEND_API_KEY:
        logger.info("[EMAIL SKIPPED] to=%s subject=%s", to, subject)
        return False
    client = _resend_client()
    if client is None:
        return False
    try:
        client.Emails.send({
            "from": from_override or settings.MAIL_FROM,
            "to": [to],
            "subject": subject,
            "html": html,
        })
        return True
    except Exception as exc:
        logger.exception("Failed to send email to %s: %s", to, exc)
        return False


async def send_order_receipt(order) -> bool:
    items_rows = ""
    for vo in order.vendor_orders:
        items_rows += (
            f'<tr><td colspan="3" style="padding-top:12px;padding-bottom:4px;'
            f'font-weight:700;color:#92400E;">{vo.vendor_name}</td></tr>'
        )
        for item in vo.items:
            items_rows += f"""
            <tr>
              <td style="padding:6px 0;border-bottom:1px solid #eee;">{item.name}</td>
              <td style="padding:6px 0;border-bottom:1px solid #eee;text-align:center;">{item.quantity}</td>
              <td style="padding:6px 0;border-bottom:1px solid #eee;text-align:right;">
                GH₵ {item.unit_price * item.quantity:.2f}
              </td>
            </tr>
            """

    frontend_url = settings.FRONTEND_URL.rstrip("/")
    html = render_template(
        "receipt.html",
        {
            "customer_name": order.customer.full_name,
            "reference": order.reference,
            "items_rows": items_rows,
            "subtotal": f"{order.subtotal:.2f}",
            "delivery_fee": f"{order.delivery_fee:.2f}",
            "total": f"{order.total:.2f}",
            "delivery_zone": order.delivery_zone_name,
            "delivery_address": order.delivery_address,
            "frontend_url": frontend_url,
        },
    )
    return await send_email(
        to=order.customer.email,
        subject=f"Your KwiqBuy order {order.reference} is confirmed 🎉",
        html=html,
    )