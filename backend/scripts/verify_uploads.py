"""
Verify file upload validation.

Uses a real embedded PNG (1x1 pixel) so the "valid" case definitely passes
PIL decoding.

Usage:
    python -m scripts.verify_uploads
"""
import argparse
import base64
import io
import json
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


def _post_json(url, body, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(url, data=json.dumps(body).encode(), headers=headers, method="POST")
    try:
        with urlopen(req, timeout=15) as resp:
            return resp.status, json.loads(resp.read())
    except HTTPError as e:
        return e.code, None
    except URLError:
        return 0, None


def _post_multipart(url, filename, content, content_type, token):
    boundary = "----KwiqBuyBoundary7MA4YWxkTrZu0gW"
    body = io.BytesIO()

    def w(s):
        body.write(s.encode() if isinstance(s, str) else s)

    w(f"--{boundary}\r\n")
    w(f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n')
    w(f"Content-Type: {content_type}\r\n\r\n")
    body.write(content)
    w("\r\n")
    w(f"--{boundary}\r\n")
    w('Content-Disposition: form-data; name="subdir"\r\n\r\n')
    w("products\r\n")
    w(f"--{boundary}--\r\n")

    payload = body.getvalue()
    headers = {
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Content-Length": str(len(payload)),
        "Authorization": f"Bearer {token}",
    }
    req = Request(url, data=payload, headers=headers, method="POST")
    try:
        with urlopen(req, timeout=30) as resp:
            return resp.status
    except HTTPError as e:
        return e.code
    except URLError:
        return 0


# A real 1x1 transparent PNG (base64, decoded at runtime).
_VALID_PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://localhost:8000")
    parser.add_argument("--email", default="admin@kwiqbuy.com")
    parser.add_argument("--password", default="Admin@1234")
    args = parser.parse_args()
    base = args.base.rstrip("/")

    print(f"Testing uploads against {base}\n")

    status, login = _post_json(
        f"{base}/api/v1/auth/login",
        {"email": args.email, "password": args.password},
    )
    if status != 200 or not login:
        print(f"  FAIL — could not log in as {args.email} (HTTP {status})")
        sys.exit(1)
    token = login["access_token"]
    print("  OK   admin login")

    upload_url = f"{base}/api/v1/uploads"

    # 1. Valid PNG
    s = _post_multipart(upload_url, "test.png", _VALID_PNG_BYTES, "image/png", token)
    ok1 = s == 201
    print(f"  [{'OK ' if ok1 else 'FAIL'}] valid PNG → HTTP {s} (expect 201)")

    # 2. Fake image
    s = _post_multipart(
        upload_url, "fake.jpg", b"this is not an image", "image/jpeg", token
    )
    ok2 = s == 400
    print(f"  [{'OK ' if ok2 else 'FAIL'}] fake JPG → HTTP {s} (expect 400)")

    # 3. PDF content type
    s = _post_multipart(
        upload_url,
        "doc.pdf",
        b"%PDF-1.4\nnot really a pdf",
        "application/pdf",
        token,
    )
    ok3 = s == 400
    print(f"  [{'OK ' if ok3 else 'FAIL'}] PDF content-type → HTTP {s} (expect 400)")

    # 4. SVG
    s = _post_multipart(
        upload_url,
        "icon.svg",
        b'<svg xmlns="http://www.w3.org/2000/svg"></svg>',
        "image/svg+xml",
        token,
    )
    ok4 = s == 400
    print(f"  [{'OK ' if ok4 else 'FAIL'}] SVG → HTTP {s} (expect 400)")

    # 5. Oversized
    big = _VALID_PNG_BYTES + b"\x00" * (6 * 1024 * 1024)
    s = _post_multipart(upload_url, "big.png", big, "image/png", token)
    ok5 = s == 400
    print(f"  [{'OK ' if ok5 else 'FAIL'}] 6MB file → HTTP {s} (expect 400)")

    all_ok = all([ok1, ok2, ok3, ok4, ok5])
    print()
    print("PASS" if all_ok else "FAIL — some upload checks did not pass")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
