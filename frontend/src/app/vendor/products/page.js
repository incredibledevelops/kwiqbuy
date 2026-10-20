"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  Plus,
  Search,
  X,
  Edit3,
  Trash2,
  Loader2,
  Package as PackageIcon,
  Eye,
  EyeOff,
} from "lucide-react";
import Button from "@/components/ui/Button";
import Modal from "@/components/ui/Modal";
import EmptyState from "@/components/ui/EmptyState";
import { useToast } from "@/components/ui/Toast";
import { vendorApi } from "@/lib/vendorApi";
import { formatGHS } from "@/lib/utils";

export default function VendorProductsPage() {
  const toast = useToast();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("all"); // all | live | hidden
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const data = await vendorApi.get("/api/v1/vendor/products?limit=500");
      setProducts(Array.isArray(data) ? data : []);
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
    let list = products;
    if (filter === "live") list = list.filter((p) => p.is_available);
    if (filter === "hidden") list = list.filter((p) => !p.is_available);
    const q = query.trim().toLowerCase();
    if (q) {
      list = list.filter(
        (p) =>
          p.name?.toLowerCase().includes(q) ||
          p.description?.toLowerCase().includes(q) ||
          (p.tags || []).some((t) => t.toLowerCase().includes(q))
      );
    }
    return list;
  }, [products, filter, query]);

  async function toggleStock(p) {
    try {
      const updated = await vendorApi.patch(
        `/api/v1/vendor/products/${p.id}/stock`,
        { is_available: !p.is_available }
      );
      setProducts((prev) =>
        prev.map((x) => (x.id === p.id ? { ...x, ...updated } : x))
      );
      toast.success(updated.is_available ? "Product is live" : "Product hidden");
    } catch (e) {
      toast.error(e.message);
    }
  }

  async function doDelete() {
    if (!confirmDelete) return;
    setDeleting(true);
    try {
      await vendorApi.del(`/api/v1/vendor/products/${confirmDelete.id}`);
      setProducts((prev) => prev.filter((x) => x.id !== confirmDelete.id));
      toast.success(`Deleted "${confirmDelete.name}"`);
      setConfirmDelete(null);
    } catch (e) {
      toast.error(e.message);
    } finally {
      setDeleting(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="font-heading text-3xl font-black text-white">Products</h1>
          <p className="text-sm text-gray-400 mt-1">
            {products.length} product{products.length === 1 ? "" : "s"} total
          </p>
        </div>
        <Link
          href="/vendor/products/new"
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-brand-primary hover:bg-brand-primaryDark text-white font-bold text-sm transition-colors"
        >
          <Plus className="w-4 h-4" />
          Add product
        </Link>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[220px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search products…"
            className="w-full pl-9 pr-9 py-2.5 rounded-xl bg-surface-card border border-surface-border text-white text-sm focus:border-brand-primary outline-none"
          />
          {query && (
            <button
              onClick={() => setQuery("")}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-lg text-gray-500 hover:text-white"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
        <div className="inline-flex rounded-xl border border-surface-border bg-surface-card p-1">
          {[
            { id: "all", label: "All" },
            { id: "live", label: "Live" },
            { id: "hidden", label: "Hidden" },
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

      {/* List */}
      {loading ? (
        <div className="py-16 text-center">
          <Loader2 className="w-8 h-8 text-brand-primary animate-spin mx-auto" />
        </div>
      ) : visible.length === 0 ? (
        <EmptyState
          icon={PackageIcon}
          title={query ? "No matches" : "No products yet"}
          message={
            query
              ? `Nothing matches "${query}"`
              : "Add your first product to start selling."
          }
          action={
            <Link
              href="/vendor/products/new"
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-brand-primary hover:bg-brand-primaryDark text-white font-bold text-sm transition-colors"
            >
              <Plus className="w-4 h-4" />
              Add product
            </Link>
          }
        />
      ) : (
        <div className="bg-surface-card border border-surface-border rounded-2xl overflow-hidden">
          <ul className="divide-y divide-surface-border">
            {visible.map((p) => (
              <li key={p.id} className="p-4 flex items-center gap-4">
                <div className="w-14 h-14 rounded-xl bg-surface-dark border border-surface-border overflow-hidden shrink-0">
                  {p.image_url ? (
                    <img
                      src={p.image_url}
                      alt={p.name}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-gray-600">
                      <PackageIcon className="w-5 h-5" />
                    </div>
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <Link
                      href={`/vendor/products/${p.id}`}
                      className="font-bold text-white hover:text-brand-primary truncate"
                    >
                      {p.name}
                    </Link>
                    {!p.is_available && (
                      <span className="text-[10px] px-2 py-0.5 rounded-md bg-red-500/10 border border-red-500/30 text-red-400 font-bold uppercase">
                        Hidden
                      </span>
                    )}
                    {p.product_type === "variable" && (
                      <span className="text-[10px] px-2 py-0.5 rounded-md bg-brand-accent/10 border border-brand-accent/30 text-brand-accent font-bold uppercase">
                        Variants
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-gray-400 mt-0.5 truncate">
                    {p.description || "No description"}
                  </div>
                  <div className="flex items-center gap-3 mt-1 text-xs">
                    <span className="text-brand-primary font-bold">
                      {formatGHS(p.price)}
                    </span>
                    {p.stock_count != null && (
                      <span className="text-gray-500">
                        Stock: {p.stock_count}
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-1.5 shrink-0">
                  <button
                    onClick={() => toggleStock(p)}
                    title={p.is_available ? "Hide" : "Show"}
                    className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/5"
                  >
                    {p.is_available ? (
                      <Eye className="w-4 h-4" />
                    ) : (
                      <EyeOff className="w-4 h-4" />
                    )}
                  </button>
                  <Link
                    href={`/vendor/products/${p.id}`}
                    title="Edit"
                    className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/5"
                  >
                    <Edit3 className="w-4 h-4" />
                  </Link>
                  <button
                    onClick={() => setConfirmDelete(p)}
                    title="Delete"
                    className="p-2 rounded-lg text-gray-400 hover:text-red-400 hover:bg-red-500/10"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      <Modal
        open={!!confirmDelete}
        onClose={() => !deleting && setConfirmDelete(null)}
        title="Delete product?"
        maxWidth="max-w-md"
        disableClose={deleting}
      >
        <p className="text-sm text-gray-300">
          Are you sure you want to delete{" "}
          <strong className="text-white">{confirmDelete?.name}</strong>? This
          cannot be undone.
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