"use client";

import { useEffect, useState } from "react";
import {
  Loader2,
  Copy,
  Users,
  Gift,
  CheckCircle2,
  AlertCircle,
  Share2,
} from "lucide-react";
import StatCard from "@/components/vendor/StatCard";
import Button from "@/components/ui/Button";
import EmptyState from "@/components/ui/EmptyState";
import { useToast } from "@/components/ui/Toast";
import { customerFetch } from "@/lib/customerAuth";
import { API_URL } from "@/lib/api";
import { formatGHS, formatDateTime } from "@/lib/utils";

export default function ReferralsPage() {
  const toast = useToast();
  const [summary, setSummary] = useState(null);
  const [refs, setRefs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const [sumRes, listRes] = await Promise.all([
        customerFetch(`${API_URL}/api/v1/referrals/me/summary`),
        customerFetch(`${API_URL}/api/v1/referrals/me`),
      ]);
      if (sumRes.ok) {
        const d = await sumRes.json().catch(() => null);
        setSummary(d);
      } else {
        throw new Error(`Failed to load summary (${sumRes.status})`);
      }
      if (listRes.ok) {
        const d = await listRes.json().catch(() => []);
        setRefs(Array.isArray(d) ? d : []);
      }
    } catch (e) {
      setError(e.message || "Failed to load referrals.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  // Referral code should come from summary, not a referee's row
  const referralCode =
    summary?.referral_code || summary?.code || summary?.my_code || "";

  async function copyCode() {
    if (!referralCode) return;
    try {
      if (navigator?.clipboard?.writeText) {
        await navigator.clipboard.writeText(referralCode);
      } else {
        // Fallback
        const ta = document.createElement("textarea");
        ta.value = referralCode;
        ta.style.position = "fixed";
        ta.style.opacity = "0";
        document.body.appendChild(ta);
        ta.select();
        document.execCommand("copy");
        ta.remove();
      }
      setCopied(true);
      toast.success("Copied to clipboard!");
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error("Couldn't copy. Long-press to copy manually.");
    }
  }

  async function share() {
    if (!referralCode) return;
    const text = `Join me on KwiqBuy and we both get GH₵ 10 off! Use code: ${referralCode}`;
    if (navigator?.share) {
      try {
        await navigator.share({ title: "KwiqBuy", text });
        return;
      } catch {
        // user cancelled or failed — fall through to copy
      }
    }
    try {
      await navigator.clipboard.writeText(text);
      toast.success("Invite copied to clipboard!");
    } catch {
      toast.error("Couldn't share. Try copying the code.");
    }
  }

  if (loading) {
    return (
      <div className="space-y-6" aria-busy="true">
        <div className="animate-pulse h-8 w-40 bg-surface-card border border-surface-border rounded-xl" />
        <div className="animate-pulse h-40 bg-surface-card border border-surface-border rounded-3xl" />
        <div className="grid grid-cols-3 gap-4">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="animate-pulse h-24 bg-surface-card border border-surface-border rounded-2xl"
            />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm flex items-start gap-2">
        <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
        <div className="flex-1">
          <div>{error}</div>
          <button onClick={load} className="mt-2 text-xs underline">
            Try again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="font-heading text-2xl font-black text-white">Referrals</h1>

      <div className="relative overflow-hidden bg-gradient-to-br from-brand-primary/20 to-brand-accent/20 border border-brand-primary/30 rounded-3xl p-6 text-center">
        <Gift className="w-10 h-10 text-brand-primary mx-auto mb-2" />
        <h2 className="font-heading text-xl font-bold text-white">
          Give GH₵ 10, Get GH₵ 10
        </h2>
        <p className="text-sm text-gray-300 mt-1 max-w-sm mx-auto">
          Share your code. When a friend places their first order, you both get
          GH₵ 10 off!
        </p>
        <div className="mt-4 inline-flex items-center gap-2 bg-surface-dark/80 px-4 py-2 rounded-xl border border-surface-border">
          <span className="font-mono text-lg font-bold text-white tracking-widest">
            {referralCode || "—"}
          </span>
          <button
            onClick={copyCode}
            disabled={!referralCode}
            aria-label="Copy referral code"
            className="p-1.5 text-brand-primary hover:bg-white/5 rounded-md disabled:opacity-40"
          >
            {copied ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            ) : (
              <Copy className="w-4 h-4" />
            )}
          </button>
        </div>
        {referralCode && (
          <div className="mt-3">
            <Button variant="secondary" size="sm" onClick={share}>
              <Share2 className="w-3.5 h-3.5" /> Share invite
            </Button>
          </div>
        )}
      </div>

      <div className="grid grid-cols-3 gap-4">
        <StatCard
          label="Referred"
          value={summary?.total_referrals || 0}
          icon={Users}
        />
        <StatCard
          label="Completed"
          value={summary?.completed_referrals || 0}
          accent="success"
        />
        <StatCard
          label="Earned"
          value={formatGHS(summary?.total_earned || 0)}
          accent="primary"
        />
      </div>

      <section className="bg-surface-card border border-surface-border rounded-2xl overflow-hidden">
        <div className="px-5 py-4 border-b border-surface-border">
          <h2 className="font-heading text-lg font-bold text-white">
            Your referrals
          </h2>
        </div>
        {refs.length === 0 ? (
          <div className="p-6">
            <EmptyState
              icon={Users}
              title="No invites yet"
              message="Share your code to start earning rewards."
            />
          </div>
        ) : (
          <ul className="divide-y divide-surface-border">
            {refs.map((r) => {
              const completed = r.status === "completed";
              return (
                <li
                  key={r.id}
                  className="px-5 py-4 flex items-center justify-between gap-4"
                >
                  <div className="min-w-0">
                    <div className="text-sm font-bold text-white truncate">
                      {r.referee_name || "Pending user"}
                    </div>
                    <div className="text-xs text-gray-500 mt-0.5">
                      Joined {formatDateTime(r.created_at)}
                    </div>
                  </div>
                  <div
                    className={`text-xs font-bold uppercase px-2 py-1 rounded-md shrink-0 ${
                      completed
                        ? "bg-emerald-500/10 text-emerald-400"
                        : "bg-amber-500/10 text-amber-400"
                    }`}
                  >
                    {r.status}
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </section>
    </div>
  );
}