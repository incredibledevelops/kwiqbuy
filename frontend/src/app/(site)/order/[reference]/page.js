"use client";

import { Suspense, useEffect, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  Clock,
  CheckCircle2,
  ChefHat,
  Utensils,
  Bike,
  Package,
  Truck,
  PartyPopper,
  XCircle,
  Phone,
  Loader2,
  Home,
  MapPin,
} from "lucide-react";
import { API_URL } from "@/lib/api";
import { formatGHS, formatDateTime } from "@/lib/utils";

const STATUS_META = {
  pending: { label: "Pending payment", color: "text-amber-400", Icon: Clock },
  paid: { label: "Confirmed", color: "text-emerald-400", Icon: CheckCircle2 },
  preparing: { label: "Preparing", color: "text-amber-400", Icon: ChefHat },
  ready: { label: "Ready", color: "text-blue-400", Icon: Utensils },
  out_for_delivery: { label: "On the way", color: "text-blue-400", Icon: Bike },
  shipped: { label: "Shipped", color: "text-blue-400", Icon: Package },
  in_transit: { label: "In transit", color: "text-blue-400", Icon: Truck },
  delivered: { label: "Delivered", color: "text-emerald-400", Icon: PartyPopper },
  cancelled: { label: "Cancelled", color: "text-red-400", Icon: XCircle },
  failed: { label: "Failed", color: "text-red-400", Icon: XCircle },
};

