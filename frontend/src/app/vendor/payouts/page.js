"use client";

import { useEffect, useState } from "react";
import {
  Loader2,
  Wallet,
  Send,
  AlertCircle,
  Clock,
  CheckCircle2,
  XCircle,
} from "lucide-react";
import StatCard from "@/components/vendor/StatCard";
import Button from "@/components/ui/Button";
import Modal from "@/components/ui/Modal";
import Input from "@/components/ui/Input";
import { useToast } from "@/components/ui/Toast";
import { vendorApi } from "@/lib/vendorApi";
import { formatGHS, formatDateTime } from "@/lib/utils";

const STATUS_COLORS = {
  requested: "text-amber-400 bg-amber-500/10 border-amber-500/30",
  processing: "text-blue-400 bg-blue-500/10 border-blue-500/30",
  paid: "text-emerald-400 bg-emerald-500/10 border-emerald-500/30",
  failed: "text-red-400 bg-red-500/10 border-red-500/30",
  cancelled: "text-gray-400 bg-white/5 border-white/10",
};

export default function VendorPayoutsPage() {
  const toast = useToast();
  const [vendor, setVendor] = useState(null);
  const [payouts, setPayouts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [requesting, setRequesting] = useState(false);
  const [requestOpen, setRequestOpen] = useState(false);
  const [note, setNote] = useState("");

  async function load() {
    setLoading(true);
    try {
      const [me, list] = await Promise.all([
        vendorApi.get("/api/v1/vendor/me"),
        vendorApi.get("/api/v1/vendor/payouts?limit=100"),
      ]);
      setVendor(me);
      setPayouts(Array.isArray(list) ? list : []);
      setError("");
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function requestPayout() {
    setRequesting(true);
    try {
      await vendorApi.post("/api/v1/vendor/payouts/request", {
        note: note.trim() || null,
      });
      toast.success("Payout requested");
      setRequestOpen(false);
      setNote("");
      await load();
    } catch (e) {
      toast.error(e.message);
    } finally {
      setRequesting(false);
    }
  }

  const balance = vendor?.available_balance || 0;
  const canRequest = balance >= 50; // MIN_VENDOR_PAYOUT_GHS default
  const hasRecipient = !!vendor?.payout_recipient_code;

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="font-heading text-3xl font-black text-white">Payouts</h1>
          <p className="text-sm text-gray-400 mt-1">
            Withdraw your earnings to your Paystack recipient account
          </p>
        </div>
        <Button
          variant="primary"
          size="md"
          disabled={!canRequest || !hasRecipient || requesting}
          onClick={() => setRequestOpen(true)}
        >
          <Send className="w-4 h-4" />
          Request payout
        </Button>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
          {error}
        </div>
      )}

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Available balance"
          value={formatGHS(balance)}
          icon={Wallet}
          hint={canRequest ? "Ready to withdraw" : "Minimum 50 GHS"}
          accent={canRequest ? "success" : "warning"}
        />
        <StatCard
          label="Lifetime gross"
          value={formatGHS(vendor?.total_gross_sales || 0)}
          icon={Wallet}
        />
        <StatCard
          label="Lifetime fees"
          value={formatGHS(vendor?.lifetime_platform_fees || 0)}
          icon={Wallet}
          accent="warning"
        />
        <StatCard
          label="Lifetime paid out"
          value={formatGHS(vendor?.lifetime_paid_out || 0)}
          icon={Wallet}
          accent="accent"
        />
      </div>

      {!hasRecipient && (
        <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-sm flex items-start gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <div>
            <div className="font-bold">Payout recipient not set</div>
            <div className="text-xs mt-0.5">
              Add your payout details in{" "}
              <a href="/vendor/profile" className="underline">
                Profile
              </a>{" "}
              before requesting a payout.
            </div>
          </div>
        </div>
      )}

      <section className="bg-surface-card border border-surface-border rounded-2xl overflow-hidden">
        <div className="px-5 py-4 border-b border-surface-border">
          <h2 className="font-heading text-lg font-bold text-white">
            Payout history
          </h2>
        </div>
        {loading ? (
          <div className="py-12 text-center">
            <Loader2 className="w-8 h-8 text-brand-primary animate-spin mx-auto" />
          </div>
        ) : payouts.length === 0 ? (
          <div className="py-12 text-center text-sm text-gray-500">
            No payouts yet.
          </div>
        ) : (
          <ul className="divide-y divide-surface-border">
            {payouts.map((p) => (
              <li
                key={p.id}
                className="px-5 py-4 flex items-center justify-between gap-4"
              >
                <div className="min-w-0">
                  <div className="font-bold text-white">
                    {formatGHS(p.net_payout)}
                  </div>
                  <div className="text-xs text-gray-500 mt-0.5">
                    {formatDateTime(p.created_at)} · {p.order_count} order
                    {p.order_count === 1 ? "" : "s"}
                  </div>
                  {p.failure_reason && (
                    <div className="text-[11px] text-red-400 mt-0.5">
                      {p.failure_reason}
                    </div>
                  )}
                </div>
                <span
                  className={`text-[10px] px-2.5 py-1 rounded-md border font-bold uppercase shrink-0 ${
                    STATUS_COLORS[p.status] || STATUS_COLORS.cancelled
                  }`}
                >
                  {p.status}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <Modal
        open={requestOpen}
        onClose={() => !requesting && setRequestOpen(false)}
        title="Request payout"
        maxWidth="max-w-md"
        disableClose={requesting}
      >
        <div className="space-y-4">
          <div className="p-4 rounded-2xl bg-brand-primary/10 border border-brand-primary/30">
            <div className="text-[10px] uppercase tracking-wider text-brand-primary font-bold">
              You will receive
            </div>
            <div className="text-2xl font-black text-white mt-1">
              {formatGHS(balance)}
            </div>
          </div>
          <Input
            label="Note (optional)"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="e.g. End of month withdrawal"
          />
          <p className="text-[11px] text-gray-500">
            Payouts are processed via Paystack transfer and usually arrive
            within 1–2 business days.
          </p>
        </div>
        <div className="flex justify-end gap-2 mt-6">
          <Button
            variant="secondary"
            onClick={() => setRequestOpen(false)}
            disabled={requesting}
          >
            Cancel
          </Button>
          <Button variant="primary" loading={requesting} onClick={requestPayout}>
            Confirm request
          </Button>
        </div>
      </Modal>
    </div>
  );
}