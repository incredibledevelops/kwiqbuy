"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Phone,
  ArrowRight,
  AlertCircle,
  ArrowLeft,
  Smartphone,
  Copy,
  Terminal,
} from "lucide-react";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import { useToast } from "@/components/ui/Toast";
import { API_URL } from "@/lib/api";
import { saveCustomerTokens, getCustomerToken } from "@/lib/customerAuth";
import { normalizePhone, isValidPhone } from "@/lib/utils";

const OTP_LENGTH = 6;

export default function AccountLoginPage() {
  const router = useRouter();
  const toast = useToast();

  const [stage, setStage] = useState("phone");
  const [phone, setPhone] = useState("");
  const [fullName, setFullName] = useState("");
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [resendIn, setResendIn] = useState(0);
  const [devCode, setDevCode] = useState(null);
  const codeRefs = useRef([]);

  useEffect(() => {
    if (getCustomerToken()) router.replace("/account/orders");
  }, [router]);

  useEffect(() => {
    if (resendIn <= 0) return;
    const t = setInterval(
      () => setResendIn((s) => (s <= 1 ? 0 : s - 1)),
      1000
    );
    return () => clearInterval(t);
  }, [resendIn]);

  const requestOtp = useCallback(
    async (e) => {
      e?.preventDefault?.();
      setError("");
      const normalized = normalizePhone(phone);
      if (!normalized) {
        setError("Enter a valid Ghanaian phone number (e.g. 024XXXXXXX).");
        return;
      }
      setLoading(true);
      try {
        const res = await fetch(`${API_URL}/api/v1/customer-auth/request-otp`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            phone: normalized,
            full_name: fullName.trim() || "Customer",
          }),
        });
        const data = await res.json().catch(() => ({}));
        
        if (!res.ok) {
          throw new Error(data.detail || "Couldn't send the code.");
        }
        
        setPhone(normalized);
        setStage("code");
        setResendIn(30);
        setCode("");

        if (data.is_dev_mode && data.dev_otp) {
          setDevCode(data.dev_otp);
          // Auto-fill for testing convenience
          setCode(data.dev_otp);
          toast.success("DEV MODE: SMS bypassed.", 5000);
        } else {
          setDevCode(null);
        }

        setTimeout(() => codeRefs.current[0]?.focus(), 50);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    },
    [phone, fullName, toast]
  );

  const verifyOtp = useCallback(
    async (e) => {
      e?.preventDefault?.();
      setError("");
      if (code.length !== OTP_LENGTH) {
        setError(`Enter the ${OTP_LENGTH}-digit code we sent you.`);
        return;
      }
      setLoading(true);
      try {
        const res = await fetch(`${API_URL}/api/v1/customer-auth/verify-otp`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ phone: phone.trim(), code: code.trim() }),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(data.detail || "Invalid code.");
        
        saveCustomerTokens(data.access_token, data.refresh_token);
        toast.success("Welcome to KwiqBuy!");
        router.replace("/account/orders");
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    },
    [phone, code, router, toast]
  );

  function handleCodeChange(i, raw) {
    const digits = raw.replace(/\D/g, "");
    if (!digits) {
      const next = (code.slice(0, i) + code.slice(i + 1)).slice(0, OTP_LENGTH);
      setCode(next);
      return;
    }
    if (digits.length > 1) {
      // Handle paste
      const start = i;
      const filled = code.slice(0, start) + digits.slice(0, OTP_LENGTH - start) + code.slice(start + digits.length);
      const next = filled.slice(0, OTP_LENGTH);
      setCode(next);
      const focusAt = Math.min(start + digits.length, OTP_LENGTH - 1);
      codeRefs.current[focusAt]?.focus();
      return;
    }
    const next = (code.slice(0, i) + digits + code.slice(i + 1)).slice(0, OTP_LENGTH);
    setCode(next);
    if (i < OTP_LENGTH - 1) codeRefs.current[i + 1]?.focus();
  }

  function handleCodeKeyDown(i, e) {
    if (e.key === "Backspace") {
      if (code[i]) {
        const next = (code.slice(0, i) + code.slice(i + 1)).slice(0, OTP_LENGTH);
        setCode(next);
        return;
      }
      if (i > 0) {
        const next = (code.slice(0, i - 1) + code.slice(i)).slice(0, OTP_LENGTH);
        setCode(next);
        codeRefs.current[i - 1]?.focus();
      }
    }
  }

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center p-4">
      <div className="w-full max-w-sm bg-surface-card border border-surface-border rounded-3xl p-8 space-y-5">
        <div className="text-center">
          <div className="w-14 h-14 rounded-2xl gradient-brand flex items-center justify-center text-white mx-auto">
            <Phone className="w-7 h-7" />
          </div>
          <h1 className="font-heading text-2xl font-extrabold text-white mt-4">
            Sign in
          </h1>
          <p className="text-xs text-gray-400 mt-1">
            {stage === "phone"
              ? "We'll send a one-time code to your phone."
              : `Enter the ${OTP_LENGTH}-digit code we sent to ${phone}.`}
          </p>
        </div>

        {error && (
          <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs flex items-start gap-2">
            <AlertCircle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {stage === "phone" ? (
          <form onSubmit={requestOtp} className="space-y-4">
            <Input
              label="Full name"
              name="fullName"
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Kwadwo Mensah"
            />
            <Input
              label="Phone number"
              name="phone"
              type="tel"
              autoComplete="tel"
              required
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="024XXXXXXX"
              error={
                phone && !isValidPhone(phone) ? "Enter a valid number" : null
              }
            />
            <Button
              type="submit"
              variant="primary"
              size="lg"
              loading={loading}
              disabled={!isValidPhone(phone)}
              className="w-full"
            >
              Send code
              <ArrowRight className="w-4 h-4" />
            </Button>
          </form>
        ) : (
          <form onSubmit={verifyOtp} className="space-y-4">
            
            {devCode ? (
              <div className="p-4 rounded-xl bg-brand-primary/10 border border-brand-primary/30 space-y-2">
                 <div className="flex items-center gap-2 text-brand-primary text-xs font-bold">
                   <Terminal className="w-4 h-4" /> Dev Environment
                 </div>
                 <p className="text-[11px] text-gray-400">
                   SMS delivery bypassed. Your code is:
                 </p>
                 <div className="flex items-center justify-between bg-surface-dark rounded-lg p-2 border border-surface-border">
                    <span className="font-mono text-xl font-bold text-white tracking-widest">{devCode}</span>
                    <button type="button" onClick={() => { navigator.clipboard.writeText(devCode); toast.success("Copied!"); }} className="p-1.5 text-gray-400 hover:text-white">
                      <Copy className="w-4 h-4" />
                    </button>
                 </div>
              </div>
            ) : (
              <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-start gap-2">
                <Smartphone className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                <div>
                  Code sent via SMS to <strong>{phone}</strong>
                </div>
              </div>
            )}

            <div>
              <label className="block text-xs font-bold text-gray-300 mb-1.5">
                {OTP_LENGTH}-digit code
              </label>
              <div className="flex gap-2 justify-between">
                {Array.from({ length: OTP_LENGTH }).map((_, i) => (
                  <input
                    key={i}
                    ref={(el) => { codeRefs.current[i] = el; }}
                    value={code[i] || ""}
                    onChange={(e) => handleCodeChange(i, e.target.value)}
                    onKeyDown={(e) => handleCodeKeyDown(i, e)}
                    inputMode="numeric"
                    autoComplete="one-time-code"
                    aria-label={`Digit ${i + 1}`}
                    maxLength={1}
                    className={`w-11 h-14 rounded-xl bg-surface-dark border text-white text-xl font-mono text-center outline-none transition-colors ${
                      devCode && code === devCode
                        ? "border-brand-primary ring-2 ring-brand-primary/40" 
                        : "border-surface-border focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/40"
                    }`}
                  />
                ))}
              </div>
            </div>

            <Button
              type="submit"
              variant="primary"
              size="lg"
              loading={loading}
              disabled={code.length !== OTP_LENGTH}
              className="w-full"
            >
              Verify &amp; sign in
            </Button>

            <div className="flex justify-between text-xs">
              <button
                type="button"
                onClick={() => {
                  setStage("phone");
                  setCode("");
                  setError("");
                  setDevCode(null);
                }}
                className="text-gray-400 hover:text-white inline-flex items-center gap-1"
              >
                <ArrowLeft className="w-3 h-3" />
                Change number
              </button>
              <button
                type="button"
                onClick={requestOtp}
                disabled={loading || resendIn > 0}
                className="text-brand-primary hover:underline disabled:opacity-50"
              >
                {resendIn > 0 ? `Resend in ${resendIn}s` : "Resend code"}
              </button>
            </div>
          </form>
        )}

        <Link
          href="/"
          className="block text-center text-xs text-gray-400 hover:text-brand-primary"
        >
          ← Back to home
        </Link>
      </div>
    </div>
  );
}