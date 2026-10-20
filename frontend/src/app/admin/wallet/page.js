"use client";

import { useState } from "react";
import {
  Wallet,
  Search,
  Loader2,
  Plus,
  Minus,
  AlertCircle,
  CheckCircle2,
} from "lucide-react";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import { useToast } from "@/components/ui/Toast";
import { adminApi } from "@/lib/adminApi";
import { formatGHS, formatDateTime, normalizePhone } from "@/lib/utils";

export default function AdminWalletPage() {
  const toast = useToast();
  const [phone, setPhone] = useState("");
  const [amount, setAmount] = useState("");
  const [note, setNote] = useState("");
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  async function lookup() {
    setError("");
    setResult(null);
    setHistory(null);
    const normalized = normalizePhone(phone);
    if (!normalized) {
      setError("Enter a valid phone number (e.g. 024XXXXXXX)");
      return;
    }
    setLoading(true);
    try {
      const data = await adminApi.get(
        `/api/v1/admin/wallet/history/${normalized}?limit=50`
      );
      setHistory(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function adjust(sign) {
    setError("");
    const normalized = normalizePhone(phone);
    if (!normalized) {
      setError("Enter a valid phone number first");
      return;
    }
    const n = parseFloat(amount);
    if (!Number.isFinite(n) || n <= 0) {
      setError("Enter an amount greater than 0");
      return;
    }
    setLoading(true);
    try {
      const adjusted = await adminApi.post("/api/v1/admin/wallet/adjust", {
        phone: normalized,
        amount: sign > 0 ? n : -n,
        note: note.trim() || null,
      });
      setResult(adjusted);
      setAmount("");
      setNote("");
      toast.success(sign > 0 ? "Wallet credited" : "Wallet debited");
      // Refresh
      const refreshed = await adminApi.get(
        `/api/v1/admin/wallet/history/${normalized}?limit=50`
      );
      setHistory(refreshed);
    } catch (e) {
      setError(e.message);
      toast.error(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-heading text-3xl font-black text-white">Wallet</h1>
        <p className="text-sm text-gray-400 mt-1">
          Adjust customer wallet balance (credits or debits)
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm flex items-start gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Search bar */}
      <section className="bg-surface-card border border-surface-border rounded-2xl p-5 space-y-3">
        <h2 className="font-heading text-lg font-bold text-white flex items-center gap-2">
          <Search className="w-5 h-5 text-brand-primary" />
          Look up customer
        </h2>
        <div className="flex gap-2">
          <input
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="024XXXXXXX"
            className="flex-1 px-4 py-3 rounded-xl bg-surface-dark border border-surface-border text-white text-sm focus:border-brand-primary outline-none"
          />
          <Button variant="primary" size="md" loading={loading} onClick={lookup}>
            Look up
          </Button>
        </div>
        {history && (
          <div className="pt-3 border-t border-surface-border">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs text-gray-500 uppercase tracking-wider font-bold">
                  Balance
                </div>
                <div className="text-2xl font-black text-white mt-0.5">
                  {formatGHS(history.balance?.balance || 0)}
                </div>
              </div>
              <div className="text-right">
                <div className="text-xs text-gray-500 uppercase tracking-wider font-bold">
                  Customer
                </div>
                <div className="text-white font-bold">
                  {history.balance?.customer_name || "—"}
                </div>
                <div className="text-[11px] text-gray-500 font-mono">
                  {history.balance?.phone}
                </div>
              </div>
            </div>
          </div>
        )}
      </section>

      {/* Adjust form */}
      {history && (
        <section className="bg-surface-card border border-surface-border rounded-2xl p-5 space-y-4">
          <h2 className="font-heading text-lg font-bold text-white flex items-center gap-2">
            <Wallet className="w-5 h-5 text-brand-primary" />
            Adjust balance
          </h2>
          <Input
            label="Amount (GHS)"
            type="number"
            min="0.01"
            step="0.01"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            placeholder="e.g. 50"
          />
          <Input
            label="Note (optional)"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="e.g. Refund for broken item"
          />
          {result && (
            <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-start gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 shrink-0 mt-0.5" />
              New balance:{" "}
              <strong className="text-white">
                {formatGHS(result.balance)}
              </strong>
            </div>
          )}
          <div className="flex gap-2">
            <Button
              variant="success"
              size="md"
              className="flex-1"
              loading={loading}
              onClick={() => adjust(+1)}
            >
              <Plus className="w-4 h-4" />
              Credit
            </Button>
            <Button
              variant="danger"
              size="md"
              className="flex-1"
              loading={loading}
              onClick={() => adjust(-1)}
            >
              <Minus className="w-4 h-4" />
              Debit
            </Button>
          </div>
        </section>
      )}

      {/* History */}
      {history && (
        <section className="bg-surface-card border border-surface-border rounded-2xl overflow-hidden">
          <div className="px-5 py-4 border-b border-surface-border">
            <h2 className="font-heading text-lg font-bold text-white">
              Recent transactions
            </h2>
          </div>
          {!history.transactions || history.transactions.length === 0 ? (
            <div className="py-10 text-center text-sm text-gray-500">
              No transactions yet.
            </div>
          ) : (
            <ul className="divide-y divide-surface-border">
              {history.transactions.map((t) => (
                <li
                  key={t.id}
                  className="px-5 py-3 flex items-center justify-between gap-3"
                >
                  <div className="min-w-0">
                    <div className="text-sm text-white font-bold capitalize">
                      {String(t.reason).replace(/_/g, " ")}
                    </div>
                    {t.note && (
                      <div className="text-xs text-gray-400 truncate">
                        {t.note}
                      </div>
                    )}
                    <div className="text-[11px] text-gray-500 mt-0.5">
                      {formatDateTime(t.created_at)}
                      {t.created_by && ` · ${t.created_by}`}
                    </div>
                  </div>
                  <div className="text-right shrink-0">
                    <div
                      className={`font-bold ${
                        t.amount >= 0 ? "text-emerald-400" : "text-red-400"
                      }`}
                    >
                      {t.amount >= 0 ? "+" : ""}
                      {formatGHS(t.amount)}
                    </div>
                    <div className="text-[11px] text-gray-500">
                      Bal {formatGHS(t.balance_after)}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}
    </div>
  );
}