"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Save, Upload, X, Trash2, Loader2 } from "lucide-react";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Modal from "@/components/ui/Modal";
import { useToast } from "@/components/ui/Toast";
import { vendorApi } from "@/lib/vendorApi";

export default function EditProductPage() {
  const params = useParams();
  const router = useRouter();
  const toast = useToast();
  const productId = params?.id;

  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [error, setError] = useState("");

  const [form, setForm] = useState({
    name: "",
    description: "",
    price: "",
    category_id: "",
    product_type: "simple",
    image_url: "",
    tags: "",
    brand: "",
    stock_count: "",
    low_stock_threshold: 5,
    is_available: true,
    display_order: 0,
  });

  useEffect(() => {
    if (!productId) return;
    (async () => {
      try {
        const [prod, cats] = await Promise.all([
          vendorApi.get(`/api/v1/vendor/products/${productId}`),
          fetch(
            `${process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"}/api/v1/categories?active_only=true`
          ).then((r) => r.json().catch(() => [])),
        ]);
        setCategories(Array.isArray(cats) ? cats : []);
        setForm({
          name: prod.name || "",
          description: prod.description || "",
          price: prod.price != null ? String(prod.price) : "",
          category_id: prod.category_id || "",
          product_type: prod.product_type || "simple",
          image_url: prod.image_url || "",
          tags: (prod.tags || []).join(", "),
          brand: prod.brand || "",
          stock_count: prod.stock_count != null ? String(prod.stock_count) : "",
          low_stock_threshold: prod.low_stock_threshold ?? 5,
          is_available: prod.is_available ?? true,
          display_order: prod.display_order ?? 0,
        });
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    })();
  }, [productId]);

  function set(k, v) {
    setForm((f) => ({ ...f, [k]: v }));
  }

  async function handleUpload(file) {
    if (!file) return;
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("subdir", "products");
      const res = await vendorApi.upload("/api/v1/uploads/vendor", fd);
      set("image_url", res.url);
      toast.success("Image uploaded");
    } catch (e) {
      toast.error(e.message);
    } finally {
      setUploading(false);
    }
  }

  async function save(e) {
    e?.preventDefault?.();
    setError("");

    const price = parseFloat(form.price);
    if (!Number.isFinite(price) || price < 0) {
      setError("Enter a valid price");
      return;
    }

    const payload = {
      name: form.name.trim(),
      description: form.description.trim() || null,
      price,
      category_id: form.category_id,
      image_url: form.image_url || null,
      tags: form.tags
        ? form.tags.split(",").map((t) => t.trim()).filter(Boolean)
        : [],
      brand: form.brand.trim() || null,
      stock_count:
        form.stock_count === "" ? null : Math.max(0, parseInt(form.stock_count, 10)),
      low_stock_threshold: Math.max(0, parseInt(form.low_stock_threshold, 10) || 5),
      is_available: form.is_available,
      display_order: parseInt(form.display_order, 10) || 0,
    };

    setSaving(true);
    try {
      await vendorApi.patch(`/api/v1/vendor/products/${productId}`, payload);
      toast.success("Product saved");
    } catch (e) {
      setError(e.message);
      toast.error(e.message);
    } finally {
      setSaving(false);
    }
  }

  async function doDelete() {
    setDeleting(true);
    try {
      await vendorApi.del(`/api/v1/vendor/products/${productId}`);
      toast.success("Product deleted");
      router.replace("/vendor/products");
    } catch (e) {
      toast.error(e.message);
      setDeleting(false);
      setConfirmDelete(false);
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
      <Link
        href="/vendor/products"
        className="inline-flex items-center gap-2 text-sm font-bold text-gray-400 hover:text-brand-primary"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to products
      </Link>

      <div className="flex items-start justify-between gap-4 flex-wrap">
        <h1 className="font-heading text-3xl font-black text-white">
          Edit product
        </h1>
        <button
          onClick={() => setConfirmDelete(true)}
          className="inline-flex items-center gap-2 px-3 py-2 rounded-xl border border-red-500/30 text-red-400 text-xs font-bold hover:bg-red-500/10"
        >
          <Trash2 className="w-4 h-4" />
          Delete product
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
          {error}
        </div>
      )}

      <form onSubmit={save} className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <section className="bg-surface-card border border-surface-border rounded-2xl p-6 space-y-4">
            <h2 className="font-heading text-lg font-bold text-white">Basics</h2>
            <Input
              label="Name"
              required
              value={form.name}
              onChange={(e) => set("name", e.target.value)}
            />
            <div>
              <label className="block text-xs font-bold text-gray-300 mb-1.5">
                Description
              </label>
              <textarea
                rows={4}
                value={form.description}
                onChange={(e) => set("description", e.target.value)}
                className="w-full px-4 py-3 rounded-xl bg-surface-dark border border-surface-border text-white text-sm focus:border-brand-primary outline-none resize-none"
              />
            </div>
            <div className="grid sm:grid-cols-2 gap-4">
              <Input
                label="Price (GHS)"
                type="number"
                min="0"
                step="0.01"
                required
                value={form.price}
                onChange={(e) => set("price", e.target.value)}
              />
              <div>
                <label className="block text-xs font-bold text-gray-300 mb-1.5">
                  Category
                </label>
                <select
                  value={form.category_id}
                  onChange={(e) => set("category_id", e.target.value)}
                  className="w-full px-4 py-3 rounded-xl bg-surface-dark border border-surface-border text-white text-sm focus:border-brand-primary outline-none"
                >
                  {categories.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </section>

          <section className="bg-surface-card border border-surface-border rounded-2xl p-6 space-y-4">
            <h2 className="font-heading text-lg font-bold text-white">
              Inventory
            </h2>
            <div className="grid sm:grid-cols-2 gap-4">
              <Input
                label="Stock count"
                type="number"
                min="0"
                value={form.stock_count}
                onChange={(e) => set("stock_count", e.target.value)}
                placeholder="Leave blank for unlimited"
              />
              <Input
                label="Low stock warning at"
                type="number"
                min="0"
                value={form.low_stock_threshold}
                onChange={(e) => set("low_stock_threshold", e.target.value)}
              />
            </div>
            <label className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer">
              <input
                type="checkbox"
                checked={form.is_available}
                onChange={(e) => set("is_available", e.target.checked)}
                className="accent-brand-primary"
              />
              Product is live and can be ordered
            </label>
          </section>

          <section className="bg-surface-card border border-surface-border rounded-2xl p-6 space-y-4">
            <h2 className="font-heading text-lg font-bold text-white">
              Metadata
            </h2>
            <Input
              label="Brand"
              value={form.brand}
              onChange={(e) => set("brand", e.target.value)}
            />
            <Input
              label="Tags (comma-separated)"
              value={form.tags}
              onChange={(e) => set("tags", e.target.value)}
            />
          </section>
        </div>

        <div className="space-y-6">
          <section className="bg-surface-card border border-surface-border rounded-2xl p-6 space-y-4">
            <h2 className="font-heading text-lg font-bold text-white">
              Product image
            </h2>
            {form.image_url ? (
              <div className="relative rounded-xl overflow-hidden border border-surface-border bg-surface-dark aspect-square">
                <img
                  src={form.image_url}
                  alt="Product"
                  className="w-full h-full object-cover"
                />
                <button
                  type="button"
                  onClick={() => set("image_url", "")}
                  className="absolute top-2 right-2 p-1.5 rounded-lg bg-black/60 text-white hover:bg-black/80"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <label className="block rounded-xl border-2 border-dashed border-surface-border bg-surface-dark aspect-square flex flex-col items-center justify-center cursor-pointer hover:border-brand-primary">
                <input
                  type="file"
                  accept="image/png,image/jpeg,image/webp"
                  className="hidden"
                  onChange={(e) => handleUpload(e.target.files?.[0])}
                  disabled={uploading}
                />
                {uploading ? (
                  <span className="text-xs text-gray-400">Uploading…</span>
                ) : (
                  <>
                    <Upload className="w-6 h-6 text-gray-500 mb-2" />
                    <span className="text-xs text-gray-400">
                      Click to upload
                    </span>
                  </>
                )}
              </label>
            )}
          </section>

          <div className="sticky top-4">
            <Button
              type="submit"
              variant="primary"
              size="lg"
              loading={saving}
              className="w-full"
            >
              <Save className="w-4 h-4" />
              Save changes
            </Button>
          </div>
        </div>
      </form>

      <Modal
        open={confirmDelete}
        onClose={() => !deleting && setConfirmDelete(false)}
        title="Delete product?"
        maxWidth="max-w-md"
        disableClose={deleting}
      >
        <p className="text-sm text-gray-300">
          Deleting is permanent. Are you sure?
        </p>
        <div className="flex justify-end gap-2 mt-6">
          <Button
            variant="secondary"
            onClick={() => setConfirmDelete(false)}
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