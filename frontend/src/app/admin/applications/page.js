"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Loader2,
  CheckCircle2,
  XCircle,
  ChevronDown,
  ChevronRight,
  Search,
} from "lucide-react";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Modal from "@/components/ui/Modal";
import EmptyState from "@/components/ui/EmptyState";
import { useToast } from "@/components/ui/Toast";
import { adminApi } from "@/lib/adminApi";
import { formatDateTime } from "@/lib/utils";

const STATUS_TABS = [
  { value: "pending", label: "Pending" },
  { value: "approved", label: "Approved" },
  { value: "rejected", label: "Rejected" },
  { value: "expired", label: "Expired" },
  { value: "withdrawn", label: "Withdrawn" },
  { value: "", label: "All" },
];

export default function AdminApplicationsPage() {
  const toast = useToast();
  const [tab, setTab] = useState("pending");
  const [apps, setApps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [expanded, setExpanded] = useState(null);

  // Approve modal
  const [approveTarget, setApproveTarget] = useState(null);
  const [approveOverride, setApproveOverride] = useState("");
  const [approving, setApproving] = useState(false);
  const [approveResult, setApproveResult] = useState(null);

  // Reject modal
  const [rejectTarget, setRejectTarget] = useState(null);
  const [rejectReason, setRejectReason] = useState("");
  const [rejecting, setRejecting] = useState(false);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const qs = tab ? `?status=${tab}&limit=200` : "?limit=200";
      const data = await adminApi.get(`/api/v1/admin/vendor-applications${qs}`);
      setApps(Array.isArray(data) ? data : []);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [tab]);

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return apps;
    return apps.filter(
      (a) =>
        a.business_name?.toLowerCase().includes(q) ||
        a.contact_name?.toLowerCase().includes(q) ||
        a.contact_email?.toLowerCase().includes(q) ||
        a.contact_phone?.includes(q)
    );
  }, [apps, query]);

  async function doApprove() {
    if (!approveTarget) return;
    setApproving(true);
    try {
      const payload = {};
      const n = parseFloat(approveOverride);
      if (Number.isFinite(n)) payload.commission_pct_override = n;
      const res = await adminApi.post(
        `/api/v1/admin/vendor-applications/${approveTarget.id}/approve`,
        payload
      );
      setApproveResult(res);
      toast.success("Application approved successfully");
      await load();
    } catch (e) {
      toast.error(e.message);
    } finally {
      setApproving(false);
    }
  }

  async function doReject() {
    if (!rejectTarget) return;
    if (rejectReason.trim().length < 4) {
      toast.error("Please provide a reason (min 4 chars)");
      return;
    }
    setRejecting(true);
    try {
      await adminApi.post(
        `/api/v1/admin/vendor-applications/${rejectTarget.id}/reject`,
        { reason: rejectReason.trim() }
      );
      toast.success("Application rejected");
      setRejectTarget(null);
      setRejectReason("");
      await load();
    } catch (e) {
      toast.error(e.message);
    } finally {
      setRejecting(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-heading text-3xl font-black text-white">
          Vendor applications
        </h1>
        <p className="text-sm text-gray-400 mt-1">
          Approve or reject new sellers before they go live.
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-3">
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
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by business, email, phone…"
            className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-surface-card border border-surface-border text-white text-sm focus:border-brand-primary outline-none"
          />
        </div>
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
      ) : visible.length === 0 ? (
        <EmptyState title="No applications" message="Nothing here yet." />
      ) : (
        <div className="space-y-3">
          {visible.map((a) => {
            const isOpen = expanded === a.id;
            return (
              <div
                key={a.id}
                className="bg-surface-card border border-surface-border rounded-2xl overflow-hidden"
              >
                <button
                  onClick={() => setExpanded(isOpen ? null : a.id)}
                  className="w-full p-4 flex items-center gap-3 text-left hover:bg-white/5"
                >
                  {isOpen ? (
                    <ChevronDown className="w-4 h-4 text-gray-500 shrink-0" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-gray-500 shrink-0" />
                  )}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-bold text-white">
                        {a.business_name}
                      </span>
                      <span className="text-[10px] px-2 py-0.5 rounded-md bg-white/5 text-gray-300 uppercase tracking-wider font-bold">
                        {a.business_category || a.business_type || "—"}
                      </span>
                    </div>
                    <div className="text-xs text-gray-400 mt-0.5 truncate">
                      {a.contact_name} · {a.contact_email} · {a.contact_phone}
                    </div>
                    <div className="text-[11px] text-gray-500 mt-0.5">
                      Applied {formatDateTime(a.created_at)}
                    </div>
                  </div>
                  {a.status === "pending" && (
                    <div className="flex items-center gap-1.5">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setApproveTarget(a);
                          setApproveOverride("");
                          setApproveResult(null);
                        }}
                        className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 text-xs font-bold hover:bg-emerald-500/25"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        Approve
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setRejectTarget(a);
                          setRejectReason("");
                        }}
                        className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-red-500/15 border border-red-500/30 text-red-400 text-xs font-bold hover:bg-red-500/25"
                      >
                        <XCircle className="w-3.5 h-3.5" />
                        Reject
                      </button>
                    </div>
                  )}
                </button>

                {isOpen && (
                  <div className="px-4 pb-4 border-t border-surface-border pt-3 text-sm space-y-2">
                    <Row label="Description" value={a.description} />
                    <Row label="Pickup address" value={a.pickup_address} />
                    <Row label="City / region" value={[a.city, a.region].filter(Boolean).join(" · ")} />
                    <Row label="Requested payout" value={a.requested_payout_method} />
                    <Row label="ID document" value={a.id_document_url} mono />
                    <Row
                      label="Business registration"
                      value={a.business_registration_url}
                      mono
                    />
                    {a.rejection_reason && (
                      <Row
                        label="Rejection reason"
                        value={a.rejection_reason}
                        danger
                      />
                    )}
                    {a.created_vendor_id && (
                      <Row
                        label="Created vendor"
                        value={a.created_vendor_id}
                        mono
                      />
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Approve modal */}
      <Modal
        open={!!approveTarget && !approveResult}
        onClose={() => !approving && setApproveTarget(null)}
        title={`Approve ${approveTarget?.business_name || ""}`}
        maxWidth="max-w-md"
        disableClose={approving}
      >
        <div className="space-y-4">
          <p className="text-sm text-gray-300">
            A vendor account and user will be created. A temporary password
            will be shown once.
          </p>
          <Input
            label="Custom commission % (optional)"
            type="number"
            min="0"
            max="100"
            step="0.5"
            value={approveOverride}
            onChange={(e) => setApproveOverride(e.target.value)}
            placeholder="Leave blank for default"
          />
        </div>
        <div className="flex justify-end gap-2 mt-6">
          <Button
            variant="secondary"
            onClick={() => setApproveTarget(null)}
            disabled={approving}
          >
            Cancel
          </Button>
          <Button variant="primary" loading={approving} onClick={doApprove}>
            Approve
          </Button>
        </div>
      </Modal>

      {/* Approve result modal */}
      <Modal
        open={!!approveResult}
        onClose={() => {
          setApproveResult(null);
          setApproveTarget(null);
        }}
        title="Application approved"
        maxWidth="max-w-md"
      >
        <div className="space-y-3 text-sm">
          <p className="text-amber-300 bg-amber-500/10 border border-amber-500/30 rounded-xl p-3 text-xs">
            Copy the temporary password now — it will not be shown again.
          </p>
          <div className="space-y-2">
            <Readonly label="Owner email" value={approveResult?.owner_email} />
            <Readonly
              label="Temporary password"
              value={approveResult?.temporary_password}
              mono
            />
          </div>
        </div>
        <div className="flex justify-end mt-6">
          <Button
            variant="primary"
            onClick={() => {
              setApproveResult(null);
              setApproveTarget(null);
            }}
          >
            Done
          </Button>
        </div>
      </Modal>

      {/* Reject modal */}
      <Modal
        open={!!rejectTarget}
        onClose={() => !rejecting && setRejectTarget(null)}
        title={`Reject ${rejectTarget?.business_name || ""}`}
        maxWidth="max-w-md"
        disableClose={rejecting}
      >
        <Input
          label="Reason"
          value={rejectReason}
          onChange={(e) => setRejectReason(e.target.value)}
          placeholder="e.g. Incomplete documentation"
        />
        <div className="flex justify-end gap-2 mt-6">
          <Button
            variant="secondary"
            onClick={() => setRejectTarget(null)}
            disabled={rejecting}
          >
            Cancel
          </Button>
          <Button variant="danger" loading={rejecting} onClick={doReject}>
            Reject
          </Button>
        </div>
      </Modal>
    </div>
  );
}

function Row({ label, value, mono, danger }) {
  if (!value) return null;
  return (
    <div className="flex justify-between gap-4">
      <span className="text-gray-500 shrink-0">{label}</span>
      <span
        className={`text-right break-all ${
          danger
            ? "text-red-400"
            : mono
            ? "text-gray-200 font-mono text-xs"
            : "text-gray-200"
        }`}
      >
        {value}
      </span>
    </div>
  );
}

function Readonly({ label, value, mono }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wider text-gray-500 font-bold mb-1">
        {label}
      </div>
      <code
        className={`block p-2.5 rounded-lg bg-surface-dark border border-surface-border text-sm text-white break-all ${
          mono ? "font-mono" : ""
        }`}
      >
        {value || "—"}
      </code>
    </div>
  );
}