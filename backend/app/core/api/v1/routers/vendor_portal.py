from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.core.config import settings
from app.core.deps import get_current_vendor
from app.core.limiter import limiter
from app.crud import analytics as analytics_crud
from app.crud import order as order_crud
from app.crud import payout as payout_crud
from app.crud import product as product_crud
from app.crud import promo_code as promo_crud
from app.crud import vendor as vendor_crud
from app.models.order import VendorOrderStatus
from app.models.payout import PayoutMethod
from app.models.promo_code import PromoCode
from app.models.user import User
from app.schemas.analytics import (
    RevenuePoint,
    StatusCount,
    TopSeller,
    VendorAnalyticsOverview,
    VendorAnalyticsSummary,
)
from app.schemas.order import (
    OrderVendorListOut,
    VendorOrderOut,
    VendorOrderStatusUpdate,
)
from app.schemas.payout import VendorPayoutOut, VendorPayoutRequestIn
from app.schemas.product import ProductCreate, ProductOut, ProductUpdate, StockToggle
from app.schemas.promo_code import (
    PromoCodeCreateVendor,
    PromoCodeOut,
    PromoCodeUpdate,
)
from app.schemas.vendor import VendorSelfOut, VendorUpdate

router = APIRouter(prefix="/vendor", tags=["Vendor Portal"])


async def _load_vendor(user: User):
    if not user.vendor_id:
        raise HTTPException(403, "This account is not linked to a vendor")
    v = await vendor_crud.get_by_id(str(user.vendor_id))
    if not v:
        raise HTTPException(404, "Vendor not found")
    return v


