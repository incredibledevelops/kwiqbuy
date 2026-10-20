"use client";

import { useEffect, useState, useMemo } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Star, Plus, Minus, Store, Truck, ShieldCheck } from "lucide-react";
import { API_URL } from "@/lib/api";
import { useCart } from "@/components/site/CartContext";
import { useToast } from "@/components/ui/Toast";
import Button from "@/components/ui/Button";
import { SkeletonBlock, SkeletonLine } from "@/components/ui/Skeleton";
import { formatGHS } from "@/lib/utils";

export default function ShopProductPage() {
  const { slug } = useParams();
  const router = useRouter();
  const { addItem } = useCart();
  const toast = useToast();

  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [qty, setQty] = useState(1);
  const [error, setError] = useState("");
  const [selections, setSelections] = useState({});

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
        const data = await res.json();
        setProduct(data);
        
        // Auto-select first available variant
        if (data.product_type === "variable" && data.variants?.length > 0) {
          setSelections(data.variants[0].selections);
        }
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    })();
  }, [slug]);

  // Find the currently selected variant based on dropdown choices
  const activeVariant = useMemo(() => {
    if (!product || product.product_type !== "variable") return null;
    return product.variants.find(v => 
      Object.keys(selections).every(key => v.selections[key] === selections[key])
    );
  }, [product, selections]);

  const currentPrice = activeVariant ? activeVariant.price : product?.price;
  const isAvailable = product?.product_type === "variable" 
    ? (activeVariant?.is_available && activeVariant?.stock_count !== 0)
    : product?.is_available;

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-8 space-y-6">
        <SkeletonLine className="h-4 w-32" />
        <div className="grid md:grid-cols-2 gap-8">
          <SkeletonBlock className="h-96" />
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
            Product not found
          </h1>
          <p className="text-gray-400 text-sm mt-2">{error}</p>
          <Button href="/shop" variant="primary" className="mt-6">
            <ArrowLeft className="w-4 h-4" />
            Back to shop
          </Button>
        </div>
      </div>
    );
  }

  function handleAdd() {
    if (product.product_type === "variable" && !activeVariant) {
      toast.error("Please select all options");
      return;
    }
    
    addItem({
      cartId: `shop-${product.id}-${activeVariant?.sku || 'base'}`,
      product_id: product.id,
      variant_sku: activeVariant?.sku,
      variant_selections: activeVariant?.selections,
      vendor_id: product.vendor_id,
      vendor_name: product.vendor_name,
      vendor_category: "retail",
      name: product.name,
      unit_price: currentPrice,
      quantity: qty,
      image_url: activeVariant?.image_url || product.image_url,
    });
    toast.success(`${product.name} added`);
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <button
        onClick={() => router.back()}
        className="inline-flex items-center gap-2 text-sm font-bold text-gray-400 hover:text-brand-accent mb-6"
      >
        <ArrowLeft className="w-4 h-4" />
        Back
      </button>

      <div className="grid md:grid-cols-2 gap-8">
        <div className="rounded-3xl overflow-hidden bg-surface-card border border-surface-border aspect-square">
          {product.image_url ? (
            <img
              src={activeVariant?.image_url || product.image_url}
              alt={product.name}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-gray-600">
              <Store className="w-10 h-10" />
            </div>
          )}
        </div>

        <div className="space-y-5">
          {product.vendor_name && (
            <div className="inline-flex items-center gap-1.5 text-xs text-brand-accent font-bold uppercase tracking-wider">
              <Store className="w-3.5 h-3.5" />
              {product.vendor_name}
            </div>
          )}

          <h1 className="font-heading text-3xl sm:text-4xl font-black text-white">
            {product.name}
          </h1>

          {product.brand && (
            <div className="text-xs text-gray-500 uppercase tracking-wider font-bold">
              Brand: {product.brand}
            </div>
          )}

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

          <div className="text-3xl font-black text-brand-accent">
            {formatGHS(currentPrice)}
          </div>

          {/* Variant Selector */}
          {product.product_type === "variable" && product.variant_options?.length > 0 && (
            <div className="space-y-3 py-2 border-y border-surface-border">
              {product.variant_options.map(opt => (
                <div key={opt.name}>
                  <label className="block text-xs font-bold text-gray-300 mb-1.5 uppercase tracking-wider">{opt.name}</label>
                  <div className="flex gap-2 flex-wrap">
                    {opt.values.map(val => {
                      const isSelected = selections[opt.name] === val;
                      const testSel = { ...selections, [opt.name]: val };
                      const exists = product.variants.some(v => Object.keys(testSel).every(k => v.selections[k] === testSel[k]));
                      
                      return (
                        <button
                          key={val}
                          onClick={() => setSelections(testSel)}
                          disabled={!exists}
                          className={`px-4 py-2 rounded-xl text-sm font-bold border transition-colors ${
                            isSelected 
                              ? "bg-brand-accent border-brand-accent text-white" 
                              : exists
                                ? "bg-surface-dark border-surface-border text-gray-300 hover:border-brand-accent"
                                : "bg-surface-dark border-surface-border text-gray-600 opacity-50 cursor-not-allowed"
                          }`}
                        >
                          {val}
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Trust badges */}
          <div className="grid grid-cols-2 gap-3 py-2">
            <div className="flex items-center gap-2 text-xs text-gray-400">
              <Truck className="w-4 h-4 text-brand-accent" />
              Nationwide shipping
            </div>
            <div className="flex items-center gap-2 text-xs text-gray-400">
              <ShieldCheck className="w-4 h-4 text-brand-accent" />
              Verified seller
            </div>
          </div>

          {!isAvailable ? (
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
                variant="success"
                size="lg"
                onClick={handleAdd}
                className="w-full"
              >
                <Plus className="w-5 h-5" />
                Add {qty} — {formatGHS(currentPrice * qty)}
              </Button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}