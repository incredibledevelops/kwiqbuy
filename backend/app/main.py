import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.v1.router import api_router
from app.api.v1.routers import ops as ops_router
from app.core.cache import cache
from app.core.config import settings
from app.core.cors import validate_cors_configuration
from app.core.database import close_db, init_db
from app.core.limiter import limiter
from app.core.logging_config import configure_logging, init_sentry
from app.core.scheduler import start_scheduler, stop_scheduler
from app.models import ALL_DOCUMENTS

configure_logging()
init_sentry()
validate_cors_configuration()

log = logging.getLogger(__name__)


def _docs_enabled() -> bool:
    if settings.APP_ENV != "production":
        return True
    return bool(settings.DEBUG)


@asynccontextmanager
async def lifespan(application: FastAPI):
    await init_db(ALL_DOCUMENTS)
    await cache.init()
    for sub in (
        "products",
        "categories",
        "vendors",
        "reviews",
        "builder",
        "vendor_applications",
    ):
        os.makedirs(os.path.join(settings.UPLOAD_DIR, sub), exist_ok=True)
    os.makedirs(settings.INVOICE_DIR, exist_ok=True)
    start_scheduler()
    yield
    stop_scheduler()
    await cache.close()
    await close_db()


_show_docs = _docs_enabled()

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description=(
        "KwiqBuy marketplace API — vendors, products, multi-vendor orders, "
        "Paystack payments & vendor payouts, commissions, and analytics."
    ),
    docs_url="/docs" if _show_docs else None,
    redoc_url="/redoc" if _show_docs else None,
    openapi_url="/openapi.json" if _show_docs else None,
    lifespan=lifespan,
    contact={"name": "KwiqBuy Support", "phone": settings.SUPPORT_PHONE},
)

app.state.limiter = limiter

# Middleware ordering in Starlette is LIFO — the LAST added runs FIRST.
# We add SlowAPI first, then CORS last so CORS wraps everything.
app.add_middleware(SlowAPIMiddleware)

log.info(
    "Registering CORSMiddleware origins=%s credentials=%s",
    settings.cors_origins_list,
    True,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["*"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining"],
    max_age=600,
)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please slow down."},
    )


os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount(
    "/uploads",
    StaticFiles(directory=settings.UPLOAD_DIR),
    name="uploads",
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    if settings.DEBUG:
        import traceback
        traceback.print_exc()
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(ops_router.router)
app.include_router(api_router, prefix=settings.API_V1_PREFIX)