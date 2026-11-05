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

    # ---------- App (Loaded from .env) ----------
    APP_NAME: str
    APP_ENV: str
    DEBUG: bool
    API_V1_PREFIX: str
    FRONTEND_URL: str
    SITE_URL: str

    HOST: str
    PORT: int

    # ---------- Logging ----------
    LOG_LEVEL: str
    LOG_JSON: bool

    # ---------- Sentry ----------
    SENTRY_DSN: str = ""
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1

    # ---------- MongoDB (Required from .env) ----------
    MONGODB_URL: str
    MONGODB_DB_NAME: str
    MONGODB_TRANSACTIONS_ENABLED: bool

    # ---------- Redis ----------
    REDIS_URL: str

    CACHE_TTL_SECONDS: int
    SEARCH_CACHE_TTL_SECONDS: int

    # ---------- JWT ----------
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    CUSTOMER_TOKEN_EXPIRE_DAYS: int
    CUSTOMER_REFRESH_EXPIRE_DAYS: int
    CUSTOMER_OTP_EXPIRE_MINUTES: int
    TWO_FA_TEMP_TOKEN_EXPIRE_MINUTES: int

    # ---------- Paystack ----------
    PAYSTACK_SECRET_KEY: str
    PAYSTACK_PUBLIC_KEY: str
    PAYSTACK_BASE_URL: str
    PAYSTACK_CALLBACK_URL: str

    PAYSTACK_TRANSFER_ENABLED: bool
    PAYSTACK_TRANSFER_TYPE: str
    PAYOUT_SCHEDULE: str
    PAYOUT_SCHEDULE_DAY: int
    PAYOUT_SCHEDULE_HOUR: int

    # ---------- CORS (Required from .env) ----------
    CORS_ORIGINS: str

    # ---------- Uploads ----------
    UPLOAD_DIR: str
    MAX_UPLOAD_SIZE_MB: int
    ALLOWED_IMAGE_TYPES: str
    EXIF_STRIP_ON_UPLOAD: bool
    MAX_CSV_IMPORT_ROWS: int

    # ---------- Business ----------
    DEFAULT_DELIVERY_FEE: float
    CURRENCY: str
    FREE_DELIVERY_THRESHOLD: float

    # ---------- Marketplace ----------
    DEFAULT_PLATFORM_COMMISSION_PCT: float
    FOOD_COMMISSION_PCT: float
    RETAIL_COMMISSION_PCT: float
    MIN_VENDOR_PAYOUT_GHS: float
    PLATFORM_DELIVERY_CUT_PCT: float

    # ---------- Wallet ----------
    WALLET_ENABLED: bool
    WALLET_MIN_ORDER_FOR_APPLY: float
    WALLET_MAX_COVERAGE_PCT: float

    # ---------- Discount stacking ----------
    STACK_PROMO_AND_LOYALTY: bool
    STACK_WALLET_WITH_DISCOUNTS: bool
    MAX_TOTAL_DISCOUNT_PCT: float

    # ---------- Marketplace behavior ----------
    ALLOW_MIXED_CARTS: bool
    FOOD_DEFAULT_RADIUS_KM: float
    FOOD_MAX_RADIUS_KM: float

    # ---------- Rider ----------
    RIDER_FEE_MODEL: str
    RIDER_FLAT_FEE_GHS: float
    RIDER_PCT_OF_DELIVERY_FEE: float
    RIDER_LOCATION_TTL_HOURS: int
    RIDER_LOCATION_UPDATE_MIN_SECONDS: int

    # ---------- Vendor apps ----------
    VENDOR_APPLICATION_TTL_DAYS: int

    # ---------- Audit ----------
    AUDIT_LOG_RETENTION_DAYS: int

    # ---------- Security ----------
    ADMIN_IP_ALLOWLIST_ENABLED: bool
    ENFORCE_CORS_IN_PRODUCTION: bool

    # ---------- Subscription tiers ----------
    VENDOR_TIERS_ENABLED: bool

    # ---------- Webhooks ----------
    WEBHOOKS_ENABLED: bool
    WEBHOOK_MAX_ATTEMPTS: int
    WEBHOOK_RETRY_INTERVAL_SECONDS: int
    WEBHOOK_TIMEOUT_SECONDS: float
    WEBHOOK_MAX_PER_VENDOR: int

    # ---------- 2FA ----------
    TWO_FA_ENABLED: bool
    TWO_FA_ISSUER: str

    # ---------- PDF invoices ----------
    INVOICE_DIR: str

    # ---------- Email ----------
    RESEND_API_KEY: str = ""
    MAIL_FROM: str
    MAIL_FROM_NAME: str

    # ---------- SMS ----------
    ARKESEL_API_KEY: str = ""
    ARKESEL_SENDER_ID: str
    ARKESEL_BASE_URL: str

    # ---------- Loyalty ----------
    LOYALTY_POINTS_PER_CEDI: int
    LOYALTY_POINTS_TO_CEDI: float
    LOYALTY_MIN_REDEEM: int

    # ---------- Idempotency ----------
    IDEMPOTENCY_TTL_HOURS: int

    # ---------- Rate limits ----------
    RATE_LIMIT_AUTH: str
    RATE_LIMIT_OTP: str
    RATE_LIMIT_ORDER: str
    RATE_LIMIT_VENDOR_APPLICATION: str
    RATE_LIMIT_VENDOR_PRODUCT_WRITE: str
    RATE_LIMIT_NEARBY: str
    RATE_LIMIT_BULK: str
    RATE_LIMIT_RIDER_LOCATION: str
    RATE_LIMIT_EXPORT: str

    # ---------- Scheduler ----------
    SCHEDULER_ENABLED: bool

    # ---------- Support ----------
    SUPPORT_PHONE: str
    SUPPORT_WHATSAPP: str

    # ------------------------------------------------------------------
    # Normalizers
    # ------------------------------------------------------------------
    @field_validator("MONGODB_URL", "PAYSTACK_SECRET_KEY", "PAYSTACK_PUBLIC_KEY", mode="before")
    @classmethod
    def _strip_quotes_and_whitespace(cls, v):
        """
        Handles common .env copy-paste traps (quotes, trailing spaces, newline chars).
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
_log.info("MONGODB_URL: %s", _mask(settings.MONGODB_URL))
_log.info("CORS_ORIGINS: %s", settings.CORS_ORIGINS)
_log.info("PAYSTACK_SECRET_KEY: %s", _mask(settings.PAYSTACK_SECRET_KEY))
_log.info("PAYSTACK_PUBLIC_KEY: %s", _mask(settings.PAYSTACK_PUBLIC_KEY))
_log.info("PAYSTACK_BASE_URL: %s", settings.PAYSTACK_BASE_URL)
_log.info("PAYSTACK_CALLBACK_URL: %s", settings.PAYSTACK_CALLBACK_URL)

if not settings.MONGODB_URL:
    _log.error("MONGODB_URL is missing. Database connection will fail.")

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
