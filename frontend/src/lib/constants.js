export const ORDER_TYPES = {
  FOOD: "food",
  RETAIL: "retail",
  MIXED: "mixed",
};

export const ORDER_STATUS = {
  PENDING: "pending",
  PAID: "paid",
  PREPARING: "preparing",
  READY: "ready",
  OUT_FOR_DELIVERY: "out_for_delivery",
  SHIPPED: "shipped",
  IN_TRANSIT: "in_transit",
  DELIVERED: "delivered",
  CANCELLED: "cancelled",
  FAILED: "failed",
  REFUNDED: "refunded",
};

export const VENDOR_STATUS = {
  PENDING: "pending",
  ACTIVE: "active",
  SUSPENDED: "suspended",
  CLOSED: "closed",
};

export const VENDOR_CATEGORY = {
  FOOD: "food",
  RETAIL: "retail",
};

export const ORDER_STATUS_META = {
  pending: { label: "Pending", color: "text-amber-400", bg: "bg-amber-500/10" },
  paid: { label: "Confirmed", color: "text-emerald-400", bg: "bg-emerald-500/10" },
  preparing: { label: "Preparing", color: "text-amber-400", bg: "bg-amber-500/10" },
  ready: { label: "Ready", color: "text-blue-400", bg: "bg-blue-500/10" },
  out_for_delivery: { label: "On the way", color: "text-blue-400", bg: "bg-blue-500/10" },
  shipped: { label: "Shipped", color: "text-blue-400", bg: "bg-blue-500/10" },
  in_transit: { label: "In transit", color: "text-blue-400", bg: "bg-blue-500/10" },
  delivered: { label: "Delivered", color: "text-emerald-400", bg: "bg-emerald-500/10" },
  cancelled: { label: "Cancelled", color: "text-red-400", bg: "bg-red-500/10" },
  failed: { label: "Failed", color: "text-red-400", bg: "bg-red-500/10" },
  refunded: { label: "Refunded", color: "text-sky-400", bg: "bg-sky-500/10" },
};

export const WEBHOOK_EVENTS = [
  { value: "order.created", label: "Order created" },
  { value: "order.status_changed", label: "Order status changed" },
  { value: "order.delivered", label: "Order delivered" },
  { value: "payout.paid", label: "Payout paid" },
  { value: "subscription.activated", label: "Subscription activated" },
  { value: "review.posted", label: "Review posted" },
];