"use client";

import { useEffect, useState, useCallback, useRef, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  Loader2, Crown, Check, Zap, Rocket, ShieldCheck,
  AlertCircle, Lock, Clock, CheckCircle2, RefreshCw
} from "lucide-react";
import Button from "@/components/ui/Button";
import Modal from "@/components/ui/Modal";
import { useToast } from "@/components/ui/Toast";
import { vendorApi } from "@/lib/vendorApi";
import { API_URL } from "@/lib/api";
import { formatGHS } from "@/lib/utils";

const TIER_ICONS = { free: ShieldCheck, growth: Zap, enterprise: Rocket };

function SubscriptionPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const toast = useToast();

  const [tiers, setTiers] = useState([]);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [confirmSubscribe, setConfirmSubscribe] = useState(null);
  const [subscribing, setSubscribing] = useState(false);
  const [cancelling, setCancelling] = useState(false);

  const [verifying, setVerifying] = useState(false);
  const [verifySuccess, setVerifySuccess] = useState(false);

  const hasVerifiedRef = useRef(false);
  const referenceParam = searchParams.get("reference") || searchParams.get("trxref");

  const load = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const [tiersRes, statusRes] = await Promise.all([
        fetch(`${API_URL}/api/v1/subscription-tiers`),
        vendorApi.get("/api/v1/vendor/subscription"),
      ]);

      if (tiersRes.ok) {
        setTiers(await tiersRes.json());
      }

      setStatus(statusRes);
      setError("");
      return statusRes;
    } catch (e) {
      setError(e.message || "Failed to load subscription data.");
      return null;
    } finally {
      if (!silent) setLoading(false);
    }
  }, []);

  // 1. Initial load
  useEffect(() => {
    load();
  }, [load]);

  // 2. Handle Paystack return
  useEffect(() => {
    if (!referenceParam || hasVerifiedRef.current) return;

    hasVerifiedRef.current = true;
    setVerifying(true);

    let isMounted = true;
    let attempts = 0;

    const verifyAndPoll = async () => {
      attempts++;

      try {
        await fetch(`${API_URL}/api/v1/payments/verify/${referenceParam}`);
        const newStatus = await load(true);

        const isPaidTierActive =
          newStatus?.has_active_subscription &&
          newStatus?.tier?.slug !== "free";

        if (isPaidTierActive) {
          if (!isMounted) return;
          setVerifying(false);
          setVerifySuccess(true);
          toast.success(`Successfully subscribed to ${newStatus.tier.name}!`);
          window.history.replaceState(null, "", "/vendor/subscription");
          setTimeout(() => {
            if (isMounted) setVerifySuccess(false);
          }, 5000);
          return;
        }

        if (attempts > 10) {
          if (!isMounted) return;
          setVerifying(false);
          setError(
            "Verification is taking longer than expected. Please refresh the page to check the status, or contact support."
          );
          toast.error("Verification timed out.");
          window.history.replaceState(null, "", "/vendor/subscription");
          return;
        }

        setTimeout(verifyAndPoll, 2000);
      } catch (err) {
        if (isMounted) {
          setVerifying(false);
          setError("Failed to verify payment. Please refresh and try again.");
        }
      }
    };

    verifyAndPoll();

    return () => {
      isMounted = false;
    };
  }, [referenceParam, load, toast]);

  async function doSubscribe(tier) {
    setSubscribing(true);
    try {
      const res = await vendorApi.post("/api/v1/vendor/subscription/subscribe", {
        tier_slug: tier.slug,
      });

      if (res.requires_payment && res.authorization_url) {
        toast.success("Redirecting to payment...");
        window.location.href = res.authorization_url;
        return;
      }

      toast.success(`Subscribed to ${tier.name}`);
      setConfirmSubscribe(null);
      await load(true);
    } catch (e) {
      toast.error(e.message);
    } finally {
      setSubscribing(false);
    }
  }

  async function cancelSubscription() {
    setCancelling(true);
    try {
      await vendorApi.post("/api/v1/vendor/subscription/cancel");
      toast.success("Subscription cancelled");
      await load(true);
    } catch (e) {
      toast.error(e.message);
    } finally {
      setCancelling(false);
    }
  }

  if (loading) {
    return (
      <div className="py-20 text-center">
        <Loader2 className="w-8 h-8 text-brand-primary animate-spin mx-auto" />
        <p className="text-gray-400 text-sm mt-4">Loading subscription data...</p>
      </div>
    );
  }

  if (error && !status) {
    return (
      <div className="max-w-xl mx-auto py-12">
        <div className="p-6 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-400">
          <AlertCircle className="w-8 h-8 mb-3" />
          <h2 className="font-bold text-lg text-white mb-1">Something went wrong</h2>
          <p className="text-sm mb-4">{error}</p>
          <Button variant="secondary" onClick={() => load()}>
            <RefreshCw className="w-4 h-4" /> Try again
          </Button>
        </div>
      </div>
    );
  }

  const current = status?.current;
  const currentSlug = status?.tier?.slug;
  const isOverride = status?.is_override;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-heading text-3xl font-black text-white">Subscription</h1>
        <p className="text-sm text-gray-400 mt-1">Lower your commission and unlock premium features.</p>
      </div>

      {verifying && (
        <div className="p-5 rounded-2xl bg-brand-primary/10 border border-brand-primary/30 flex items-start gap-4">
          <Loader2 className="w-6 h-6 text-brand-primary animate-spin shrink-0 mt-0.5" />
          <div>
            <div className="font-bold text-white">Confirming your payment...</div>
            <div className="text-sm text-gray-400 mt-1">Talking to Paystack. This usually takes a few seconds.</div>
          </div>
        </div>
      )}

      {verifySuccess && (
        <div className="p-5 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex items-start gap-4">
          <CheckCircle2 className="w-6 h-6 text-emerald-400 shrink-0 mt-0.5" />
          <div>
            <div className="font-bold text-emerald-400">Subscription Activated!</div>
            <div className="text-sm text-emerald-300/80 mt-1">Your new plan is now active. Your commission rate has been updated.</div>
          </div>
        </div>
      )}

      {error && status && (
        <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm flex items-start gap-2">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <div>{error}</div>
        </div>
      )}

      <section className="bg-surface-card border border-surface-border rounded-2xl p-6">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <div className="text-[10px] uppercase tracking-wider font-bold text-gray-500">Current plan</div>
            <div className="text-2xl font-black text-white mt-1 flex items-center gap-2">
              <Crown className={`w-6 h-6 ${currentSlug === "free" || !currentSlug ? "text-gray-400" : "text-brand-gold"}`} />
              {status?.tier?.name || "Free"}
            </div>
            <div className="text-sm text-gray-400 mt-2">
              Effective commission: <span className="text-brand-primary font-bold">{status?.effective_commission_pct}%</span>
              {status?.base_commission_pct != null && (
                <span className="text-gray-500"> (base {status.base_commission_pct}%)</span>
              )}
            </div>

            {current?.current_period_end && currentSlug !== "free" && (
              <LiveCountdown targetDate={current.current_period_end} />
            )}

            {isOverride && (
              <div className="mt-2 inline-flex items-center gap-1.5 text-[11px] px-2 py-1 rounded-md bg-amber-500/10 border border-amber-500/30 text-amber-300">
                <AlertCircle className="w-3 h-3" /> Admin override applied
              </div>
            )}
          </div>

          {current && currentSlug !== "free" && (
            <Button
              variant="secondary"
              size="sm"
              loading={cancelling}
              onClick={cancelSubscription}
              disabled={verifying}
            >
              Cancel plan
            </Button>
          )}
        </div>
      </section>

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {tiers.map((t) => {
          const Icon = TIER_ICONS[t.slug] || Crown;
          const isCurrent = currentSlug === t.slug;
          return (
            <div
              key={t.id}
              className={`p-6 rounded-2xl border transition-all ${
                isCurrent
                  ? "bg-brand-primary/10 border-brand-primary shadow-[0_0_20px_rgba(37,99,235,0.15)] ring-1 ring-brand-primary/50"
                  : "bg-surface-card border-surface-border"
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div
                    className={`w-9 h-9 rounded-xl flex items-center justify-center ${
                      isCurrent ? "bg-brand-primary/20 text-brand-primary" : "bg-white/5 text-gray-400"
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                  </div>
                  <div className="font-heading font-black text-lg text-white">{t.name}</div>
                </div>
                {isCurrent && (
                  <span className="text-[10px] font-bold uppercase tracking-wider bg-brand-primary text-white px-2 py-1 rounded-md">
                    Active
                  </span>
                )}
              </div>

              <div className="mt-4 text-3xl font-black text-white">
                {t.monthly_price === 0 ? "Free" : formatGHS(t.monthly_price)}
                {t.monthly_price > 0 && <span className="text-sm font-normal text-gray-500">/mo</span>}
              </div>
              {t.commission_discount_pct > 0 && (
                <div className="text-xs text-emerald-400 font-bold mt-1">
                  −{t.commission_discount_pct}% commission
                </div>
              )}
              {t.description && <div className="text-xs text-gray-400 mt-3">{t.description}</div>}

              <ul className="space-y-1.5 mt-4">
                {(t.features || []).map((f, i) => (
                  <li key={i} className="flex items-start gap-2 text-xs text-gray-300">
                    <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" /> {f}
                  </li>
                ))}
              </ul>

              <div className="mt-6">
                {isCurrent ? (
                  <Button variant="secondary" className="w-full opacity-50 cursor-not-allowed" disabled>
                    Current Plan
                  </Button>
                ) : (
                  <Button
                    variant="primary"
                    className="w-full"
                    onClick={() => setConfirmSubscribe(t)}
                    disabled={verifying}
                  >
                    {t.monthly_price === 0
                      ? "Switch to Free"
                      : currentSlug && currentSlug !== "free"
                      ? "Change plan"
                      : "Subscribe"}
                  </Button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <Modal
        open={!!confirmSubscribe}
        onClose={() => !subscribing && setConfirmSubscribe(null)}
        title={`Subscribe to ${confirmSubscribe?.name}?`}
        maxWidth="max-w-md"
        disableClose={subscribing}
      >
        {confirmSubscribe && (
          <>
            <div className="text-sm text-gray-300 space-y-2">
              <p>
                You'll move to <strong className="text-white">{confirmSubscribe.name}</strong>.
              </p>
              {confirmSubscribe.monthly_price > 0 ? (
                <>
                  <p>
                    Price:{" "}
                    <strong className="text-white">
                      {formatGHS(confirmSubscribe.monthly_price)}/month
                    </strong>
                  </p>
                  <div className="flex items-center gap-1.5 text-[11px] text-brand-primary bg-brand-primary/10 p-2 rounded-lg mt-2">
                    <Lock className="w-3.5 h-3.5 shrink-0" />
                    You will be redirected to Paystack to complete payment securely.
                  </div>
                </>
              ) : (
                <p>This plan is free. You will lose any premium features immediately.</p>
              )}
              {confirmSubscribe.commission_discount_pct > 0 && (
                <p className="text-emerald-400 text-xs mt-2">
                  Commission drops by {confirmSubscribe.commission_discount_pct}% for 30 days.
                </p>
              )}
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <Button
                variant="secondary"
                onClick={() => setConfirmSubscribe(null)}
                disabled={subscribing}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                loading={subscribing}
                onClick={() => doSubscribe(confirmSubscribe)}
              >
                {confirmSubscribe.monthly_price > 0
                  ? `Pay ${formatGHS(confirmSubscribe.monthly_price)}`
                  : "Confirm"}
              </Button>
            </div>
          </>
        )}
      </Modal>
    </div>
  );
}

function LiveCountdown({ targetDate }) {
  const [timeLeft, setTimeLeft] = useState(() => calcTimeLeft(targetDate));

  useEffect(() => {
    const timer = setInterval(() => {
      setTimeLeft(calcTimeLeft(targetDate));
    }, 1000);
    return () => clearInterval(timer);
  }, [targetDate]);

  if (!timeLeft || timeLeft.total <= 0) {
    return (
      <div className="mt-3 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-xs font-bold text-amber-400">
        <Clock className="w-4 h-4" />
        Billing cycle ended — renewal pending
      </div>
    );
  }

  const urgency =
    timeLeft.days <= 3
      ? "bg-red-500/10 border-red-500/30 text-red-400"
      : timeLeft.days <= 7
      ? "bg-amber-500/10 border-amber-500/30 text-amber-400"
      : "bg-brand-primary/10 border-brand-primary/20 text-brand-primary";

  return (
    <div className={`mt-3 inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-bold ${urgency}`}>
      <Clock className="w-4 h-4" />
      <span className="text-white/70">Renews in</span>
      <span className="font-mono tabular-nums">
        {timeLeft.days}d : {String(timeLeft.hours).padStart(2, "0")}h : {String(timeLeft.minutes).padStart(2, "0")}m : {String(timeLeft.seconds).padStart(2, "0")}s
      </span>
    </div>
  );
}

function calcTimeLeft(targetDate) {
  const total = new Date(targetDate).getTime() - Date.now();
  if (total <= 0) return { total: 0, days: 0, hours: 0, minutes: 0, seconds: 0 };
  return {
    total,
    days: Math.floor(total / (1000 * 60 * 60 * 24)),
    hours: Math.floor((total / (1000 * 60 * 60)) % 24),
    minutes: Math.floor((total / (1000 * 60)) % 60),
    seconds: Math.floor((total / 1000) % 60),
  };
}

export default function VendorSubscriptionPage() {
  return (
    <Suspense
      fallback={
        <div className="py-20 text-center">
          <Loader2 className="w-8 h-8 text-brand-primary animate-spin mx-auto" />
        </div>
      }
    >
      <SubscriptionPageContent />
    </Suspense>
  );
}