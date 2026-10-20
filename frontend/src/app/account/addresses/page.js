"use client";

import { useEffect, useState } from "react";
import {
  MapPin,
  Loader2,
  Plus,
  Trash2,
  AlertCircle,
  RefreshCw,
} from "lucide-react";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Modal from "@/components/ui/Modal";
import EmptyState from "@/components/ui/EmptyState";
import { useToast } from "@/components/ui/Toast";
import { customerFetch } from "@/lib/customerAuth";
import { API_URL } from "@/lib/api";

const EMPTY_FORM = {
  label: "Home",
  zone_name: "",
  address: "",
  is_default: false,
};

export default function AddressesPage() {
  const toast = useToast();
  const [addresses, setAddresses] = useState([]);
  const [zones, setZones] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [open, setOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const [aRes, zRes] = await Promise.all([
        customerFetch(`${API_URL}/api/v1/customer-account/addresses`),
        fetch(`${API_URL}/api/v1/delivery-zones?active_only=true`),
      ]);
      if (aRes.ok) {
        const data = await aRes.json().catch(() => []);
        setAddresses(Array.isArray(data) ? data : []);
      }
      if (zRes.ok) {
        const data = await zRes.json().catch(() => []);
        setZones(Array.isArray(data) ? data : []);
      }
      if (!aRes.ok) throw new Error(`Failed to load addresses (${aRes.status})`);
    } catch (e) {
      setError(e.message || "Failed to load");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  function closeModal() {
    if (saving) return;
    setOpen(false);
    setForm(EMPTY_FORM);
  }

  async function save() {
    if (!form.zone_name || !form.address.trim()) {
      toast.error("Zone and address are required");
      return;
    }
    setSaving(true);
    try {
      const res = await customerFetch(
        `${API_URL}/api/v1/customer-account/addresses`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            ...form,
            address: form.address.trim(),
          }),
        }
      );
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || `Failed (${res.status})`);
      }
      toast.success("Address saved");
      closeModal();
      await load();
    } catch (e) {
      toast.error(e.message || "Failed to save address");
    } finally {
      setSaving(false);
    }
  }

  async function remove(id) {
    if (!id) return;
    if (!window.confirm("Remove this address?")) return;
    setDeletingId(id);
    const prev = addresses;
    setAddresses((list) => list.filter((a) => a.id !== id)); // optimistic
    try {
      const res = await customerFetch(
        `${API_URL}/api/v1/customer-account/addresses/${id}`,
        { method: "DELETE" }
      );
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Failed to remove");
      }
      toast.success("Address removed");
    } catch (e) {
      setAddresses(prev); // rollback
      toast.error(e.message || "Failed to remove address");
    } finally {
      setDeletingId(null);
    }
  }

  if (loading) {
    return (
      <div className="space-y-4" aria-busy="true">
        <div className="animate-pulse h-8 w-40 bg-surface-card border border-surface-border rounded-xl" />
        {[0, 1].map((i) => (
          <div
            key={i}
            className="animate-pulse h-24 bg-surface-card border border-surface-border rounded-2xl"
          />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <h1 className="font-heading text-2xl font-black text-white">
          Addresses
        </h1>
        <div className="flex items-center gap-2">
          <button
            onClick={load}
            aria-label="Refresh addresses"
            className="p-2 rounded-xl bg-surface-card border border-surface-border text-gray-300 hover:text-white hover:border-brand-primary transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <Button variant="primary" size="sm" onClick={() => setOpen(true)}>
            <Plus className="w-4 h-4" /> Add
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm flex items-start gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {addresses.length === 0 ? (
        <EmptyState
          icon={MapPin}
          title="No saved addresses"
          message="Add a delivery address to speed up checkout."
          action={
            <Button onClick={() => setOpen(true)}>
              <Plus className="w-4 h-4" /> Add address
            </Button>
          }
        />
      ) : (
        <ul className="space-y-3">
          {addresses.map((a) => (
            <li
              key={a.id}
              className="flex items-start justify-between gap-3 p-4 bg-surface-card border border-surface-border rounded-2xl"
            >
              <div className="min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-bold text-white">{a.label}</span>
                  {a.is_default && (
                    <span className="text-[10px] bg-brand-primary/20 text-brand-primary px-2 py-0.5 rounded-md font-bold uppercase">
                      Default
                    </span>
                  )}
                </div>
                <div className="text-sm text-gray-400 mt-1">{a.address}</div>
                <div className="text-xs text-gray-500">{a.zone_name}</div>
              </div>
              <button
                onClick={() => remove(a.id)}
                disabled={deletingId === a.id}
                aria-label={`Remove ${a.label} address`}
                className="p-2 text-red-400 hover:bg-red-500/10 rounded-lg transition-colors disabled:opacity-40 shrink-0"
              >
                {deletingId === a.id ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Trash2 className="w-4 h-4" />
                )}
              </button>
            </li>
          ))}
        </ul>
      )}

      <Modal
        open={open}
        onClose={closeModal}
        title="Add address"
        disableClose={saving}
      >
        <div className="space-y-4">
          <Input
            label="Label"
            placeholder="Home, Work…"
            value={form.label}
            onChange={(e) => setForm({ ...form, label: e.target.value })}
          />

          <div>
            <label
              htmlFor="zone-select"
              className="block text-xs font-bold text-gray-300 mb-1.5"
            >
              Delivery zone
            </label>
            <select
              id="zone-select"
              value={form.zone_name}
              onChange={(e) =>
                setForm({ ...form, zone_name: e.target.value })
              }
              className="w-full px-4 py-3 rounded-xl bg-surface-dark border border-surface-border text-white text-sm focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/40 outline-none"
            >
              <option value="">Select a zone…</option>
              {zones.map((z) => (
                <option key={z.id} value={z.name}>
                  {z.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label
              htmlFor="address-input"
              className="block text-xs font-bold text-gray-300 mb-1.5"
            >
              Full address
            </label>
            <textarea
              id="address-input"
              rows={3}
              value={form.address}
              onChange={(e) => setForm({ ...form, address: e.target.value })}
              className="w-full px-4 py-3 rounded-xl bg-surface-dark border border-surface-border text-white text-sm focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/40 outline-none resize-none"
              placeholder="e.g. Pent Block C Room 204, UG Legon"
            />
          </div>

          <label className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer">
            <input
              type="checkbox"
              checked={form.is_default}
              onChange={(e) =>
                setForm({ ...form, is_default: e.target.checked })
              }
              className="accent-brand-primary"
            />
            Set as default address
          </label>
        </div>
        <div className="flex justify-end gap-2 mt-6">
          <Button
            variant="secondary"
            onClick={closeModal}
            disabled={saving}
          >
            Cancel
          </Button>
          <Button variant="primary" loading={saving} onClick={save}>
            Save
          </Button>
        </div>
      </Modal>
    </div>
  );
}