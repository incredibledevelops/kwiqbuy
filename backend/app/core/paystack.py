import hashlib
import hmac
import logging
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class PaystackError(Exception):
    def __init__(self, message: str, status_code: int = 400, payload: Any = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload = payload


def _clean_secret(raw: str) -> str:
    """
    Strip whitespace, newlines, and matching surrounding quotes.
    Handles the common `.env` copy-paste traps.
    """
    s = (raw or "").strip().replace("\r", "").replace("\n", "")
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        s = s[1:-1].strip()
    return s


class PaystackClient:
    def __init__(
        self,
        secret_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 20.0,
    ):
        self.secret_key = _clean_secret(secret_key or settings.PAYSTACK_SECRET_KEY)
        self.base_url = (base_url or settings.PAYSTACK_BASE_URL).rstrip("/")
        self.timeout = timeout

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _assert_configured(self) -> None:
        if not self.secret_key:
            raise PaystackError(
                "PAYSTACK_SECRET_KEY is not configured on the server. "
                "Add it to backend/.env and restart the server.",
                status_code=500,
            )
        if not self.secret_key.startswith("sk_"):
            raise PaystackError(
                "PAYSTACK_SECRET_KEY does not look like a Paystack secret key "
                "(must start with 'sk_'). Check backend/.env.",
                status_code=500,
            )

    async def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        self._assert_configured()

        url = f"{self.base_url}{path}"
        headers = self._headers()

        # Masked log so we can debug "invalid key" without leaking the key
        auth = headers["Authorization"]
        masked = auth[:14] + "..." + auth[-6:] if len(auth) > 25 else auth
        logger.debug("Paystack %s %s auth=%s", method, path, masked)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.request(method, url, headers=headers, **kwargs)

        # Try to decode JSON regardless of status code
        try:
            data = response.json()
        except Exception:
            data = {"status": False, "message": response.text[:500] or "Non-JSON response from Paystack"}

        if response.status_code >= 400 or not data.get("status", True):
            message = data.get("message") or f"Paystack request failed (HTTP {response.status_code})"
            logger.error(
                "Paystack error on %s %s: status=%s message=%s body=%s",
                method, path, response.status_code, message, str(data)[:500],
            )
            raise PaystackError(
                message,
                status_code=response.status_code,
                payload=data,
            )
        return data

    # ---------- Transactions ----------

    async def initialize_transaction(
        self,
        email: str,
        amount_pesewas: int,
        reference: str,
        currency: str = "GHS",
        callback_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        channels: Optional[list] = None,
    ) -> Dict[str, Any]:
        # Guard against 0 / negative amounts — Paystack rejects them
        amount_pesewas = int(amount_pesewas)
        if amount_pesewas <= 0:
            raise PaystackError(
                f"Invalid amount: {amount_pesewas} pesewas. Must be > 0.",
                status_code=400,
            )

        if not email or "@" not in email:
            raise PaystackError(
                f"Invalid email passed to Paystack: {email!r}",
                status_code=400,
            )

        payload: Dict[str, Any] = {
            "email": email,
            "amount": amount_pesewas,
            "reference": reference,
            "currency": currency,
        }

        cb = callback_url or settings.PAYSTACK_CALLBACK_URL
        if cb:
            payload["callback_url"] = cb

        if metadata:
            payload["metadata"] = metadata
        if channels:
            payload["channels"] = channels

        return await self._request("POST", "/transaction/initialize", json=payload)

    async def verify_transaction(self, reference: str) -> Dict[str, Any]:
        return await self._request("GET", f"/transaction/verify/{reference}")

    # ---------- Transfers ----------

    async def create_transfer_recipient(
        self,
        *,
        name: str,
        account_number: str,
        bank_code: str,
        currency: str = "GHS",
        type_: str = "ghipss",
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = {
            "type": type_,
            "name": name,
            "account_number": account_number,
            "bank_code": bank_code,
            "currency": currency,
        }
        if description:
            payload["description"] = description
        return await self._request("POST", "/transferrecipient", json=payload)

    async def initiate_transfer(
        self,
        *,
        amount_ghs: float,
        recipient_code: str,
        reason: str,
        reference: str,
        currency: str = "GHS",
    ) -> Dict[str, Any]:
        payload = {
            "source": "balance",
            "amount": int(round(amount_ghs * 100)),
            "recipient": recipient_code,
            "reason": reason,
            "reference": reference,
            "currency": currency,
        }
        return await self._request("POST", "/transfer", json=payload)

    async def verify_transfer(self, reference: str) -> Dict[str, Any]:
        return await self._request("GET", f"/transfer/verify/{reference}")

    # ---------- Webhooks ----------

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        if not signature:
            return False
        computed = hmac.new(
            self.secret_key.encode("utf-8"),
            payload,
            hashlib.sha512,
        ).hexdigest()
        return hmac.compare_digest(computed, signature)


paystack_client = PaystackClient()