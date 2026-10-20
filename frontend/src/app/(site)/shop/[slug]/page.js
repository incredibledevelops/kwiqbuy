"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Plus, Store, Star } from "lucide-react";
import { API_URL } from "@/lib/api";
import { useCart } from "@/components/site/CartContext";
import { useToast } from "@/components/ui/Toast";
import Button from "@/components/ui/Button";
import { GridSkeleton, SkeletonLine } from "@/components/ui/Skeleton";
import EmptyState from "@/components/ui/EmptyState";
import { formatGHS } from "@/lib/utils";

export default function ShopVendorPage() {
  const { slug } = useParams();
  const { addItem } = useCart();
  const toast = useToast();

  const [vendor, setVendor] = useState(null);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!slug) return;
    (async () => {
      setLoading(true);
      try {
        const vRes = await fetch(`${API_URL}/api/v1/vendors/public/${slug}`);
        if (!vRes.ok) {
          setError("Vendor not found");
          return;
        }
        const v = await vRes.json();
        setVendor(v);
        const pRes = await fetch(
          `${API_URL}/api/v1/products?vendor_id=${v.id}&limit=200`
        );
        const p = await pRes.json();
        setProducts(Array.isArray(p) ? p : []);
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    })();
  }, [slug]);

  function handleAdd(product) {
    addItem({
      cartId: `shop-${product.id}`,
      product_id: product.id,
      vendor_id: product.vendor_id,
      vendor_name: vendor?.business_name,
      vendor_category: "retail",
      name: product.name,
      unit_price: product.price,
      quantity: 1,
      image_url: product.image_url,
    });
    toast.success(`${product.name} added`);
  }

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
        <SkeletonLine className="h-4 w-32" />
        <SkeletonLine className="h-10 w-64" />
        <GridSkeleton count={8} />
      </div>
    );
  }

  if (error || !vendor) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center p-4">
        <EmptyState
          icon={Store}
          title="Vendor not found"
          message={error}
          action={
            <Button href="/shop" variant="primary">
              <ArrowLeft className="w-4 h-4" />
              All shops
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <Link
        href="/shop"
        className="inline-flex items-center gap-2 text-sm font-bold text-gray-400 hover:text-brand-accent mb-6"
      >
        <ArrowLeft className="w-4 h-4" />
        All shops
      </Link>

      <div className="rounded-3xl bg-surface-card border border-surface-border p-6 mb-8">
        <div className="flex items-start gap-4">
          <div className="w-16 h-16 rounded-2xl bg-brand-accent/10 border border-brand-accent/20 flex items-center justify-center overflow-hidden shrink-0">
            {vendor.logo_url ? (
              <img src={vendor.logo_url} alt="" className="w-full h-full object-cover" />
            ) : (
              <span className="font-heading text-2xl font-black text-brand-accent">
                {vendor.business_name.slice(0, 1)}
              </span>
            )}
          </div>
          <div className="flex-1 min-w-0">
            <div className="inline-flex items-center gap-1.5 text-brand-accent font-bold text-[10px] uppercase tracking-widest bg-brand-accent/10 px-2 py-0.5 rounded-full border border-brand-accent/20 mb-1">
              <Store className="w-2.5 h-2.5" />
              Seller
            </div>
            <h1 className="font-heading text-2xl sm:text-3xl font-black text-white">
              {vendor.business_name}
            </h1>
            {vendor.description && (
              <p className="text-sm text-gray-400 mt-2 leading-relaxed">
                {vendor.description}
              </p>
            )}
            {vendor.average_rating > 0 && (
              <div className="inline-flex items-center gap-1 mt-3 text-xs text-gray-500">
                <Star className="w-3.5 h-3.5 text-brand-gold fill-brand-gold" />
                {vendor.average_rating.toFixed(1)} ({vendor.total_reviews})
              </div>
            )}
          </div>
        </div>
      </div>

      {products.length === 0 ? (
        <EmptyState icon={Store} title="No products listed" />
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
          {products.map((p) => (
            <div
              key={p.id}
              className="bg-surface-card border border-surface-border rounded-2xl overflow-hidden flex flex-col hover:border-brand-accent/60 transition-colors"
            >
              <Link
                href={`/shop/product/${p.slug}`}
                className="block aspect-square overflow-hidden bg-surface-dark"
              >
                {p.image_url ? (
                  <img src={p.image_url} alt={p.name} className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-gray-600">
                    <Store className="w-8 h-8" />
                  </div>
                )}
              </Link>
              <div className="p-3 flex-1 flex flex-col">
                <Link href={`/shop/product/${p.slug}`}>
                  <h3 className="font-bold text-white text-sm hover:text-brand-accent line-clamp-2 leading-snug">
                    {p.name}
                  </h3>
                </Link>
                <div className="mt-auto pt-3 flex items-center justify-between gap-2">
                  <div className="text-brand-accent font-bold text-sm">
                    {formatGHS(p.price)}
                  </div>
                  <button
                    onClick={() => handleAdd(p)}
                    className="w-8 h-8 rounded-lg bg-brand-accent hover:bg-brand-accentDark text-white flex items-center justify-center transition-colors"
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}