"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Package,
  ClipboardList,
  Wallet,
  Star,
  TrendingUp,
  AlertTriangle,
  ArrowRight,
  Loader2,
  BadgeCheck,
  Clock,
} from "lucide-react";
import StatCard from "@/components/vendor/StatCard";
import { vendorApi } from "@/lib/vendorApi";
import { formatGHS, formatDateTime } from "@/lib/utils";

export default function VendorDashboardPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [vendor, setVendor] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [orders, setOrders] = useState([]);
  const [products, setProducts] = useState([]);

  useEffect(() => {
    (async () => {
      try {
        const [me, overview, pendingOrders, myProducts] = await Promise.all([
          vendorApi.get("/api/v1/vendor/me"),
          vendorApi.get("/api/v1/vendor/analytics/overview?days=7").catch(() => null),
          vendorApi.get("/api/v1/vendor/orders?status=pending&limit=10").catch(() => []),
          vendorApi.get("/api/v1/vendor/products?limit=200").catch(() => []),
        ]);
        setVendor(me);
        setAnalytics(overview);
        setOrders(Array.isArray(pendingOrders) ? pendingOrders : []);
        setProducts(Array.isArray(myProducts) ? myProducts : []);
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) {
    return (
      <div className="py-16 text-center">
        <Loader2 className="w-8 h-8 text-brand-primary animate-spin mx-auto" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
        {error}
      </div>
    );
  }

  const summary = analytics?.summary || {};
  const outOfStock = products.filter((p) => !p.is_available).length;

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="font-heading text-3xl font-black text-white">
            Welcome back, {vendor?.business_name?.split(" ")[0] || "Vendor"}
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Last 7 days performance ·{" "}
            {vendor?.business_category?.toUpperCase?.() || "—"}
          </p>
        </div>
        <Link
          href="/vendor/products/new"
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-brand-primary hover:bg-brand-primaryDark text-white font-bold text-sm transition-colors"
        >
          <Package className="w-4 h-4" />
          Add product
        </Link>
      </div>

      {/* Stat grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Gross sales · 7d"
          value={formatGHS(summary.gross_sales || 0)}
          hint={`${summary.orders_total || 0} orders`}
          icon={TrendingUp}
          accent="primary"
        />
        <StatCard
          label="Net earnings · 7d"
          value={formatGHS(summary.net_earnings || 0)}
          hint={`After ${formatGHS(summary.platform_fees || 0)} fees`}
          icon={Wallet}
          accent="success"
        />
        <StatCard
          label="Available balance"
          value={formatGHS(vendor?.available_balance || 0)}
          hint={`Lifetime paid: ${formatGHS(vendor?.lifetime_paid_out || 0)}`}
          icon={Wallet}
          accent="accent"
        />
        <StatCard
          label="Rating"
          value={
            vendor?.average_rating > 0
              ? vendor.average_rating.toFixed(1)
              : "—"
          }
          hint={`${vendor?.total_reviews || 0} reviews`}
          icon={Star}
          accent="warning"
        />
      </div>

      {/* Pending actions */}
      <div className="grid md:grid-cols-3 gap-4">
        <ActionCard
          href="/vendor/orders?status=pending"
          icon={Clock}
          title="Pending orders"
          value={orders.length}
          hint={
            orders.length > 0
              ? "Accept or reject now"
              : "You're all caught up"
          }
          accent={orders.length > 0 ? "warning" : "success"}
        />
        <ActionCard
          href="/vendor/products"
          icon={AlertTriangle}
          title="Out-of-stock items"
          value={outOfStock}
          hint={outOfStock > 0 ? "Restock to keep selling" : "All products live"}
          accent={outOfStock > 0 ? "warning" : "success"}
        />
        <ActionCard
          href="/vendor/payouts"
          icon={Wallet}
          title="Balance to withdraw"
          value={formatGHS(vendor?.available_balance || 0)}
          hint="Request a payout"
          accent="primary"
        />
      </div>

      {/* Recent pending orders */}
      <section className="bg-surface-card border border-surface-border rounded-2xl overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-surface-border">
          <h2 className="font-heading text-lg font-bold text-white">
            Recent pending orders
          </h2>
          <Link
            href="/vendor/orders"
            className="inline-flex items-center gap-1 text-xs font-bold text-brand-primary hover:underline"
          >
            View all <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
        {orders.length === 0 ? (
          <div className="p-8 text-center text-sm text-gray-500">
            No pending orders right now.
          </div>
        ) : (
          <ul className="divide-y divide-surface-border">
            {orders.slice(0, 5).map((o) => (
              <li key={o.order_id}>
                <Link
                  href={`/vendor/orders/${o.order_id}`}
                  className="flex items-center justify-between gap-4 px-5 py-3 hover:bg-white/5 transition-colors"
                >
                  <div className="min-w-0">
                    <div className="font-mono text-xs text-brand-primary font-bold">
                      {o.reference}
                    </div>
                    <div className="text-sm text-white truncate">
                      {o.customer_name}
                    </div>
                    <div className="text-[11px] text-gray-500">
                      {formatDateTime(o.created_at)}
                    </div>
                  </div>
                  <div className="text-right shrink-0">
                    <div className="text-xs text-gray-400">
                      {o.items_count} item{o.items_count === 1 ? "" : "s"}
                    </div>
                    <div className="text-brand-primary font-bold">
                      {formatGHS(o.vendor_payout)}
                    </div>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* Profile completeness */}
      <section className="bg-surface-card border border-surface-border rounded-2xl p-5">
        <h2 className="font-heading text-lg font-bold text-white mb-3">
          Profile & compliance
        </h2>
        <div className="grid sm:grid-cols-2 gap-3 text-sm">
          <ChecklistItem
            label="Business info"
            done={!!vendor?.business_name && !!vendor?.description}
          />
          <ChecklistItem
            label="Pickup location"
            done={vendor?.pickup_lat != null && vendor?.pickup_lng != null}
          />
          <ChecklistItem
            label="Payout recipient (Paystack)"
            done={!!vendor?.payout_recipient_code}
          />
          <ChecklistItem
            label="Logo uploaded"
            done={!!vendor?.logo_url}
          />
        </div>
        <Link
          href="/vendor/profile"
          className="mt-4 inline-flex items-center gap-2 text-xs font-bold text-brand-primary hover:underline"
        >
          Manage profile <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </section>
    </div>
  );
}

function ActionCard({ href, icon: Icon, title, value, hint, accent }) {
  const accents = {
    primary: "border-brand-primary/30 text-brand-primary",
    warning: "border-amber-500/30 text-amber-400",
    success: "border-emerald-500/30 text-emerald-400",
  };
  return (
    <Link
      href={href}
      className={`block p-5 rounded-2xl bg-surface-card border ${accents[accent] || accents.primary} hover:bg-white/5 transition-colors`}
    >
      <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider">
        <Icon className="w-4 h-4" />
        {title}
      </div>
      <div className="mt-2 text-2xl font-black text-white">{value}</div>
      <div className="text-xs text-gray-500 mt-1">{hint}</div>
    </Link>
  );
}

function ChecklistItem({ label, done }) {
  return (
    <div className="flex items-center gap-2">
      {done ? (
        <BadgeCheck className="w-4 h-4 text-emerald-400" />
      ) : (
        <AlertTriangle className="w-4 h-4 text-amber-400" />
      )}
      <span className={done ? "text-gray-300" : "text-amber-300"}>{label}</span>
    </div>
  );
}