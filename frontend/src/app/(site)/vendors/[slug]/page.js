"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, MapPin, Star, Plus, Utensils, Store } from "lucide-react";
import { API_URL } from "@/lib/api";
import { useCart } from "@/components/site/CartContext";
import { useToast } from "@/components/ui/Toast";
import Button from "@/components/ui/Button";
import { GridSkeleton, SkeletonLine } from "@/components/ui/Skeleton";
import EmptyState from "@/components/ui/EmptyState";
import { formatGHS } from "@/lib/utils";

export default function VendorStorefrontPage() {
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
        
        const pRes = await fetch(`${API_URL}/api/v1/products?vendor_id=${v.id}&limit=200`);
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
      cartId: `vendor-${product.id}`,
      product_id: product.id,
      vendor_id: product.vendor_id,
      vendor_name: vendor?.business_name,
      vendor_category: vendor?.business_category,
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
          title="Vendor not found"
          message={error}
          action={
            <Button href="/vendors" variant="primary">
              <ArrowLeft className="w-4 h-4" />
              All vendors
            </Button>
          }
        />
      </div>
    );
  }

  const isFood = vendor.business_category === "food";
  const themeColor = isFood ? "text-brand-primary" : "text-brand-accent";
  const themeBorder = isFood ? "border-brand-primary/30" : "border-brand-accent/30";
  const themeBg = isFood ? "bg-brand-primary/10" : "bg-brand-accent/10";
  const ThemeIcon = isFood ? Utensils : Store;

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <Link
        href={isFood ? "/food" : "/shop"}
        className={`inline-flex items-center gap-2 text-sm font-bold text-gray-400 hover:${themeColor} mb-6`}
      >
        <ArrowLeft className="w-4 h-4" />
        Back to {isFood ? "food" : "shop"}
      </Link>

      <div className={`rounded-3xl bg-surface-card border ${themeBorder} p-6 mb-8`}>
        <div className="flex items-start gap-4">
          <div className={`w-16 h-16 rounded-2xl ${themeBg} border ${themeBorder} flex items-center justify-center overflow-hidden shrink-0`}>
            {vendor.logo_url ? (
              <img src={vendor.logo_url} alt="" className="w-full h-full object-cover" />
            ) : (
              <span className={`font-heading text-2xl font-black ${themeColor}`}>
                {vendor.business_name.slice(0, 1)}
              </span>
            )}
          </div>
          <div className="flex-1 min-w-0">
            <div className={`inline-flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-widest ${themeColor} ${themeBg} px-2 py-0.5 rounded-full border ${themeBorder} mb-1`}>
              <ThemeIcon className="w-2.5 h-2.5" />
              {vendor.business_category}
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
        <EmptyState icon={ThemeIcon} title="No products listed" />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {products.map((p) => {
            const productRoute = isFood ? `/food/product/${p.slug}` : `/shop/product/${p.slug}`;
            return (
              <div
                key={p.id}
                className={`bg-surface-card border border-surface-border rounded-2xl overflow-hidden flex flex-col hover:${themeBorder} transition-colors`}
              >
                <Link href={productRoute} className="block h-44 overflow-hidden bg-surface-dark">
                  {p.image_url ? (
                    <img src={p.image_url} alt={p.name} className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-gray-600">
                      <ThemeIcon className="w-8 h-8" />
                    </div>
                  )}
                </Link>
                <div className="p-4 flex-1 flex flex-col">
                  <Link href={productRoute}>
                    <h3 className={`font-bold text-white hover:${themeColor} line-clamp-2`}>
                      {p.name}
                    </h3>
                  </Link>
                  <p className="text-xs text-gray-400 mt-2 line-clamp-2 flex-1">
                    {p.description}
                  </p>
                  <div className={`${themeColor} font-bold mt-3`}>
                    {formatGHS(p.price)}
                  </div>
                  <Button
                    variant={isFood ? "primary" : "success"}
                    size="md"
                    onClick={() => handleAdd(p)}
                    className="mt-3 w-full"
                  >
                    <Plus className="w-4 h-4" />
                    Add to cart
                  </Button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}