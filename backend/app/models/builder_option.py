from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from beanie import Document
from pydantic import Field


class BuilderOptionType(str, Enum):
    BASE = "base"
    PROTEIN = "protein"
    SAUCE = "sauce"
    TOPPING = "topping"


class BuilderOption(Document):
    type: BuilderOptionType
    name: str
    description: Optional[str] = None
    price: float = Field(ge=0, default=0.0)
    image_url: Optional[str] = None
    is_default: bool = False
    is_available: bool = True
    display_order: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "builder_options"