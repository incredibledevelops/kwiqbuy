"use client";

import { useEffect, useMemo, useState } from "react";
import { Loader2, TrendingUp, Package, CheckCircle2, XCircle } from "lucide-react";
import StatCard from "@/components/vendor/StatCard";
import { vendorApi } from "@/lib/vendorApi";
import { formatGHS } from "@/lib/utils";

export default function VendorAnalyticsPage() {
  const [days, setDays] = useState(30);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      setLoading(true);
      setError("");
      try {
        const res = await vendorApi.get(
          `/api/v1/vendor/analytics/overview?days=${days}`
        );
        setData(res);
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    })();
  }, [days]);

  const summary = data?.summary || {};
  const daily = data?.daily || [];
  const statusBreakdown = data?.status_breakdown || [];
  const topSellers = data?.top_sellers || [];

  const maxRevenue = useMemo(
    () => Math.max(1, ...daily.map((d) => d.revenue || 0)),
    [daily]
  );

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="font-heading text-3xl font-black text-white">
            Analytics
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Performance over the last {days} days
          </p>
        </div>
        <div className="inline-flex rounded-xl border border-surface-border bg-surface-card p-1">
          {[7, 30, 90].map((d) => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-colors ${
                days === d
                  ? "bg-brand-primary text-white"
                  : "text-gray-400 hover:text-white"
              }`}
            >
              {d}d
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="py-16 text-center">
          <Loader2 className="w-8 h-8 text-brand-primary animate-spin mx-auto" />
        </div>
      ) : error ? (
        <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
          {error}
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              label="Gross sales"
              value={formatGHS(summary.gross_sales || 0)}
              hint={`${summary.orders_total || 0} orders`}
              icon={TrendingUp}
            />
            <StatCard
              label="Net earnings"
              value={formatGHS(summary.net_earnings || 0)}
              hint={`After ${formatGHS(summary.platform_fees || 0)} in fees`}
              icon={TrendingUp}
              accent="success"
            />
            <StatCard
              label="Delivered"
              value={summary.orders_delivered || 0}
              hint={`${summary.items_sold || 0} items sold`}
              icon={CheckCircle2}
              accent="success"
            />
            <StatCard
              label="Cancelled"
              value={summary.orders_cancelled || 0}
              hint="Rejected by you or the customer"
              icon={XCircle}
              accent="warning"
            />
          </div>

          {/* Revenue chart */}
          <section className="bg-surface-card border border-surface-border rounded-2xl p-6">
            <h2 className="font-heading text-lg font-bold text-white mb-4">
              Revenue
            </h2>
            {daily.length === 0 ? (
              <div className="text-sm text-gray-500 py-8 text-center">
                No data for this period.
              </div>
            ) : (
              <div className="flex items-end gap-1 h-48">
                {daily.map((d, i) => {
                  const h = Math.max(
                    2,
                    Math.round((d.revenue / maxRevenue) * 100)
                  );
                  return (
                    <div
                      key={i}
                      className="flex-1 min-w-[3px] bg-brand-primary/70 hover:bg-brand-primary rounded-t"
                      style={{ height: `${h}%` }}
                      title={`${d.date}: ${formatGHS(d.revenue)}`}
                    />
                  );
                })}
              </div>
            )}
            <div className="flex justify-between text-[10px] text-gray-500 mt-2">
              <span>{daily[0]?.date || ""}</span>
              <span>{daily[daily.length - 1]?.date || ""}</span>
            </div>
          </section>

          <div className="grid lg:grid-cols-2 gap-6">
            {/* Top sellers */}
            <section className="bg-surface-card border border-surface-border rounded-2xl p-5">
              <h2 className="font-heading text-lg font-bold text-white mb-3">
                Top sellers
              </h2>
              {topSellers.length === 0 ? (
                <div className="text-sm text-gray-500 py-4 text-center">
                  No sales yet
                </div>
              ) : (
                <ul className="space-y-2">
                  {topSellers.map((s, i) => (
                    <li
                      key={i}
                      className="flex items-center justify-between p-3 rounded-xl bg-surface-dark border border-surface-border"
                    >
                      <div className="min-w-0">
                        <div className="text-sm text-white font-bold truncate">
                          {s.name}
                        </div>
                        <div className="text-xs text-gray-500">
                          {s.quantity} sold
                        </div>
                      </div>
                      <div className="text-brand-primary font-bold shrink-0">
                        {formatGHS(s.revenue)}
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            {/* Status breakdown */}
            <section className="bg-surface-card border border-surface-border rounded-2xl p-5">
              <h2 className="font-heading text-lg font-bold text-white mb-3">
                Order breakdown
              </h2>
              {statusBreakdown.length === 0 ? (
                <div className="text-sm text-gray-500 py-4 text-center">
                  No orders yet
                </div>
              ) : (
                <ul className="space-y-2">
                  {statusBreakdown.map((s, i) => (
                    <li
                      key={i}
                      className="flex items-center justify-between text-sm"
                    >
                      <span className="text-gray-300 capitalize">
                        {s.label}
                      </span>
                      <span className="text-white font-bold">{s.count}</span>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </div>
        </>
      )}
    </div>
  );
}