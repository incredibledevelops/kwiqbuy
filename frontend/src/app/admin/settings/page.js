"use client";

import { useEffect, useState } from "react";
import { Loader2, Save, Percent, Truck, Banknote, MessageCircle } from "lucide-react";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import { useToast } from "@/components/ui/Toast";
import { adminApi } from "@/lib/adminApi";

export default function AdminSettingsPage() {
  const toast = useToast();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const data = await adminApi.get("/api/v1/admin/settings");
        setForm(data);
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  function set(k, v) {
    setForm((f) => ({ ...f, [k]: v }));
  }

  async function save() {
    setSaving(true);
    try {
      const editable = [
        "commission_pct",
        "food_commission_pct",
        "retail_commission_pct",
        "platform_delivery_cut_pct",
        "min_payout_ghs",
        "payout_schedule",
        "free_delivery_threshold",
        "rider_fee_model",
        "rider_flat_fee_ghs",
        "rider_pct_of_delivery_fee",
        "support_phone",
        "support_email",
        "support_whatsapp",
        "maintenance_mode",
        "customer_ordering_enabled",
        "vendor_signups_enabled",
      ];
      const payload = {};
      for (const k of editable) {
        if (form[k] !== undefined && form[k] !== null && form[k] !== "") {
          payload[k] = form[k];
        }
      }
      const updated = await adminApi.patch("/api/v1/admin/settings", payload);
      setForm(updated);
      toast.success("Settings saved");
    } catch (e) {
      toast.error(e.message);
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="py-16 text-center">
        <Loader2 className="w-8 h-8 text-brand-primary animate-spin mx-auto" />
      </div>
    );
  }

  if (error || !form) {
    return (
      <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
        {error || "Failed to load settings"}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-heading text-3xl font-black text-white">Settings</h1>
        <p className="text-sm text-gray-400 mt-1">
          Platform-wide defaults for commissions, delivery, and support.
        </p>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <Card icon={Percent} title="Commission">
          <Num
            label="Default commission %"
            value={form.commission_pct}
            onChange={(v) => set("commission_pct", v)}
            hint="Fallback for categories not covered below."
          />
          <Num
            label="Food commission %"
            value={form.food_commission_pct}
            onChange={(v) => set("food_commission_pct", v)}
          />
          <Num
            label="Retail commission %"
            value={form.retail_commission_pct}
            onChange={(v) => set("retail_commission_pct", v)}
          />
        </Card>

        <Card icon={Truck} title="Delivery">
          <Num
            label="Platform cut from delivery fee %"
            value={form.platform_delivery_cut_pct}
            onChange={(v) => set("platform_delivery_cut_pct", v)}
            hint="Rider keeps the rest."
          />
          <Num
            label="Free delivery threshold (GHS)"
            value={form.free_delivery_threshold}
            onChange={(v) => set("free_delivery_threshold", v)}
            hint="Subtotal at or above this ships free."
          />
        </Card>

        <Card icon={Banknote} title="Payouts">
          <Num
            label="Minimum payout (GHS)"
            value={form.min_payout_ghs}
            onChange={(v) => set("min_payout_ghs", v)}
          />
          <Select
            label="Payout schedule"
            value={form.payout_schedule}
            onChange={(v) => set("payout_schedule", v)}
            options={[
              { value: "manual", label: "Manual" },
              { value: "weekly", label: "Weekly" },
              { value: "monthly", label: "Monthly" },
            ]}
          />
        </Card>

        <Card icon={Truck} title="Rider fees">
          <Select
            label="Fee model"
            value={form.rider_fee_model}
            onChange={(v) => set("rider_fee_model", v)}
            options={[
              { value: "flat", label: "Flat fee" },
              { value: "pct_of_delivery_fee", label: "Percent of delivery fee" },
            ]}
          />
          <Num
            label="Flat fee (GHS)"
            value={form.rider_flat_fee_ghs}
            onChange={(v) => set("rider_flat_fee_ghs", v)}
          />
          <Num
            label="% of delivery fee"
            value={form.rider_pct_of_delivery_fee}
            onChange={(v) => set("rider_pct_of_delivery_fee", v)}
          />
        </Card>

        <Card icon={MessageCircle} title="Support">
          <Input
            label="Support phone"
            value={form.support_phone || ""}
            onChange={(e) => set("support_phone", e.target.value)}
          />
          <Input
            label="Support WhatsApp"
            value={form.support_whatsapp || ""}
            onChange={(e) => set("support_whatsapp", e.target.value)}
          />
          <Input
            label="Support email"
            type="email"
            value={form.support_email || ""}
            onChange={(e) => set("support_email", e.target.value)}
          />
        </Card>

        <Card icon={Save} title="Platform controls">
          <Toggle
            label="Maintenance mode"
            value={!!form.maintenance_mode}
            onChange={(v) => set("maintenance_mode", v)}
            hint="Blocks all customer-facing traffic."
          />
          <Toggle
            label="Customer ordering enabled"
            value={!!form.customer_ordering_enabled}
            onChange={(v) => set("customer_ordering_enabled", v)}
          />
          <Toggle
            label="Vendor signups enabled"
            value={!!form.vendor_signups_enabled}
            onChange={(v) => set("vendor_signups_enabled", v)}
          />
        </Card>
      </div>

      <div className="sticky bottom-4 bg-surface-dark/90 backdrop-blur border border-surface-border rounded-2xl p-3">
        <Button
          variant="primary"
          size="lg"
          className="w-full"
          loading={saving}
          onClick={save}
        >
          <Save className="w-4 h-4" />
          Save all settings
        </Button>
      </div>
    </div>
  );
}

function Card({ icon: Icon, title, children }) {
  return (
    <section className="bg-surface-card border border-surface-border rounded-2xl p-5 space-y-3">
      <h2 className="font-heading text-lg font-bold text-white flex items-center gap-2">
        <Icon className="w-5 h-5 text-brand-primary" />
        {title}
      </h2>
      {children}
    </section>
  );
}

function Num({ label, value, onChange, hint }) {
  return (
    <Input
      label={label}
      type="number"
      step="0.01"
      value={value ?? ""}
      onChange={(e) => onChange(e.target.value === "" ? "" : parseFloat(e.target.value))}
      hint={hint}
    />
  );
}

function Select({ label, value, onChange, options }) {
  return (
    <div>
      <label className="block text-xs font-bold text-gray-300 mb-1.5">
        {label}
      </label>
      <select
        value={value || ""}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-4 py-3 rounded-xl bg-surface-dark border border-surface-border text-white text-sm focus:border-brand-primary outline-none"
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </div>
  );
}

function Toggle({ label, value, onChange, hint }) {
  return (
    <label className="flex items-start gap-2 cursor-pointer text-sm text-gray-300">
      <input
        type="checkbox"
        checked={value}
        onChange={(e) => onChange(e.target.checked)}
        className="accent-brand-primary mt-1"
      />
      <div>
        <div className="font-bold text-white">{label}</div>
        {hint && <div className="text-xs text-gray-500">{hint}</div>}
      </div>
    </label>
  );
}