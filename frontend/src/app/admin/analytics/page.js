"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Loader2,
  Download,
  TrendingUp,
  DollarSign,
  ShoppingBag,
  Store,
  MapPin,
  Sparkles,
} from "lucide-react";
import Button from "@/components/ui/Button";
import StatCard from "@/components/vendor/StatCard";
import { useToast } from "@/components/ui/Toast";
import { adminApi } from "@/lib/adminApi";
import { formatGHS } from "@/lib/utils";

export default function AdminAnalyticsPage() {
  const toast = useToast();
  const [days, setDays] = useState(30);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [downloading, setDownloading] = useState(null);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const res = await adminApi.get(
          `/api/v1/analytics/overview?days=${days}`
        );
        setData(res);
        setError("");
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    })();
  }, [days]);

  async function download(format) {
    setDownloading(format);
    try {
      const ext = format === "xlsx" ? "xlsx" : "csv";
      const filename = `kwiqbuy-analytics-${days}d-${Date.now()}.${ext}`;
      await adminApi.download(
        `/api/v1/admin/analytics/export?format=${format}&days=${days}`,
        filename
      );
      toast.success(`Downloaded ${format.toUpperCase()}`);
    } catch (e) {
      toast.error(e.message);
    } finally {
      setDownloading(null);
    }
  }

  const summary = data?.summary || {};
  const daily = data?.daily || [];
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
            Platform performance over the last {days} days
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
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
          <Button
            variant="secondary"
            size="md"
            loading={downloading === "csv"}
            onClick={() => download("csv")}
          >
            <Download className="w-4 h-4" />
            CSV
          </Button>
          <Button
            variant="secondary"
            size="md"
            loading={downloading === "xlsx"}
            onClick={() => download("xlsx")}
          >
            <Download className="w-4 h-4" />
            XLSX
          </Button>
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
              label="Revenue"
              value={formatGHS(summary.total_revenue || 0)}
              hint={`${summary.total_orders || 0} orders`}
              icon={TrendingUp}
            />
            <StatCard
              label="Platform fees"
              value={formatGHS(summary.platform_fees_earned || 0)}
              hint={`+${formatGHS(summary.platform_delivery_cut || 0)} delivery`}
              icon={DollarSign}
              accent="success"
            />
            <StatCard
              label="Avg order value"
              value={formatGHS(summary.average_order_value || 0)}
              icon={ShoppingBag}
            />
            <StatCard
              label="Delivered"
              value={summary.delivered_orders || 0}
              hint={`${summary.pending_orders || 0} pending`}
              icon={Store}
              accent="accent"
            />
          </div>

          {/* Revenue chart */}
          <section className="bg-surface-card border border-surface-border rounded-2xl p-6">
            <h2 className="font-heading text-lg font-bold text-white mb-4">
              Daily revenue
            </h2>
            {daily.length === 0 ? (
              <div className="text-sm text-gray-500 py-8 text-center">
                No data.
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
                      title={`${d.date}: ${formatGHS(d.revenue)} (${d.orders} orders)`}
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

          <div className="grid lg:grid-cols-2 gap-4">
            <ListCard
              title="Top vendors"
              icon={Store}
              items={(data.top_vendors || []).map((v) => ({
                primary: v.vendor_name,
                secondary: `${v.orders} orders`,
                value: formatGHS(v.revenue),
              }))}
            />
            <ListCard
              title="Top sellers"
              icon={ShoppingBag}
              items={(data.top_sellers || []).map((s) => ({
                primary: s.name,
                secondary: `${s.quantity} sold`,
                value: formatGHS(s.revenue),
              }))}
            />
            <ListCard
              title="Top zones"
              icon={MapPin}
              items={(data.top_zones || []).map((z) => ({
                primary: z.zone,
                secondary: `${z.orders} orders`,
                value: formatGHS(z.revenue),
              }))}
            />
            <ListCard
              title="Top promos"
              icon={Sparkles}
              items={(data.top_promos || []).map((p) => ({
                primary: p.code,
                secondary: `${p.times_used} uses`,
                value: formatGHS(p.discount_given),
              }))}
            />
          </div>
        </>
      )}
    </div>
  );
}

function ListCard({ title, icon: Icon, items }) {
  return (
    <section className="bg-surface-card border border-surface-border rounded-2xl p-5">
      <h2 className="font-heading text-lg font-bold text-white flex items-center gap-2 mb-3">
        <Icon className="w-5 h-5 text-brand-primary" />
        {title}
      </h2>
      {items.length === 0 ? (
        <div className="text-sm text-gray-500 py-3 text-center">No data</div>
      ) : (
        <ul className="space-y-2">
          {items.map((it, i) => (
            <li
              key={i}
              className="flex items-center justify-between gap-3 p-2.5 rounded-xl bg-surface-dark border border-surface-border"
            >
              <div className="min-w-0">
                <div className="text-sm text-white font-bold truncate">
                  {it.primary}
                </div>
                <div className="text-xs text-gray-500">{it.secondary}</div>
              </div>
              <div className="text-brand-primary font-bold shrink-0">
                {it.value}
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}