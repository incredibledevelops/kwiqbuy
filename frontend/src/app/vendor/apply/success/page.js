"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  CheckCircle2,
  ArrowRight,
  Copy,
  Loader2,
  AlertCircle,
  Clock,
  XCircle,
  Home,
} from "lucide-react";
import Button from "@/components/ui/Button";
import { useToast } from "@/components/ui/Toast";
import { API_URL } from "@/lib/api";

const STATUS_META = {
  pending: {
    label: "Under review",
    color: "text-amber-400",
    bg: "bg-amber-500/15",
    icon: Clock,
    message: "We'll review your application within 2 business days.",
  },
  approved: {
    label: "Approved",
    color: "text-emerald-400",
    bg: "bg-emerald-500/15",
    icon: CheckCircle2,
    message: "Check your email for your temporary password.",
  },
  rejected: {
    label: "Rejected",
    color: "text-red-400",
    bg: "bg-red-500/15",
    icon: XCircle,
    message: "",
  },
  expired: {
    label: "Expired",
    color: "text-gray-400",
    bg: "bg-white/5",
    icon: Clock,
    message: "This application has expired. Please re-apply.",
  },
  withdrawn: {
    label: "Withdrawn",
    color: "text-gray-400",
    bg: "bg-white/5",
    icon: XCircle,
    message: "This application was withdrawn.",
  },
};

function SuccessInner() {
  const search = useSearchParams();
  const toast = useToast();
  const id = search.get("id") || "";

  const [status, setStatus] = useState("pending");
  const [rejection, setRejection] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const res = await fetch(
          `${API_URL}/api/v1/vendor-applications/status/${id}`
        );
        if (res.ok) {
          const data = await res.json();
          if (!cancelled) {
            setStatus(data.status || "pending");
            setRejection(data.rejection_reason || "");
          }
        }
      } catch {
        // Ignore — default to "pending"
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [id]);

  const meta = STATUS_META[status] || STATUS_META.pending;
  const Icon = meta.icon;

  return (
    <div className="min-h-screen bg-surface-dark">
      <div className="border-b border-surface-border bg-surface-card/40">
        <div className="max-w-3xl mx-auto px-4 py-3 flex items-center justify-between">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-sm font-bold text-gray-400 hover:text-brand-primary"
          >
            <Home className="w-4 h-4" />
            Back to KwiqBuy
          </Link>
        </div>
      </div>

      <div className="max-w-xl mx-auto px-4 py-16">
        <div className="bg-surface-card border border-surface-border rounded-3xl p-8 text-center">
          <div
            className={`w-20 h-20 rounded-full ${meta.bg} mx-auto flex items-center justify-center`}
          >
            <Icon className={`w-10 h-10 ${meta.color}`} />
          </div>
          <h1 className={`font-heading text-2xl font-black mt-5 ${meta.color}`}>
            {status === "pending"
              ? "Application received!"
              : `Application ${meta.label.toLowerCase()}`}
          </h1>
          <p className="text-sm text-gray-400 mt-2">
            {meta.message || (status === "rejected" && rejection) || ""}
          </p>

          {id && (
            <div className="mt-6 p-3 rounded-xl bg-surface-dark border border-surface-border inline-flex items-center gap-2 text-xs">
              <span className="text-gray-500">Application ID</span>
              <code className="text-white font-mono break-all">{id}</code>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(id);
                  toast.success("Copied");
                }}
                className="p-1 rounded-md text-gray-400 hover:text-white hover:bg-white/5"
              >
                <Copy className="w-3.5 h-3.5" />
              </button>
            </div>
          )}

          {loading && (
            <div className="mt-4 inline-flex items-center gap-2 text-xs text-gray-500">
              <Loader2 className="w-3 h-3 animate-spin" />
              Checking status…
            </div>
          )}

          <div className="mt-8 space-y-3">
            {id && (
              <a
                href={`mailto:hello@kwiqbuy.com?subject=Application%20${id}`}
                className="inline-flex items-center gap-2 text-xs text-gray-400 hover:text-brand-primary"
              >
                <AlertCircle className="w-3.5 h-3.5" />
                Questions? Email us about this application
              </a>
            )}
          </div>

          <div className="flex flex-col sm:flex-row gap-3 justify-center mt-8 pt-6 border-t border-surface-border">
            <Button href="/" variant="secondary" size="md">
              <Home className="w-4 h-4" />
              Back to home
            </Button>
            <Button href="/vendor/login" variant="primary" size="md">
              Vendor sign-in
              <ArrowRight className="w-4 h-4" />
            </Button>
          </div>
        </div>

        <div className="mt-6 text-center text-[11px] text-gray-500">
          Save the application ID above — you can use it to check status by
          contacting support.
        </div>
      </div>
    </div>
  );
}

export default function SuccessPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-surface-dark">
          <Loader2 className="w-8 h-8 text-brand-primary animate-spin" />
        </div>
      }
    >
      <SuccessInner />
    </Suspense>
  );
}