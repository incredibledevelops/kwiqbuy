"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Star, Plus, Minus, Utensils } from "lucide-react";
import { API_URL } from "@/lib/api";
import { useCart } from "@/components/site/CartContext";
import { useToast } from "@/components/ui/Toast";
import Button from "@/components/ui/Button";
import { SkeletonBlock, SkeletonLine } from "@/components/ui/Skeleton";
import { formatGHS } from "@/lib/utils";

export default function FoodProductPage() {
  const { slug } = useParams();
  const router = useRouter();
  const { addItem } = useCart();
  const toast = useToast();

  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [qty, setQty] = useState(1);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!slug) return;
    (async () => {
      setLoading(true);
      try {
        const res = await fetch(`${API_URL}/api/v1/products/slug/${slug}`);
        if (!res.ok) {
          setError("Product not found");
          return;
        }
        setProduct(await res.json());
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    })();
  }, [slug]);

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-8 space-y-6">
        <SkeletonLine className="h-4 w-32" />
        <div className="grid md:grid-cols-2 gap-8">
          <SkeletonBlock className="h-80" />
          <div className="space-y-4">
            <SkeletonLine className="h-8 w-3/4" />
            <SkeletonLine className="h-4 w-1/2" />
            <SkeletonLine className="h-4 w-full" />
            <SkeletonBlock className="h-12 w-full" />
          </div>
        </div>
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center p-4">
        <div className="text-center">
          <h1 className="font-heading text-2xl font-black text-white">
            Item not found
          </h1>
          <p className="text-gray-400 text-sm mt-2">{error}</p>
          <Button href="/food" variant="primary" className="mt-6">
            <ArrowLeft className="w-4 h-4" />
            Back to food
          </Button>
        </div>
      </div>
    );
  }

  function handleAdd() {
    addItem({
      cartId: `food-${product.id}`,
      product_id: product.id,
      vendor_id: product.vendor_id,
      vendor_name: product.vendor_name,
      vendor_category: "food",
      name: product.name,
      unit_price: product.price,
      quantity: qty,
      image_url: product.image_url,
    });
    toast.success(`${product.name} added`);
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <button
        onClick={() => router.back()}
        className="inline-flex items-center gap-2 text-sm font-bold text-gray-400 hover:text-brand-primary mb-6"
      >
        <ArrowLeft className="w-4 h-4" />
        Back
      </button>

      <div className="grid md:grid-cols-2 gap-8">
        <div className="rounded-3xl overflow-hidden bg-surface-card border border-surface-border aspect-square">
          {product.image_url ? (
            <img
              src={product.image_url}
              alt={product.name}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-gray-600">
              <Utensils className="w-10 h-10" />
            </div>
          )}
        </div>

        <div className="space-y-5">
          {product.vendor_name && (
            <div className="inline-flex items-center gap-1.5 text-xs text-brand-primary font-bold uppercase tracking-wider">
              <Utensils className="w-3.5 h-3.5" />
              {product.vendor_name}
            </div>
          )}

          <h1 className="font-heading text-3xl sm:text-4xl font-black text-white">
            {product.name}
          </h1>

          {product.total_reviews > 0 && (
            <div className="flex items-center gap-1.5 text-sm">
              <Star className="w-4 h-4 fill-brand-gold text-brand-gold" />
              <span className="text-white font-bold">
                {product.average_rating.toFixed(1)}
              </span>
              <span className="text-gray-500">
                ({product.total_reviews} reviews)
              </span>
            </div>
          )}

          {product.description && (
            <p className="text-gray-300 text-sm leading-relaxed">
              {product.description}
            </p>
          )}

          <div className="text-3xl font-black text-brand-primary">
            {formatGHS(product.price)}
          </div>

          {!product.is_available ? (
            <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm font-bold">
              Out of stock
            </div>
          ) : (
            <>
              <div className="flex items-center gap-3">
                <span className="text-xs text-gray-400 font-bold uppercase tracking-wider">
                  Quantity
                </span>
                <div className="inline-flex items-center gap-1 bg-surface-card px-1 py-1 rounded-xl border border-surface-border">
                  <button
                    onClick={() => setQty(Math.max(1, qty - 1))}
                    className="w-8 h-8 rounded-lg flex items-center justify-center text-gray-400 hover:text-white hover:bg-white/5"
                  >
                    <Minus className="w-3.5 h-3.5" />
                  </button>
                  <span className="text-white font-bold w-8 text-center">
                    {qty}
                  </span>
                  <button
                    onClick={() => setQty(qty + 1)}
                    className="w-8 h-8 rounded-lg flex items-center justify-center text-gray-400 hover:text-white hover:bg-white/5"
                  >
                    <Plus className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              <Button
                variant="primary"
                size="lg"
                onClick={handleAdd}
                className="w-full"
              >
                <Plus className="w-5 h-5" />
                Add {qty} — {formatGHS(product.price * qty)}
              </Button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}