def _product_out(p) -> ProductOut:
    return ProductOut(
        id=str(p.id),
        vendor_id=str(p.vendor_id),
        name=p.name,
        slug=p.slug,
        description=p.description,
        price=p.price,
        category_id=str(p.category_id),
        product_type=p.product_type,
        image_url=p.image_url,
        image_urls=p.image_urls,
        tags=p.tags,
        brand=p.brand,
        weight_grams=p.weight_grams,
        is_available=p.is_available,
        stock_count=p.stock_count,
        low_stock_threshold=p.low_stock_threshold,
        variant_options=[
            {"name": o.name, "values": o.values} for o in p.variant_options
        ],
        variants=[
            {
                "sku": v.sku,
                "selections": v.selections,
                "price": v.price,
                "stock_count": v.stock_count,
                "image_url": v.image_url,
                "is_available": v.is_available,
            }
            for v in p.variants
        ],
        display_order=p.display_order,
        average_rating=p.average_rating,
        total_reviews=p.total_reviews,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


def _vendor_order_out(order, vo) -> VendorOrderOut:
    return VendorOrderOut(
        vendor_id=str(vo.vendor_id),
        vendor_name=vo.vendor_name,
        vendor_category=getattr(vo, "vendor_category", "food"),
        items=[
            {
                "product_id": str(i.product_id) if i.product_id else None,
                "variant_sku": getattr(i, "variant_sku", None),
                "variant_selections": getattr(i, "variant_selections", None),
                "name": i.name,
                "unit_price": i.unit_price,
                "quantity": i.quantity,
                "is_custom_bowl": i.is_custom_bowl,
                "customizations": i.customizations,
            }
            for i in vo.items
        ],
        subtotal=vo.subtotal,
        commission_pct=vo.commission_pct,
        platform_fee=vo.platform_fee,
        vendor_payout=vo.vendor_payout,
        status=vo.status,
        status_history=vo.status_history,
        rejection_reason=vo.rejection_reason,
        accepted_at=getattr(vo, "accepted_at", None),
        ready_at=getattr(vo, "ready_at", None),
        picked_up_at=getattr(vo, "picked_up_at", None),
        packed_at=getattr(vo, "packed_at", None),
        shipped_at=getattr(vo, "shipped_at", None),
        delivered_at=getattr(vo, "delivered_at", None),
    )


def _promo_out(p: PromoCode) -> PromoCodeOut:
    return PromoCodeOut(
        id=str(p.id),
        vendor_id=str(p.vendor_id) if p.vendor_id else None,
        code=p.code,
        description=p.description,
        discount_type=p.discount_type,
        discount_value=p.discount_value,
        min_order_total=p.min_order_total,
        max_discount=p.max_discount,
        usage_limit=p.usage_limit,
        per_customer_limit=p.per_customer_limit,
        times_used=p.times_used,
        valid_from=p.valid_from,
        valid_until=p.valid_until,
        is_active=p.is_active,
        created_by=p.created_by,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


def _payout_out(p) -> VendorPayoutOut:
    return VendorPayoutOut(
        id=str(p.id),
        vendor_id=str(p.vendor_id),
        vendor_name=p.vendor_name,
        gross_sales=p.gross_sales,
        platform_fees=p.platform_fees,
        net_payout=p.net_payout,
        currency=p.currency,
        period_start=p.period_start,
        period_end=p.period_end,
        order_count=len(p.vendor_order_ids),
        status=p.status,
        method=p.method,
        paystack_transfer_code=p.paystack_transfer_code,
        paystack_transfer_reference=p.paystack_transfer_reference,
        failure_reason=p.failure_reason,
        requested_by=p.requested_by,
        processed_by=p.processed_by,
        created_at=p.created_at,
        processed_at=p.processed_at,
        paid_at=p.paid_at,
    )


@router.get("/me", response_model=VendorSelfOut)
async def get_my_vendor(user: User = Depends(get_current_vendor)):
    v = await _load_vendor(user)
    return VendorSelfOut(
        id=str(v.id),
        business_name=v.business_name,
        slug=v.slug,
        business_category=v.business_category,
        business_subtype=v.business_subtype,
        description=v.description,
        logo_url=v.logo_url,
        banner_url=v.banner_url,
        contact_email=v.contact_email,
        contact_phone=v.contact_phone,
        pickup_address=v.pickup_address,
        pickup_lat=v.pickup_lat,
        pickup_lng=v.pickup_lng,
        delivery_radius_km=v.delivery_radius_km,
        prep_minutes=v.prep_minutes,
        status=v.status,
        commission_pct_override=v.commission_pct_override,
        average_rating=v.average_rating,
        total_reviews=v.total_reviews,
        total_orders=v.total_orders,
        available_balance=v.available_balance,
        total_gross_sales=v.total_gross_sales,
        lifetime_platform_fees=v.lifetime_platform_fees,
        lifetime_paid_out=v.lifetime_paid_out,
        payout_recipient_type=v.payout_recipient_type,
        payout_account_name=v.payout_account_name,
        payout_account_number=v.payout_account_number,
        payout_bank_code=v.payout_bank_code,
        payout_mobile_provider=v.payout_mobile_provider,
        payout_recipient_code=v.payout_recipient_code,
        created_at=v.created_at,
        updated_at=v.updated_at,
        approved_at=v.approved_at,
    )


@router.patch("/me", response_model=VendorSelfOut)
async def update_my_vendor(
    payload: VendorUpdate,
    request: Request,
    user: User = Depends(get_current_vendor),
):
    v = await _load_vendor(user)
    await vendor_crud.update_vendor(
        v,
        payload.model_dump(exclude_unset=True),
        actor_id=str(user.id),
        actor_email=user.email,
        request=request,
    )
    return await get_my_vendor(user)


@router.get("/products", response_model=list[ProductOut])
async def my_products(
    available_only: bool = False,
    search: str | None = None,
    user: User = Depends(get_current_vendor),
):
    v = await _load_vendor(user)
    products = await product_crud.list_products(
        vendor_id=str(v.id),
        available_only=available_only,
        search=search,
        limit=500,
    )
    return [_product_out(p) for p in products]


@router.post("/products", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_VENDOR_PRODUCT_WRITE)
async def create_my_product(
    request: Request,
    payload: ProductCreate,
    user: User = Depends(get_current_vendor),
):
    v = await _load_vendor(user)
    from app.crud import category as category_crud
    cat = await category_crud.get_category(payload.category_id)
    if not cat:
        raise HTTPException(400, "Invalid category_id")
    product = await product_crud.create_product(str(v.id), payload.model_dump())
    return _product_out(product)


@router.get("/products/{product_id}", response_model=ProductOut)
async def get_my_product(
    product_id: str,
    user: User = Depends(get_current_vendor),
):
    v = await _load_vendor(user)
    p = await product_crud.get_product(product_id)
    if not p or p.vendor_id != v.id:
        raise HTTPException(404, "Product not found")
    return _product_out(p)


@router.patch("/products/{product_id}", response_model=ProductOut)
async def update_my_product(
    product_id: str,
    payload: ProductUpdate,
    user: User = Depends(get_current_vendor),
):
    v = await _load_vendor(user)
    p = await product_crud.get_product(product_id)
    if not p or p.vendor_id != v.id:
        raise HTTPException(404, "Product not found")
    p = await product_crud.update_product(p, payload.model_dump(exclude_unset=True))
    return _product_out(p)


@router.patch("/products/{product_id}/stock", response_model=ProductOut)
async def toggle_my_product_stock(
    product_id: str,
    payload: StockToggle,
    user: User = Depends(get_current_vendor),
):
    v = await _load_vendor(user)
    p = await product_crud.get_product(product_id)
    if not p or p.vendor_id != v.id:
        raise HTTPException(404, "Product not found")
    p = await product_crud.toggle_stock(p, payload.is_available)
    return _product_out(p)


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_product(
    product_id: str,
    user: User = Depends(get_current_vendor),
):
    v = await _load_vendor(user)
    p = await product_crud.get_product(product_id)
    if not p or p.vendor_id != v.id:
        raise HTTPException(404, "Product not found")
    await product_crud.delete_product(p)


@router.get("/orders", response_model=list[OrderVendorListOut])
async def my_orders(
    status_filter: VendorOrderStatus | None = Query(None, alias="status"),
    limit: int = Query(100, ge=1, le=500),
    skip: int = Query(0, ge=0),
    user: User = Depends(get_current_vendor),
):
    v = await _load_vendor(user)
    orders = await order_crud.list_orders_for_vendor(
        str(v.id),
        statuses=[status_filter] if status_filter else None,
        limit=limit,
        skip=skip,
    )
    out: list[OrderVendorListOut] = []
    for o in orders:
        for vo in o.vendor_orders:
            if vo.vendor_id != v.id:
                continue
            if status_filter and vo.status != status_filter:
                continue
            out.append(
                OrderVendorListOut(
                    order_id=str(o.id),
                    reference=o.reference,
                    order_type=o.order_type,
                    customer_name=o.customer.full_name,
                    delivery_zone_name=o.delivery_zone_name,
                    items_count=sum(i.quantity for i in vo.items),
                    subtotal=vo.subtotal,
                    platform_fee=vo.platform_fee,
                    vendor_payout=vo.vendor_payout,
                    status=vo.status,
                    created_at=o.created_at,
                )
            )
    return out


@router.get("/orders/{order_id}", response_model=VendorOrderOut)
async def get_order_slice(
    order_id: str,
    user: User = Depends(get_current_vendor),
):
    v = await _load_vendor(user)
    order = await order_crud.get_order(order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    for vo in order.vendor_orders:
        if vo.vendor_id == v.id:
            return _vendor_order_out(order, vo)
    raise HTTPException(404, "This order has no slice for your vendor")


@router.patch("/orders/{order_id}/status", response_model=VendorOrderOut)
async def advance_order_slice(
    order_id: str,
    payload: VendorOrderStatusUpdate,
    user: User = Depends(get_current_vendor),
):
    v = await _load_vendor(user)
    order = await order_crud.get_order(order_id)
    if not order:
        raise HTTPException(404, "Order not found")

    try:
        order = await order_crud.update_vendor_order_status(
            order,
            str(v.id),
            payload.status,
            by=user.email,
            note=payload.note,
            reason=payload.reason,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

    for vo in order.vendor_orders:
        if vo.vendor_id == v.id:
            return _vendor_order_out(order, vo)
    raise HTTPException(500, "Vendor slice disappeared")


@router.get("/analytics/overview", response_model=VendorAnalyticsOverview)
async def my_analytics(
    days: int = Query(30, ge=1, le=365),
    user: User = Depends(get_current_vendor),
):
    v = await _load_vendor(user)
    start, end = analytics_crud.default_range(days=days)
    summary = await analytics_crud.vendor_summary(str(v.id), start, end)
    daily = await analytics_crud.daily_series(start, end, vendor_id=str(v.id))
    status_bd = await analytics_crud.status_breakdown(start, end, vendor_id=str(v.id))
    top = await analytics_crud.top_sellers(start, end, limit=5, vendor_id=str(v.id))
    return VendorAnalyticsOverview(
        summary=VendorAnalyticsSummary(**summary),
        daily=[RevenuePoint(**d) for d in daily],
        status_breakdown=[StatusCount(**s) for s in status_bd],
        top_sellers=[TopSeller(**t) for t in top],
    )


@router.get("/promos", response_model=list[PromoCodeOut])
async def my_promos(user: User = Depends(get_current_vendor)):
    v = await _load_vendor(user)
    promos = await promo_crud.list_promos(vendor_id=str(v.id))
    return [_promo_out(p) for p in promos if p.vendor_id == v.id]


@router.post("/promos", response_model=PromoCodeOut, status_code=201)
async def create_promo(
    payload: PromoCodeCreateVendor,
    user: User = Depends(get_current_vendor),
):
    v = await _load_vendor(user)
    if await promo_crud.get_by_code(payload.code):
        raise HTTPException(409, "A promo with that code already exists")
    data = payload.model_dump()
    data["vendor_id"] = str(v.id)
    promo = await promo_crud.create_promo(data, created_by=f"vendor:{v.id}")
    return _promo_out(promo)


@router.patch("/promos/{promo_id}", response_model=PromoCodeOut)
async def update_promo(
    promo_id: str,
    payload: PromoCodeUpdate,
    user: User = Depends(get_current_vendor),
):
    v = await _load_vendor(user)
    promo = await promo_crud.get_by_id(promo_id)
    if not promo or promo.vendor_id != v.id:
        raise HTTPException(404, "Promo not found")
    promo = await promo_crud.update_promo(promo, payload.model_dump(exclude_unset=True))
    return _promo_out(promo)


@router.delete("/promos/{promo_id}", status_code=204)
async def delete_promo(
    promo_id: str,
    user: User = Depends(get_current_vendor),
):
    v = await _load_vendor(user)
    promo = await promo_crud.get_by_id(promo_id)
    if not promo or promo.vendor_id != v.id:
        raise HTTPException(404, "Promo not found")
    await promo_crud.delete_promo(promo)


@router.get("/payouts", response_model=list[VendorPayoutOut])
async def my_payouts(
    limit: int = Query(100, ge=1, le=500),
    skip: int = Query(0, ge=0),
    user: User = Depends(get_current_vendor),
):
    v = await _load_vendor(user)
    payouts = await payout_crud.list_for_vendor(str(v.id), limit=limit, skip=skip)
    return [_payout_out(p) for p in payouts]


@router.post("/payouts/request", response_model=VendorPayoutOut, status_code=201)
async def request_payout(
    payload: VendorPayoutRequestIn,
    request: Request,
    user: User = Depends(get_current_vendor),
):
    v = await _load_vendor(user)
    
    if not v.payout_recipient_code:
        raise HTTPException(
            400, 
            "No payout recipient configured. Please add your Paystack recipient code in your profile."
        )

    try:
        p = await payout_crud.request_payout(
            v,
            requested_by=f"vendor:{v.id}",
            method=PayoutMethod.PAYSTACK_TRANSFER,
            request=request,
        )
    except ValueError as e:
        # This catches "No settled earnings available for payout"
        raise HTTPException(400, str(e))
        
    return _payout_out(p)