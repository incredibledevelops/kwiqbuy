from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.webhook import WebhookEvent, WebhookStatus


class WebhookCreate(BaseModel):
    url: str = Field(min_length=8, max_length=500)
    description: Optional[str] = Field(default=None, max_length=200)
    events: Optional[List[WebhookEvent]] = None


class WebhookUpdate(BaseModel):
    url: Optional[str] = Field(default=None, min_length=8, max_length=500)
    description: Optional[str] = None
    events: Optional[List[WebhookEvent]] = None
    is_active: Optional[bool] = None


class WebhookOut(BaseModel):
    id: str
    url: str
    description: Optional[str] = None
    events: List[str]
    is_active: bool
    last_success_at: Optional[datetime] = None
    last_failure_at: Optional[datetime] = None
    consecutive_failures: int = 0
    created_at: datetime
    updated_at: datetime


class WebhookWithSecretOut(WebhookOut):
    secret: str


class WebhookDeliveryOut(BaseModel):
    id: str
    event: str
    url: str
    status: WebhookStatus
    attempts: int
    response_status: Optional[int] = None
    response_body: Optional[str] = None
    error: Optional[str] = None
    next_attempt_at: Optional[datetime] = None
    created_at: datetime


class WebhookTestOut(BaseModel):
    delivered: bool
    status_code: Optional[int] = None
    response_body: Optional[str] = None
    error: Optional[str] = None
