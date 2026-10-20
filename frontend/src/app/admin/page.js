"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Loader2,
  TrendingUp,
  Users,
  Store,
  AlertTriangle,
  Banknote,
  ArrowRight,
  ShieldAlert,
  Bike,
} from "lucide-react";
import StatCard from "@/components/vendor/StatCard";
import { adminApi } from "@/lib/adminApi";
import { formatGHS, formatDateTime } from "@/lib/utils";

export default function AdminOverviewPage() {
  const [data, setData] = useState({
    analytics: null,
    apps: [],
    disputes: [],
    payouts: [],
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const [
          analyticsRes,
          appsRes,
          disputesRes,
          payoutsRes,
        ] = await Promise.all([
          adminApi.get("/api/v1/analytics/overview?days=30").catch(() => null),
          adminApi.get("/api/v1/admin/vendor-applications?status=pending&limit=5").catch(() => []),
          adminApi.get("/api/v1/admin/review-disputes?status=open&limit=5").catch(() => ({ items: [] })),
          adminApi.get("/api/v1/admin/payouts?status=requested&limit=5").catch(() => []),
        ]);

        setData({
          analytics: analyticsRes,
          apps: Array.isArray(appsRes) ? appsRes : [],
          disputes: disputesRes?.items || [],
          payouts: Array.isArray(payoutsRes) ? payoutsRes : [],
        });
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) {
    return (
      <div className="py-20 text-center">
        <Loader2 className="w-10 h-10 text-brand-primary animate-spin mx-auto" />
        <p className="text-gray-400 text-sm mt-4">Loading your command center...</p>
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

  const summary = data.analytics?.summary || {};

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-heading text-3xl font-black text-white">Overview</h1>
        <p className="text-sm text-gray-400 mt-1">
          Here is what is happening on KwiqBuy today.
        </p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total Revenue (30d)"
          value={formatGHS(summary.total_revenue || 0)}
          hint={`${summary.total_orders || 0} total orders`}
          icon={TrendingUp}
          accent="success"
        />
        <StatCard
          label="Platform Fees (30d)"
          value={formatGHS(summary.platform_fees_earned || 0)}
          hint="Commission + delivery cuts"
          icon={Store}
          accent="primary"
        />
        <StatCard
          label="Average Order"
          value={formatGHS(summary.average_order_value || 0)}
          hint="Per order value"
          icon={Banknote}
          accent="warning"
        />
        <StatCard
          label="Pending Actions"
          value={data.apps.length + data.disputes.length + data.payouts.length}
          hint="Needs your attention"
          icon={AlertTriangle}
          accent={data.apps.length + data.disputes.length + data.payouts.length > 0 ? "warning" : "success"}
        />
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <div className="space-y-6">
          <section className="bg-surface-card border border-surface-border rounded-2xl overflow-hidden">
            <div className="flex items-center justify-between px-5 py-4 border-b border-surface-border">
              <h2 className="font-heading text-lg font-bold text-white flex items-center gap-2">
                <Users className="w-5 h-5 text-brand-primary" /> Pending Applications
              </h2>
              <Link href="/admin/applications" className="text-xs font-bold text-brand-primary hover:underline flex items-center gap-1">
                View all <ArrowRight className="w-3 h-3" />
              </Link>
            </div>
            {data.apps.length === 0 ? (
              <div className="p-6 text-center text-sm text-gray-500">No pending applications.</div>
            ) : (
              <ul className="divide-y divide-surface-border">
                {data.apps.map((app) => (
                  <li key={app.id} className="p-4 flex items-center justify-between gap-4 hover:bg-white/5">
                    <div>
                      <div className="font-bold text-white text-sm">{app.business_name}</div>
                      <div className="text-xs text-gray-500">{app.contact_email}</div>
                    </div>
                    <Link href="/admin/applications" className="px-3 py-1.5 rounded-lg bg-brand-primary/10 text-brand-primary text-xs font-bold hover:bg-brand-primary/20">
                      Review
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section className="bg-surface-card border border-surface-border rounded-2xl overflow-hidden">
            <div className="flex items-center justify-between px-5 py-4 border-b border-surface-border">
              <h2 className="font-heading text-lg font-bold text-white flex items-center gap-2">
                <ShieldAlert className="w-5 h-5 text-amber-400" /> Open Disputes
              </h2>
              <Link href="/admin/disputes" className="text-xs font-bold text-brand-primary hover:underline flex items-center gap-1">
                View all <ArrowRight className="w-3 h-3" />
              </Link>
            </div>
            {data.disputes.length === 0 ? (
              <div className="p-6 text-center text-sm text-gray-500">No open disputes.</div>
            ) : (
              <ul className="divide-y divide-surface-border">
                {data.disputes.map((d) => (
                  <li key={d.id} className="p-4 flex items-center justify-between gap-4 hover:bg-white/5">
                    <div>
                      <div className="font-mono text-xs text-brand-primary font-bold">{d.order_reference}</div>
                      <div className="text-sm text-white truncate max-w-[200px]">{d.reason}</div>
                    </div>
                    <Link href="/admin/disputes" className="px-3 py-1.5 rounded-lg bg-amber-500/10 text-amber-400 text-xs font-bold hover:bg-amber-500/20">
                      Resolve
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>

        <div className="space-y-6">
          <section className="bg-surface-card border border-surface-border rounded-2xl overflow-hidden">
            <div className="flex items-center justify-between px-5 py-4 border-b border-surface-border">
              <h2 className="font-heading text-lg font-bold text-white flex items-center gap-2">
                <Banknote className="w-5 h-5 text-emerald-400" /> Payout Requests
              </h2>
              <Link href="/admin/payouts" className="text-xs font-bold text-brand-primary hover:underline flex items-center gap-1">
                View all <ArrowRight className="w-3 h-3" />
              </Link>
            </div>
            {data.payouts.length === 0 ? (
              <div className="p-6 text-center text-sm text-gray-500">No pending payout requests.</div>
            ) : (
              <ul className="divide-y divide-surface-border">
                {data.payouts.map((p) => (
                  <li key={p.id} className="p-4 flex items-center justify-between gap-4 hover:bg-white/5">
                    <div>
                      <div className="font-bold text-white text-sm">{p.vendor_name}</div>
                      <div className="text-xs text-gray-500">{formatDateTime(p.created_at)}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-brand-primary font-bold">{formatGHS(p.net_payout)}</div>
                      <Link href="/admin/payouts" className="text-[10px] text-emerald-400 font-bold hover:underline uppercase">Process</Link>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section className="bg-surface-card border border-surface-border rounded-2xl p-5">
            <h2 className="font-heading text-lg font-bold text-white mb-4">Quick Actions</h2>
            <div className="grid grid-cols-2 gap-3">
              <Link href="/admin/vendors" className="p-3 rounded-xl bg-surface-dark border border-surface-border hover:border-brand-primary text-center transition-colors">
                <Store className="w-5 h-5 text-gray-400 mx-auto mb-1" />
                <div className="text-xs font-bold text-white">Manage Vendors</div>
              </Link>
              <Link href="/admin/riders" className="p-3 rounded-xl bg-surface-dark border border-surface-border hover:border-brand-primary text-center transition-colors">
                <Bike className="w-5 h-5 text-gray-400 mx-auto mb-1" />
                <div className="text-xs font-bold text-white">Manage Riders</div>
              </Link>
              <Link href="/admin/settings" className="p-3 rounded-xl bg-surface-dark border border-surface-border hover:border-brand-primary text-center transition-colors">
                <ShieldAlert className="w-5 h-5 text-gray-400 mx-auto mb-1" />
                <div className="text-xs font-bold text-white">Platform Settings</div>
              </Link>
              <Link href="/admin/wallet" className="p-3 rounded-xl bg-surface-dark border border-surface-border hover:border-brand-primary text-center transition-colors">
                <Banknote className="w-5 h-5 text-gray-400 mx-auto mb-1" />
                <div className="text-xs font-bold text-white">Wallet Adjust</div>
              </Link>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}