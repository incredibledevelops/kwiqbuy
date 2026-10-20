"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  ArrowRight,
  Building2,
  User,
  MapPin,
  FileText,
  CheckCircle2,
  AlertCircle,
  Upload,
  X,
  Loader2,
  Store,
  ShieldCheck,
  Clock,
} from "lucide-react";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import { useToast } from "@/components/ui/Toast";
import { API_URL } from "@/lib/api";
import { normalizePhone, isValidPhone } from "@/lib/utils";

const STEPS = [
  { id: "business", label: "Business", icon: Building2 },
  { id: "contact", label: "Contact", icon: User },
  { id: "location", label: "Location", icon: MapPin },
  { id: "documents", label: "Documents", icon: FileText },
  { id: "review", label: "Review", icon: CheckCircle2 },
];

const BUSINESS_CATEGORIES = [
  { value: "food", label: "Food & restaurant" },
  { value: "retail", label: "Retail & general merchandise" },
];

const BUSINESS_TYPES = [
  { value: "restaurant", label: "Restaurant / kitchen" },
  { value: "grocery", label: "Grocery / supermarket" },
  { value: "pharmacy", label: "Pharmacy" },
  { value: "electronics", label: "Electronics" },
  { value: "fashion", label: "Fashion & apparel" },
  { value: "other", label: "Other" },
];

