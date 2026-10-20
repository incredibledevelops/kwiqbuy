from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# ---------------------------------------------------------------------------
# Resolve .env relative to THIS file, not the current working directory.
# backend/app/core/config.py  →  backend/.env
# ---------------------------------------------------------------------------
_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
_ENV_FILE = _BACKEND_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # ---------- App ----------
    APP_NAME: str = "KwiqBuy API"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    FRONTEND_URL: str = "http://localhost:3000"
    SITE_URL: str = "http://localhost:3000"

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ---------- Logging ----------
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = True

    # ---------- Sentry ----------
    SENTRY_DSN: str = ""
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1

    # ---------- MongoDB ----------
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "kwiqbuy"
    MONGODB_TRANSACTIONS_ENABLED: bool = True

    # ---------- Redis ----------
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL_SECONDS: int = 60
    SEARCH_CACHE_TTL_SECONDS: int = 900

    # ---------- JWT ----------
    JWT_SECRET_KEY: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    CUSTOMER_TOKEN_EXPIRE_DAYS: int = 30
    CUSTOMER_REFRESH_EXPIRE_DAYS: int = 90
    CUSTOMER_OTP_EXPIRE_MINUTES: int = 10
    TWO_FA_TEMP_TOKEN_EXPIRE_MINUTES: int = 5

    # ---------- Paystack ----------
    PAYSTACK_SECRET_KEY: str = ""
    PAYSTACK_PUBLIC_KEY: str = ""
    PAYSTACK_BASE_URL: str = "https://api.paystack.co"
    PAYSTACK_CALLBACK_URL: str = "http://localhost:3000/order/callback"

    PAYSTACK_TRANSFER_ENABLED: bool = False
    PAYSTACK_TRANSFER_TYPE: str = "ghipss"
    PAYOUT_SCHEDULE: str = "manual"
    PAYOUT_SCHEDULE_DAY: int = 1
    PAYOUT_SCHEDULE_HOUR: int = 9

    # ---------- CORS ----------
    CORS_ORIGINS: str = (
        "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000"
    )

    # ---------- Uploads ----------
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 5
    ALLOWED_IMAGE_TYPES: str = "image/jpeg,image/png,image/webp"
    EXIF_STRIP_ON_UPLOAD: bool = True
    MAX_CSV_IMPORT_ROWS: int = 1000

    # ---------- Business ----------
    DEFAULT_DELIVERY_FEE: float = 15.00
    CURRENCY: str = "GHS"
    FREE_DELIVERY_THRESHOLD: float = 100.0

    # ---------- Marketplace ----------
    DEFAULT_PLATFORM_COMMISSION_PCT: float = 15.0
    FOOD_COMMISSION_PCT: float = 20.0
    RETAIL_COMMISSION_PCT: float = 10.0
    MIN_VENDOR_PAYOUT_GHS: float = 50.0
    PLATFORM_DELIVERY_CUT_PCT: float = 20.0

    # ---------- Wallet ----------
    WALLET_ENABLED: bool = True
    WALLET_MIN_ORDER_FOR_APPLY: float = 1.0
    WALLET_MAX_COVERAGE_PCT: float = 100.0

    # ---------- Discount stacking ----------
    STACK_PROMO_AND_LOYALTY: bool = True
    STACK_WALLET_WITH_DISCOUNTS: bool = True
    MAX_TOTAL_DISCOUNT_PCT: float = 0.0

    # ---------- Marketplace behavior ----------
    ALLOW_MIXED_CARTS: bool = False
    FOOD_DEFAULT_RADIUS_KM: float = 15.0
    FOOD_MAX_RADIUS_KM: float = 50.0

    # ---------- Rider ----------
    RIDER_FEE_MODEL: str = "pct_of_delivery_fee"
    RIDER_FLAT_FEE_GHS: float = 8.0
    RIDER_PCT_OF_DELIVERY_FEE: float = 100.0
    RIDER_LOCATION_TTL_HOURS: int = 24
    RIDER_LOCATION_UPDATE_MIN_SECONDS: int = 10

    # ---------- Vendor apps ----------
    VENDOR_APPLICATION_TTL_DAYS: int = 30

    # ---------- Audit ----------
    AUDIT_LOG_RETENTION_DAYS: int = 730

    # ---------- Security ----------
    ADMIN_IP_ALLOWLIST_ENABLED: bool = False
    ENFORCE_CORS_IN_PRODUCTION: bool = True

    # ---------- Subscription tiers ----------
    VENDOR_TIERS_ENABLED: bool = True

    # ---------- Webhooks ----------
    WEBHOOKS_ENABLED: bool = True
    WEBHOOK_MAX_ATTEMPTS: int = 3
    WEBHOOK_RETRY_INTERVAL_SECONDS: int = 60
    WEBHOOK_TIMEOUT_SECONDS: float = 10.0
    WEBHOOK_MAX_PER_VENDOR: int = 10

    # ---------- 2FA ----------
    TWO_FA_ENABLED: bool = True
    TWO_FA_ISSUER: str = "KwiqBuy Admin"

    # ---------- PDF invoices ----------
    INVOICE_DIR: str = "uploads/invoices"

    # ---------- Email ----------
    RESEND_API_KEY: str = ""
    MAIL_FROM: str = "KwiqBuy <onboarding@resend.dev>"
    MAIL_FROM_NAME: str = "KwiqBuy"

    # ---------- SMS ----------
    ARKESEL_API_KEY: str = ""
    ARKESEL_SENDER_ID: str = "KwiqBuy"
    ARKESEL_BASE_URL: str = "https://sms.arkesel.com/api/v2"

    # ---------- Loyalty ----------
    LOYALTY_POINTS_PER_CEDI: int = 1
    LOYALTY_POINTS_TO_CEDI: float = 0.01
    LOYALTY_MIN_REDEEM: int = 100

    # ---------- Idempotency ----------
    IDEMPOTENCY_TTL_HOURS: int = 24

    # ---------- Rate limits ----------
    RATE_LIMIT_AUTH: str = "5/minute"
    RATE_LIMIT_OTP: str = "3/minute"
    RATE_LIMIT_ORDER: str = "20/minute"
    RATE_LIMIT_VENDOR_APPLICATION: str = "3/hour"
    RATE_LIMIT_VENDOR_PRODUCT_WRITE: str = "60/hour"
    RATE_LIMIT_NEARBY: str = "30/minute"
    RATE_LIMIT_BULK: str = "5/hour"
    RATE_LIMIT_RIDER_LOCATION: str = "120/minute"
    RATE_LIMIT_EXPORT: str = "10/hour"

    # ---------- Scheduler ----------
    SCHEDULER_ENABLED: bool = True

    # ---------- Support ----------
    SUPPORT_PHONE: str = "0534634845"
    SUPPORT_WHATSAPP: str = "233534634845"

    # ------------------------------------------------------------------
    # Normalizers
    # ------------------------------------------------------------------
    @field_validator("PAYSTACK_SECRET_KEY", "PAYSTACK_PUBLIC_KEY", mode="before")
    @classmethod
    def _strip_quotes_and_whitespace(cls, v):
        """
        Handles the common .env copy-paste traps:
            PAYSTACK_SECRET_KEY="sk_test_abc"    →  sk_test_abc
            PAYSTACK_SECRET_KEY='sk_test_abc'    →  sk_test_abc
            PAYSTACK_SECRET_KEY=sk_test_abc      →  sk_test_abc  (unchanged)
            PAYSTACK_SECRET_KEY=sk_test_abc\\r\\n  →  sk_test_abc
        """
        if v is None:
            return ""
        s = str(v).strip().replace("\r", "").replace("\n", "")
        if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
            s = s[1:-1].strip()
        return s

    @property
    def cors_origins_list(self) -> List[str]:
        raw = self.CORS_ORIGINS or ""
        out: list[str] = []
        for piece in raw.split(","):
            origin = piece.strip()
            if not origin:
                continue
            if len(origin) >= 2 and origin[0] == origin[-1] and origin[0] in ("'", '"'):
                origin = origin[1:-1].strip()
            origin = origin.rstrip("/")
            if origin:
                out.append(origin)
        return out

    @property
    def allowed_image_types_list(self) -> List[str]:
        return [t.strip() for t in self.ALLOWED_IMAGE_TYPES.split(",") if t.strip()]

    def commission_for_category(self, category: str) -> float:
        if category == "food":
            return float(self.FOOD_COMMISSION_PCT)
        if category == "retail":
            return float(self.RETAIL_COMMISSION_PCT)
        return float(self.DEFAULT_PLATFORM_COMMISSION_PCT)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

