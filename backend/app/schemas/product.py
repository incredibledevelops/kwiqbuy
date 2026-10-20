from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.product import ProductType


class VariantOptionIn(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    values: List[str] = Field(min_length=1, max_length=30)


class ProductVariantIn(BaseModel):
    sku: Optional[str] = Field(default=None, max_length=64)
    selections: dict[str, str] = Field(default_factory=dict)
    price: float = Field(ge=0)
    stock_count: Optional[int] = Field(default=None, ge=0)
    image_url: Optional[str] = None
    is_available: bool = True


class ProductVariantOut(BaseModel):
    sku: Optional[str] = None
    selections: dict[str, str] = Field(default_factory=dict)
    price: float
    stock_count: Optional[int] = None
    image_url: Optional[str] = None
    is_available: bool = True


class ProductBase(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    slug: Optional[str] = None
    description: Optional[str] = Field(default=None, max_length=2000)
    price: float = Field(ge=0)
    category_id: str
    product_type: ProductType = ProductType.SIMPLE
    image_url: Optional[str] = None
    image_urls: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    brand: Optional[str] = None
    weight_grams: Optional[int] = Field(default=None, ge=0)
    is_available: bool = True
    stock_count: Optional[int] = Field(default=None, ge=0)
    low_stock_threshold: int = Field(default=5, ge=0)
    variant_options: List[VariantOptionIn] = Field(default_factory=list)
    variants: List[ProductVariantIn] = Field(default_factory=list)
    display_order: int = 0


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    slug: Optional[str] = None
    description: Optional[str] = Field(default=None, max_length=2000)
    price: Optional[float] = Field(default=None, ge=0)
    category_id: Optional[str] = None
    product_type: Optional[ProductType] = None
    image_url: Optional[str] = None
    image_urls: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    brand: Optional[str] = None
    weight_grams: Optional[int] = Field(default=None, ge=0)
    is_available: Optional[bool] = None
    stock_count: Optional[int] = Field(default=None, ge=0)
    low_stock_threshold: Optional[int] = Field(default=None, ge=0)
    variant_options: Optional[List[VariantOptionIn]] = None
    variants: Optional[List[ProductVariantIn]] = None
    display_order: Optional[int] = None


class ProductOut(ProductBase):
    id: str
    vendor_id: str
    created_at: datetime
    updated_at: datetime
    average_rating: float = 0.0
    total_reviews: int = 0


class ProductPublicOut(BaseModel):
    id: str
    vendor_id: str
    vendor_name: Optional[str] = None
    vendor_category: Optional[str] = None
    name: str
    slug: str
    description: Optional[str] = None
    price: float
    category_id: str
    category_name: Optional[str] = None
    product_type: ProductType = ProductType.SIMPLE
    image_url: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    brand: Optional[str] = None
    is_available: bool = True
    variant_options: List[VariantOptionIn] = Field(default_factory=list)
    variants: List[ProductVariantOut] = Field(default_factory=list)
    average_rating: float = 0.0
    total_reviews: int = 0


class StockToggle(BaseModel):
    is_available: bool
