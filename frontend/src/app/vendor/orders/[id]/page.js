"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Loader2,
  Check,
  ChefHat,
  Package,
  Truck,
  X,
  AlertCircle,
} from "lucide-react";
import Button from "@/components/ui/Button";
import Modal from "@/components/ui/Modal";
import Input from "@/components/ui/Input";
import { useToast } from "@/components/ui/Toast";
import { vendorApi } from "@/lib/vendorApi";
import { formatGHS, formatDateTime } from "@/lib/utils";

// Food flow: pending → accepted → preparing → ready → picked_up → delivered
// Retail flow: pending → confirmed → preparing → packed → shipped → in_transit → delivered
const NEXT_ACTION = {
  pending: { next: "ACCEPT", label: "Accept order", icon: Check },
  accepted: { next: "PREPARING", label: "Start preparing", icon: ChefHat },
  confirmed: { next: "PREPARING", label: "Start preparing", icon: ChefHat },
  preparing: { next: "READY", label: "Mark as ready", icon: Package },
  ready: { next: "PICKED_UP", label: "Mark picked up", icon: Truck },
  packed: { next: "SHIPPED", label: "Mark shipped", icon: Truck },
  shipped: { next: "IN_TRANSIT", label: "Mark in transit", icon: Truck },
  in_transit: { next: "DELIVERED", label: "Mark delivered", icon: Check },
  picked_up: { next: "DELIVERED", label: "Mark delivered", icon: Check },
};

