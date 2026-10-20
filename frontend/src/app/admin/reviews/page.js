"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Loader2,
  Star,
  Search,
  Eye,
  EyeOff,
  Sparkles,
  Trash2,
} from "lucide-react";
import Button from "@/components/ui/Button";
import Modal from "@/components/ui/Modal";
import EmptyState from "@/components/ui/EmptyState";
import { useToast } from "@/components/ui/Toast";
import { adminApi } from "@/lib/adminApi";
import { formatDateTime } from "@/lib/utils";

export default function AdminReviewsPage() {
  const toast = useToast();
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("all"); // all | published | hidden | featured
  const [busyId, setBusyId] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const data = await adminApi.get(
        "/api/v1/reviews?published_only=false&limit=500"
      );
      setReviews(Array.isArray(data) ? data : []);
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

  const visible = useMemo(() => {
    let list = reviews;
    if (filter === "published") list = list.filter((r) => r.is_published);
    if (filter === "hidden") list = list.filter((r) => !r.is_published);
    if (filter === "featured") list = list.filter((r) => r.is_featured);
    const q = query.trim().toLowerCase();
    if (q) {
      list = list.filter(
        (r) =>
          r.customer_name?.toLowerCase().includes(q) ||
          r.vendor_name?.toLowerCase().includes(q) ||
          r.comment?.toLowerCase().includes(q) ||
          r.order_reference?.toLowerCase().includes(q)
      );
    }
    return list;
  }, [reviews, filter, query]);

  async function togglePublished(r) {
    setBusyId(r.id);
    try {
      const updated = await adminApi.patch(`/api/v1/reviews/${r.id}`, {
        is_published: !r.is_published,
      });
      setReviews((prev) => prev.map((x) => (x.id === r.id ? updated : x)));
      toast.success(updated.is_published ? "Published" : "Hidden");
    } catch (e) {
      toast.error(e.message);
    } finally {
      setBusyId(null);
    }
  }

  async function toggleFeatured(r) {
    setBusyId(r.id);
    try {
      const updated = await adminApi.patch(`/api/v1/reviews/${r.id}`, {
        is_featured: !r.is_featured,
      });
      setReviews((prev) => prev.map((x) => (x.id === r.id ? updated : x)));
      toast.success(updated.is_featured ? "Featured" : "Unfeatured");
    } catch (e) {
      toast.error(e.message);
    } finally {
      setBusyId(null);
    }
  }

  async function doDelete() {
    if (!confirmDelete) return;
    setDeleting(true);
    try {
      await adminApi.del(`/api/v1/reviews/${confirmDelete.id}`);
      setReviews((prev) => prev.filter((x) => x.id !== confirmDelete.id));
      toast.success("Deleted");
      setConfirmDelete(null);
    } catch (e) {
      toast.error(e.message);
    } finally {
      setDeleting(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-heading text-3xl font-black text-white">Reviews</h1>
        <p className="text-sm text-gray-400 mt-1">
          Moderate, hide, feature, or delete customer reviews.
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search customer, vendor, or comment…"
            className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-surface-card border border-surface-border text-white text-sm focus:border-brand-primary outline-none"
          />
        </div>
        <div className="inline-flex rounded-xl border border-surface-border bg-surface-card p-1">
          {[
            { id: "all", label: "All" },
            { id: "published", label: "Published" },
            { id: "hidden", label: "Hidden" },
            { id: "featured", label: "Featured" },
          ].map((f) => (
            <button
              key={f.id}
              onClick={() => setFilter(f.id)}
              className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-colors ${
                filter === f.id
                  ? "bg-brand-primary text-white"
                  : "text-gray-400 hover:text-white"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
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
      ) : visible.length === 0 ? (
        <EmptyState icon={Star} title="No reviews" />
      ) : (
        <div className="space-y-3">
          {visible.map((r) => (
            <div
              key={r.id}
              className="bg-surface-card border border-surface-border rounded-2xl p-5"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <div className="flex items-center gap-0.5">
                      {Array.from({ length: 5 }).map((_, i) => (
                        <Star
                          key={i}
                          className={`w-3.5 h-3.5 ${
                            i < r.rating
                              ? "fill-brand-gold text-brand-gold"
                              : "text-gray-600"
                          }`}
                        />
                      ))}
                    </div>
                    <span className="text-xs text-gray-500">
                      {r.rating}/5
                    </span>
                    {r.is_published ? (
                      <span className="text-[10px] px-2 py-0.5 rounded-md bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 uppercase font-bold">
                        Published
                      </span>
                    ) : (
                      <span className="text-[10px] px-2 py-0.5 rounded-md bg-red-500/10 border border-red-500/30 text-red-400 uppercase font-bold">
                        Hidden
                      </span>
                    )}
                    {r.is_featured && (
                      <span className="text-[10px] px-2 py-0.5 rounded-md bg-brand-gold/10 border border-brand-gold/30 text-brand-gold uppercase font-bold">
                        Featured
                      </span>
                    )}
                  </div>
                  <div className="text-sm text-white font-bold mt-2">
                    {r.customer_name || "Anonymous"}
                    {r.vendor_name && (
                      <span className="text-gray-500 font-normal">
                        {" "}
                        · on {r.vendor_name}
                      </span>
                    )}
                  </div>
                  <div className="text-[11px] text-gray-500 mt-0.5 font-mono">
                    {r.order_reference} · {formatDateTime(r.created_at)}
                  </div>
                  {r.comment && (
                    <p className="text-sm text-gray-300 mt-2 whitespace-pre-wrap">
                      {r.comment}
                    </p>
                  )}
                </div>
              </div>
              <div className="flex flex-wrap gap-2 mt-3 pt-3 border-t border-surface-border">
                <Button
                  variant="secondary"
                  size="sm"
                  loading={busyId === r.id}
                  onClick={() => togglePublished(r)}
                >
                  {r.is_published ? (
                    <EyeOff className="w-3.5 h-3.5" />
                  ) : (
                    <Eye className="w-3.5 h-3.5" />
                  )}
                  {r.is_published ? "Hide" : "Publish"}
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  loading={busyId === r.id}
                  onClick={() => toggleFeatured(r)}
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  {r.is_featured ? "Unfeature" : "Feature"}
                </Button>
                <Button
                  variant="danger"
                  size="sm"
                  onClick={() => setConfirmDelete(r)}
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  Delete
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      <Modal
        open={!!confirmDelete}
        onClose={() => !deleting && setConfirmDelete(null)}
        title="Delete review?"
        maxWidth="max-w-md"
        disableClose={deleting}
      >
        <p className="text-sm text-gray-300">
          This permanently removes the review. Consider hiding instead if you
          only want it off the storefront.
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