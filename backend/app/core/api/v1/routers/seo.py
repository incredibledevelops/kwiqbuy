"""SEO endpoints — dynamic sitemap + robots.txt."""
from fastapi import APIRouter, Response
from fastapi.responses import PlainTextResponse

from app.core.config import settings
from app.crud import product as product_crud

router = APIRouter(tags=["SEO"])


def _iso_date(dt) -> str:
    if not dt:
        return ""
    try:
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return ""


@router.get("/sitemap.xml", response_class=Response)
async def sitemap():
    site = settings.SITE_URL.rstrip("/")
    products = await product_crud.list_products(available_only=True, limit=5000)

    urls: list[tuple[str, str, str, str]] = [
        (f"{site}/", "1.0", "daily", ""),
        (f"{site}/menu", "0.9", "daily", ""),
        (f"{site}/vendors", "0.8", "daily", ""),
    ]
    for p in products:
        urls.append(
            (
                f"{site}/menu/{p.slug}",
                "0.8",
                "weekly",
                _iso_date(getattr(p, "updated_at", None)),
            )
        )

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for url, priority, changefreq, lastmod in urls:
        lines.append("  <url>")
        lines.append(f"    <loc>{url}</loc>")
        if lastmod:
            lines.append(f"    <lastmod>{lastmod}</lastmod>")
        lines.append(f"    <changefreq>{changefreq}</changefreq>")
        lines.append(f"    <priority>{priority}</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")

    return Response(content="\n".join(lines), media_type="application/xml")


@router.get("/robots.txt", response_class=PlainTextResponse)
async def robots():
    site = settings.SITE_URL.rstrip("/")
    return (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /admin/\n"
        "Disallow: /vendor/\n"
        "Disallow: /rider/\n"
        "Disallow: /account/\n"
        "Disallow: /order/\n"
        "Disallow: /api/\n"
        "\n"
        f"Sitemap: {site}/sitemap.xml\n"
    )