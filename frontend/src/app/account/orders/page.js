"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Package,
  AlertCircle,
  Loader2,
  Utensils,
  RefreshCw,
} from "lucide-react";
import Button from "@/components/ui/Button";
import EmptyState from "@/components/ui/EmptyState";
import { API_URL } from "@/lib/api";
import {
  getCustomerToken,
  clearCustomerTokens,
  customerFetch,
} from "@/lib/customerAuth";
import { formatGHS, relativeTime } from "@/lib/utils";

const STATUS_META = {
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

export default function MyOrdersPage() {
  const router = useRouter();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await customerFetch(
        `${API_URL}/api/v1/customer-account/orders?limit=50`
      );
      if (res.status === 401) {
        clearCustomerTokens();
        router.replace("/account");
        return;
      }
      if (!res.ok) {
        throw new Error(`Failed to load orders (${res.status})`);
      }
      const data = await res.json().catch(() => []);
      setOrders(Array.isArray(data) ? data : []);
    } catch (e) {
      setError(e.message || "Failed to load orders.");
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    if (!getCustomerToken()) {
      router.replace("/account");
      return;
    }
    load();
  }, [load, router]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="font-heading text-2xl font-black text-white">
            My orders
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            {loading
              ? "Loading…"
              : `${orders.length} order${orders.length === 1 ? "" : "s"}`}
          </p>
        </div>
        <button
          onClick={load}
          disabled={loading}
          aria-label="Refresh orders"
          className="p-2 rounded-xl bg-surface-card border border-surface-border text-gray-300 hover:text-white hover:border-brand-primary transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm flex items-start gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <div className="flex-1">
            <div>{error}</div>
            <button
              onClick={load}
              className="mt-2 text-xs underline hover:text-red-300"
            >
              Try again
            </button>
          </div>
        </div>
      )}

      {loading ? (
        <div className="space-y-3" aria-busy="true">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="animate-pulse bg-surface-card border border-surface-border rounded-2xl h-40"
            />
          ))}
        </div>
      ) : orders.length === 0 && !error ? (
        <EmptyState
          icon={Package}
          title="No orders yet"
          message="Your order history will appear here after your first purchase."
          action={
            <Button href="/food" variant="primary">
              <Utensils className="w-4 h-4" />
              Browse food
            </Button>
          }
        />
      ) : (
        <div className="space-y-3">
          {orders.map((o) => {
            const meta = STATUS_META[o.status] || STATUS_META.pending;
            const items = Array.isArray(o.items) ? o.items : [];
            const shown = items.slice(0, 3);
            const extra = items.length - shown.length;
            return (
              <Link
                key={o.id}
                href={`/order/${o.reference}`}
                className="block bg-surface-card border border-surface-border rounded-2xl p-5 hover:border-brand-primary transition-colors"
              >
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div>
                    <div className="font-mono text-xs text-brand-primary font-bold">
                      {o.reference}
                    </div>
                    <div className="text-[11px] text-gray-500 mt-0.5">
                      {relativeTime(o.created_at)}
                    </div>
                  </div>
                  <span
                    className={`text-[10px] px-2.5 py-1 rounded-full font-bold ${meta.color} ${meta.bg}`}
                  >
                    {meta.label}
                  </span>
                </div>

                {shown.length > 0 && (
                  <div className="space-y-1 text-xs text-gray-300 border-t border-surface-border pt-3">
                    {shown.map((it, i) => (
                      <div key={i} className="flex justify-between gap-3">
                        <span className="truncate">
                          <span className="text-brand-primary font-bold">
                            {it.quantity}×
                          </span>{" "}
                          {it.name}
                        </span>
                        <span className="shrink-0">
                          {formatGHS((it.unit_price || 0) * (it.quantity || 0))}
                        </span>
                      </div>
                    ))}
                    {extra > 0 && (
                      <div className="text-[11px] text-gray-500 italic">
                        + {extra} more item{extra === 1 ? "" : "s"}
                      </div>
                    )}
                  </div>
                )}

                <div className="flex items-center justify-between mt-3 pt-3 border-t border-surface-border">
                  <span className="text-xs text-gray-400 truncate">
                    {o.delivery_zone_name || "—"}
                  </span>
                  <span className="text-brand-primary font-bold shrink-0">
                    {formatGHS(o.total)}
                  </span>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}