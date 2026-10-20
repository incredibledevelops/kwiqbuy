"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ShieldCheck, ArrowRight, AlertCircle, KeyRound } from "lucide-react";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import { useToast } from "@/components/ui/Toast";
import { API_URL } from "@/lib/api";
import { saveAdminSession, getAdminToken } from "@/lib/adminAuth";

export default function AdminLoginPage() {
  const router = useRouter();
  const toast = useToast();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // 2FA state
  const [twoFA, setTwoFA] = useState(null); // { temp_token }
  const [code, setCode] = useState("");

  useEffect(() => {
    if (getAdminToken()) router.replace("/admin");
  }, [router]);

  async function submitPassword(e) {
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

      if (data.needs_2fa) {
        setTwoFA({ temp_token: data.temp_token });
        setLoading(false);
        return;
      }

      if (!data.access_token) throw new Error("No token returned");

      const meRes = await fetch(`${API_URL}/api/v1/auth/me`, {
        headers: { Authorization: `Bearer ${data.access_token}` },
      });
      const me = await meRes.json().catch(() => ({}));

      if (!meRes.ok || me.role !== "admin") {
        throw new Error("This account is not an admin account.");
      }

      saveAdminSession(data.access_token, {
        id: me.id,
        email: me.email,
        full_name: me.full_name,
        role: me.role,
      });
      toast.success("Welcome back");
      router.replace("/admin");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function submit2FA(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/auth/login/2fa`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          temp_token: twoFA.temp_token,
          code: code.trim(),
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || "Invalid code");

      const meRes = await fetch(`${API_URL}/api/v1/auth/me`, {
        headers: { Authorization: `Bearer ${data.access_token}` },
      });
      const me = await meRes.json().catch(() => ({}));

      saveAdminSession(data.access_token, {
        id: me.id,
        email: me.email,
        full_name: me.full_name,
        role: me.role,
      });
      toast.success("Welcome back");
      router.replace("/admin");
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
            <ShieldCheck className="w-7 h-7" />
          </div>
          <h1 className="font-heading text-2xl font-extrabold text-white mt-4">
            Admin sign-in
          </h1>
          <p className="text-xs text-gray-400 mt-1">
            {twoFA ? "Enter the code from your authenticator" : "Restricted access"}
          </p>
        </div>

        {error && (
          <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs flex items-start gap-2">
            <AlertCircle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {!twoFA ? (
          <form onSubmit={submitPassword} className="space-y-4">
            <Input
              label="Email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@kwiqbuy.com"
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
        ) : (
          <form onSubmit={submit2FA} className="space-y-4">
            <Input
              label="Authenticator code"
              required
              value={code}
              onChange={(e) => setCode(e.target.value.toUpperCase())}
              placeholder="123456"
              autoComplete="one-time-code"
            />
            <Button
              type="submit"
              variant="primary"
              size="lg"
              loading={loading}
              disabled={code.trim().length < 4}
              className="w-full"
            >
              <KeyRound className="w-4 h-4" />
              Verify & sign in
            </Button>
            <button
              type="button"
              onClick={() => {
                setTwoFA(null);
                setCode("");
                setError("");
              }}
              className="w-full text-xs text-gray-400 hover:text-white"
            >
              ← Use a different account
            </button>
          </form>
        )}

        <div className="pt-2 border-t border-surface-border text-center">
          <Link href="/" className="text-xs text-gray-400 hover:text-brand-primary">
            ← Back to site
          </Link>
        </div>
      </div>
    </div>
  );
}