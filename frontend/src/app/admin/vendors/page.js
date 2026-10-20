"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  Loader2,
  Search,
  ChevronRight,
  Store,
  ShieldOff,
  ShieldCheck,
  Lock,
} from "lucide-react";
import Button from "@/components/ui/Button";
import Modal from "@/components/ui/Modal";
import Input from "@/components/ui/Input";
import EmptyState from "@/components/ui/EmptyState";
import { useToast } from "@/components/ui/Toast";
import { adminApi } from "@/lib/adminApi";
import { formatDateTime } from "@/lib/utils";

const STATUS_OPTIONS = [
  { value: "", label: "All" },
  { value: "pending", label: "Pending" },
  { value: "active", label: "Active" },
  { value: "suspended", label: "Suspended" },
  { value: "closed", label: "Closed" },
];

const CATEGORY_OPTIONS = [
  { value: "", label: "All categories" },
  { value: "food", label: "Food" },
  { value: "retail", label: "Retail" },
];

const STATUS_BADGE = {
  pending: "text-amber-400 bg-amber-500/10 border-amber-500/30",
  active: "text-emerald-400 bg-emerald-500/10 border-emerald-500/30",
  suspended: "text-red-400 bg-red-500/10 border-red-500/30",
  closed: "text-gray-400 bg-white/5 border-white/10",
};

export default function AdminVendorsPage() {
  const toast = useToast();
  const [vendors, setVendors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  const [category, setCategory] = useState("");
  const [query, setQuery] = useState("");

  const [actionModal, setActionModal] = useState(null); // { vendor, newStatus }
  const [actionReason, setActionReason] = useState("");
  const [actioning, setActioning] = useState(false);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams();
      if (status) params.set("status", status);
      if (category) params.set("category", category);
      if (query.trim()) params.set("search", query.trim());
      params.set("limit", "200");
      const data = await adminApi.get(`/api/v1/vendors?${params.toString()}`);
      setVendors(Array.isArray(data) ? data : []);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const t = setTimeout(load, query ? 300 : 0);
    return () => clearTimeout(t);
  }, [status, category, query]);

  async function doSetStatus() {
    if (!actionModal) return;
    setActioning(true);
    try {
      await adminApi.post(
        `/api/v1/vendors/${actionModal.vendor.id}/status`,
        {
          status: actionModal.newStatus,
          reason: actionReason.trim() || null,
        }
      );
      toast.success(`Vendor ${actionModal.newStatus}`);
      setActionModal(null);
      setActionReason("");
      await load();
    } catch (e) {
      toast.error(e.message);
    } finally {
      setActioning(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-heading text-3xl font-black text-white">Vendors</h1>
        <p className="text-sm text-gray-400 mt-1">
          Manage all sellers on the platform
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by name or slug…"
            className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-surface-card border border-surface-border text-white text-sm focus:border-brand-primary outline-none"
          />
        </div>
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="px-3 py-2.5 rounded-xl bg-surface-card border border-surface-border text-white text-sm focus:border-brand-primary outline-none"
        >
          {STATUS_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="px-3 py-2.5 rounded-xl bg-surface-card border border-surface-border text-white text-sm focus:border-brand-primary outline-none"
        >
          {CATEGORY_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
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
      ) : vendors.length === 0 ? (
        <EmptyState icon={Store} title="No vendors" />
      ) : (
        <div className="bg-surface-card border border-surface-border rounded-2xl overflow-hidden">
          <ul className="divide-y divide-surface-border">
            {vendors.map((v) => (
              <li key={v.id} className="p-4 flex items-center gap-3">
                <div className="w-12 h-12 rounded-xl bg-brand-primary/10 border border-brand-primary/20 flex items-center justify-center shrink-0 overflow-hidden">
                  {v.logo_url ? (
                    <img
                      src={v.logo_url}
                      alt=""
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <Store className="w-5 h-5 text-brand-primary" />
                  )}
                </div>
                <Link
                  href={`/admin/vendors/${v.id}`}
                  className="flex-1 min-w-0 hover:text-brand-primary"
                >
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-bold text-white truncate">
                      {v.business_name}
                    </span>
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded-md border font-bold uppercase ${
                        STATUS_BADGE[v.status] || STATUS_BADGE.closed
                      }`}
                    >
                      {v.status}
                    </span>
                    <span className="text-[10px] px-2 py-0.5 rounded-md bg-white/5 text-gray-300 uppercase font-bold">
                      {v.business_category}
                    </span>
                  </div>
                  <div className="text-xs text-gray-400 mt-0.5 truncate">
                    {v.contact_email || "—"} · {v.contact_phone || "—"}
                  </div>
                  <div className="text-[11px] text-gray-500 mt-0.5">
                    Joined {formatDateTime(v.created_at)} ·{" "}
                    {v.total_orders} order{v.total_orders === 1 ? "" : "s"}
                  </div>
                </Link>
                <div className="flex items-center gap-1.5 shrink-0">
                  {v.status !== "active" && (
                    <button
                      onClick={() =>
                        setActionModal({ vendor: v, newStatus: "active" })
                      }
                      className="p-2 rounded-lg text-emerald-400 hover:bg-emerald-500/10"
                      title="Activate"
                    >
                      <ShieldCheck className="w-4 h-4" />
                    </button>
                  )}
                  {v.status === "active" && (
                    <button
                      onClick={() =>
                        setActionModal({ vendor: v, newStatus: "suspended" })
                      }
                      className="p-2 rounded-lg text-amber-400 hover:bg-amber-500/10"
                      title="Suspend"
                    >
                      <ShieldOff className="w-4 h-4" />
                    </button>
                  )}
                  {v.status !== "closed" && (
                    <button
                      onClick={() =>
                        setActionModal({ vendor: v, newStatus: "closed" })
                      }
                      className="p-2 rounded-lg text-red-400 hover:bg-red-500/10"
                      title="Close"
                    >
                      <Lock className="w-4 h-4" />
                    </button>
                  )}
                  <Link
                    href={`/admin/vendors/${v.id}`}
                    className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/5"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </Link>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      <Modal
        open={!!actionModal}
        onClose={() => !actioning && setActionModal(null)}
        title={`Set status to "${actionModal?.newStatus}"?`}
        maxWidth="max-w-md"
        disableClose={actioning}
      >
        <p className="text-sm text-gray-300 mb-3">
          <strong className="text-white">{actionModal?.vendor?.business_name}</strong>{" "}
          will be marked <strong className="text-white">{actionModal?.newStatus}</strong>.
        </p>
        <Input
          label="Reason (optional)"
          value={actionReason}
          onChange={(e) => setActionReason(e.target.value)}
          placeholder="Why are you changing this vendor's status?"
        />
        <div className="flex justify-end gap-2 mt-6">
          <Button
            variant="secondary"
            onClick={() => setActionModal(null)}
            disabled={actioning}
          >
            Cancel
          </Button>
          <Button variant="primary" loading={actioning} onClick={doSetStatus}>
            Confirm
          </Button>
        </div>
      </Modal>
    </div>
  );
}