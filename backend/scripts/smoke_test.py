"""
Standalone smoke test — no pytest needed.

Usage:
    python -m scripts.smoke_test
    python -m scripts.smoke_test --base http://localhost:8000
"""
import argparse
import json
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


def _request(method, url, body=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body is not None else None
    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=15) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else None
    except HTTPError as e:
        return e.code, None
    except URLError as e:
        print(f"  !! connection error: {e.reason}")
        return 0, None


def _check(label, status, expected, data=None):
    ok = status in expected if isinstance(expected, (list, tuple, set)) else status == expected
    mark = "OK " if ok else "FAIL"
    print(f"  [{mark}] {label}  (HTTP {status})")
    return ok


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://localhost:8000")
    args = parser.parse_args()
    base = args.base.rstrip("/")

    print(f"Smoke test against {base}\n")
    failed = 0

    print("Health:")
    st, _ = _request("GET", f"{base}/health")
    if not _check("GET /health", st, 200): failed += 1

    st, _ = _request("GET", f"{base}/live")
    if not _check("GET /live", st, 200): failed += 1

    st, _ = _request("GET", f"{base}/ready")
    if not _check("GET /ready", st, (200, 503)): failed += 1

    print("\nPublic:")
    st, cfg = _request("GET", f"{base}/api/v1/config/public")
    if not _check("GET /config/public", st, 200): failed += 1

    st, vendors = _request("GET", f"{base}/api/v1/vendors/public")
    if not _check("GET /vendors/public", st, 200): failed += 1
    else:
        print(f"       {len(vendors)} vendors")

    st, nearby = _request(
        "GET",
        f"{base}/api/v1/vendors/nearby?lat=5.6355&lng=-0.1766&radius_km=15",
    )
    if not _check("GET /vendors/nearby", st, 200): failed += 1
    else:
        print(f"       {len(nearby.get('vendors', []))} food vendors nearby")

    st, products = _request("GET", f"{base}/api/v1/products")
    if not _check("GET /products", st, 200): failed += 1
    else:
        print(f"       {len(products)} products")

    st, food_products = _request("GET", f"{base}/api/v1/products?vendor_category=food")
    if not _check("GET /products?vendor_category=food", st, 200): failed += 1

    print("\nAuth:")
    st, login = _request(
        "POST",
        f"{base}/api/v1/auth/login",
        body={"email": "admin@kwiqbuy.com", "password": "Admin@1234"},
    )
    admin_token = None
    if not _check("POST /auth/login (admin)", st, 200): failed += 1
    elif login and login.get("access_token"):
        admin_token = login["access_token"]

    if admin_token:
        print("\nAdmin:")
        for label, path in [
            ("GET /admin/settings", "/api/v1/admin/settings"),
            ("GET /admin/audit", "/api/v1/admin/audit"),
            ("GET /vendors", "/api/v1/vendors"),
            ("GET /orders", "/api/v1/orders"),
        ]:
            st, _ = _request("GET", f"{base}{path}", token=admin_token)
            if not _check(label, st, 200): failed += 1

    print("\nVendor:")
    st, vlogin = _request(
        "POST",
        f"{base}/api/v1/auth/login",
        body={"email": "ali@kwiqbuy.com", "password": "Vendor@1234"},
    )
    vendor_token = None
    if not _check("POST /auth/login (vendor)", st, 200): failed += 1
    elif vlogin and vlogin.get("access_token"):
        vendor_token = vlogin["access_token"]

    if vendor_token:
        for label, path in [
            ("GET /vendor/me", "/api/v1/vendor/me"),
            ("GET /vendor/products", "/api/v1/vendor/products"),
            ("GET /vendor/orders", "/api/v1/vendor/orders"),
            ("GET /vendor/payouts", "/api/v1/vendor/payouts"),
        ]:
            st, _ = _request("GET", f"{base}{path}", token=vendor_token)
            if not _check(label, st, 200): failed += 1

    print("\nCart:")
    st, _ = _request(
        "POST",
        f"{base}/api/v1/cart/validate",
        body={"product_ids": [p["id"] for p in (products or [])[:1]]},
    )
    if not _check("POST /cart/validate", st, 200): failed += 1

    print(f"\n{'ALL PASSED' if failed == 0 else f'{failed} CHECKS FAILED'}")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
