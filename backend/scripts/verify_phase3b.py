import argparse
import json
import random
import re
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
        with urlopen(req, timeout=20) as resp:
            raw = resp.read()
            try:
                return resp.status, json.loads(raw) if raw else None
            except Exception:
                return resp.status, {"raw_len": len(raw)}
    except HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except Exception:
            return e.code, None
    except URLError as e:
        print(f"  !! {e.reason}")
        return 0, None


def _check(label, cond, extra=""):
    mark = "OK " if cond else "FAIL"
    print(f"  [{mark}] {label}{(' -- ' + extra) if extra else ''}")
    return cond


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://localhost:8000")
    args = parser.parse_args()
    base = args.base.rstrip("/")
    print(f"Phase 3b verifier -- {base}\n")
    failed = 0

    st, login = _req("POST", f"{base}/api/v1/auth/login",
                     body={"email": "admin@kwiqbuy.com", "password": "Admin@1234"})
    if st != 200 or not login:
        print("  FAIL -- admin login"); sys.exit(1)
    admin_token = login["access_token"]

    st, vlogin = _req("POST", f"{base}/api/v1/auth/login",
                      body={"email": "ali@kwiqbuy.com", "password": "Vendor@1234"})
    if st != 200 or not vlogin:
        print("  FAIL -- vendor login"); sys.exit(1)
    vendor_token = vlogin["access_token"]

    print("[Webhooks]")
    st, evts = _req("GET", f"{base}/api/v1/vendor/webhooks/events", token=vendor_token)
    if not _check("GET /vendor/webhooks/events", st == 200): failed += 1

    rand = "".join(random.choices(string.ascii_lowercase, k=6))
    st, created_wh = _req("POST", f"{base}/api/v1/vendor/webhooks",
                          body={
                              "url": "https://example.com/kwiqbuy-test-hook",
                              "description": f"verify {rand}",
                              "events": ["order.created"],
                          },
                          token=vendor_token)
    if not _check("POST /vendor/webhooks", st == 201): failed += 1
    else:
        if not _check("secret returned", bool(created_wh.get("secret"))): failed += 1
        wh_id = created_wh["id"]
        st, whs = _req("GET", f"{base}/api/v1/vendor/webhooks", token=vendor_token)
        if not _check("GET /vendor/webhooks", st == 200 and isinstance(whs, list)):
            failed += 1
        st, dels = _req("GET", f"{base}/api/v1/vendor/webhooks/{wh_id}/deliveries", token=vendor_token)
        if not _check("GET /webhooks/{id}/deliveries", st == 200): failed += 1
        st, _ = _req("DELETE", f"{base}/api/v1/vendor/webhooks/{wh_id}", token=vendor_token)
        if not _check("DELETE /vendor/webhooks/{id}", st in (204, 200)): failed += 1

    print()
    print("[PDF Invoice]")
    st, orders = _req("GET", f"{base}/api/v1/orders?limit=1", token=admin_token)
    if st == 200 and isinstance(orders, list) and orders:
        order_id = orders[0]["id"]
        st, pdf = _req("GET", f"{base}/api/v1/orders/{order_id}/invoice.pdf", token=admin_token)
        if not _check("GET /orders/{id}/invoice.pdf",
                      st == 200 and pdf and pdf.get("raw_len", 0) > 500,
                      f"bytes={pdf.get('raw_len') if pdf else 'n/a'}"):
            failed += 1
    else:
        print("  WARN -- no orders to test PDF with")

    print()
    print("[Analytics Export]")
    st, csv = _req("GET", f"{base}/api/v1/admin/analytics/export?format=csv&days=7", token=admin_token)
    if not _check("GET /admin/analytics/export?format=csv",
                  st == 200 and csv and csv.get("raw_len", 0) > 50):
        failed += 1
    st, xlsx = _req("GET", f"{base}/api/v1/admin/analytics/export?format=xlsx&days=7", token=admin_token)
    if not _check("GET /admin/analytics/export?format=xlsx",
                  st == 200 and xlsx and xlsx.get("raw_len", 0) > 500):
        failed += 1

    print()
    print("[Search Ranking]")
    st, sres = _req("GET", f"{base}/api/v1/search?q=bowl&limit=5")
    if not _check("GET /search?q=bowl", st == 200): failed += 1
    else:
        _check("returns items",
               isinstance(sres.get("items"), list) and len(sres["items"]) >= 1,
               f"count={len(sres.get('items', []))}")

    print()
    print("[2FA]")
    st, status = _req("GET", f"{base}/api/v1/admin/2fa/status", token=admin_token)
    if not _check("GET /admin/2fa/status", st == 200 and "enabled" in status):
        failed += 1
    st, setup = _req("POST", f"{base}/api/v1/admin/2fa/setup", token=admin_token)
    if not _check("POST /admin/2fa/setup", st == 200 and setup.get("secret")):
        failed += 1
    else:
        if not _check("QR data URL present",
                      str(setup.get("qr_data_url", "")).startswith("data:image/png;base64,")):
            failed += 1

    print()
    print("[GDPR]")
    suffix = "".join(str(random.randint(0, 9)) for _ in range(7))
    test_phone = f"024{suffix}"
    st, otp_resp = _req("POST", f"{base}/api/v1/customer-auth/request-otp",
                        body={"phone": test_phone, "full_name": "GDPR Tester"})
    if st == 200 and otp_resp:
        m = re.search(r"(\d{4,8})", otp_resp.get("message", ""))
        if m:
            st, verify = _req("POST", f"{base}/api/v1/customer-auth/verify-otp",
                              body={"phone": test_phone, "code": m.group(1)})
            if st == 200 and verify:
                cust_token = verify["access_token"]
                st, exp = _req("GET", f"{base}/api/v1/customer-account/me/export", token=cust_token)
                if not _check("GET /customer-account/me/export",
                              st == 200 and exp and "profile" in exp):
                    failed += 1
                st, dele = _req("DELETE", f"{base}/api/v1/customer-account/me", token=cust_token)
                if not _check("DELETE /customer-account/me",
                              st == 200 and dele and dele.get("deleted") is True):
                    failed += 1
        else:
            print("  WARN -- no OTP dev code, skipping GDPR test")

    print()
    print(f"{'ALL PASSED' if failed == 0 else f'{failed} CHECKS FAILED'}")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