# ---------------------------------------------------------------------------
# Boot-time diagnostics — printed once, visible in uvicorn logs.
# ---------------------------------------------------------------------------
import logging as _logging

_log = _logging.getLogger(__name__)


def _mask(s: str) -> str:
    if not s:
        return "(empty)"
    if len(s) < 12:
        return "*" * len(s)
    return f"{s[:8]}...{s[-4:]}"


_log.info("Loaded .env from: %s", _ENV_FILE)
_log.info("PAYSTACK_SECRET_KEY: %s", _mask(settings.PAYSTACK_SECRET_KEY))
_log.info("PAYSTACK_PUBLIC_KEY: %s", _mask(settings.PAYSTACK_PUBLIC_KEY))
_log.info("PAYSTACK_BASE_URL: %s", settings.PAYSTACK_BASE_URL)
_log.info("PAYSTACK_CALLBACK_URL: %s", settings.PAYSTACK_CALLBACK_URL)

if not settings.PAYSTACK_SECRET_KEY:
    _log.warning(
        "PAYSTACK_SECRET_KEY is EMPTY. Payments will fail. "
        "Ensure .env exists at %s and contains PAYSTACK_SECRET_KEY=sk_test_...",
        _ENV_FILE,
    )
elif not settings.PAYSTACK_SECRET_KEY.startswith("sk_"):
    _log.warning(
        "PAYSTACK_SECRET_KEY does not start with 'sk_'. "
        "It may be a public key or a malformed value."
    )