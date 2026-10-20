"use client";

import { useEffect, useState } from "react";
import { Loader2, Wallet, CheckCircle2, Clock } from "lucide-react";
import StatCard from "@/components/vendor/StatCard";
import { riderApi } from "@/lib/riderApi";
import { formatGHS, formatDateTime } from "@/lib/utils";

export default function RiderEarningsPage() {
  const [data, setData] = useState(null);
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const [summary, detailedRows] = await Promise.all([
          riderApi.get("/api/v1/riders/me/earnings"),
          riderApi.get("/api/v1/riders/me/earnings/rows"),
        ]);
        setData(summary);
        setRows(Array.isArray(detailedRows) ? detailedRows : []);
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

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-heading text-3xl font-black text-white">Earnings</h1>
        <p className="text-sm text-gray-400 mt-1">
          Your delivery payouts and history.
        </p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatCard
          label="Available"
          value={formatGHS(data?.available || 0)}
          icon={Wallet}
          accent="success"
          hint="Ready to be paid out"
        />
        <StatCard
          label="Total Earned"
          value={formatGHS(data?.total_earned || 0)}
          icon={CheckCircle2}
          accent="primary"
        />
        <StatCard
          label="Pending"
          value={formatGHS(data?.pending || 0)}
          icon={Clock}
          accent="warning"
          hint="Awaiting delivery"
        />
        <StatCard
          label="Paid Out"
          value={formatGHS(data?.total_paid_out || 0)}
          icon={Wallet}
        />
      </div>

      <section className="bg-surface-card border border-surface-border rounded-2xl overflow-hidden">
        <div className="px-5 py-4 border-b border-surface-border">
          <h2 className="font-heading text-lg font-bold text-white">
            Per-delivery breakdown
          </h2>
        </div>
        {rows.length === 0 ? (
          <div className="py-12 text-center text-sm text-gray-500">
            No deliveries yet.
          </div>
        ) : (
          <ul className="divide-y divide-surface-border">
            {rows.map((r) => (
              <li key={r.id} className="px-5 py-4 flex items-center justify-between gap-4">
                <div>
                  <div className="font-mono text-xs text-brand-primary font-bold">
                    {r.order_reference}
                  </div>
                  <div className="text-xs text-gray-400 mt-0.5">
                    {formatDateTime(r.created_at)}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-white font-bold">{formatGHS(r.rider_amount)}</div>
                  <div className="text-[10px] uppercase font-bold text-emerald-400 mt-0.5">
                    {r.status}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}