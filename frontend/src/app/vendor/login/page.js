"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Store, ArrowRight, AlertCircle, Loader2 } from "lucide-react";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import { useToast } from "@/components/ui/Toast";
import { API_URL } from "@/lib/api";
import { saveVendorSession, getVendorToken } from "@/lib/vendorAuth";

export default function VendorLoginPage() {
  const router = useRouter();
  const toast = useToast();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (getVendorToken()) {
      router.replace("/vendor/dashboard");
    }
  }, [router]);

  async function submit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim(), password }),
      });

      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        throw new Error(data.detail || "Sign-in failed");
      }

      // 2FA-required response — the backend returns { needs_2fa, temp_token }
      if (data.needs_2fa) {
        setError("This account requires 2FA. Please use the admin panel for now.");
        setLoading(false);
        return;
      }

      if (!data.access_token) {
        throw new Error("Server did not return an access token");
      }

      // Fetch user profile to confirm it's a vendor account
      const meRes = await fetch(`${API_URL}/api/v1/auth/me`, {
        headers: { Authorization: `Bearer ${data.access_token}` },
      });
      const me = await meRes.json().catch(() => ({}));

      if (!meRes.ok || me.role !== "vendor") {
        throw new Error(
          "This account is not a vendor account. Please sign in at /account."
        );
      }

      // Fetch the vendor profile (business_name etc.)
      let vendorProfile = null;
      try {
        const vRes = await fetch(`${API_URL}/api/v1/vendor/me`, {
          headers: { Authorization: `Bearer ${data.access_token}` },
        });
        if (vRes.ok) vendorProfile = await vRes.json();
      } catch {}

      saveVendorSession({
        accessToken: data.access_token,
        refreshToken: data.refresh_token,
        user: {
          id: me.id,
          email: me.email,
          full_name: me.full_name,
          role: me.role,
          vendor_id: me.vendor_id,
          business_name: vendorProfile?.business_name || me.full_name,
        },
      });

      toast.success("Welcome back!");
      router.replace("/vendor/dashboard");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-sm bg-surface-card border border-surface-border rounded-3xl p-8 space-y-5">
        <div className="text-center">
          <div className="w-14 h-14 rounded-2xl gradient-brand flex items-center justify-center text-white mx-auto">
            <Store className="w-7 h-7" />
          </div>
          <h1 className="font-heading text-2xl font-extrabold text-white mt-4">
            Vendor sign-in
          </h1>
          <p className="text-xs text-gray-400 mt-1">
            Access your KwiqBuy vendor dashboard
          </p>
        </div>

        {error && (
          <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs flex items-start gap-2">
            <AlertCircle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={submit} className="space-y-4">
          <Input
            label="Email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@business.com"
            autoComplete="email"
          />
          <Input
            label="Password"
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            autoComplete="current-password"
          />
          <Button
            type="submit"
            variant="primary"
            size="lg"
            loading={loading}
            disabled={!email || !password}
            className="w-full"
          >
            Sign in
            <ArrowRight className="w-4 h-4" />
          </Button>
        </form>

        <div className="pt-2 border-t border-surface-border text-center">
          <p className="text-xs text-gray-400">
            Not a vendor yet?{" "}
            <Link href="/vendor/apply" className="text-brand-primary hover:underline font-bold">
              Apply to sell
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}