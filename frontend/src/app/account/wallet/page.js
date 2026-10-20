"use client";

import { useEffect, useState } from "react";
import {
  Wallet,
  Loader2,
  AlertCircle,
  ArrowDownCircle,
  ArrowUpCircle,
  Gift,
} from "lucide-react";
import StatCard from "@/components/vendor/StatCard";
import EmptyState from "@/components/ui/EmptyState";
import { customerFetch } from "@/lib/customerAuth";
import { API_URL } from "@/lib/api";
import { formatGHS, formatDateTime } from "@/lib/utils";

const REASON_META = {
  referral_bonus: { icon: Gift, label: "Referral bonus", accent: "text-brand-primary" },
  order_refund: { icon: ArrowDownCircle, label: "Order refund", accent: "text-emerald-400" },
  order_payment: { icon: ArrowUpCircle, label: "Order payment", accent: "text-red-400" },
  top_up: { icon: ArrowDownCircle, label: "Top up", accent: "text-emerald-400" },
};

export default function WalletPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      const res = await customerFetch(
        `${API_URL}/api/v1/wallet/me/history?limit=50`
      );
      if (!res.ok) throw new Error(`Failed (${res.status})`);
      const json = await res.json().catch(() => null);
      if (!json) throw new Error("Invalid response");
      setData(json);
    } catch (e) {
      setError(e.message || "Failed to load wallet.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6" aria-busy="true">
        <div className="animate-pulse h-8 w-40 bg-surface-card border border-surface-border rounded-xl" />
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="animate-pulse h-24 bg-surface-card border border-surface-border rounded-2xl"
            />
          ))}
        </div>
        <div className="animate-pulse h-64 bg-surface-card border border-surface-border rounded-2xl" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm flex items-start gap-2">
        <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
        <div className="flex-1">
          <div>{error}</div>
          <button onClick={load} className="mt-2 text-xs underline">
            Try again
          </button>
        </div>
      </div>
    );
  }

  const balance = data?.balance || {};
  const transactions = Array.isArray(data?.transactions)
    ? data.transactions
    : [];

  return (
    <div className="space-y-6">
      <h1 className="font-heading text-2xl font-black text-white">Wallet</h1>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
        <StatCard
          label="Current balance"
          value={formatGHS(balance.balance || 0)}
          icon={Wallet}
          accent="success"
        />
        <StatCard
          label="Total credited"
          value={formatGHS(balance.lifetime_credited || 0)}
        />
        <StatCard
          label="Total spent"
          value={formatGHS(balance.lifetime_spent || 0)}
        />
      </div>

      <section className="bg-surface-card border border-surface-border rounded-2xl overflow-hidden">
        <div className="px-5 py-4 border-b border-surface-border">
          <h2 className="font-heading text-lg font-bold text-white">
            Transactions
          </h2>
        </div>
        {transactions.length === 0 ? (
          <div className="p-6">
            <EmptyState
              icon={Wallet}
              title="No transactions yet"
              message="Your wallet activity will appear here."
            />
          </div>
        ) : (
          <ul className="divide-y divide-surface-border">
            {transactions.map((t) => {
              const meta = REASON_META[t.reason] || {};
              const Icon = meta.icon || Wallet;
              const positive = (t.amount || 0) >= 0;
              return (
                <li
                  key={t.id}
                  className="px-5 py-4 flex items-center justify-between gap-4"
                >
                  <div className="flex items-start gap-3 min-w-0">
                    <div
                      className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${
                        positive
                          ? "bg-emerald-500/10 text-emerald-400"
                          : "bg-red-500/10 text-red-400"
                      }`}
                    >
                      <Icon className="w-4 h-4" />
                    </div>
                    <div className="min-w-0">
                      <div className="font-bold text-white capitalize truncate">
                        {meta.label || String(t.reason || "").replace(/_/g, " ")}
                      </div>
                      <div className="text-xs text-gray-500 mt-0.5">
                        {formatDateTime(t.created_at)}
                      </div>
                      {t.note && (
                        <div className="text-xs text-gray-400 mt-1 truncate">
                          {t.note}
                        </div>
                      )}
                    </div>
                  </div>
                  <div
                    className={`font-bold shrink-0 ${
                      positive ? "text-emerald-400" : "text-red-400"
                    }`}
                  >
                    {positive ? "+" : ""}
                    {formatGHS(Math.abs(t.amount || 0))}
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </section>
    </div>
  );
}