"""
Verify that SlowAPI rate limits are actually enforced.

Hits /auth/login N+1 times and expects the last one to return 429.

Usage:
    python -m scripts.verify_rate_limits
    python -m scripts.verify_rate_limits --base http://localhost:8000
"""
import argparse
import json
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


def _post(url, body):
    data = json.dumps(body).encode()
    req = Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=15) as resp:
            return resp.status
    except HTTPError as e:
        return e.code
    except URLError:
        return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://localhost:8000")
    args = parser.parse_args()

    url = f"{args.base.rstrip('/')}/api/v1/auth/login"
    print(f"Testing rate limits against {url}\n")
    print("Limit is 5/minute per IP. Sending 7 requests...\n")

    results = []
    for i in range(7):
        status = _post(url, {"email": "nobody@example.com", "password": "wrong"})
        results.append(status)
        mark = "OK " if status in (401, 429) else "?? "
        print(f"  [{mark}] request #{i+1}: HTTP {status}")

    got_429 = 429 in results
    print()
    if got_429:
        print("PASS — rate limit was enforced (429 seen)")
        sys.exit(0)
    else:
        print("FAIL — no 429 observed after 7 requests")
        print("       Check that @limiter.limit is applied and slowapi is wired up.")
        sys.exit(1)


if __name__ == "__main__":
    main()
