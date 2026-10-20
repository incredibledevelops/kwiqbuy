"use client";

import { useEffect, useState } from "react";
import {
  Loader2,
  Webhook as WebhookIcon,
  Plus,
  Copy,
  Trash2,
  Send,
  Eye,
  EyeOff,
} from "lucide-react";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Modal from "@/components/ui/Modal";
import EmptyState from "@/components/ui/EmptyState";
import { useToast } from "@/components/ui/Toast";
import { vendorApi } from "@/lib/vendorApi";
import { formatDateTime } from "@/lib/utils";

const ALL_EVENTS = [
  { value: "order.created", label: "Order created" },
  { value: "order.status_changed", label: "Order status changed" },
  { value: "order.delivered", label: "Order delivered" },
  { value: "payout.paid", label: "Payout paid" },
  { value: "subscription.activated", label: "Subscription activated" },
  { value: "review.posted", label: "Review posted" },
];

export default function VendorWebhooksPage() {
  const toast = useToast();
  const [webhooks, setWebhooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [createOpen, setCreateOpen] = useState(false);
  const [newSecret, setNewSecret] = useState(null);
  const [deliveryModal, setDeliveryModal] = useState(null);
  const [deliveries, setDeliveries] = useState([]);
  const [loadingDeliveries, setLoadingDeliveries] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const [form, setForm] = useState({
    url: "",
    description: "",
    events: ALL_EVENTS.map((e) => e.value),
  });
  const [saving, setSaving] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const data = await vendorApi.get("/api/v1/vendor/webhooks");
      setWebhooks(Array.isArray(data) ? data : []);
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

  async function createWebhook() {
    if (!form.url.trim()) {
      toast.error("URL is required");
      return;
    }
    setSaving(true);
    try {
      const created = await vendorApi.post("/api/v1/vendor/webhooks", {
        url: form.url.trim(),
        description: form.description.trim() || null,
        events: form.events,
      });
      setNewSecret({
        id: created.id,
        secret: created.secret,
        url: created.url,
      });
      setForm({
        url: "",
        description: "",
        events: ALL_EVENTS.map((e) => e.value),
      });
      setCreateOpen(false);
      await load();
    } catch (e) {
      toast.error(e.message);
    } finally {
      setSaving(false);
    }
  }

  async function toggleActive(wh) {
    try {
      await vendorApi.patch(`/api/v1/vendor/webhooks/${wh.id}`, {
        is_active: !wh.is_active,
      });
      await load();
    } catch (e) {
      toast.error(e.message);
    }
  }

  async function testWebhook(wh) {
    try {
      const res = await vendorApi.post(
        `/api/v1/vendor/webhooks/${wh.id}/test`
      );
      if (res.delivered) {
        toast.success(`Delivered (HTTP ${res.status_code})`);
      } else {
        toast.error(res.error || `Failed (HTTP ${res.status_code || "—"})`);
      }
    } catch (e) {
      toast.error(e.message);
    }
  }

  async function openDeliveries(wh) {
    setDeliveryModal(wh);
    setLoadingDeliveries(true);
    try {
      const data = await vendorApi.get(
        `/api/v1/vendor/webhooks/${wh.id}/deliveries?limit=50`
      );
      setDeliveries(Array.isArray(data) ? data : []);
    } catch (e) {
      toast.error(e.message);
    } finally {
      setLoadingDeliveries(false);
    }
  }

  async function doDelete() {
    if (!confirmDelete) return;
    setDeleting(true);
    try {
      await vendorApi.del(`/api/v1/vendor/webhooks/${confirmDelete.id}`);
      toast.success("Webhook deleted");
      setConfirmDelete(null);
      await load();
    } catch (e) {
      toast.error(e.message);
    } finally {
      setDeleting(false);
    }
  }

  function toggleEvent(value) {
    setForm((f) => ({
      ...f,
      events: f.events.includes(value)
        ? f.events.filter((v) => v !== value)
        : [...f.events, value],
    }));
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="font-heading text-3xl font-black text-white">
            Webhooks
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Receive real-time events from KwiqBuy to your server.
          </p>
        </div>
        <Button variant="primary" size="md" onClick={() => setCreateOpen(true)}>
          <Plus className="w-4 h-4" />
          Add webhook
        </Button>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
          {error}
        </div>
      )}

      {loading ? (
        <div className="py-16 text-center">
          <Loader2 className="w-8 h-8 text-brand-primary animate-spin mx-auto" />
        </div>
      ) : webhooks.length === 0 ? (
        <EmptyState
          icon={WebhookIcon}
          title="No webhooks yet"
          message="Add a webhook to receive order and payout events on your server."
        />
      ) : (
        <ul className="space-y-3">
          {webhooks.map((wh) => (
            <li
              key={wh.id}
              className="p-5 rounded-2xl bg-surface-card border border-surface-border"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-mono text-xs text-brand-primary break-all">
                      {wh.url}
                    </span>
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded-md border font-bold uppercase ${
                        wh.is_active
                          ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/30"
                          : "text-gray-400 bg-white/5 border-white/10"
                      }`}
                    >
                      {wh.is_active ? "active" : "paused"}
                    </span>
                  </div>
                  {wh.description && (
                    <div className="text-xs text-gray-400 mt-1">
                      {wh.description}
                    </div>
                  )}
                  <div className="flex flex-wrap gap-1 mt-2">
                    {wh.events.map((e) => (
                      <span
                        key={e}
                        className="text-[10px] px-2 py-0.5 rounded bg-white/5 text-gray-300 font-mono"
                      >
                        {e}
                      </span>
                    ))}
                  </div>
                  <div className="text-[11px] text-gray-500 mt-2">
                    {wh.last_success_at &&
                      `Last success: ${formatDateTime(wh.last_success_at)} · `}
                    {wh.consecutive_failures > 0 &&
                      `${wh.consecutive_failures} consecutive failures`}
                  </div>
                </div>
              </div>
              <div className="flex flex-wrap gap-2 mt-4">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => testWebhook(wh)}
                >
                  <Send className="w-3.5 h-3.5" />
                  Test
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => openDeliveries(wh)}
                >
                  <Eye className="w-3.5 h-3.5" />
                  Deliveries
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => toggleActive(wh)}
                >
                  {wh.is_active ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                  {wh.is_active ? "Pause" : "Activate"}
                </Button>
                <Button
                  variant="danger"
                  size="sm"
                  onClick={() => setConfirmDelete(wh)}
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  Delete
                </Button>
              </div>
            </li>
          ))}
        </ul>
      )}

      {/* Create modal */}
      <Modal
        open={createOpen}
        onClose={() => !saving && setCreateOpen(false)}
        title="Add webhook"
        maxWidth="max-w-lg"
        disableClose={saving}
      >
        <div className="space-y-4">
          <Input
            label="URL"
            required
            value={form.url}
            onChange={(e) => setForm({ ...form, url: e.target.value })}
            placeholder="https://yourdomain.com/webhooks/kwiqbuy"
            hint="Must be HTTPS in production."
          />
          <Input
            label="Description (optional)"
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            placeholder="e.g. Production endpoint"
          />
          <div>
            <div className="text-xs font-bold text-gray-300 mb-2">
              Subscribe to events
            </div>
            <div className="space-y-1.5">
              {ALL_EVENTS.map((e) => (
                <label
                  key={e.value}
                  className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={form.events.includes(e.value)}
                    onChange={() => toggleEvent(e.value)}
                    className="accent-brand-primary"
                  />
                  <span className="font-mono text-xs">{e.value}</span>
                  <span className="text-xs text-gray-500">— {e.label}</span>
                </label>
              ))}
            </div>
          </div>
        </div>
        <div className="flex justify-end gap-2 mt-6">
          <Button
            variant="secondary"
            onClick={() => setCreateOpen(false)}
            disabled={saving}
          >
            Cancel
          </Button>
          <Button variant="primary" loading={saving} onClick={createWebhook}>
            Create webhook
          </Button>
        </div>
      </Modal>

      {/* Secret-shown-once modal */}
      <Modal
        open={!!newSecret}
        onClose={() => setNewSecret(null)}
        title="Webhook created"
        maxWidth="max-w-lg"
      >
        <div className="space-y-4">
          <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs">
            Copy the signing secret now. It will not be shown again.
          </div>
          <div>
            <div className="text-xs font-bold text-gray-300 mb-1.5">
              Signing secret
            </div>
            <div className="flex items-center gap-2">
              <code className="flex-1 px-3 py-2 rounded-lg bg-surface-dark border border-surface-border text-xs text-white font-mono break-all">
                {newSecret?.secret}
              </code>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(newSecret?.secret || "");
                  toast.success("Copied");
                }}
                className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/5"
              >
                <Copy className="w-4 h-4" />
              </button>
            </div>
          </div>
          <p className="text-xs text-gray-500">
            Verify incoming payloads with HMAC-SHA256 of the raw body, keyed by
            this secret, and compare to the{" "}
            <code className="font-mono">X-KwiqBuy-Signature</code> header.
          </p>
        </div>
        <div className="flex justify-end mt-6">
          <Button variant="primary" onClick={() => setNewSecret(null)}>
            I've saved it
          </Button>
        </div>
      </Modal>

      {/* Deliveries modal */}
      <Modal
        open={!!deliveryModal}
        onClose={() => setDeliveryModal(null)}
        title={`Deliveries — ${deliveryModal?.url || ""}`}
        maxWidth="max-w-2xl"
      >
        {loadingDeliveries ? (
          <div className="py-8 text-center">
            <Loader2 className="w-6 h-6 text-brand-primary animate-spin mx-auto" />
          </div>
        ) : deliveries.length === 0 ? (
          <div className="py-8 text-center text-sm text-gray-500">
            No deliveries yet.
          </div>
        ) : (
          <ul className="space-y-2 max-h-[60vh] overflow-y-auto">
            {deliveries.map((d) => (
              <li
                key={d.id}
                className="p-3 rounded-xl bg-surface-dark border border-surface-border"
              >
                <div className="flex items-center justify-between gap-3">
                  <span className="text-xs font-mono text-brand-primary">
                    {d.event}
                  </span>
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded-md font-bold uppercase ${
                      d.status === "success"
                        ? "text-emerald-400 bg-emerald-500/10"
                        : d.status === "failed"
                        ? "text-amber-400 bg-amber-500/10"
                        : "text-red-400 bg-red-500/10"
                    }`}
                  >
                    {d.status}
                  </span>
                </div>
                <div className="text-[11px] text-gray-500 mt-1">
                  {formatDateTime(d.created_at)} · attempts {d.attempts}
                  {d.response_status && ` · HTTP ${d.response_status}`}
                </div>
                {d.error && (
                  <div className="text-[11px] text-red-400 mt-1">{d.error}</div>
                )}
              </li>
            ))}
          </ul>
        )}
      </Modal>

      {/* Delete confirmation */}
      <Modal
        open={!!confirmDelete}
        onClose={() => !deleting && setConfirmDelete(null)}
        title="Delete webhook?"
        maxWidth="max-w-md"
        disableClose={deleting}
      >
        <p className="text-sm text-gray-300">
          You will stop receiving events at{" "}
          <strong className="text-white font-mono">{confirmDelete?.url}</strong>.
        </p>
        <div className="flex justify-end gap-2 mt-6">
          <Button
            variant="secondary"
            onClick={() => setConfirmDelete(null)}
            disabled={deleting}
          >
            Cancel
          </Button>
          <Button variant="danger" loading={deleting} onClick={doDelete}>
            Delete
          </Button>
        </div>
      </Modal>
    </div>
  );
}