export default function VendorApplyPage() {
  const router = useRouter();
  const toast = useToast();

  const [step, setStep] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [rateLimited, setRateLimited] = useState(false);
  const [uploading, setUploading] = useState({ id: false, reg: false });

  const [form, setForm] = useState({
    business_name: "",
    business_category: "food",
    business_type: "restaurant",
    description: "",
    contact_name: "",
    contact_email: "",
    contact_phone: "",
    pickup_address: "",
    city: "",
    region: "",
    requested_payout_method: "mobile_money",
    requested_payout_account_name: "",
    requested_payout_account_number: "",
    id_document_url: "",
    business_registration_url: "",
  });

  function set(k, v) {
    setForm((f) => ({ ...f, [k]: v }));
    // Clear errors when the user starts typing
    if (error) setError("");
  }

  // Per-step validation with clear messages
  function validateStep() {
    const s = STEPS[step].id;
    if (s === "business") {
      if (form.business_name.trim().length < 2) return "Enter your business name (min 2 characters).";
      if (form.description.trim().length < 10) return "Describe your business in at least 10 characters.";
    }
    if (s === "contact") {
      if (form.contact_name.trim().length < 2) return "Enter the contact person's name.";
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.contact_email.trim())) return "Enter a valid email address.";
      if (!isValidPhone(form.contact_phone)) return "Enter a valid Ghanaian phone number (e.g. 024XXXXXXX).";
    }
    if (s === "location") {
      if (form.pickup_address.trim().length < 4) return "Enter your full pickup address.";
    }
    if (s === "documents") {
      if (!form.id_document_url) return "Upload your ID document to continue.";
    }
    return null;
  }

  function next() {
    const err = validateStep();
    if (err) {
      setError(err);
      return;
    }
    setError("");
    setStep((s) => Math.min(s + 1, STEPS.length - 1));
  }

  function back() {
    setError("");
    setStep((s) => Math.max(0, s - 1));
  }

  async function uploadFile(file, field) {
    if (!file) return;
    setUploading((u) => ({ ...u, [field === "id_document_url" ? "id" : "reg"]: true }));
    try {
      const fd = new FormData();
      fd.append("file", file);
      const res = await fetch(`${API_URL}/api/v1/uploads/vendor-application`, {
        method: "POST",
        body: fd,
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Upload failed");
      }
      const data = await res.json();
      set(field, data.url);
      toast.success("Uploaded successfully");
    } catch (e) {
      toast.error(e.message);
    } finally {
      setUploading((u) => ({
        ...u,
        [field === "id_document_url" ? "id" : "reg"]: false,
      }));
    }
  }

  async function submit() {
    setSubmitting(true);
    setError("");
    try {
      const payload = {
        business_name: form.business_name.trim(),
        business_category: form.business_category,
        business_type: form.business_type,
        description: form.description.trim(),
        contact_name: form.contact_name.trim(),
        contact_email: form.contact_email.trim(),
        contact_phone: normalizePhone(form.contact_phone),
        pickup_address: form.pickup_address.trim(),
        city: form.city.trim() || null,
        region: form.region.trim() || null,
        requested_payout_method: form.requested_payout_method || null,
        requested_payout_account_name: form.requested_payout_account_name.trim() || null,
        requested_payout_account_number: form.requested_payout_account_number.trim() || null,
        id_document_url: form.id_document_url || null,
        business_registration_url: form.business_registration_url || null,
      };

      const res = await fetch(`${API_URL}/api/v1/vendor-applications`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        // Handle Rate Limit (429)
        if (res.status === 429) {
          setRateLimited(true);
          throw new Error("Too many applications submitted from your network. Please wait a while before trying again.");
        }
        // Handle Duplicate (409)
        if (res.status === 409) {
          throw new Error(data.detail || "You already have a pending application. We will contact you soon.");
        }
        throw new Error(data.detail || "Application submission failed");
      }

      toast.success("Application submitted");
      router.replace(`/vendor/apply/success?id=${data.id}`);
    } catch (e) {
      setError(e.message);
      toast.error("Submission failed. See message above.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-surface-dark">
      <div className="border-b border-surface-border bg-surface-card/40">
        <div className="max-w-3xl mx-auto px-4 py-3 flex items-center justify-between">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-sm font-bold text-gray-400 hover:text-brand-primary"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to KwiqBuy
          </Link>
          <span className="text-xs text-gray-500">
            Already a vendor?{" "}
            <Link href="/vendor/login" className="text-brand-primary hover:underline font-bold">
              Sign in
            </Link>
          </span>
        </div>
      </div>

      <div className="max-w-3xl mx-auto px-4 py-10">
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-2xl gradient-brand flex items-center justify-center mx-auto text-white">
            <Store className="w-7 h-7" />
          </div>
          <h1 className="font-heading text-3xl sm:text-4xl font-black text-white mt-4">
            Sell on KwiqBuy
          </h1>
          <p className="text-gray-400 text-sm mt-2 max-w-lg mx-auto">
            Apply in 3 minutes. We review within 2 business days.
          </p>
        </div>

        <ol className="flex items-center justify-between mb-8">
          {STEPS.map((s, i) => {
            const done = i < step;
            const active = i === step;
            const Icon = s.icon;
            return (
              <li key={s.id} className="flex-1 flex items-center">
                <div
                  className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 border-2 transition-colors ${
                    active
                      ? "border-brand-primary bg-brand-primary/20 text-brand-primary"
                      : done
                      ? "border-emerald-500 bg-emerald-500/10 text-emerald-400"
                      : "border-surface-border bg-surface-card text-gray-500"
                  }`}
                >
                  {done ? <CheckCircle2 className="w-4 h-4" /> : <Icon className="w-4 h-4" />}
                </div>
                <div
                  className={`ml-2 text-[10px] uppercase tracking-wider font-bold hidden sm:block ${
                    active ? "text-brand-primary" : done ? "text-emerald-400" : "text-gray-500"
                  }`}
                >
                  {s.label}
                </div>
                {i < STEPS.length - 1 && (
                  <div className={`flex-1 h-0.5 mx-2 ${done ? "bg-emerald-500" : "bg-surface-border"}`} />
                )}
              </li>
            );
          })}
        </ol>

        {error && (
          <div className="mb-6 p-4 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm flex items-start gap-3 shadow-lg">
            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
            <div className="flex-1">
              <div className="font-bold">Hold on</div>
              <div className="text-xs text-red-300 mt-1">{error}</div>
              {rateLimited && (
                <div className="mt-3 inline-flex items-center gap-1.5 text-[11px] bg-red-500/20 px-2 py-1 rounded-md">
                  <Clock className="w-3 h-3" /> Rate limit: Max 3 applications per hour.
                </div>
              )}
            </div>
          </div>
        )}

        <div className="bg-surface-card border border-surface-border rounded-3xl p-6 sm:p-8">
          {step === 0 && (
            <div className="space-y-4">
              <SectionTitle icon={Building2} title="Business details" subtitle="Tell us what you sell." />
              <Input
                label="Business name"
                required
                value={form.business_name}
                onChange={(e) => set("business_name", e.target.value)}
                placeholder="e.g. Ali's Kitchen"
              />
              <div className="grid sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-gray-300 mb-1.5">Business category</label>
                  <select
                    value={form.business_category}
                    onChange={(e) => set("business_category", e.target.value)}
                    className="w-full px-4 py-3 rounded-xl bg-surface-dark border border-surface-border text-white text-sm focus:border-brand-primary outline-none"
                  >
                    {BUSINESS_CATEGORIES.map((o) => (
                      <option key={o.value} value={o.value}>{o.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-300 mb-1.5">Business type</label>
                  <select
                    value={form.business_type}
                    onChange={(e) => set("business_type", e.target.value)}
                    className="w-full px-4 py-3 rounded-xl bg-surface-dark border border-surface-border text-white text-sm focus:border-brand-primary outline-none"
                  >
                    {BUSINESS_TYPES.map((o) => (
                      <option key={o.value} value={o.value}>{o.label}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-xs font-bold text-gray-300 mb-1.5">Description</label>
                <textarea
                  rows={4}
                  value={form.description}
                  onChange={(e) => set("description", e.target.value)}
                  placeholder="What do you sell? What makes your business unique?"
                  className="w-full px-4 py-3 rounded-xl bg-surface-dark border border-surface-border text-white text-sm focus:border-brand-primary outline-none resize-none"
                />
                <div className="text-[10px] text-gray-500 mt-1 flex justify-between">
                  <span>Min 10 characters</span>
                  <span className={form.description.length > 0 && form.description.length < 10 ? "text-amber-400 font-bold" : ""}>
                    {form.description.length}/2000
                  </span>
                </div>
              </div>
            </div>
          )}

          {step === 1 && (
            <div className="space-y-4">
              <SectionTitle icon={User} title="Contact details" subtitle="How can we reach you?" />
              <Input
                label="Contact name"
                required
                value={form.contact_name}
                onChange={(e) => set("contact_name", e.target.value)}
                placeholder="Full name"
              />
              <Input
                label="Email"
                type="email"
                required
                value={form.contact_email}
                onChange={(e) => set("contact_email", e.target.value)}
                placeholder="you@business.com"
                hint="We'll send approvals and updates here."
              />
              <Input
                label="Phone"
                type="tel"
                required
                value={form.contact_phone}
                onChange={(e) => set("contact_phone", e.target.value)}
                placeholder="024XXXXXXX"
              />
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <SectionTitle
                icon={MapPin}
                title="Pickup location"
                subtitle="Where do customers pick up or where do you dispatch from?"
              />
              <Input
                label="Pickup address"
                required
                value={form.pickup_address}
                onChange={(e) => set("pickup_address", e.target.value)}
                placeholder="e.g. Boundary Road, East Legon, Accra"
              />
              <div className="grid sm:grid-cols-2 gap-4">
                <Input
                  label="City"
                  value={form.city}
                  onChange={(e) => set("city", e.target.value)}
                  placeholder="Accra"
                />
                <Input
                  label="Region"
                  value={form.region}
                  onChange={(e) => set("region", e.target.value)}
                  placeholder="Greater Accra"
                />
              </div>
              <div className="rounded-xl bg-surface-dark border border-surface-border p-4">
                <div className="text-xs font-bold text-gray-300 mb-2">Payout details (optional)</div>
                <div className="grid sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-bold text-gray-300 mb-1.5">Method</label>
                    <select
                      value={form.requested_payout_method}
                      onChange={(e) => set("requested_payout_method", e.target.value)}
                      className="w-full px-4 py-3 rounded-xl bg-surface-dark border border-surface-border text-white text-sm focus:border-brand-primary outline-none"
                    >
                      <option value="mobile_money">Mobile money</option>
                      <option value="bank">Bank transfer</option>
                    </select>
                  </div>
                  <Input
                    label="Account name"
                    value={form.requested_payout_account_name}
                    onChange={(e) => set("requested_payout_account_name", e.target.value)}
                  />
                </div>
                <div className="mt-3">
                  <Input
                    label="Account number"
                    value={form.requested_payout_account_number}
                    onChange={(e) => set("requested_payout_account_number", e.target.value)}
                  />
                </div>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-4">
              <SectionTitle
                icon={FileText}
                title="Documents"
                subtitle="Upload your ID. Business registration is optional but helps us review faster."
              />
              <DocUpload
                label="ID document"
                required
                value={form.id_document_url}
                uploading={uploading.id}
                onChange={(f) => uploadFile(f, "id_document_url")}
                onClear={() => set("id_document_url", "")}
              />
              <DocUpload
                label="Business registration (optional)"
                value={form.business_registration_url}
                uploading={uploading.reg}
                onChange={(f) => uploadFile(f, "business_registration_url")}
                onClear={() => set("business_registration_url", "")}
              />
              <div className="rounded-xl bg-surface-dark border border-surface-border p-4 flex items-start gap-3">
                <ShieldCheck className="w-4 h-4 text-brand-primary shrink-0 mt-0.5" />
                <div className="text-xs text-gray-400">
                  Your documents are used only for verification and are not shared publicly.
                </div>
              </div>
            </div>
          )}

          {step === 4 && (
            <div className="space-y-4">
              <SectionTitle
                icon={CheckCircle2}
                title="Review & submit"
                subtitle="Check the details before we review."
              />
              <ReviewBlock label="Business">
                <Row label="Name" value={form.business_name} />
                <Row label="Category" value={BUSINESS_CATEGORIES.find((c) => c.value === form.business_category)?.label} />
                <Row label="Type" value={BUSINESS_TYPES.find((c) => c.value === form.business_type)?.label} />
                <Row label="Description" value={form.description} />
              </ReviewBlock>
              <ReviewBlock label="Contact">
                <Row label="Name" value={form.contact_name} />
                <Row label="Email" value={form.contact_email} />
                <Row label="Phone" value={form.contact_phone} />
              </ReviewBlock>
              <ReviewBlock label="Location">
                <Row label="Address" value={form.pickup_address} />
                <Row label="City" value={form.city} />
                <Row label="Region" value={form.region} />
              </ReviewBlock>
              <ReviewBlock label="Documents">
                <Row label="ID document" value={form.id_document_url ? "Uploaded ✓" : "Missing"} />
                <Row label="Registration" value={form.business_registration_url ? "Uploaded ✓" : "Not provided"} />
              </ReviewBlock>
            </div>
          )}

          <div className="flex items-center justify-between gap-3 mt-8 pt-6 border-t border-surface-border">
            <Button
              variant="secondary"
              size="lg"
              onClick={back}
              disabled={step === 0 || submitting}
            >
              <ArrowLeft className="w-4 h-4" />
              Back
            </Button>
            {step < STEPS.length - 1 ? (
              <Button
                variant="primary"
                size="lg"
                onClick={next}
                // We DO NOT disable based on validity here anymore.
                // Clicking will trigger validateStep() and show an error message.
              >
                Continue
                <ArrowRight className="w-4 h-4" />
              </Button>
            ) : (
              <Button
                variant="primary"
                size="lg"
                loading={submitting}
                onClick={submit}
              >
                Submit application
                <CheckCircle2 className="w-4 h-4" />
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function SectionTitle({ icon: Icon, title, subtitle }) {
  return (
    <div className="flex items-start gap-3 mb-2">
      <div className="w-10 h-10 rounded-xl bg-brand-primary/10 border border-brand-primary/20 flex items-center justify-center shrink-0">
        <Icon className="w-5 h-5 text-brand-primary" />
      </div>
      <div>
        <h2 className="font-heading text-lg font-bold text-white">{title}</h2>
        {subtitle && <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>}
      </div>
    </div>
  );
}

function DocUpload({ label, required, value, uploading, onChange, onClear }) {
  return (
    <div>
      <label className="block text-xs font-bold text-gray-300 mb-1.5">
        {label} {required && <span className="text-red-400">*</span>}
      </label>
      {value ? (
        <div className="flex items-center justify-between p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30">
          <div className="flex items-center gap-2 text-sm text-emerald-300 min-w-0">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <a href={value} target="_blank" rel="noopener noreferrer" className="truncate underline hover:no-underline">
              {value.split("/").pop()}
            </a>
          </div>
          <button
            type="button"
            onClick={onClear}
            className="p-1.5 rounded-lg text-red-400 hover:bg-red-500/10 shrink-0"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      ) : (
        <label className="block rounded-xl border-2 border-dashed border-surface-border bg-surface-dark p-6 text-center cursor-pointer hover:border-brand-primary transition-colors">
          <input
            type="file"
            accept="image/png,image/jpeg,image/webp"
            className="hidden"
            onChange={(e) => onChange(e.target.files?.[0])}
            disabled={uploading}
          />
          {uploading ? (
            <span className="inline-flex items-center gap-2 text-xs text-gray-400">
              <Loader2 className="w-4 h-4 animate-spin" />
              Uploading…
            </span>
          ) : (
            <>
              <Upload className="w-5 h-5 text-gray-500 mx-auto mb-2" />
              <span className="text-xs text-gray-400">Click to upload</span>
              <div className="text-[10px] text-gray-600 mt-1">PNG, JPG, or WebP · max 5MB</div>
            </>
          )}
        </label>
      )}
    </div>
  );
}

function ReviewBlock({ label, children }) {
  return (
    <div className="rounded-xl bg-surface-dark border border-surface-border p-4 space-y-1.5 text-sm">
      <div className="text-[10px] uppercase tracking-wider font-bold text-gray-500 mb-1">{label}</div>
      {children}
    </div>
  );
}

function Row({ label, value }) {
  if (!value) return null;
  return (
    <div className="flex justify-between gap-3">
      <span className="text-gray-500 shrink-0">{label}</span>
      <span className="text-gray-200 text-right break-all">{value}</span>
    </div>
  );
}