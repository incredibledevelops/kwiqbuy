"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Loader2,
  Banknote,
  Plus,
  CheckCircle2,
  XCircle,
  Ban,
} from "lucide-react";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Modal from "@/components/ui/Modal";
import { useToast } from "@/components/ui/Toast";
import { adminApi } from "@/lib/adminApi";
import { formatGHS, formatDateTime } from "@/lib/utils";

const STATUS_TABS = [
  { value: "", label: "All" },
  { value: "requested", label: "Requested" },
  { value: "processing", label: "Processing" },
  { value: "paid", label: "Paid" },
  { value: "failed", label: "Failed" },
  { value: "cancelled", label: "Cancelled" },
];

const STATUS_BADGE = {
  requested: "text-amber-400 bg-amber-500/10 border-amber-500/30",
  processing: "text-blue-400 bg-blue-500/10 border-blue-500/30",
  paid: "text-emerald-400 bg-emerald-500/10 border-emerald-500/30",
  failed: "text-red-400 bg-red-500/10 border-red-500/30",
  cancelled: "text-gray-400 bg-white/5 border-white/10",
};

export default function AdminPayoutsPage() {
  const toast = useToast();
  const [tab, setTab] = useState("");
  const [payouts, setPayouts] = useState([]);
  const [vendors, setVendors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Create payout
  const [createOpen, setCreateOpen] = useState(false);
  const [vendorId, setVendorId] = useState("");
  const [method, setMethod] = useState("paystack_transfer");
  const [creating, setCreating] = useState(false);

  // Mark failed
  const [failTarget, setFailTarget] = useState(null);
  const [failReason, setFailReason] = useState("");
  const [failing, setFailing] = useState(false);

  // Cancel
  const [cancelTarget, setCancelTarget] = useState(null);
  const [cancelReason, setCancelReason] = useState("");
  const [cancelling, setCancelling] = useState(false);

  // Per-row busy
  const [busyId, setBusyId] = useState(null);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const qs = tab ? `?status=${tab}&limit=200` : "?limit=200";
      // Fetch payouts first (critical)
      const list = await adminApi.get(`/api/v1/admin/payouts${qs}`);
      setPayouts(Array.isArray(list) ? list : []);

      // Fetch vendors separately (non-critical for viewing payouts)
      try {
        const vs = await adminApi.get("/api/v1/vendors?limit=500&status=active");
        setVendors(Array.isArray(vs) ? vs : []);
      } catch (vErr) {
        console.warn("Could not load vendors list for dropdown:", vErr);
        // Don't set main error state, just empty vendors list
      }
    } catch (e) {
      setError(e.message || "Failed to load payouts");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [tab]);

  async function createPayout() {
    if (!vendorId) {
      toast.error("Select a vendor");
      return;
    }
    setCreating(true);
    try {
      await adminApi.post("/api/v1/admin/payouts", {
        vendor_id: vendorId,
        method,
      });
      toast.success("Payout created");
      setCreateOpen(false);
      setVendorId("");
      await load();
    } catch (e) {
      toast.error(e.message);
    } finally {
      setCreating(false);
    }
  }

  async function markPaid(p) {
    setBusyId(p.id);
    try {
      await adminApi.post(`/api/v1/admin/payouts/${p.id}/mark-paid`);
      toast.success("Marked paid");
      await load();
    } catch (e) {
      toast.error(e.message);
    } finally {
      setBusyId(null);
    }
  }

  async function doMarkFailed() {
    if (!failTarget) return;
    if (failReason.trim().length < 4) {
      toast.error("Please enter a reason");
      return;
    }
    setFailing(true);
    try {
      await adminApi.post(`/api/v1/admin/payouts/${failTarget.id}/mark-failed`, {
        reason: failReason.trim(),
      });
      toast.success("Marked failed");
      setFailTarget(null);
      setFailReason("");
      await load();
    } catch (e) {
      toast.error(e.message);
    } finally {
      setFailing(false);
    }
  }

  async function doCancel() {
    if (!cancelTarget) return;
    setCancelling(true);
    try {
      await adminApi.post(`/api/v1/admin/payouts/${cancelTarget.id}/cancel`, {
        reason: cancelReason.trim() || null,
      });
      toast.success("Payout cancelled");
      setCancelTarget(null);
      setCancelReason("");
      await load();
    } catch (e) {
      toast.error(e.message);
    } finally {
      setCancelling(false);
    }
  }

  const totals = useMemo(() => {
    let paid = 0;
    let pending = 0;
    for (const p of payouts) {
      if (p.status === "paid") paid += Number(p.net_payout || 0);
      if (p.status === "requested" || p.status === "processing")
        pending += Number(p.net_payout || 0);
    }
    return { paid, pending };
  }, [payouts]);

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="font-heading text-3xl font-black text-white">Payouts</h1>
          <p className="text-sm text-gray-400 mt-1">
            Manage vendor payouts
          </p>
        </div>
        <Button variant="primary" size="md" onClick={() => setCreateOpen(true)}>
          <Plus className="w-4 h-4" />
          Create payout
        </Button>
      </div>

      <div className="grid sm:grid-cols-2 gap-4">
        <SummaryCard
          label="Paid (in view)"
          value={formatGHS(totals.paid)}
          accent="success"
        />
        <SummaryCard
          label="Pending (in view)"
          value={formatGHS(totals.pending)}
          accent="warning"
        />
      </div>

      <div className="inline-flex rounded-xl border border-surface-border bg-surface-card p-1 overflow-x-auto">
        {STATUS_TABS.map((t) => (
          <button
            key={t.value || "all"}
            onClick={() => setTab(t.value)}
            className={`px-3 py-1.5 text-xs font-bold rounded-lg whitespace-nowrap transition-colors ${
              tab === t.value
                ? "bg-brand-primary text-white"
                : "text-gray-400 hover:text-white"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
          {error}
        </div>
      )}

      {loading ? (
        <div className="py-16 text-center">
          <Loader2 className="w-8 h-8 text-brand-primary animate-spin mx-auto" />
        </div>
      ) : payouts.length === 0 ? (
        <div className="py-16 text-center text-sm text-gray-500">
          No payouts found.
        </div>
      ) : (
        <div className="bg-surface-card border border-surface-border rounded-2xl overflow-hidden">
          <ul className="divide-y divide-surface-border">
            {payouts.map((p) => (
              <li key={p.id} className="p-4">
                <div className="flex items-start justify-between gap-3 flex-wrap">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-bold text-white">
                        {p.vendor_name}
                      </span>
                      <span
                        className={`text-[10px] px-2 py-0.5 rounded-md border font-bold uppercase ${
                          STATUS_BADGE[p.status] || STATUS_BADGE.cancelled
                        }`}
                      >
                        {p.status}
                      </span>
                    </div>
                    <div className="text-xs text-gray-400 mt-0.5">
                      {formatDateTime(p.created_at)} · {p.method} ·{" "}
                      {p.order_count} order{p.order_count === 1 ? "" : "s"}
                    </div>
                    {p.failure_reason && (
                      <div className="text-[11px] text-red-400 mt-1">
                        {p.failure_reason}
                      </div>
                    )}
                  </div>
                  <div className="text-right shrink-0">
                    <div className="text-xs text-gray-500">Net</div>
                    <div className="text-brand-primary font-bold">
                      {formatGHS(p.net_payout)}
                    </div>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2 mt-3">
                  {["requested", "processing"].includes(p.status) && (
                    <>
                      <Button
                        variant="success"
                        size="sm"
                        loading={busyId === p.id}
                        onClick={() => markPaid(p)}
                      >
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        Mark paid
                      </Button>
                      <Button
                        variant="danger"
                        size="sm"
                        onClick={() => setFailTarget(p)}
                      >
                        <XCircle className="w-3.5 h-3.5" />
                        Mark failed
                      </Button>
                    </>
                  )}
                  {["requested", "failed"].includes(p.status) && (
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => setCancelTarget(p)}
                    >
                      <Ban className="w-3.5 h-3.5" />
                      Cancel
                    </Button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Create modal */}
      <Modal
        open={createOpen}
        onClose={() => !creating && setCreateOpen(false)}
        title="Create payout"
        maxWidth="max-w-md"
        disableClose={creating}
      >
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-gray-300 mb-1.5">
              Vendor
            </label>
            <select
              value={vendorId}
              onChange={(e) => setVendorId(e.target.value)}
              className="w-full px-4 py-3 rounded-xl bg-surface-dark border border-surface-border text-white text-sm focus:border-brand-primary outline-none"
            >
              <option value="">Select a vendor…</option>
              {vendors.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.business_name} · {v.status}
                </option>
              ))}
            </select>
            {vendors.length === 0 && (
              <div className="text-[11px] text-amber-400 mt-2">
                No active vendors found. Ensure you have active vendors in the system.
              </div>
            )}
          </div>
          <div>
            <label className="block text-xs font-bold text-gray-300 mb-1.5">
              Method
            </label>
            <select
              value={method}
              onChange={(e) => setMethod(e.target.value)}
              className="w-full px-4 py-3 rounded-xl bg-surface-dark border border-surface-border text-white text-sm focus:border-brand-primary outline-none"
            >
              <option value="paystack_transfer">Paystack transfer</option>
              <option value="manual">Manual</option>
            </select>
          </div>
        </div>
        <div className="flex justify-end gap-2 mt-6">
          <Button
            variant="secondary"
            onClick={() => setCreateOpen(false)}
            disabled={creating}
          >
            Cancel
          </Button>
          <Button variant="primary" loading={creating} onClick={createPayout}>
            Create
          </Button>
        </div>
      </Modal>

      {/* Mark failed */}
      <Modal
        open={!!failTarget}
        onClose={() => !failing && setFailTarget(null)}
        title={`Mark payout as failed?`}
        maxWidth="max-w-md"
        disableClose={failing}
      >
        <Input
          label="Reason"
          value={failReason}
          onChange={(e) => setFailReason(e.target.value)}
          placeholder="e.g. Recipient account closed"
        />
        <div className="flex justify-end gap-2 mt-6">
          <Button
            variant="secondary"
            onClick={() => setFailTarget(null)}
            disabled={failing}
          >
            Cancel
          </Button>
          <Button variant="danger" loading={failing} onClick={doMarkFailed}>
            Confirm
          </Button>
        </div>
      </Modal>

      {/* Cancel */}
      <Modal
        open={!!cancelTarget}
        onClose={() => !cancelling && setCancelTarget(null)}
        title={`Cancel payout?`}
        maxWidth="max-w-md"
        disableClose={cancelling}
      >
        <Input
          label="Reason (optional)"
          value={cancelReason}
          onChange={(e) => setCancelReason(e.target.value)}
        />
        <div className="flex justify-end gap-2 mt-6">
          <Button
            variant="secondary"
            onClick={() => setCancelTarget(null)}
            disabled={cancelling}
          >
            Cancel
          </Button>
          <Button variant="danger" loading={cancelling} onClick={doCancel}>
            Confirm cancel
          </Button>
        </div>
      </Modal>
    </div>
  );
}

function SummaryCard({ label, value, accent }) {
  const colors = {
    success: "text-emerald-400 border-emerald-500/30",
    warning: "text-amber-400 border-amber-500/30",
  };
  return (
    <div className="bg-surface-card border border-surface-border rounded-2xl p-5">
      <div className="text-[10px] uppercase tracking-wider font-bold text-gray-500 flex items-center gap-1">
        <Banknote className={`w-3 h-3 ${colors[accent]?.split(" ")[0] || ""}`} />
        {label}
      </div>
      <div className="mt-2 text-2xl font-black text-white">{value}</div>
    </div>
  );
}