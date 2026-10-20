"""
Verify CORS headers.

Tests both:
  - Simple requests (GET with Origin header) — should return ACAO
  - Preflight (OPTIONS) — should return ACAO + ACAM + ACAH

Handles uvicorn's lowercase header names by normalizing on read.

Usage:
    python -m scripts.verify_cors
"""
import argparse
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


def _lower_headers(headers) -> dict:
    """Normalize HTTPMessage headers to a lowercase dict."""
    out = {}
    for k, v in headers.items():
        out[k.lower()] = v
    return out


def _get_with_origin(url, origin):
    req = Request(url, method="GET", headers={"Origin": origin})
    try:
        with urlopen(req, timeout=10) as resp:
            return resp.status, _lower_headers(resp.headers)
    except HTTPError as e:
        return e.code, _lower_headers(e.headers)
    except URLError as e:
        print(f"       (connection error: {e.reason})")
        return 0, {}


def _preflight(url, origin):
    req = Request(
        url,
        method="OPTIONS",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    try:
        with urlopen(req, timeout=10) as resp:
            return resp.status, _lower_headers(resp.headers)
    except HTTPError as e:
        return e.code, _lower_headers(e.headers)
    except URLError as e:
        print(f"       (connection error: {e.reason})")
        return 0, {}


def _show(headers):
    print(f"       ACAO={headers.get('access-control-allow-origin', '')!r}")
    print(f"       ACAC={headers.get('access-control-allow-credentials', '')!r}")
    print(f"       ACAM={headers.get('access-control-allow-methods', '')!r}")
    print(f"       ACAH={headers.get('access-control-allow-headers', '')!r}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://localhost:8000")
    parser.add_argument("--origin", default="http://localhost:3000")
    parser.add_argument("--bad-origin", default="http://evil.example.com")
    args = parser.parse_args()
    base = args.base.rstrip("/")

    print(f"Testing CORS against {base}")
    print(f"Configured origin: {args.origin}\n")

    # Simple GET with Origin header
    print("[Simple GET with Origin]")
    s, headers = _get_with_origin(f"{base}/health", args.origin)
    acao = headers.get("access-control-allow-origin", "")
    ok1 = s == 200 and acao == args.origin
    print(f"  [{'OK ' if ok1 else 'FAIL'}] status={s}")
    _show(headers)

    # Preflight OPTIONS
    print()
    print("[Preflight OPTIONS]")
    s, headers = _preflight(f"{base}/health", args.origin)
    acao = headers.get("access-control-allow-origin", "")
    acam = headers.get("access-control-allow-methods", "")
    ok2 = s in (200, 204) and acao == args.origin and "GET" in acam
    print(f"  [{'OK ' if ok2 else 'FAIL'}] status={s}")
    _show(headers)

    # Bad origin — should NOT echo back
    print()
    print("[Bad origin — should NOT echo]")
    s, headers = _preflight(f"{base}/health", args.bad_origin)
    acao = headers.get("access-control-allow-origin", "")
    ok3 = acao != args.bad_origin
    print(f"  [{'OK ' if ok3 else 'FAIL'}] status={s}, ACAO={acao!r}")

    all_ok = ok1 and ok2 and ok3
    print()
    print("PASS" if all_ok else "FAIL")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()