"""
Verify email sending.

If RESEND_API_KEY is set, sends a real test email and tells you to
check your inbox.

If it's not set, renders the receipt template and prints it to the
console so you can visually inspect the layout.

Usage:
    python -m scripts.verify_email --to you@example.com
"""
import argparse
import asyncio
import sys
from datetime import datetime, timezone

from app.core.config import settings
from app.core.email import render_template, send_email


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--to", required=False, default="test@example.com")
    args = parser.parse_args()

    print(f"Resend API key configured: {bool(settings.RESEND_API_KEY)}")
    print(f"From: {settings.MAIL_FROM}")
    print()

    context = {
        "customer_name": "Test Customer",
        "reference": "KB-20260101-ABC123",
        "items_rows": (
            "<tr><td>Sample Burger</td>"
            "<td style='text-align:center;'>2</td>"
            "<td style='text-align:right;'>GH₵ 100.00</td></tr>"
        ),
        "subtotal": "100.00",
        "delivery_fee": "15.00",
        "total": "115.00",
        "delivery_zone": "East Legon",
        "delivery_address": "Boundary Road, East Legon, Accra",
        "frontend_url": settings.FRONTEND_URL.rstrip("/"),
        "year": datetime.now(timezone.utc).year,
    }
    html = render_template("receipt.html", context)

    if settings.RESEND_API_KEY:
        print(f"Sending real email to {args.to}...")
        ok = await send_email(
            to=args.to,
            subject="KwiqBuy test email — verify delivery",
            html=html,
        )
        print("PASS — check your inbox" if ok else "FAIL — Resend send returned False")
        sys.exit(0 if ok else 1)

    print("No RESEND_API_KEY — printing rendered HTML instead:\n")
    print("=" * 70)
    print(html[:2000])
    print("=" * 70)
    print()
    print("PASS — template rendered without error (email not actually sent)")


if __name__ == "__main__":
    asyncio.run(main())
