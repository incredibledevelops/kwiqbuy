"""
CORS origin validation + startup logging.

We log the resolved origin list at boot so it's visible in uvicorn
output. If you ever wonder "why is my frontend getting CORS errors?",
check the uvicorn log for this line.
"""
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


def validate_cors_configuration() -> None:
    origins = settings.cors_origins_list

    logger.info("CORS configured origins: %s", origins)

    if "*" in origins:
        if settings.APP_ENV == "production" and settings.ENFORCE_CORS_IN_PRODUCTION:
            raise RuntimeError(
                "CORS_ORIGINS contains '*' but APP_ENV=production. "
                "Wildcard CORS with credentials is unsafe. "
                "Set explicit origins or set ENFORCE_CORS_IN_PRODUCTION=False."
            )
        if settings.APP_ENV == "production":
            logger.warning(
                "CORS_ORIGINS contains '*' in production — this is discouraged."
            )
        else:
            logger.warning("CORS wildcard allowed (dev only).")

    if not origins:
        logger.warning(
            "CORS_ORIGINS is empty. No cross-origin requests will be allowed."
        )