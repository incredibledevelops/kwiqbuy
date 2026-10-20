from app.schemas.order import OrderItemOut, VendorOrderOut


def to_vendor_order_public(vo) -> VendorOrderOut:
    return VendorOrderOut(
        vendor_id=str(vo.vendor_id),
        vendor_name=vo.vendor_name,
        vendor_category=getattr(vo, "vendor_category", "food"),
        items=[
            OrderItemOut(
                product_id=str(i.product_id) if i.product_id else None,
                variant_sku=getattr(i, "variant_sku", None),
                variant_selections=getattr(i, "variant_selections", None),
                name=i.name,
                unit_price=i.unit_price,
                quantity=i.quantity,
                is_custom_bowl=i.is_custom_bowl,
                customizations=i.customizations,
            )
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
