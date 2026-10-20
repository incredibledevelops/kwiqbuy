"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Save, Upload, X, Plus } from "lucide-react";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import { useToast } from "@/components/ui/Toast";
import { vendorApi } from "@/lib/vendorApi";
import { formatGHS } from "@/lib/utils";

export default function NewProductPage() {
  const router = useRouter();
  const toast = useToast();

  const [categories, setCategories] = useState([]);
  const [loadingCats, setLoadingCats] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
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
    (async () => {
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"}/api/v1/categories?active_only=true`
        );
        const data = await res.json();
        const list = Array.isArray(data) ? data : [];
        setCategories(list);
        if (list[0]) setForm((f) => ({ ...f, category_id: list[0].id }));
      } catch {
        setCategories([]);
      } finally {
        setLoadingCats(false);
      }
    })();
  }, []);

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

    if (!form.name.trim() || form.name.trim().length < 1) {
      setError("Product name is required");
      return;
    }
    const price = parseFloat(form.price);
    if (!Number.isFinite(price) || price < 0) {
      setError("Enter a valid price (0 or more)");
      return;
    }
    if (!form.category_id) {
      setError("Please select a category");
      return;
    }

    const payload = {
      name: form.name.trim(),
      description: form.description.trim() || null,
      price,
      category_id: form.category_id,
      product_type: form.product_type,
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
      const created = await vendorApi.post("/api/v1/vendor/products", payload);
      toast.success("Product created");
      router.replace(`/vendor/products/${created.id}`);
    } catch (e) {
      setError(e.message);
      toast.error(e.message);
    } finally {
      setSaving(false);
    }
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

      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="font-heading text-3xl font-black text-white">
            New product
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Fill in the details and publish when ready.
          </p>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
          {error}
        </div>
      )}

      <form onSubmit={save} className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <section className="bg-surface-card border border-surface-border rounded-2xl p-6 space-y-4">
            <h2 className="font-heading text-lg font-bold text-white">
              Basics
            </h2>
            <Input
              label="Name"
              required
              value={form.name}
              onChange={(e) => set("name", e.target.value)}
              placeholder="e.g. Wireless Earbuds Pro"
            />
            <div>
              <label className="block text-xs font-bold text-gray-300 mb-1.5">
                Description
              </label>
              <textarea
                rows={4}
                value={form.description}
                onChange={(e) => set("description", e.target.value)}
                placeholder="Tell customers what makes this product great…"
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
                placeholder="0.00"
              />
              <div>
                <label className="block text-xs font-bold text-gray-300 mb-1.5">
                  Category
                </label>
                <select
                  value={form.category_id}
                  onChange={(e) => set("category_id", e.target.value)}
                  disabled={loadingCats}
                  className="w-full px-4 py-3 rounded-xl bg-surface-dark border border-surface-border text-white text-sm focus:border-brand-primary outline-none"
                >
                  {loadingCats && <option>Loading…</option>}
                  {!loadingCats && categories.length === 0 && (
                    <option value="">No categories available</option>
                  )}
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
                label="Stock count (leave blank for unlimited)"
                type="number"
                min="0"
                value={form.stock_count}
                onChange={(e) => set("stock_count", e.target.value)}
                placeholder="e.g. 25"
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
              label="Brand (optional)"
              value={form.brand}
              onChange={(e) => set("brand", e.target.value)}
              placeholder="e.g. Sony"
            />
            <Input
              label="Tags (comma-separated)"
              value={form.tags}
              onChange={(e) => set("tags", e.target.value)}
              placeholder="audio, wireless, premium"
              hint="Helps customers find your product in search."
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
                    <span className="text-[10px] text-gray-600 mt-1">
                      PNG, JPG, or WebP · max 5MB
                    </span>
                  </>
                )}
              </label>
            )}
          </section>

          <div className="sticky top-4 space-y-3">
            <Button
              type="submit"
              variant="primary"
              size="lg"
              loading={saving}
              className="w-full"
            >
              <Save className="w-4 h-4" />
              Save product
            </Button>
            <Button
              type="button"
              variant="secondary"
              size="lg"
              className="w-full"
              onClick={() => router.push("/vendor/products")}
            >
              Cancel
            </Button>
          </div>
        </div>
      </form>
    </div>
  );
}