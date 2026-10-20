"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Loader2,
  Banknote,
  AlertCircle,
  Save,
  CheckCircle2,
  ShieldOff,
  Lock,
} from "lucide-react";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Modal from "@/components/ui/Modal";
import { useToast } from "@/components/ui/Toast";
import { adminApi } from "@/lib/adminApi";
import { formatGHS, formatDateTime } from "@/lib/utils";

const STATUS_BADGE = {
  pending: "text-amber-400 bg-amber-500/10 border-amber-500/30",
  active: "text-emerald-400 bg-emerald-500/10 border-emerald-500/30",
  suspended: "text-red-400 bg-red-500/10 border-red-500/30",
  closed: "text-gray-400 bg-white/5 border-white/10",
};

export default function AdminVendorDetailPage() {
  const params = useParams();
  const router = useRouter();
  const toast = useToast();
  const vendorId = params?.id;

  const [vendor, setVendor] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [override, setOverride] = useState("");
  const [savingOverride, setSavingOverride] = useState(false);

  const [payoutOpen, setPayoutOpen] = useState(false);
  const [payoutMethod, setPayoutMethod] = useState("paystack_transfer");
  const [payoutNote, setPayoutNote] = useState("");
  const [payouting, setPayouting] = useState(false);

  const [statusOpen, setStatusOpen] = useState(null);
  const [statusReason, setStatusReason] = useState("");
  const [statusSaving, setStatusSaving] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const data = await adminApi.get(`/api/v1/vendors/${vendorId}`);
      setVendor(data);
      setOverride(
        data.commission_pct_override != null
          ? String(data.commission_pct_override)
          : ""
      );
      setError("");
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (vendorId) load();
  }, [vendorId]);

  async function saveOverride() {
    setSavingOverride(true);
    try {
      const n = parseFloat(override);
      const payload = {
        commission_pct_override: Number.isFinite(n) ? n : null,
      };
      await adminApi.patch(`/api/v1/vendors/${vendorId}`, payload);
      toast.success("Commission saved");
      await load();
    } catch (e) {
      toast.error(e.message);
    } finally {
      setSavingOverride(false);
    }
  }

  async function createPayout() {
    setPayouting(true);
    try {
      await adminApi.post("/api/v1/admin/payouts", {
        vendor_id: vendorId,
        method: payoutMethod,
        note: payoutNote.trim() || null,
      });
      toast.success("Payout created");
      setPayoutOpen(false);
      setPayoutNote("");
      await load();
    } catch (e) {
      toast.error(e.message);
    } finally {
      setPayouting(false);
    }
  }

  async function setStatus() {
    if (!statusOpen) return;
    setStatusSaving(true);
    try {
      await adminApi.post(`/api/v1/vendors/${vendorId}/status`, {
        status: statusOpen,
        reason: statusReason.trim() || null,
      });
      toast.success(`Status set to ${statusOpen}`);
      setStatusOpen(null);
      setStatusReason("");
      await load();
    } catch (e) {
      toast.error(e.message);
    } finally {
      setStatusSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="py-16 text-center">
        <Loader2 className="w-8 h-8 text-brand-primary animate-spin mx-auto" />
      </div>
    );
  }

  if (error || !vendor) {
    return (
      <div className="space-y-4">
        <Link
          href="/admin/vendors"
          className="inline-flex items-center gap-2 text-sm font-bold text-gray-400 hover:text-brand-primary"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to vendors
        </Link>
        <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm flex items-start gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <span>{error || "Vendor not found"}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Link
        href="/admin/vendors"
        className="inline-flex items-center gap-2 text-sm font-bold text-gray-400 hover:text-brand-primary"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to vendors
      </Link>

      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-2xl bg-brand-primary/10 border border-brand-primary/20 flex items-center justify-center overflow-hidden">
            {vendor.logo_url ? (
              <img
                src={vendor.logo_url}
                alt=""
                className="w-full h-full object-cover"
              />
            ) : (
              <span className="font-heading text-2xl font-black text-brand-primary">
                {vendor.business_name.slice(0, 1)}
              </span>
            )}
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="font-heading text-2xl sm:text-3xl font-black text-white">
                {vendor.business_name}
              </h1>
              <span
                className={`text-[10px] px-2 py-0.5 rounded-md border font-bold uppercase ${
                  STATUS_BADGE[vendor.status] || STATUS_BADGE.closed
                }`}
              >
                {vendor.status}
              </span>
            </div>
            <div className="text-xs text-gray-500 mt-1 font-mono">
              {vendor.slug}
            </div>
          </div>
        </div>
        <div className="flex gap-2 flex-wrap">
          {vendor.status === "active" ? (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setStatusOpen("suspended")}
            >
              <ShieldOff className="w-4 h-4" />
              Suspend
            </Button>
          ) : (
            <Button
              variant="success"
              size="sm"
              onClick={() => setStatusOpen("active")}
            >
              <CheckCircle2 className="w-4 h-4" />
              Activate
            </Button>
          )}
          {vendor.status !== "closed" && (
            <Button
              variant="danger"
              size="sm"
              onClick={() => setStatusOpen("closed")}
            >
              <Lock className="w-4 h-4" />
              Close
            </Button>
          )}
          <Button
            variant="primary"
            size="sm"
            onClick={() => setPayoutOpen(true)}
          >
            <Banknote className="w-4 h-4" />
            Force payout
          </Button>
        </div>
      </div>

      {/* Financials */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Metric
          label="Available balance"
          value={formatGHS(vendor.available_balance)}
        />
        <Metric
          label="Lifetime gross"
          value={formatGHS(vendor.total_gross_sales)}
        />
        <Metric
          label="Lifetime fees"
          value={formatGHS(vendor.lifetime_platform_fees)}
        />
        <Metric
          label="Lifetime paid"
          value={formatGHS(vendor.lifetime_paid_out)}
        />
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <Card title="Business">
            <Row label="Description" value={vendor.description} />
            <Row label="Category" value={vendor.business_category} />
            <Row label="Subtype" value={vendor.business_subtype} />
            <Row label="Contact email" value={vendor.contact_email} />
            <Row label="Contact phone" value={vendor.contact_phone} />
          </Card>

          <Card title="Pickup">
            <Row label="Address" value={vendor.pickup_address} />
            <Row
              label="Coordinates"
              value={
                vendor.pickup_lat != null && vendor.pickup_lng != null
                  ? `${vendor.pickup_lat}, ${vendor.pickup_lng}`
                  : null
              }
            />
            <Row
              label="Delivery radius"
              value={
                vendor.delivery_radius_km != null
                  ? `${vendor.delivery_radius_km} km`
                  : null
              }
            />
            <Row
              label="Prep time"
              value={
                vendor.prep_minutes != null
                  ? `${vendor.prep_minutes} min`
                  : null
              }
            />
          </Card>

          <Card title="Payout recipient">
            <Row label="Recipient code" value={vendor.payout_recipient_code} mono />
            <Row label="Type" value={vendor.payout_recipient_type} />
            <Row label="Account name" value={vendor.payout_account_name} />
            <Row label="Account number" value={vendor.payout_account_number} mono />
            <Row label="Bank code" value={vendor.payout_bank_code} />
            <Row label="Mobile provider" value={vendor.payout_mobile_provider} />
          </Card>
        </div>

        <div className="space-y-4">
          <Card title="Commission override">
            <p className="text-xs text-gray-400 mb-3">
              Leave blank to use the platform default (
              {vendor.business_category === "food" ? "food" : "retail"}).
            </p>
            <Input
              label="Override %"
              type="number"
              min="0"
              max="100"
              step="0.5"
              value={override}
              onChange={(e) => setOverride(e.target.value)}
              placeholder="e.g. 18"
            />
            <Button
              variant="primary"
              size="md"
              className="w-full mt-3"
              loading={savingOverride}
              onClick={saveOverride}
            >
              <Save className="w-4 h-4" />
              Save override
            </Button>
          </Card>

          <Card title="Meta">
            <Row label="Created" value={formatDateTime(vendor.created_at)} />
            <Row label="Approved" value={formatDateTime(vendor.approved_at)} />
            <Row label="Orders" value={String(vendor.total_orders)} />
            <Row
              label="Rating"
              value={
                vendor.average_rating > 0
                  ? `${vendor.average_rating.toFixed(1)} (${vendor.total_reviews})`
                  : "—"
              }
            />
          </Card>
        </div>
      </div>

      {/* Force payout modal */}
      <Modal
        open={payoutOpen}
        onClose={() => !payouting && setPayoutOpen(false)}
        title={`Force payout — ${vendor.business_name}`}
        maxWidth="max-w-md"
        disableClose={payouting}
      >
        <div className="space-y-4">
          <div className="p-3 rounded-xl bg-brand-primary/10 border border-brand-primary/30">
            <div className="text-[10px] uppercase font-bold text-brand-primary tracking-wider">
              Amount
            </div>
            <div className="text-2xl font-black text-white mt-1">
              {formatGHS(vendor.available_balance)}
            </div>
          </div>
          <div>
            <label className="block text-xs font-bold text-gray-300 mb-1.5">
              Method
            </label>
            <select
              value={payoutMethod}
              onChange={(e) => setPayoutMethod(e.target.value)}
              className="w-full px-4 py-3 rounded-xl bg-surface-dark border border-surface-border text-white text-sm focus:border-brand-primary outline-none"
            >
              <option value="paystack_transfer">Paystack transfer</option>
              <option value="manual">Manual</option>
            </select>
          </div>
          <Input
            label="Note (optional)"
            value={payoutNote}
            onChange={(e) => setPayoutNote(e.target.value)}
          />
        </div>
        <div className="flex justify-end gap-2 mt-6">
          <Button
            variant="secondary"
            onClick={() => setPayoutOpen(false)}
            disabled={payouting}
          >
            Cancel
          </Button>
          <Button variant="primary" loading={payouting} onClick={createPayout}>
            Create payout
          </Button>
        </div>
      </Modal>

      {/* Status modal */}
      <Modal
        open={!!statusOpen}
        onClose={() => !statusSaving && setStatusOpen(null)}
        title={`Set status to "${statusOpen}"?`}
        maxWidth="max-w-md"
        disableClose={statusSaving}
      >
        <Input
          label="Reason (optional)"
          value={statusReason}
          onChange={(e) => setStatusReason(e.target.value)}
        />
        <div className="flex justify-end gap-2 mt-6">
          <Button
            variant="secondary"
            onClick={() => setStatusOpen(null)}
            disabled={statusSaving}
          >
            Cancel
          </Button>
          <Button variant="primary" loading={statusSaving} onClick={setStatus}>
            Confirm
          </Button>
        </div>
      </Modal>
    </div>
  );
}

function Metric({ label, value }) {
  return (
    <div className="bg-surface-card border border-surface-border rounded-2xl p-5">
      <div className="text-[10px] uppercase tracking-wider font-bold text-gray-500">
        {label}
      </div>
      <div className="mt-2 text-xl font-black text-white">{value}</div>
    </div>
  );
}

function Card({ title, children }) {
  return (
    <section className="bg-surface-card border border-surface-border rounded-2xl p-5">
      <h2 className="font-heading text-lg font-bold text-white mb-3">{title}</h2>
      <div className="space-y-2 text-sm">{children}</div>
    </section>
  );
}

function Row({ label, value, mono }) {
  if (!value) return null;
  return (
    <div className="flex justify-between gap-3">
      <span className="text-gray-500 shrink-0">{label}</span>
      <span
        className={`text-right break-all ${
          mono ? "text-gray-200 font-mono text-xs" : "text-gray-200"
        }`}
      >
        {value}
      </span>
    </div>
  );
}