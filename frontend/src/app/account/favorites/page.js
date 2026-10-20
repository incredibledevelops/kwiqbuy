"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Heart, Loader2, Plus, AlertCircle, Trash2 } from "lucide-react";
import EmptyState from "@/components/ui/EmptyState";
import Button from "@/components/ui/Button";
import { useCart } from "@/components/site/CartContext";
import { useToast } from "@/components/ui/Toast";
import { customerFetch } from "@/lib/customerAuth";
import { API_URL } from "@/lib/api";
import { formatGHS } from "@/lib/utils";

export default function FavoritesPage() {
  const toast = useToast();
  const { addItem } = useCart();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await customerFetch(
        `${API_URL}/api/v1/customer-account/favorites`
      );
      if (!res.ok) throw new Error(`Failed (${res.status})`);
      const data = await res.json().catch(() => []);
      setItems(Array.isArray(data) ? data : []);
    } catch (e) {
      setError(e.message || "Failed to load favorites.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  function handleAdd(p) {
    addItem({
      // Stable cartId so the same product from any entry point de-duplicates
      cartId: `${p.vendor_id ?? "v"}:${p.id}`,
      id: p.id,
      product_id: p.id,
      vendor_id: p.vendor_id,
      vendor_name: p.vendor_name,
      vendor_category: p.vendor_category,
      name: p.name,
      unit_price: p.price,
      quantity: 1,
      image_url: p.image_url,
    });
    toast.success(`${p.name} added to cart`);
  }

  async function removeFavorite(id) {
    const prev = items;
    setItems((list) => list.filter((x) => x.id !== id));
    try {
      const res = await customerFetch(
        `${API_URL}/api/v1/customer-account/favorites/${id}`,
        { method: "DELETE" }
      );
      if (!res.ok) throw new Error("Failed to remove");
      toast.success("Removed from favorites");
    } catch (e) {
      setItems(prev);
      toast.error(e.message || "Failed to remove");
    }
  }

  function productHref(p) {
    const base = p.vendor_category === "retail" ? "/shop" : "/food";
    return `${base}/${p.slug || p.id}`;
  }

  if (loading) {
    return (
      <div className="space-y-4" aria-busy="true">
        <div className="animate-pulse h-8 w-40 bg-surface-card border border-surface-border rounded-xl" />
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
          {[0, 1, 2, 3].map((i) => (
            <div
              key={i}
              className="animate-pulse aspect-[3/4] bg-surface-card border border-surface-border rounded-2xl"
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

  if (items.length === 0) {
    return (
      <EmptyState
        icon={Heart}
        title="No favorites yet"
        message="Tap the heart icon on any product to save it here."
        action={
          <Button href="/food" variant="primary">
            Browse food
          </Button>
        }
      />
    );
  }

  return (
    <div className="space-y-4">
      <h1 className="font-heading text-2xl font-black text-white">
        Favorites
      </h1>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
        {items.map((p) => (
          <div
            key={p.id}
            className="bg-surface-card border border-surface-border rounded-2xl overflow-hidden flex flex-col"
          >
            <Link
              href={productHref(p)}
              className="block aspect-square overflow-hidden bg-surface-dark"
            >
              {p.image_url ? (
                <img
                  src={p.image_url}
                  alt={p.name}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-gray-600">
                  ?
                </div>
              )}
            </Link>
            <div className="p-3 flex-1 flex flex-col">
              <Link
                href={productHref(p)}
                className="font-bold text-white text-sm line-clamp-2 hover:text-brand-primary"
              >
                {p.name}
              </Link>
              {p.vendor_name && (
                <div className="text-[10px] text-gray-500 mt-0.5 truncate">
                  {p.vendor_name}
                </div>
              )}
              <div className="text-brand-primary font-bold mt-1 text-sm">
                {formatGHS(p.price)}
              </div>
              <div className="mt-3 flex gap-2">
                <button
                  onClick={() => handleAdd(p)}
                  className="flex-1 py-1.5 rounded-lg bg-brand-primary/10 text-brand-primary border border-brand-primary/30 text-xs font-bold hover:bg-brand-primary/20 flex items-center justify-center gap-1 transition-colors"
                >
                  <Plus className="w-3.5 h-3.5" /> Add
                </button>
                <button
                  onClick={() => removeFavorite(p.id)}
                  aria-label={`Remove ${p.name} from favorites`}
                  className="p-1.5 rounded-lg text-gray-500 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}