"use client";

import { useEffect, useState } from "react";
import {
  Loader2,
  Save,
  Upload,
  MapPin,
  Building2,
  Phone,
  Banknote,
  X,
  AlertCircle,
} from "lucide-react";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import { useToast } from "@/components/ui/Toast";
import { vendorApi } from "@/lib/vendorApi";

export default function VendorProfilePage() {
  const toast = useToast();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploadingLogo, setUploadingLogo] = useState(false);
  const [uploadingBanner, setUploadingBanner] = useState(false);
  const [error, setError] = useState("");

  const [form, setForm] = useState({
    business_name: "",
    business_subtype: "",
    description: "",
    contact_email: "",
    contact_phone: "",
    pickup_address: "",
    pickup_lat: "",
    pickup_lng: "",
    delivery_radius_km: 15,
    prep_minutes: 20,
    logo_url: "",
    banner_url: "",
    // Payout
    payout_recipient_type: "",
    payout_account_name: "",
    payout_account_number: "",
    payout_bank_code: "",
    payout_mobile_provider: "",
    payout_recipient_code: "", // <--- Added this
  });

  useEffect(() => {
    (async () => {
      try {
        const me = await vendorApi.get("/api/v1/vendor/me");
        setForm({
          business_name: me.business_name || "",
          business_subtype: me.business_subtype || "",
          description: me.description || "",
          contact_email: me.contact_email || "",
          contact_phone: me.contact_phone || "",
          pickup_address: me.pickup_address || "",
          pickup_lat: me.pickup_lat != null ? String(me.pickup_lat) : "",
          pickup_lng: me.pickup_lng != null ? String(me.pickup_lng) : "",
          delivery_radius_km: me.delivery_radius_km ?? 15,
          prep_minutes: me.prep_minutes ?? 20,
          logo_url: me.logo_url || "",
          banner_url: me.banner_url || "",
          payout_recipient_type: me.payout_recipient_type || "",
          payout_account_name: me.payout_account_name || "",
          payout_account_number: me.payout_account_number || "",
          payout_bank_code: me.payout_bank_code || "",
          payout_mobile_provider: me.payout_mobile_provider || "",
          payout_recipient_code: me.payout_recipient_code || "",
        });
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

  async function uploadImage(file, kind) {
    if (!file) return;
    kind === "logo" ? setUploadingLogo(true) : setUploadingBanner(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("subdir", "vendors");
      const res = await vendorApi.upload("/api/v1/uploads/vendor", fd);
      set(kind === "logo" ? "logo_url" : "banner_url", res.url);
      toast.success(`${kind} uploaded`);
    } catch (e) {
      toast.error(e.message);
    } finally {
      kind === "logo" ? setUploadingLogo(false) : setUploadingBanner(false);
    }
  }

  async function save(e) {
    e?.preventDefault?.();
    setSaving(true);
    setError("");
    try {
      const payload = {
        business_name: form.business_name.trim(),
        business_subtype: form.business_subtype.trim() || null,
        description: form.description.trim() || null,
        contact_email: form.contact_email.trim() || null,
        contact_phone: form.contact_phone.trim() || null,
        pickup_address: form.pickup_address.trim(),
        pickup_lat: form.pickup_lat === "" ? null : parseFloat(form.pickup_lat),
        pickup_lng: form.pickup_lng === "" ? null : parseFloat(form.pickup_lng),
        delivery_radius_km: parseFloat(form.delivery_radius_km) || 15,
        prep_minutes: parseInt(form.prep_minutes, 10) || 20,
        logo_url: form.logo_url || null,
        banner_url: form.banner_url || null,
        // Payout fields
        payout_recipient_type: form.payout_recipient_type.trim() || null,
        payout_account_name: form.payout_account_name.trim() || null,
        payout_account_number: form.payout_account_number.trim() || null,
        payout_bank_code: form.payout_bank_code.trim() || null,
        payout_mobile_provider: form.payout_mobile_provider.trim() || null,
        payout_recipient_code: form.payout_recipient_code.trim() || null, // <--- Save this
      };
      
      await vendorApi.patch("/api/v1/vendor/me", payload);
      toast.success("Profile and payout details saved");
    } catch (e) {
      setError(e.message);
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

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-heading text-3xl font-black text-white">Profile</h1>
        <p className="text-sm text-gray-400 mt-1">
          Your business identity, contact details, and payout information.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
          {error}
        </div>
      )}

      <form onSubmit={save} className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {/* Business info */}
          <section className="bg-surface-card border border-surface-border rounded-2xl p-6 space-y-4">
            <h2 className="font-heading text-lg font-bold text-white flex items-center gap-2">
              <Building2 className="w-5 h-5 text-brand-primary" />
              Business info
            </h2>
            <Input
              label="Business name"
              required
              value={form.business_name}
              onChange={(e) => set("business_name", e.target.value)}
            />
            <Input
              label="Business subtype"
              value={form.business_subtype}
              onChange={(e) => set("business_subtype", e.target.value)}
              placeholder="e.g. restaurant, pharmacy, electronics"
            />
            <div>
              <label className="block text-xs font-bold text-gray-300 mb-1.5">
                Description
              </label>
              <textarea
                rows={3}
                value={form.description}
                onChange={(e) => set("description", e.target.value)}
                className="w-full px-4 py-3 rounded-xl bg-surface-dark border border-surface-border text-white text-sm focus:border-brand-primary outline-none resize-none"
              />
            </div>
          </section>

          {/* Contact */}
          <section className="bg-surface-card border border-surface-border rounded-2xl p-6 space-y-4">
            <h2 className="font-heading text-lg font-bold text-white flex items-center gap-2">
              <Phone className="w-5 h-5 text-brand-primary" />
              Contact
            </h2>
            <div className="grid sm:grid-cols-2 gap-4">
              <Input
                label="Contact email"
                type="email"
                value={form.contact_email}
                onChange={(e) => set("contact_email", e.target.value)}
              />
              <Input
                label="Contact phone"
                value={form.contact_phone}
                onChange={(e) => set("contact_phone", e.target.value)}
              />
            </div>
          </section>

          {/* Pickup location */}
          <section className="bg-surface-card border border-surface-border rounded-2xl p-6 space-y-4">
            <h2 className="font-heading text-lg font-bold text-white flex items-center gap-2">
              <MapPin className="w-5 h-5 text-brand-primary" />
              Pickup location
            </h2>
            <Input
              label="Pickup address"
              value={form.pickup_address}
              onChange={(e) => set("pickup_address", e.target.value)}
            />
            <div className="grid sm:grid-cols-2 gap-4">
              <Input
                label="Latitude"
                type="number"
                step="0.0001"
                value={form.pickup_lat}
                onChange={(e) => set("pickup_lat", e.target.value)}
                placeholder="e.g. 5.6355"
              />
              <Input
                label="Longitude"
                type="number"
                step="0.0001"
                value={form.pickup_lng}
                onChange={(e) => set("pickup_lng", e.target.value)}
                placeholder="e.g. -0.1766"
              />
            </div>
            <div className="grid sm:grid-cols-2 gap-4">
              <Input
                label="Delivery radius (km)"
                type="number"
                min="0.1"
                max="100"
                step="0.1"
                value={form.delivery_radius_km}
                onChange={(e) => set("delivery_radius_km", e.target.value)}
              />
              <Input
                label="Prep time (minutes)"
                type="number"
                min="1"
                max="1440"
                value={form.prep_minutes}
                onChange={(e) => set("prep_minutes", e.target.value)}
              />
            </div>
          </section>

          {/* Payout */}
          <section className="bg-surface-card border border-surface-border rounded-2xl p-6 space-y-4">
            <h2 className="font-heading text-lg font-bold text-white flex items-center gap-2">
              <Banknote className="w-5 h-5 text-brand-primary" />
              Payout details
            </h2>
            
            <div className="rounded-xl bg-brand-primary/10 border border-brand-primary/30 p-4 mb-2">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-brand-primary shrink-0 mt-0.5" />
                <div className="text-xs text-brand-primary">
                  To enable automated payouts, go to your <strong>Paystack Dashboard &rarr; Transfers &rarr; Recipients</strong>, create a recipient for this business, and paste the generated <strong>Recipient Code</strong> below.
                </div>
              </div>
            </div>

            <Input
              label="Paystack Recipient Code (e.g. RCP_xxxxxx)"
              value={form.payout_recipient_code}
              onChange={(e) => set("payout_recipient_code", e.target.value)}
              placeholder="RCP_..."
              required
            />

            <div className="grid sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-gray-300 mb-1.5">
                  Recipient type (optional)
                </label>
                <select
                  value={form.payout_recipient_type}
                  onChange={(e) =>
                    set("payout_recipient_type", e.target.value)
                  }
                  className="w-full px-4 py-3 rounded-xl bg-surface-dark border border-surface-border text-white text-sm focus:border-brand-primary outline-none"
                >
                  <option value="">Select…</option>
                  <option value="mobile_money">Mobile money</option>
                  <option value="ghipss">Bank (Ghipss)</option>
                </select>
              </div>
              <Input
                label="Mobile provider (optional)"
                value={form.payout_mobile_provider}
                onChange={(e) => set("payout_mobile_provider", e.target.value)}
                placeholder="e.g. mtn, vodafone"
              />
            </div>
            <div className="grid sm:grid-cols-2 gap-4">
              <Input
                label="Account name (optional)"
                value={form.payout_account_name}
                onChange={(e) => set("payout_account_name", e.target.value)}
              />
              <Input
                label="Account number (optional)"
                value={form.payout_account_number}
                onChange={(e) => set("payout_account_number", e.target.value)}
              />
            </div>
          </section>
        </div>

        {/* Sidebar — branding */}
        <div className="space-y-6">
          <section className="bg-surface-card border border-surface-border rounded-2xl p-6 space-y-4">
            <h2 className="font-heading text-lg font-bold text-white">
              Logo
            </h2>
            {form.logo_url ? (
              <div className="relative rounded-xl overflow-hidden border border-surface-border bg-surface-dark aspect-square">
                <img
                  src={form.logo_url}
                  alt="Logo"
                  className="w-full h-full object-contain"
                />
                <button
                  type="button"
                  onClick={() => set("logo_url", "")}
                  className="absolute top-2 right-2 p-1.5 rounded-lg bg-black/60 text-white hover:bg-black/80"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <label className="block rounded-xl border-2 border-dashed border-surface-border bg-surface-dark aspect-square flex flex-col items-center justify-center cursor-pointer hover:border-brand-primary">
                <input
                  type="file"
                  accept="image/png,image/jpeg,image/webp"
                  className="hidden"
                  onChange={(e) => uploadImage(e.target.files?.[0], "logo")}
                  disabled={uploadingLogo}
                />
                {uploadingLogo ? (
                  <span className="text-xs text-gray-400">Uploading…</span>
                ) : (
                  <>
                    <Upload className="w-6 h-6 text-gray-500 mb-2" />
                    <span className="text-xs text-gray-400">Upload logo</span>
                  </>
                )}
              </label>
            )}
          </section>

          <section className="bg-surface-card border border-surface-border rounded-2xl p-6 space-y-4">
            <h2 className="font-heading text-lg font-bold text-white">
              Banner
            </h2>
            {form.banner_url ? (
              <div className="relative rounded-xl overflow-hidden border border-surface-border bg-surface-dark aspect-[3/1]">
                <img
                  src={form.banner_url}
                  alt="Banner"
                  className="w-full h-full object-cover"
                />
                <button
                  type="button"
                  onClick={() => set("banner_url", "")}
                  className="absolute top-2 right-2 p-1.5 rounded-lg bg-black/60 text-white hover:bg-black/80"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <label className="block rounded-xl border-2 border-dashed border-surface-border bg-surface-dark aspect-[3/1] flex flex-col items-center justify-center cursor-pointer hover:border-brand-primary">
                <input
                  type="file"
                  accept="image/png,image/jpeg,image/webp"
                  className="hidden"
                  onChange={(e) => uploadImage(e.target.files?.[0], "banner")}
                  disabled={uploadingBanner}
                />
                {uploadingBanner ? (
                  <span className="text-xs text-gray-400">Uploading…</span>
                ) : (
                  <>
                    <Upload className="w-6 h-6 text-gray-500 mb-2" />
                    <span className="text-xs text-gray-400">Upload banner</span>
                  </>
                )}
              </label>
            )}
          </section>

          <div className="sticky top-4">
            <Button
              type="submit"
              variant="primary"
              size="lg"
              loading={saving}
              className="w-full"
            >
              <Save className="w-4 h-4" />
              Save profile
            </Button>
          </div>
        </div>
      </form>
    </div>
  );
}