function OrderInner() {
  const params = useParams();
  const search = useSearchParams();
  const reference = params.reference || search.get("reference");

  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!reference) return;
    let cancelled = false;
    let timer = null;

    async function fetchOrder() {
      try {
        const res = await fetch(`${API_URL}/api/v1/orders/track/${reference}`);
        if (!res.ok) throw new Error("Order not found");
        const data = await res.json();
        if (!cancelled) {
          setOrder(data);
          setError("");
        }
      } catch (e) {
        if (!cancelled) setError(e.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchOrder();
    timer = setInterval(fetchOrder, 15000);
    return () => {
      cancelled = true;
      if (timer) clearInterval(timer);
    };
  }, [reference]);

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-brand-primary animate-spin" />
      </div>
    );
  }

  if (error || !order) {
    return (
      <div className="max-w-lg mx-auto px-4 py-16 text-center">
        <XCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
        <h1 className="font-heading text-2xl font-black text-white">
          Order not found
        </h1>
        <p className="text-gray-400 text-sm mt-2">{error}</p>
        <Link
          href="/"
          className="inline-flex items-center gap-2 mt-6 px-5 py-2.5 rounded-xl bg-brand-primary hover:bg-brand-primaryDark text-white font-bold text-sm transition-colors"
        >
          <Home className="w-4 h-4" />
          Back home
        </Link>
      </div>
    );
  }

  const meta = STATUS_META[order.status] || STATUS_META.pending;
  const StatusIcon = meta.Icon;

  return (
    <div className="max-w-2xl mx-auto px-4 py-8 space-y-6">
      <Link
        href="/"
        className="inline-flex items-center gap-2 text-sm font-bold text-gray-400 hover:text-brand-primary"
      >
        <Home className="w-4 h-4" />
        Back home
      </Link>

      <div className="bg-surface-card border border-surface-border rounded-3xl p-6 sm:p-8">
        <div className="text-center">
          <div
            className={`w-20 h-20 rounded-full mx-auto flex items-center justify-center bg-white/5`}
          >
            <StatusIcon className={`w-10 h-10 ${meta.color}`} strokeWidth={2} />
          </div>
          <h1 className={`font-heading text-2xl font-black mt-4 ${meta.color}`}>
            {meta.label}
          </h1>
          <p className="text-gray-400 text-sm mt-2">
            {order.status === "pending"
              ? "Waiting for payment confirmation."
              : order.status === "delivered"
              ? "Enjoy your order!"
              : "We're tracking your order in real time."}
          </p>
        </div>

        <div className="mt-6 space-y-3 text-sm">
          <Row label="Reference" value={order.reference} mono />
          <Row label="Total" value={formatGHS(order.total)} accent />
          {order.wallet_applied > 0 && (
            <Row
              label="Wallet"
              value={`−${formatGHS(order.wallet_applied)}`}
              accent
            />
          )}
        </div>

        {order.rider_name && (
          <div className="mt-4 p-4 rounded-2xl bg-brand-primary/10 border border-brand-primary/30">
            <div className="text-[10px] text-brand-primary font-bold uppercase tracking-wider mb-1 inline-flex items-center gap-1.5">
              <Bike className="w-3.5 h-3.5" />
              Assigned rider
            </div>
            <div className="text-white font-bold">{order.rider_name}</div>
            {order.rider_phone && (
              <a
                href={`tel:${order.rider_phone}`}
                className="inline-flex items-center gap-1.5 text-emerald-400 text-xs underline mt-1"
              >
                <Phone className="w-3 h-3" />
                {order.rider_phone}
              </a>
            )}
          </div>
        )}

        {order.vendor_statuses?.length > 0 && (
          <div className="mt-6 pt-6 border-t border-surface-border">
            <div className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">
              Vendors
            </div>
            <div className="space-y-2">
              {order.vendor_statuses.map((v) => (
                <div
                  key={v.vendor_id}
                  className="flex items-center justify-between p-3 rounded-xl bg-surface-dark border border-surface-border"
                >
                  <div>
                    <div className="text-sm text-white font-bold">
                      {v.vendor_name}
                    </div>
                    <div className="text-[11px] text-gray-500">
                      {v.items_count} item{v.items_count === 1 ? "" : "s"}
                    </div>
                  </div>
                  <div
                    className={`text-xs font-bold capitalize ${
                      STATUS_META[v.status]?.color || "text-gray-400"
                    }`}
                  >
                    {v.status.replace(/_/g, " ")}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {order.status_history?.length > 0 && (
          <div className="mt-6 pt-6 border-t border-surface-border">
            <div className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-4">
              Timeline
            </div>
            <div className="space-y-3">
              {order.status_history.map((h, i, arr) => {
                const isLast = i === arr.length - 1;
                const hmeta = STATUS_META[h.status] || STATUS_META.pending;
                const HIcon = hmeta.Icon;
                return (
                  <div key={i} className="flex items-start gap-3">
                    <div className="flex flex-col items-center shrink-0">
                      <div
                        className={`w-7 h-7 rounded-full flex items-center justify-center border-2 ${
                          isLast
                            ? "border-brand-primary bg-brand-primary/20"
                            : "border-surface-border bg-surface-dark"
                        }`}
                      >
                        <HIcon
                          className={`w-3.5 h-3.5 ${
                            isLast ? "text-brand-primary" : "text-gray-500"
                          }`}
                        />
                      </div>
                      {!isLast && (
                        <div className="w-px h-6 bg-surface-border" />
                      )}
                    </div>
                    <div className="flex-1">
                      <div
                        className={`text-sm capitalize font-semibold ${
                          isLast ? "text-white" : "text-gray-400"
                        }`}
                      >
                        {h.status.replace(/_/g, " ")}
                      </div>
                      <div className="text-xs text-gray-500 mt-0.5">
                        {formatDateTime(h.at)}
                      </div>
                      {h.note && (
                        <div className="text-xs text-gray-400 mt-1 italic">
                          {h.note}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        <div className="mt-6 pt-6 border-t border-surface-border text-sm space-y-2">
          <div className="flex items-start gap-2 text-gray-300">
            <MapPin className="w-4 h-4 text-gray-500 shrink-0 mt-0.5" />
            <div>
              <div>{order.delivery_address}</div>
              <div className="text-xs text-gray-500 mt-0.5">
                {order.delivery_zone_name}
              </div>
            </div>
          </div>
        </div>
      </div>

      <Link
        href="/"
        className="block w-full py-3.5 rounded-2xl bg-brand-primary hover:bg-brand-primaryDark text-white font-bold text-center transition-colors"
      >
        Order something else
      </Link>
    </div>
  );
}

function Row({ label, value, mono, accent }) {
  return (
    <div className="flex justify-between items-center">
      <span className="text-gray-400">{label}</span>
      <span
        className={`${mono ? "font-mono text-xs" : ""} ${
          accent ? "text-brand-primary font-bold" : "text-white font-semibold"
        }`}
      >
        {value}
      </span>
    </div>
  );
}

export default function OrderPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-[60vh] flex items-center justify-center">
          <Loader2 className="w-8 h-8 text-brand-primary animate-spin" />
        </div>
      }
    >
      <OrderInner />
    </Suspense>
  );
}