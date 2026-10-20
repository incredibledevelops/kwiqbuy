"""
Verify /health, /ready, /live behave correctly.

Usage:
    python -m scripts.verify_health_probe
"""
import argparse
import json
import sys
from urllib.request import urlopen
from urllib.error import HTTPError, URLError


def _get(url):
    try:
        with urlopen(url, timeout=10) as resp:
            return resp.status, json.loads(resp.read())
    except HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except Exception:
            return e.code, None
    except URLError as e:
        print(f"       (connection error: {e.reason})")
        return 0, None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://localhost:8000")
    args = parser.parse_args()
    base = args.base.rstrip("/")

    print(f"Testing health probes against {base}\n")

    s, body = _get(f"{base}/live")
    ok1 = s == 200 and body and body.get("alive") is True
    print(f"  [{'OK ' if ok1 else 'FAIL'}] GET /live → HTTP {s}, alive={body.get('alive') if body else None}")

    s, body = _get(f"{base}/health")
    ok2 = s in (200, 503) and body and body.get("status") in ("ok", "degraded")
    print(f"  [{'OK ' if ok2 else 'FAIL'}] GET /health → HTTP {s}")
    if body:
        print(f"        status={body.get('status')}")
        print(f"        mongo={body.get('mongo')}")
        print(f"        redis={body.get('redis')}")

    s, body = _get(f"{base}/ready")
    ok3 = s in (200, 503) and body is not None
    print(f"  [{'OK ' if ok3 else 'FAIL'}] GET /ready → HTTP {s}, ready={body.get('ready') if body else None}")

    s, body = _get(f"{base}/metrics")
    ok4 = s == 200 and body is not None
    print(f"  [{'OK ' if ok4 else 'FAIL'}] GET /metrics → HTTP {s}")

    all_ok = ok1 and ok2 and ok3 and ok4
    print()
    print("PASS" if all_ok else "FAIL")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
