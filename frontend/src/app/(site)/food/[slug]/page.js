"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, MapPin, Star, Plus, Utensils } from "lucide-react";
import { API_URL } from "@/lib/api";
import { useCart } from "@/components/site/CartContext";
import { useToast } from "@/components/ui/Toast";
import Button from "@/components/ui/Button";
import { GridSkeleton, SkeletonLine } from "@/components/ui/Skeleton";
import EmptyState from "@/components/ui/EmptyState";
import { formatGHS } from "@/lib/utils";

export default function FoodVendorPage() {
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
      cartId: `food-${product.id}`,
      product_id: product.id,
      vendor_id: product.vendor_id,
      vendor_name: vendor?.business_name,
      vendor_category: "food",
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
        <GridSkeleton count={6} />
      </div>
    );
  }

  if (error || !vendor) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center p-4">
        <EmptyState
          icon={Utensils}
          title="Restaurant not found"
          message={error}
          action={
            <Button href="/food" variant="primary">
              <ArrowLeft className="w-4 h-4" />
              All food
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <Link
        href="/food"
        className="inline-flex items-center gap-2 text-sm font-bold text-gray-400 hover:text-brand-primary mb-6"
      >
        <ArrowLeft className="w-4 h-4" />
        All food
      </Link>

      <div className="rounded-3xl bg-surface-card border border-surface-border p-6 mb-8">
        <div className="flex items-start gap-4">
          <div className="w-16 h-16 rounded-2xl bg-brand-primary/10 border border-brand-primary/20 flex items-center justify-center overflow-hidden shrink-0">
            {vendor.logo_url ? (
              <img src={vendor.logo_url} alt="" className="w-full h-full object-cover" />
            ) : (
              <span className="font-heading text-2xl font-black text-brand-primary">
                {vendor.business_name.slice(0, 1)}
              </span>
            )}
          </div>
          <div className="flex-1 min-w-0">
            <div className="inline-flex items-center gap-1.5 text-brand-primary font-bold text-[10px] uppercase tracking-widest bg-brand-primary/10 px-2 py-0.5 rounded-full border border-brand-primary/20 mb-1">
              <Utensils className="w-2.5 h-2.5" />
              Restaurant
            </div>
            <h1 className="font-heading text-2xl sm:text-3xl font-black text-white">
              {vendor.business_name}
            </h1>
            {vendor.description && (
              <p className="text-sm text-gray-400 mt-2 leading-relaxed">
                {vendor.description}
              </p>
            )}
            <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
              {vendor.average_rating > 0 && (
                <span className="inline-flex items-center gap-1">
                  <Star className="w-3.5 h-3.5 text-brand-gold fill-brand-gold" />
                  {vendor.average_rating.toFixed(1)} ({vendor.total_reviews})
                </span>
              )}
              {vendor.prep_minutes && (
                <span className="inline-flex items-center gap-1">
                  <MapPin className="w-3.5 h-3.5" />
                  ~{vendor.prep_minutes} min
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {products.length === 0 ? (
        <EmptyState icon={Utensils} title="Menu coming soon" />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {products.map((p) => (
            <div
              key={p.id}
              className="bg-surface-card border border-surface-border rounded-2xl overflow-hidden flex flex-col"
            >
              <Link
                href={`/food/product/${p.slug}`}
                className="block h-44 overflow-hidden bg-surface-dark"
              >
                {p.image_url ? (
                  <img src={p.image_url} alt={p.name} className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-gray-600">
                    <Utensils className="w-8 h-8" />
                  </div>
                )}
              </Link>
              <div className="p-4 flex-1 flex flex-col">
                <Link href={`/food/product/${p.slug}`}>
                  <h3 className="font-bold text-white hover:text-brand-primary line-clamp-2">
                    {p.name}
                  </h3>
                </Link>
                <p className="text-xs text-gray-400 mt-2 line-clamp-2 flex-1">
                  {p.description}
                </p>
                <div className="text-brand-primary font-bold mt-3">
                  {formatGHS(p.price)}
                </div>
                <Button
                  variant="primary"
                  size="md"
                  onClick={() => handleAdd(p)}
                  className="mt-3 w-full"
                >
                  <Plus className="w-4 h-4" />
                  Add to cart
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}