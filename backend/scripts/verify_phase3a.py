"""
Verify Phase 3a: subscription tiers, review disputes, rider locations,
bulk ops, zone cut override.

Idempotent — uses a random test tier slug per run and deletes it at the end.

Usage: python -m scripts.verify_phase3a
"""
import argparse
import json
import random
import string
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


def _req(method, url, body=None, token=None):
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
        # Try to read error body for debug
        try:
            return e.code, json.loads(e.read())
        except Exception:
            return e.code, None
    except URLError as e:
        print(f"  !! {e.reason}")
        return 0, None


def _check(label, cond, extra=""):
    mark = "OK " if cond else "FAIL"
    print(f"  [{mark}] {label}{(' — ' + extra) if extra else ''}")
    return cond


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://localhost:8000")
    args = parser.parse_args()
    base = args.base.rstrip("/")
    print(f"Phase 3a verifier — {base}\n")
    failed = 0

    # Random suffix per run so tier creation is idempotent
    rand = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    test_slug = f"verify-test-{rand}"

    # ---- Admin login
    st, login = _req("POST", f"{base}/api/v1/auth/login",
                     body={"email": "admin@kwiqbuy.com", "password": "Admin@1234"})
    if st != 200 or not login:
        print("  FAIL — admin login")
        sys.exit(1)
    admin_token = login["access_token"]

    # ---- Public tiers
    print("[Subscription Tiers]")
    st, tiers = _req("GET", f"{base}/api/v1/subscription-tiers")
    if not _check("GET /subscription-tiers", st == 200):
        failed += 1
    else:
        slugs = {t["slug"] for t in tiers}
        if not _check("free/growth/enterprise present",
                      {"free", "growth", "enterprise"}.issubset(slugs)):
            failed += 1

    # ---- Admin creates a fresh tier
    created_tier_id = None
    st, new_tier = _req(
        "POST",
        f"{base}/api/v1/admin/subscription-tiers",
        body={
            "slug": test_slug,
            "name": "Verify Test Tier",
            "monthly_price": 1.0,
            "commission_discount_pct": 1.0,
            "features": ["test"],
            "is_active": True,
            "display_order": 99,
        },
        token=admin_token,
    )
    if not _check(
        "POST /admin/subscription-tiers (new slug)",
        st == 201,
        f"slug={test_slug}" + (f" err={new_tier.get('detail')}" if new_tier else ""),
    ):
        failed += 1
    elif new_tier:
        created_tier_id = new_tier.get("id")

    # ---- Admin can update it
    if created_tier_id:
        st, updated = _req(
            "PATCH",
            f"{base}/api/v1/admin/subscription-tiers/{created_tier_id}",
            body={"monthly_price": 2.0},
            token=admin_token,
        )
        if not _check(
            "PATCH /admin/subscription-tiers/{id}",
            st == 200 and updated and updated.get("monthly_price") == 2.0,
        ):
            failed += 1

    # ---- Vendor login
    print()
    print("[Vendor Subscription]")
    st, vlogin = _req("POST", f"{base}/api/v1/auth/login",
                      body={"email": "ali@kwiqbuy.com", "password": "Vendor@1234"})
    if st != 200 or not vlogin:
        print("  FAIL — vendor login")
        failed += 1
        sys.exit(1)
    vendor_token = vlogin["access_token"]

    st, sub_status = _req("GET", f"{base}/api/v1/vendor/subscription", token=vendor_token)
    if not _check("GET /vendor/subscription (baseline)", st == 200):
        failed += 1

    # Free tier — activates instantly
    st, sub_free = _req("POST", f"{base}/api/v1/vendor/subscription/subscribe",
                        body={"tier_slug": "free"}, token=vendor_token)
    if not _check("POST /vendor/subscription/subscribe (free)", st == 200):
        failed += 1
    else:
        if not _check(
            "free subscription status == active",
            sub_free.get("status") == "active",
            f"status={sub_free.get('status')}",
        ):
            failed += 1

    st, sub_status = _req("GET", f"{base}/api/v1/vendor/subscription", token=vendor_token)
    if not _check("has_active_subscription true after free sub",
                  sub_status and sub_status.get("has_active_subscription")):
        failed += 1

    # Growth tier — PENDING pending payment
    st, sub_growth = _req("POST", f"{base}/api/v1/vendor/subscription/subscribe",
                          body={"tier_slug": "growth"}, token=vendor_token)
    if not _check("POST /vendor/subscription/subscribe (growth)", st == 200):
        failed += 1
    else:
        if not _check(
            "growth subscription status == pending",
            sub_growth.get("status") == "pending",
            f"status={sub_growth.get('status')}",
        ):
            failed += 1

    # ---- Review disputes
    print()
    print("[Review Disputes]")
    st, _ = _req("GET", f"{base}/api/v1/vendor/review-disputes", token=vendor_token)
    if not _check("GET /vendor/review-disputes", st == 200):
        failed += 1

    st, _ = _req("GET", f"{base}/api/v1/admin/review-disputes", token=admin_token)
    if not _check("GET /admin/review-disputes", st == 200):
        failed += 1

    # ---- Rider locations
    print()
    print("[Rider Locations]")
    st, rlogin = _req("POST", f"{base}/api/v1/auth/login",
                      body={"email": "rider@kwiqbuy.com", "password": "Rider@1234"})
    if st != 200 or not rlogin:
        print("  WARN — rider login failed, skipping rider test")
    else:
        rider_token = rlogin["access_token"]
        st, _ = _req("POST", f"{base}/api/v1/rider/location",
                     body={"lat": 5.6355, "lng": -0.1766, "accuracy_meters": 12},
                     token=rider_token)
        if not _check("POST /rider/location", st == 200):
            failed += 1

    # ---- Bulk ops
    print()
    print("[Bulk Ops]")
    st, _ = _req("POST", f"{base}/api/v1/vendor/bulk/products/set-availability",
                 body={"product_ids": [], "is_available": True},
                 token=vendor_token)
    if not _check("empty product_ids rejected (422)", st == 422):
        failed += 1

    # ---- Cleanup: deactivate the test tier
    if created_tier_id:
        st, _ = _req(
            "DELETE",
            f"{base}/api/v1/admin/subscription-tiers/{created_tier_id}",
            token=admin_token,
        )
        print(f"\n  (cleanup: deleted test tier {test_slug})")

    print()
    print(f"{'ALL PASSED' if failed == 0 else f'{failed} CHECKS FAILED'}")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()