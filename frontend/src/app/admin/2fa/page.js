"use client";

import { useEffect, useState } from "react";
import {
  Loader2,
  ShieldCheck,
  ShieldOff,
  Copy,
  CheckCircle2,
  KeyRound,
} from "lucide-react";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Modal from "@/components/ui/Modal";
import { useToast } from "@/components/ui/Toast";
import { adminApi } from "@/lib/adminApi";

export default function Admin2FAPage() {
  const toast = useToast();
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Setup flow
  const [setupData, setSetupData] = useState(null); // { secret, qr_data_url }
  const [setupCode, setSetupCode] = useState("");
  const [setupLoading, setSetupLoading] = useState(false);
  const [recoveryCodes, setRecoveryCodes] = useState(null);

  // Disable flow
  const [disableOpen, setDisableOpen] = useState(false);
  const [disablePassword, setDisablePassword] = useState("");
  const [disableCode, setDisableCode] = useState("");
  const [disabling, setDisabling] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const data = await adminApi.get("/api/v1/admin/2fa/status");
      setStatus(data);
      setError("");
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function beginSetup() {
    setSetupLoading(true);
    try {
      const data = await adminApi.post("/api/v1/admin/2fa/setup");
      setSetupData(data);
    } catch (e) {
      toast.error(e.message);
    } finally {
      setSetupLoading(false);
    }
  }

  async function verifySetup() {
    if (setupCode.trim().length < 6) {
      toast.error("Enter the 6-digit code from your app");
      return;
    }
    setSetupLoading(true);
    try {
      const res = await adminApi.post("/api/v1/admin/2fa/verify", {
        code: setupCode.trim(),
      });
      setRecoveryCodes(res.recovery_codes);
      setSetupData(null);
      setSetupCode("");
      await load();
    } catch (e) {
      toast.error(e.message);
    } finally {
      setSetupLoading(false);
    }
  }

  async function doDisable() {
    setDisabling(true);
    try {
      await adminApi.post("/api/v1/admin/2fa/disable", {
        password: disablePassword,
        code: disableCode.trim() || null,
      });
      toast.success("2FA disabled");
      setDisableOpen(false);
      setDisablePassword("");
      setDisableCode("");
      await load();
    } catch (e) {
      toast.error(e.message);
    } finally {
      setDisabling(false);
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
        <h1 className="font-heading text-3xl font-black text-white">
          Two-factor authentication
        </h1>
        <p className="text-sm text-gray-400 mt-1">
          Protect your admin account with a TOTP authenticator app.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
          {error}
        </div>
      )}

      <section className="bg-surface-card border border-surface-border rounded-2xl p-6 space-y-4">
        <div className="flex items-start gap-4">
          <div
            className={`w-12 h-12 rounded-xl flex items-center justify-center ${
              status?.enabled
                ? "bg-emerald-500/15 text-emerald-400"
                : "bg-amber-500/15 text-amber-400"
            }`}
          >
            {status?.enabled ? (
              <ShieldCheck className="w-6 h-6" />
            ) : (
              <ShieldOff className="w-6 h-6" />
            )}
          </div>
          <div className="flex-1">
            <div className="font-bold text-white">
              {status?.enabled ? "2FA is enabled" : "2FA is disabled"}
            </div>
            <div className="text-xs text-gray-500 mt-0.5">
              {status?.enabled
                ? `Verified${status.verified_at ? ` on ${new Date(status.verified_at).toLocaleDateString()}` : ""} · ${status.recovery_codes_remaining} recovery code${status.recovery_codes_remaining === 1 ? "" : "s"} left`
                : "Add a second factor to protect your account."}
            </div>
          </div>
          {status?.enabled ? (
            <Button
              variant="danger"
              size="md"
              onClick={() => setDisableOpen(true)}
            >
              Disable
            </Button>
          ) : (
            <Button
              variant="primary"
              size="md"
              loading={setupLoading}
              onClick={beginSetup}
            >
              Enable 2FA
            </Button>
          )}
        </div>
      </section>

      {/* Setup flow */}
      {setupData && (
        <section className="bg-surface-card border border-surface-border rounded-2xl p-6 space-y-4">
          <h2 className="font-heading text-lg font-bold text-white">
            Scan this QR code
          </h2>
          <div className="grid sm:grid-cols-2 gap-6">
            <div>
              <div className="p-3 rounded-xl bg-white inline-block">
                <img
                  src={setupData.qr_data_url}
                  alt="2FA QR code"
                  className="w-48 h-48"
                />
              </div>
              <div className="text-[11px] text-gray-500 mt-2">
                Can't scan? Enter this secret manually:
              </div>
              <div className="flex items-center gap-2 mt-1">
                <code className="flex-1 px-2 py-1.5 rounded-lg bg-surface-dark border border-surface-border text-xs text-white font-mono break-all">
                  {setupData.secret}
                </code>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(setupData.secret);
                    toast.success("Copied");
                  }}
                  className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/5"
                >
                  <Copy className="w-4 h-4" />
                </button>
              </div>
            </div>
            <div className="space-y-3">
              <div className="text-xs text-gray-400">
                1. Open your authenticator app (Google Authenticator, Authy, etc.)
              </div>
              <div className="text-xs text-gray-400">
                2. Scan the QR code or enter the secret above
              </div>
              <div className="text-xs text-gray-400">
                3. Enter the 6-digit code shown in the app
              </div>
              <Input
                label="6-digit code"
                value={setupCode}
                onChange={(e) => setSetupCode(e.target.value)}
                placeholder="123456"
                autoComplete="one-time-code"
              />
              <Button
                variant="primary"
                size="md"
                className="w-full"
                loading={setupLoading}
                onClick={verifySetup}
              >
                <KeyRound className="w-4 h-4" />
                Verify & enable
              </Button>
            </div>
          </div>
        </section>
      )}

      {/* Recovery codes */}
      <Modal
        open={!!recoveryCodes}
        onClose={() => setRecoveryCodes(null)}
        title="Save your recovery codes"
        maxWidth="max-w-md"
      >
        <div className="space-y-3">
          <p className="text-xs text-amber-300 bg-amber-500/10 border border-amber-500/30 rounded-xl p-3">
            These codes will not be shown again. Store them in a safe place —
            they are the only way to recover access if you lose your
            authenticator.
          </p>
          <div className="grid grid-cols-2 gap-2">
            {(recoveryCodes || []).map((c) => (
              <code
                key={c}
                className="p-2 rounded-lg bg-surface-dark border border-surface-border text-xs text-white font-mono text-center"
              >
                {c}
              </code>
            ))}
          </div>
          <Button
            variant="secondary"
            className="w-full"
            onClick={() => {
              navigator.clipboard.writeText((recoveryCodes || []).join("\n"));
              toast.success("Copied all codes");
            }}
          >
            <Copy className="w-4 h-4" />
            Copy all
          </Button>
        </div>
        <div className="flex justify-end mt-6">
          <Button variant="primary" onClick={() => setRecoveryCodes(null)}>
            I've saved them
          </Button>
        </div>
      </Modal>

      {/* Disable modal */}
      <Modal
        open={disableOpen}
        onClose={() => !disabling && setDisableOpen(false)}
        title="Disable 2FA"
        maxWidth="max-w-md"
        disableClose={disabling}
      >
        <div className="space-y-4">
          <p className="text-sm text-gray-300">
            This makes your account less secure. Confirm with your password
            and a current 2FA code.
          </p>
          <Input
            label="Password"
            type="password"
            value={disablePassword}
            onChange={(e) => setDisablePassword(e.target.value)}
          />
          <Input
            label="2FA code (or recovery code)"
            value={disableCode}
            onChange={(e) => setDisableCode(e.target.value)}
          />
        </div>
        <div className="flex justify-end gap-2 mt-6">
          <Button
            variant="secondary"
            onClick={() => setDisableOpen(false)}
            disabled={disabling}
          >
            Cancel
          </Button>
          <Button
            variant="danger"
            loading={disabling}
            disabled={!disablePassword || !disableCode}
            onClick={doDisable}
          >
            Disable 2FA
          </Button>
        </div>
      </Modal>
    </div>
  );
}