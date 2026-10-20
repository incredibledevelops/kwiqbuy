"""
Cart validation endpoint — cheap pre-flight check before checkout.
Enforces the mixed-cart rule at add-to-cart time so customers get an
early error rather than at payment.
"""
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings
from app.crud import product as product_crud
from app.crud import vendor as vendor_crud

router = APIRouter(prefix="/cart", tags=["Cart"])


class CartValidateIn(BaseModel):
    product_ids: List[str] = Field(min_length=1, max_length=200)


class CartValidateOut(BaseModel):
    valid: bool
    order_type: str  # food | retail | mixed
    message: str
    vendor_categories: dict[str, str] = Field(default_factory=dict)


@router.post("/validate", response_model=CartValidateOut)
async def validate_cart(payload: CartValidateIn):
    """
    Given a list of product IDs, return whether they can coexist in one
    checkout. Enforces ALLOW_MIXED_CARTS.
    """
    categories: set[str] = set()
    vendor_categories: dict[str, str] = {}

    for pid in payload.product_ids:
        p = await product_crud.get_product(pid)
        if not p:
            raise HTTPException(400, f"Product not found: {pid}")
        v = await vendor_crud.get_by_id(str(p.vendor_id))
        if not v:
            raise HTTPException(400, f"Vendor not found for product: {pid}")
        categories.add(v.business_category.value)
        vendor_categories[str(v.id)] = v.business_category.value

    if len(categories) == 1:
        return CartValidateOut(
            valid=True,
            order_type=categories.pop(),
            message="Cart is valid.",
            vendor_categories=vendor_categories,
        )

    if settings.ALLOW_MIXED_CARTS:
        return CartValidateOut(
            valid=True,
            order_type="mixed",
            message="Cart contains food and retail items.",
            vendor_categories=vendor_categories,
        )

    return CartValidateOut(
        valid=False,
        order_type="mixed",
        message=(
            "You can't mix food and retail items in one order. "
            "Please check out separately."
        ),
        vendor_categories=vendor_categories,
    )
