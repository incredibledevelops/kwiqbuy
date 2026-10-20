"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Loader2, ClipboardList, ArrowRight } from "lucide-react";
import EmptyState from "@/components/ui/EmptyState";
import { vendorApi } from "@/lib/vendorApi";
import { formatGHS, formatDateTime } from "@/lib/utils";

const STATUS_OPTIONS = [
  { value: "", label: "All" },
  { value: "pending", label: "Pending" },
  { value: "accepted", label: "Accepted" },
  { value: "confirmed", label: "Confirmed" },
  { value: "preparing", label: "Preparing" },
  { value: "ready", label: "Ready" },
  { value: "packed", label: "Packed" },
  { value: "picked_up", label: "Picked up" },
  { value: "shipped", label: "Shipped" },
  { value: "in_transit", label: "In transit" },
  { value: "delivered", label: "Delivered" },
  { value: "rejected", label: "Rejected" },
  { value: "cancelled", label: "Cancelled" },
];

const STATUS_COLORS = {
  pending: "text-amber-400 bg-amber-500/10 border-amber-500/30",
  accepted: "text-blue-400 bg-blue-500/10 border-blue-500/30",
  confirmed: "text-blue-400 bg-blue-500/10 border-blue-500/30",
  preparing: "text-amber-400 bg-amber-500/10 border-amber-500/30",
  ready: "text-emerald-400 bg-emerald-500/10 border-emerald-500/30",
  packed: "text-emerald-400 bg-emerald-500/10 border-emerald-500/30",
  picked_up: "text-purple-400 bg-purple-500/10 border-purple-500/30",
  shipped: "text-purple-400 bg-purple-500/10 border-purple-500/30",
  in_transit: "text-purple-400 bg-purple-500/10 border-purple-500/30",
  delivered: "text-emerald-400 bg-emerald-500/10 border-emerald-500/30",
  rejected: "text-red-400 bg-red-500/10 border-red-500/30",
  cancelled: "text-red-400 bg-red-500/10 border-red-500/30",
};

export default function VendorOrdersPage() {
  const [status, setStatus] = useState("");
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      setLoading(true);
      setError("");
      try {
        const qs = status ? `?status=${status}&limit=200` : "?limit=200";
        const data = await vendorApi.get(`/api/v1/vendor/orders${qs}`);
        setOrders(Array.isArray(data) ? data : []);
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    })();
  }, [status]);

  const totals = useMemo(() => {
    return orders.reduce(
      (acc, o) => {
        acc.count += 1;
        acc.revenue += Number(o.vendor_payout || 0);
        return acc;
      },
      { count: 0, revenue: 0 }
    );
  }, [orders]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-heading text-3xl font-black text-white">Orders</h1>
        <p className="text-sm text-gray-400 mt-1">
          {totals.count} order{totals.count === 1 ? "" : "s"} ·{" "}
          {formatGHS(totals.revenue)} payout
        </p>
      </div>

      {/* Status filter chips */}
      <div className="flex gap-2 overflow-x-auto pb-2 no-scrollbar">
        {STATUS_OPTIONS.map((opt) => (
          <button
            key={opt.value || "all"}
            onClick={() => setStatus(opt.value)}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition-colors ${
              status === opt.value
                ? "bg-brand-primary text-white"
                : "bg-surface-card border border-surface-border text-gray-300 hover:text-white"
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
          {error}
        </div>
      )}

      {loading ? (
        <div className="py-16 text-center">
          <Loader2 className="w-8 h-8 text-brand-primary animate-spin mx-auto" />
        </div>
      ) : orders.length === 0 ? (
        <EmptyState
          icon={ClipboardList}
          title="No orders"
          message={status ? `No ${status} orders` : "Orders will appear here as they arrive."}
        />
      ) : (
        <div className="bg-surface-card border border-surface-border rounded-2xl overflow-hidden">
          <ul className="divide-y divide-surface-border">
            {orders.map((o) => (
              <li key={o.order_id}>
                <Link
                  href={`/vendor/orders/${o.order_id}`}
                  className="flex items-center gap-4 p-4 hover:bg-white/5 transition-colors"
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-mono text-xs text-brand-primary font-bold">
                        {o.reference}
                      </span>
                      <span
                        className={`text-[10px] px-2 py-0.5 rounded-md border font-bold uppercase ${
                          STATUS_COLORS[o.status] ||
                          "text-gray-400 bg-white/5 border-white/10"
                        }`}
                      >
                        {String(o.status).replace(/_/g, " ")}
                      </span>
                    </div>
                    <div className="text-sm text-white mt-1 truncate">
                      {o.customer_name} · {o.delivery_zone_name || "—"}
                    </div>
                    <div className="text-[11px] text-gray-500 mt-0.5">
                      {formatDateTime(o.created_at)} · {o.items_count} item
                      {o.items_count === 1 ? "" : "s"}
                    </div>
                  </div>
                  <div className="text-right shrink-0">
                    <div className="text-[10px] text-gray-500 uppercase tracking-wider font-bold">
                      Payout
                    </div>
                    <div className="text-brand-primary font-bold">
                      {formatGHS(o.vendor_payout)}
                    </div>
                  </div>
                  <ArrowRight className="w-4 h-4 text-gray-500 shrink-0" />
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}