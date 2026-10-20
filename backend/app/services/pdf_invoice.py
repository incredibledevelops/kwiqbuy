import io
from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from app.core.config import settings


def _fmt(v: float) -> str:
    return f"{v:.2f}"


def render_invoice(order) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=18 * mm, bottomMargin=18 * mm,
        title=f"KwiqBuy Invoice {order.reference}", author="KwiqBuy",
    )
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Heading1"], fontSize=22, textColor=colors.HexColor("#2563EB"))
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=13, textColor=colors.HexColor("#111827"))
    small = ParagraphStyle("small", parent=styles["BodyText"], fontSize=9, textColor=colors.HexColor("#6B7280"))
    body = ParagraphStyle("body", parent=styles["BodyText"], fontSize=10, textColor=colors.HexColor("#111827"))

    story = []
    story.append(Paragraph("KwiqBuy", h1))
    story.append(Paragraph("Marketplace Receipt", small))
    story.append(Spacer(1, 6 * mm))

    created = order.created_at.strftime("%Y-%m-%d %H:%M UTC")
    story.append(Paragraph(f"<b>Order:</b> {order.reference}", body))
    story.append(Paragraph(f"<b>Date:</b> {created}", body))
    story.append(Paragraph(f"<b>Status:</b> {order.status.value}", body))
    story.append(Paragraph(f"<b>Order type:</b> {order.order_type.value}", body))
    story.append(Spacer(1, 4 * mm))

    story.append(Paragraph("Customer", h2))
    story.append(Paragraph(order.customer.full_name, body))
    story.append(Paragraph(order.customer.email, body))
    story.append(Paragraph(order.customer.phone, body))
    story.append(Paragraph(order.delivery_address, body))
    story.append(Spacer(1, 4 * mm))

    for vo in order.vendor_orders:
        story.append(Paragraph(vo.vendor_name, h2))
        rows = [["Item", "Qty", "Unit", "Line"]]
        for item in vo.items:
            rows.append([
                item.name, str(item.quantity),
                _fmt(item.unit_price), _fmt(item.unit_price * item.quantity),
            ])
        rows.append(["", "", "Subtotal", _fmt(vo.subtotal)])
        rows.append(["", "", "Platform fee", _fmt(vo.platform_fee)])
        rows.append(["", "", "Vendor payout", _fmt(vo.vendor_payout)])

        table = Table(rows, colWidths=[95 * mm, 15 * mm, 30 * mm, 30 * mm], hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DBEAFE")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1E40AF")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
            ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#E5E7EB")),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("FONTNAME", (0, len(rows) - 1), (-1, -1), "Helvetica-Bold"),
        ]))
        story.append(table)
        story.append(Spacer(1, 4 * mm))

    story.append(Paragraph("Totals", h2))
    totals = [
        ["Subtotal", _fmt(order.subtotal)],
        ["Delivery fee", _fmt(order.delivery_fee)],
    ]
    if order.promo_discount:
        totals.append([f"Promo ({order.promo_code})", f"-{_fmt(order.promo_discount)}"])
    if order.loyalty_discount:
        totals.append(["Loyalty discount", f"-{_fmt(order.loyalty_discount)}"])
    if order.wallet_applied:
        totals.append(["Wallet applied", f"-{_fmt(order.wallet_applied)}"])
    totals.append(["Total", _fmt(order.total)])
    if order.amount_due_external:
        totals.append(["Amount charged", _fmt(order.amount_due_external)])

    t = Table(totals, colWidths=[120 * mm, 50 * mm], hAlign="RIGHT")
    t.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("FONTNAME", (0, len(totals) - 1), (-1, -1), "Helvetica-Bold"),
        ("LINEABOVE", (0, len(totals) - 1), (-1, len(totals) - 1), 0.5, colors.HexColor("#111827")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph(
        f"Questions? Call {settings.SUPPORT_PHONE}. Thank you for shopping with KwiqBuy.", small,
    ))
    story.append(Paragraph(
        f"Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", small,
    ))

    doc.build(story)
    return buf.getvalue()
