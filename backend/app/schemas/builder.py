from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.builder_option import BuilderOptionType


class BuilderOptionBase(BaseModel):
    type: BuilderOptionType
    name: str
    description: Optional[str] = None
    price: float = Field(default=0.0, ge=0)
    image_url: Optional[str] = None
    is_default: bool = False
    is_available: bool = True
    display_order: int = 0


class BuilderOptionCreate(BuilderOptionBase):
    pass


class BuilderOptionUpdate(BaseModel):
    type: Optional[BuilderOptionType] = None
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    is_default: Optional[bool] = None
    is_available: Optional[bool] = None
    display_order: Optional[int] = None


class BuilderOptionOut(BuilderOptionBase):
    id: str
    created_at: datetime
    updated_at: datetime


class BuilderGroupedOut(BaseModel):
    bases: list[BuilderOptionOut]
    proteins: list[BuilderOptionOut]
    sauces: list[BuilderOptionOut]
    toppings: list[BuilderOptionOut]