"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Loader2,
  Search,
  Bike,
  ShieldCheck,
  ShieldOff,
} from "lucide-react";
import Button from "@/components/ui/Button";
import Modal from "@/components/ui/Modal";
import EmptyState from "@/components/ui/EmptyState";
import { useToast } from "@/components/ui/Toast";
import { adminApi } from "@/lib/adminApi";
import { formatDateTime } from "@/lib/utils";

export default function AdminRidersPage() {
  const toast = useToast();
  const [riders, setRiders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  
  // Status modal state
  const [actionModal, setActionModal] = useState(null);
  const [actioning, setActioning] = useState(false);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const data = await adminApi.get("/api/v1/admin/riders");
      setRiders(Array.isArray(data) ? data : []);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return riders;
    return riders.filter(
      (r) =>
        r.full_name?.toLowerCase().includes(q) ||
        r.email?.toLowerCase().includes(q) ||
        r.phone?.includes(q) ||
        r.plate_number?.toLowerCase().includes(q)
    );
  }, [riders, query]);

  async function toggleStatus() {
    if (!actionModal) return;
    setActioning(true);
    try {
      await adminApi.patch(`/api/v1/admin/riders/${actionModal.rider.id}/status`, {
        is_active: actionModal.newStatus,
      });
      toast.success(`Rider ${actionModal.newStatus ? "activated" : "suspended"}`);
      setActionModal(null);
      await load();
    } catch (e) {
      toast.error(e.message);
    } finally {
      setActioning(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="font-heading text-3xl font-black text-white">Riders</h1>
          <p className="text-sm text-gray-400 mt-1">
            Manage delivery personnel
          </p>
        </div>
      </div>

      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search by name, email, or plate number…"
          className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-surface-card border border-surface-border text-white text-sm focus:border-brand-primary outline-none"
        />
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
        <EmptyState icon={Bike} title="No riders found" message="Riders will appear here once added." />
      ) : (
        <div className="bg-surface-card border border-surface-border rounded-2xl overflow-hidden">
          <ul className="divide-y divide-surface-border">
            {visible.map((r) => (
              <li key={r.id} className="p-4 flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-brand-primary/10 border border-brand-primary/20 flex items-center justify-center shrink-0">
                  <Bike className="w-5 h-5 text-brand-primary" />
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-bold text-white truncate">
                      {r.full_name}
                    </span>
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded-md border font-bold uppercase ${
                        r.is_active
                          ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/30"
                          : "text-red-400 bg-red-500/10 border-red-500/30"
                      }`}
                    >
                      {r.is_active ? "Active" : "Suspended"}
                    </span>
                  </div>
                  <div className="text-xs text-gray-400 mt-0.5 truncate">
                    {r.email} · {r.phone || "No phone"}
                  </div>
                  <div className="text-[11px] text-gray-500 mt-0.5">
                    Vehicle: {r.vehicle || "—"} · Plate: {r.plate_number || "—"} · Joined {formatDateTime(r.created_at)}
                  </div>
                </div>

                <div className="flex items-center gap-1.5 shrink-0">
                  {r.is_active ? (
                    <button
                      onClick={() => setActionModal({ rider: r, newStatus: false })}
                      className="p-2 rounded-lg text-amber-400 hover:bg-amber-500/10"
                      title="Suspend Rider"
                    >
                      <ShieldOff className="w-4 h-4" />
                    </button>
                  ) : (
                    <button
                      onClick={() => setActionModal({ rider: r, newStatus: true })}
                      className="p-2 rounded-lg text-emerald-400 hover:bg-emerald-500/10"
                      title="Activate Rider"
                    >
                      <ShieldCheck className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      <Modal
        open={!!actionModal}
        onClose={() => !actioning && setActionModal(null)}
        title={actionModal?.newStatus ? "Activate Rider?" : "Suspend Rider?"}
        maxWidth="max-w-md"
        disableClose={actioning}
      >
        <p className="text-sm text-gray-300">
          {actionModal?.newStatus
            ? `This will allow ${actionModal?.rider?.full_name} to log in and claim new deliveries.`
            : `This will immediately log ${actionModal?.rider?.full_name} out and prevent them from claiming new deliveries.`}
        </p>
        <div className="flex justify-end gap-2 mt-6">
          <Button
            variant="secondary"
            onClick={() => setActionModal(null)}
            disabled={actioning}
          >
            Cancel
          </Button>
          <Button
            variant={actionModal?.newStatus ? "success" : "danger"}
            loading={actioning}
            onClick={toggleStatus}
          >
            Confirm
          </Button>
        </div>
      </Modal>
    </div>
  );
}