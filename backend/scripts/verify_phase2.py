"""
Verify Phase 2: wallet + rider earnings + delivery cut.

Uses a fresh random phone per run so re-runs don't collide.

Usage:
    python -m scripts.verify_phase2
"""
import argparse
import json
import random
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

    print(f"Phase 2 verifier — {base}\n")
    failed = 0

    # Fresh phone per run: 024 + 7 random digits
    suffix = "".join(str(random.randint(0, 9)) for _ in range(7))
    test_phone = f"024{suffix}"
    print(f"Using test phone: {test_phone}\n")

    # --- Admin login
    st, login = _req(
        "POST",
        f"{base}/api/v1/auth/login",
        body={"email": "admin@kwiqbuy.com", "password": "Admin@1234"},
    )
    if st != 200 or not login:
        print("  FAIL — admin login failed")
        sys.exit(1)
    admin_token = login["access_token"]

    # --- Admin settings
    print("[Admin Settings]")
    st, settings_doc = _req("GET", f"{base}/api/v1/admin/settings", token=admin_token)
    if not _check("GET /admin/settings", st == 200):
        failed += 1
    else:
        if not _check(
            "platform_delivery_cut_pct present",
            "platform_delivery_cut_pct" in settings_doc,
            f"= {settings_doc.get('platform_delivery_cut_pct')}%",
        ):
            failed += 1

    # --- Customer auth
    print()
    print("[Customer + Wallet]")
    st, otp_resp = _req(
        "POST",
        f"{base}/api/v1/customer-auth/request-otp",
        body={"phone": test_phone, "full_name": "Phase2 Tester"},
    )
    if not _check(
        "POST /customer-auth/request-otp",
        st == 200,
        otp_resp.get("message", "") if otp_resp else "",
    ):
        failed += 1

    dev_code = None
    if otp_resp and otp_resp.get("message", "").startswith("DEV MODE"):
        import re
        m = re.search(r"(\d{4,8})", otp_resp["message"])
        if m:
            dev_code = m.group(1)

    if not dev_code:
        print("  !! No DEV MODE code returned — cannot proceed")
        sys.exit(1)

    st, verify = _req(
        "POST",
        f"{base}/api/v1/customer-auth/verify-otp",
        body={"phone": test_phone, "code": dev_code},
    )
    if not _check("POST /customer-auth/verify-otp", st == 200):
        failed += 1
        sys.exit(1)
    cust_token = verify["access_token"]

    # --- Wallet starts at 0
    st, wallet = _req("GET", f"{base}/api/v1/wallet/me", token=cust_token)
    if not _check("GET /wallet/me", st == 200):
        failed += 1
    else:
        if not _check(
            "wallet starts at 0",
            wallet.get("balance") == 0.0,
            f"balance={wallet.get('balance')}",
        ):
            failed += 1

    # --- Admin credits wallet
    st, adjusted = _req(
        "POST",
        f"{base}/api/v1/admin/wallet/adjust",
        body={"phone": test_phone, "amount": 100.0, "note": "Phase2 test credit"},
        token=admin_token,
    )
    if not _check("POST /admin/wallet/adjust (+100)", st == 200):
        failed += 1
    else:
        if not _check(
            "balance is now 100",
            adjusted.get("balance") == 100.0,
            f"balance={adjusted.get('balance')}",
        ):
            failed += 1

    # --- Wallet history
    st, history = _req("GET", f"{base}/api/v1/wallet/me/history", token=cust_token)
    if not _check("GET /wallet/me/history", st == 200):
        failed += 1
    else:
        if not _check(
            "has 1 transaction",
            len(history.get("transactions", [])) == 1,
            f"count={len(history.get('transactions', []))}",
        ):
            failed += 1

    # --- Compute
    st, compute = _req(
        "POST",
        f"{base}/api/v1/wallet/me/compute",
        body={"order_total": 80.0},
        token=cust_token,
    )
    if not _check("POST /wallet/me/compute (80 total, 100 balance)", st == 200):
        failed += 1
    else:
        if not _check(
            "wallet applied == 80",
            compute.get("wallet_applied") == 80.0,
            f"applied={compute.get('wallet_applied')}",
        ):
            failed += 1
        if not _check(
            "amount_due_external == 0",
            compute.get("amount_due_external") == 0.0,
        ):
            failed += 1

    print()
    print(f"{'ALL PASSED' if failed == 0 else f'{failed} CHECKS FAILED'}")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()