export default function VendorOrderDetailPage() {
  const params = useParams();
  const router = useRouter();
  const toast = useToast();
  const orderId = params?.id;

  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [updating, setUpdating] = useState(false);
  const [rejectOpen, setRejectOpen] = useState(false);
  const [rejectReason, setRejectReason] = useState("");

  async function load() {
    try {
      const data = await vendorApi.get(`/api/v1/vendor/orders/${orderId}`);
      setOrder(data);
      setError("");
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (orderId) load();
  }, [orderId]);

  async function setStatus(status, extra = {}) {
    setUpdating(true);
    try {
      const updated = await vendorApi.patch(
        `/api/v1/vendor/orders/${orderId}/status`,
        { status, ...extra }
      );
      setOrder(updated);
      toast.success(`Order marked as ${status.replace(/_/g, " ")}`);
    } catch (e) {
      toast.error(e.message);
    } finally {
      setUpdating(false);
    }
  }

  async function rejectOrder() {
    if (rejectReason.trim().length < 4) {
      toast.error("Please provide a reason (min 4 characters)");
      return;
    }
    await setStatus("rejected", { reason: rejectReason.trim() });
    setRejectOpen(false);
    setRejectReason("");
  }

  if (loading) {
    return (
      <div className="py-16 text-center">
        <Loader2 className="w-8 h-8 text-brand-primary animate-spin mx-auto" />
      </div>
    );
  }

  if (error || !order) {
    return (
      <div className="space-y-4">
        <Link
          href="/vendor/orders"
          className="inline-flex items-center gap-2 text-sm font-bold text-gray-400 hover:text-brand-primary"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to orders
        </Link>
        <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm flex items-start gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <span>{error || "Order not found"}</span>
        </div>
      </div>
    );
  }

  const action = NEXT_ACTION[order.status];
  const ActionIcon = action?.icon;

  return (
    <div className="space-y-6">
      <Link
        href="/vendor/orders"
        className="inline-flex items-center gap-2 text-sm font-bold text-gray-400 hover:text-brand-primary"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to orders
      </Link>

      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <div className="font-mono text-xs text-brand-primary font-bold">
            {order.vendor_id ? "Vendor order" : ""}
          </div>
          <h1 className="font-heading text-2xl sm:text-3xl font-black text-white mt-1">
            Order details
          </h1>
          <div className="text-xs text-gray-500 mt-1">
            Status:{" "}
            <span className="text-white font-bold capitalize">
              {String(order.status).replace(/_/g, " ")}
            </span>
          </div>
        </div>
        {action && (
          <Button
            variant="primary"
            size="lg"
            loading={updating}
            onClick={() => setStatus(action.next)}
          >
            {ActionIcon && <ActionIcon className="w-4 h-4" />}
            {action.label}
          </Button>
        )}
      </div>

      {/* Items */}
      <section className="bg-surface-card border border-surface-border rounded-2xl overflow-hidden">
        <div className="px-5 py-4 border-b border-surface-border">
          <h2 className="font-heading text-lg font-bold text-white">Items</h2>
        </div>
        <ul className="divide-y divide-surface-border">
          {(order.items || []).map((item, i) => (
            <li key={i} className="px-5 py-3 flex items-center justify-between gap-4">
              <div className="min-w-0">
                <div className="font-bold text-white truncate">{item.name}</div>
                <div className="text-xs text-gray-500 mt-0.5">
                  {formatGHS(item.unit_price)} × {item.quantity}
                  {item.variant_sku && ` · SKU: ${item.variant_sku}`}
                </div>
              </div>
              <div className="text-brand-primary font-bold shrink-0">
                {formatGHS(item.unit_price * item.quantity)}
              </div>
            </li>
          ))}
        </ul>
        <div className="px-5 py-4 border-t border-surface-border bg-surface-dark/40 text-sm">
          <div className="flex justify-between text-gray-400">
            <span>Subtotal</span>
            <span className="text-white font-semibold">
              {formatGHS(order.subtotal)}
            </span>
          </div>
          <div className="flex justify-between text-gray-400 mt-1">
            <span>
              Platform fee ({order.commission_pct}%)
            </span>
            <span className="text-red-400">
              −{formatGHS(order.platform_fee)}
            </span>
          </div>
          <div className="flex justify-between font-extrabold text-white mt-2 pt-2 border-t border-surface-border">
            <span>Your payout</span>
            <span className="text-brand-primary">
              {formatGHS(order.vendor_payout)}
            </span>
          </div>
        </div>
      </section>

      {/* Status history */}
      {order.status_history?.length > 0 && (
        <section className="bg-surface-card border border-surface-border rounded-2xl p-5">
          <h2 className="font-heading text-lg font-bold text-white mb-3">
            Timeline
          </h2>
          <ul className="space-y-3">
            {order.status_history.map((h, i) => (
              <li key={i} className="flex items-start gap-3">
                <div className="w-2 h-2 rounded-full bg-brand-primary mt-1.5 shrink-0" />
                <div>
                  <div className="text-sm text-white capitalize font-semibold">
                    {String(h.status).replace(/_/g, " ")}
                  </div>
                  <div className="text-[11px] text-gray-500">
                    {formatDateTime(h.at)}
                    {h.by && ` · ${h.by}`}
                  </div>
                  {h.note && (
                    <div className="text-xs text-gray-400 italic mt-0.5">
                      {h.note}
                    </div>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Reject */}
      {["pending", "accepted", "confirmed"].includes(order.status) && (
        <div className="pt-4 border-t border-surface-border">
          <button
            onClick={() => setRejectOpen(true)}
            className="inline-flex items-center gap-2 px-3 py-2 rounded-xl border border-red-500/30 text-red-400 text-sm font-bold hover:bg-red-500/10"
          >
            <X className="w-4 h-4" />
            Reject order
          </button>
        </div>
      )}

      <Modal
        open={rejectOpen}
        onClose={() => !updating && setRejectOpen(false)}
        title="Reject this order?"
        maxWidth="max-w-md"
        disableClose={updating}
      >
        <p className="text-sm text-gray-300 mb-4">
          The customer will be notified and refunded. Please tell them why.
        </p>
        <Input
          label="Reason"
          value={rejectReason}
          onChange={(e) => setRejectReason(e.target.value)}
          placeholder="e.g. Out of stock"
        />
        <div className="flex justify-end gap-2 mt-6">
          <Button
            variant="secondary"
            onClick={() => setRejectOpen(false)}
            disabled={updating}
          >
            Cancel
          </Button>
          <Button variant="danger" loading={updating} onClick={rejectOrder}>
            Reject order
          </Button>
        </div>
      </Modal>
    </div>
  );
}