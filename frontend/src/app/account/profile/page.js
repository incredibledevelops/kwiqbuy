"use client";

import { useEffect, useState } from "react";
import { Loader2, Save, AlertCircle } from "lucide-react";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import { useToast } from "@/components/ui/Toast";
import { customerFetch } from "@/lib/customerAuth";
import { API_URL } from "@/lib/api";

export default function ProfilePage() {
  const toast = useToast();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    phone: "",
  });

  useEffect(() => {
    (async () => {
      try {
        const res = await customerFetch(
          `${API_URL}/api/v1/customer-account/me`
        );
        if (res.ok) {
          const data = await res.json().catch(() => ({}));
          setForm({
            full_name: data.full_name || "",
            email: data.email || "",
            phone: data.phone || "",
          });
        } else {
          setError(`Failed to load profile (${res.status})`);
        }
      } catch (e) {
        setError(e.message || "Failed to load profile.");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  async function save(e) {
    e.preventDefault();
    setSaving(true);
    try {
      const res = await customerFetch(
        `${API_URL}/api/v1/customer-account/me`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            full_name: form.full_name.trim(),
            email: form.email.trim(),
          }),
        }
      );
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Failed to update profile");
      }
      toast.success("Profile updated");
    } catch (e) {
      toast.error(e.message || "Failed to update profile");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="space-y-4 max-w-md" aria-busy="true">
        <div className="animate-pulse h-8 w-40 bg-surface-card border border-surface-border rounded-xl" />
        <div className="animate-pulse h-72 bg-surface-card border border-surface-border rounded-2xl" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm flex items-start gap-2">
        <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
        <span>{error}</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="font-heading text-2xl font-black text-white">
        Profile settings
      </h1>

      <form
        onSubmit={save}
        className="bg-surface-card border border-surface-border rounded-2xl p-6 space-y-4 max-w-md"
      >
        <Input
          label="Full name"
          name="fullName"
          value={form.full_name}
          onChange={(e) => setForm({ ...form, full_name: e.target.value })}
        />
        <Input
          label="Email address"
          name="email"
          type="email"
          autoComplete="email"
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
        />
        <Input
          label="Phone number"
          name="phone"
          value={form.phone}
          disabled
          hint="Phone number cannot be changed."
        />

        <Button
          type="submit"
          variant="primary"
          loading={saving}
          className="w-full mt-2"
        >
          <Save className="w-4 h-4" /> Save changes
        </Button>
      </form>
    </div>
  );
}