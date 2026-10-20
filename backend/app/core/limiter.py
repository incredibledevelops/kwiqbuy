from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],  # only endpoints with @limiter.limit get limited
    storage_uri="memory://",  # swap for redis://... in production
)