"use client";

import { useEffect, useState } from "react";
import {
  Loader2,
  AlertTriangle,
  CheckCircle2,
  XCircle,
} from "lucide-react";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Modal from "@/components/ui/Modal";
import EmptyState from "@/components/ui/EmptyState";
import { useToast } from "@/components/ui/Toast";
import { adminApi } from "@/lib/adminApi";
import { formatDateTime } from "@/lib/utils";

const STATUS_TABS = [
  { value: "open", label: "Open" },
  { value: "upheld", label: "Upheld" },
  { value: "rejected", label: "Rejected" },
  { value: "withdrawn", label: "Withdrawn" },
  { value: "", label: "All" },
];

const STATUS_BADGE = {
  open: "text-amber-400 bg-amber-500/10 border-amber-500/30",
  upheld: "text-emerald-400 bg-emerald-500/10 border-emerald-500/30",
  rejected: "text-red-400 bg-red-500/10 border-red-500/30",
  withdrawn: "text-gray-400 bg-white/5 border-white/10",
};

export default function AdminDisputesPage() {
  const toast = useToast();
  const [tab, setTab] = useState("open");
  const [disputes, setDisputes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Resolve
  const [target, setTarget] = useState(null); // { dispute, status }
  const [notes, setNotes] = useState("");
  const [resolving, setResolving] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const qs = tab ? `?status=${tab}&limit=200` : "?limit=200";
      const data = await adminApi.get(`/api/v1/admin/review-disputes${qs}`);
      setDisputes(Array.isArray(data?.items) ? data.items : []);
      setError("");
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [tab]);

  async function doResolve() {
    if (!target) return;
    setResolving(true);
    try {
      await adminApi.post(
        `/api/v1/admin/review-disputes/${target.dispute.id}/resolve`,
        {
          status: target.status,
          review_notes: notes.trim() || null,
        }
      );
      toast.success(
        target.status === "upheld"
          ? "Dispute upheld — review hidden"
          : "Dispute rejected — review stays"
      );
      setTarget(null);
      setNotes("");
      await load();
    } catch (e) {
      toast.error(e.message);
    } finally {
      setResolving(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-heading text-3xl font-black text-white">
          Review disputes
        </h1>
        <p className="text-sm text-gray-400 mt-1">
          Vendors can challenge reviews. Uphold to hide the review, or reject
          to keep it.
        </p>
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
      ) : disputes.length === 0 ? (
        <EmptyState icon={AlertTriangle} title="No disputes" />
      ) : (
        <div className="space-y-3">
          {disputes.map((d) => (
            <div
              key={d.id}
              className="bg-surface-card border border-surface-border rounded-2xl p-5"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded-md border font-bold uppercase ${
                        STATUS_BADGE[d.status] || STATUS_BADGE.withdrawn
                      }`}
                    >
                      {d.status}
                    </span>
                    <span className="font-mono text-xs text-brand-primary">
                      {d.order_reference}
                    </span>
                  </div>
                  <div className="text-[11px] text-gray-500 mt-1">
                    Review ID: {d.review_id.slice(0, 8)} · Vendor:{" "}
                    {d.vendor_id.slice(0, 8)}
                  </div>
                  <p className="text-sm text-gray-300 mt-2 whitespace-pre-wrap">
                    <span className="text-gray-500">Reason:</span> {d.reason}
                  </p>
                  {d.reviewed_at && (
                    <div className="text-[11px] text-gray-500 mt-2">
                      Resolved {formatDateTime(d.reviewed_at)}
                      {d.review_notes && ` — ${d.review_notes}`}
                    </div>
                  )}
                </div>
              </div>
              {d.status === "open" && (
                <div className="flex flex-wrap gap-2 mt-3 pt-3 border-t border-surface-border">
                  <Button
                    variant="success"
                    size="sm"
                    onClick={() => {
                      setTarget({ dispute: d, status: "upheld" });
                      setNotes("");
                    }}
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Uphold (hide review)
                  </Button>
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={() => {
                      setTarget({ dispute: d, status: "rejected" });
                      setNotes("");
                    }}
                  >
                    <XCircle className="w-3.5 h-3.5" />
                    Reject (keep review)
                  </Button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <Modal
        open={!!target}
        onClose={() => !resolving && setTarget(null)}
        title={
          target?.status === "upheld"
            ? "Uphold dispute — hide review?"
            : "Reject dispute — keep review?"
        }
        maxWidth="max-w-md"
        disableClose={resolving}
      >
        <div className="space-y-3">
          <p className="text-sm text-gray-300">
            {target?.status === "upheld"
              ? "The review will be hidden from the storefront."
              : "The review will stay live."}
          </p>
          <Input
            label="Notes (optional, stored for audit)"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
        </div>
        <div className="flex justify-end gap-2 mt-6">
          <Button
            variant="secondary"
            onClick={() => setTarget(null)}
            disabled={resolving}
          >
            Cancel
          </Button>
          <Button
            variant={target?.status === "upheld" ? "success" : "danger"}
            loading={resolving}
            onClick={doResolve}
          >
            Confirm
          </Button>
        </div>
      </Modal>
    </div>
  );
}