"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Loader2, CheckCircle2, XCircle, ShieldCheck } from "lucide-react";
import { API_URL } from "@/lib/api";

function extractOrderReference(input) {
  if (!input) return "";
  const match = String(input).match(/^(KB-\d{8}-[A-Z0-9]+)/);
  return match ? match[1] : String(input);
}

function CallbackInner() {
  const router = useRouter();
  const search = useSearchParams();
  const [stage, setStage] = useState("verifying");
  const [message, setMessage] = useState("");

  useEffect(() => {
    const reference = search.get("reference") || search.get("trxref");
    if (!reference) {
      setStage("error");
      setMessage("No payment reference found.");
      return;
    }

    let cancelled = false;

    (async () => {
      try {
        const res = await fetch(
          `${API_URL}/api/v1/payments/verify/${encodeURIComponent(reference)}`
        );
        const data = await res.json().catch(() => ({}));
        if (cancelled) return;

        const status = data.status || "";
        const orderRef = extractOrderReference(
          data?.gateway_response?.metadata?.order_reference || reference
        );

        if (["success", "paid"].includes(status)) {
          setStage("success");
          setMessage("Payment confirmed.");
        } else if (["failed", "abandoned"].includes(status)) {
          setStage("failed");
          setMessage(data?.gateway_response?.message || "Payment failed.");
        } else {
          setStage("pending");
          setMessage("Payment is still being processed.");
        }

        setTimeout(() => {
          if (cancelled) return;
          router.replace(
            orderRef ? `/order/${orderRef}?reference=${encodeURIComponent(reference)}` : "/"
          );
        }, 2200);
      } catch (e) {
        if (cancelled) return;
        setStage("error");
        setMessage(e.message);
        setTimeout(() => router.replace("/"), 2400);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [router, search]);

  const meta = {
    verifying: {
      color: "text-brand-primary",
      bg: "bg-brand-primary/15",
      label: "Verifying payment…",
      Icon: ShieldCheck,
      spin: true,
    },
    success: {
      color: "text-emerald-400",
      bg: "bg-emerald-500/15",
      label: "Payment confirmed!",
      Icon: CheckCircle2,
      spin: false,
    },
    failed: {
      color: "text-red-400",
      bg: "bg-red-500/15",
      label: "Payment failed",
      Icon: XCircle,
      spin: false,
    },
    pending: {
      color: "text-amber-400",
      bg: "bg-amber-500/15",
      label: "Processing…",
      Icon: Loader2,
      spin: true,
    },
    error: {
      color: "text-red-400",
      bg: "bg-red-500/15",
      label: "Something went wrong",
      Icon: XCircle,
      spin: false,
    },
  }[stage];

  const Icon = meta.Icon;

  return (
    <div className="min-h-[70vh] flex items-center justify-center p-4">
      <div className="text-center max-w-sm">
        <div
          className={`w-24 h-24 rounded-full ${meta.bg} mx-auto flex items-center justify-center relative`}
        >
          <Icon
            className={`w-12 h-12 ${meta.color} ${meta.spin ? "animate-spin" : ""}`}
            strokeWidth={2}
          />
        </div>
        <h1 className={`font-heading text-2xl font-black mt-6 ${meta.color}`}>
          {meta.label}
        </h1>
        <p className="text-gray-400 text-sm mt-2">{message || "Just a moment…"}</p>
        <p className="text-[11px] text-gray-600 mt-6">
          You'll be redirected to your order shortly
        </p>
      </div>
    </div>
  );
}

export default function CallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-[70vh] flex items-center justify-center">
          <Loader2 className="w-10 h-10 text-brand-primary animate-spin" />
        </div>
      }
    >
      <CallbackInner />
    </Suspense>
  );
}