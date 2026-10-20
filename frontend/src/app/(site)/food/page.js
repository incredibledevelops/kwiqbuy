"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Search, Star, Plus, X, Utensils, MapPin } from "lucide-react";
import { API_URL } from "@/lib/api";
import { useCart } from "@/components/site/CartContext";
import { useToast } from "@/components/ui/Toast";
import Button from "@/components/ui/Button";
import { GridSkeleton } from "@/components/ui/Skeleton";
import EmptyState from "@/components/ui/EmptyState";
import { formatGHS } from "@/lib/utils";

export default function FoodPage() {
  const { addItem } = useCart();
  const toast = useToast();

  const [vendors, setVendors] = useState([]);
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [activeCategory, setActiveCategory] = useState("all");
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const [vRes, pRes, cRes] = await Promise.all([
          fetch(`${API_URL}/api/v1/vendors/public?category=food&limit=100`),
          fetch(`${API_URL}/api/v1/products?vendor_category=food&limit=200`),
          fetch(`${API_URL}/api/v1/categories?active_only=true`),
        ]);
        const [v, p, c] = await Promise.all([
          vRes.json(),
          pRes.json(),
          cRes.json(),
        ]);
        setVendors(Array.isArray(v) ? v : []);
        setProducts(Array.isArray(p) ? p : []);
        setCategories(Array.isArray(c) ? c : []);
      } catch {
        setVendors([]);
        setProducts([]);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const visibleProducts = useMemo(() => {
    let items = products;
    if (activeCategory !== "all") {
      const cat = categories.find((c) => c.slug === activeCategory);
      if (cat) items = items.filter((p) => p.category_id === cat.id);
    }
    const q = query.trim().toLowerCase();
    if (q) {
      items = items.filter(
        (p) =>
          p.name?.toLowerCase().includes(q) ||
          p.description?.toLowerCase().includes(q)
      );
    }
    return items;
  }, [products, categories, activeCategory, query]);

  function handleAdd(item) {
    addItem({
      cartId: `food-${item.id}`,
      product_id: item.id,
      vendor_id: item.vendor_id,
      vendor_name: item.vendor_name,
      vendor_category: "food",
      name: item.name,
      unit_price: item.price,
      quantity: 1,
      image_url: item.image_url,
    });
    toast.success(`${item.name} added to cart`);
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-6">
        <div className="inline-flex items-center gap-1.5 text-brand-primary font-bold text-xs uppercase tracking-widest bg-brand-primary/10 px-3 py-1 rounded-full border border-brand-primary/20 mb-3">
          <Utensils className="w-3.5 h-3.5" />
          Food
        </div>
        <h1 className="font-heading text-4xl font-black text-white">
          Order food
        </h1>
        <p className="text-gray-400 text-sm mt-1">
          Fresh meals from {vendors.length} food joint{vendors.length === 1 ? "" : "s"} near you
        </p>
      </div>

      {/* Search */}
      <div className="relative max-w-md mb-8">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search food…"
          className="w-full pl-9 pr-9 py-3 rounded-xl bg-surface-card border border-surface-border text-white text-sm focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/40 outline-none"
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

      {/* Food Joints Strip (Thin horizontal cards) */}
      {!loading && vendors.length > 0 && (
        <div className="mb-10">
          <h2 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">
            Food Joints
          </h2>
          <div className="flex gap-3 overflow-x-auto pb-4 no-scrollbar">
            {vendors.map((v) => (
              <Link
                key={v.id}
                href={`/food/${v.slug}`}
                className="shrink-0 w-64 p-3 rounded-2xl bg-surface-card border border-surface-border hover:border-brand-primary/60 transition-colors flex items-center gap-3 group"
              >
                <div className="w-12 h-12 rounded-xl bg-brand-primary/10 border border-brand-primary/20 flex items-center justify-center shrink-0 overflow-hidden">
                  {v.logo_url ? (
                    <img src={v.logo_url} alt="" className="w-full h-full object-cover" />
                  ) : (
                    <span className="font-heading text-lg font-black text-brand-primary">
                      {v.business_name.slice(0, 1)}
                    </span>
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="font-bold text-white text-sm truncate group-hover:text-brand-primary transition-colors">
                    {v.business_name}
                  </div>
                  <div className="text-[11px] text-gray-500 mt-0.5 flex items-center gap-2">
                    {v.prep_minutes && (
                      <span className="inline-flex items-center gap-1">
                        <MapPin className="w-3 h-3" />
                        ~{v.prep_minutes} min
                      </span>
                    )}
                    {v.average_rating > 0 && (
                      <span className="inline-flex items-center gap-1 text-brand-gold">
                        <Star className="w-3 h-3 fill-brand-gold" />
                        {v.average_rating.toFixed(1)}
                      </span>
                    )}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Categories */}
      {!loading && categories.length > 0 && (
        <div className="flex gap-2 overflow-x-auto pb-2 mb-6 no-scrollbar">
          <button
            onClick={() => setActiveCategory("all")}
            className={`px-4 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition-colors ${
              activeCategory === "all"
                ? "bg-brand-primary text-white"
                : "bg-surface-card border border-surface-border text-gray-300 hover:text-white"
            }`}
          >
            All ({products.length})
          </button>
          {categories.map((c) => {
            const count = products.filter((p) => p.category_id === c.id).length;
            if (count === 0) return null;
            return (
              <button
                key={c.id}
                onClick={() => setActiveCategory(c.slug)}
                className={`px-4 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition-colors ${
                  activeCategory === c.slug
                    ? "bg-brand-primary text-white"
                    : "bg-surface-card border border-surface-border text-gray-300 hover:text-white"
                }`}
              >
                {c.name} ({count})
              </button>
            );
          })}
        </div>
      )}

      {/* Products grid */}
      {loading ? (
        <GridSkeleton count={6} />
      ) : visibleProducts.length === 0 ? (
        <EmptyState
          icon={Utensils}
          title="No food items found"
          message={query ? `Nothing matches "${query}"` : "No food listed yet."}
        />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {visibleProducts.map((p) => (
            <FoodCard key={p.id} product={p} onAdd={() => handleAdd(p)} />
          ))}
        </div>
      )}
    </div>
  );
}

function FoodCard({ product, onAdd }) {
  return (
    <div className="bg-surface-card border border-surface-border rounded-2xl overflow-hidden flex flex-col hover:border-brand-primary/60 transition-colors group">
      <Link
        href={`/food/product/${product.slug}`}
        className="block relative h-44 overflow-hidden bg-surface-dark"
      >
        {product.image_url ? (
          <img
            src={product.image_url}
            alt={product.name}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-600">
            <Utensils className="w-8 h-8" />
          </div>
        )}
        <div className="absolute top-2 right-2 bg-surface-dark/90 backdrop-blur px-2.5 py-1 rounded-lg text-brand-primary font-extrabold text-sm border border-surface-border">
          {formatGHS(product.price)}
        </div>
      </Link>
      <div className="p-4 flex-1 flex flex-col">
        <Link href={`/food/product/${product.slug}`}>
          <h3 className="font-heading font-bold text-white hover:text-brand-primary line-clamp-2">
            {product.name}
          </h3>
        </Link>
        {product.vendor_name && (
          <div className="text-[10px] text-gray-500 mt-1 uppercase tracking-wider font-bold">
            {product.vendor_name}
          </div>
        )}
        <p className="text-xs text-gray-400 mt-2 line-clamp-2 flex-1">
          {product.description}
        </p>
        <Button variant="primary" size="md" onClick={onAdd} className="mt-4 w-full">
          <Plus className="w-4 h-4" />
          Add to cart
        </Button>
      </div>
    </div>
  );
}