"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Search, Plus, X, ShoppingBag, Store } from "lucide-react";
import { API_URL } from "@/lib/api";
import { useCart } from "@/components/site/CartContext";
import { useToast } from "@/components/ui/Toast";
import Button from "@/components/ui/Button";
import { GridSkeleton } from "@/components/ui/Skeleton";
import EmptyState from "@/components/ui/EmptyState";
import { formatGHS } from "@/lib/utils";

export default function ShopPage() {
  const { addItem } = useCart();
  const toast = useToast();

  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [vendors, setVendors] = useState([]);
  const [activeCategory, setActiveCategory] = useState("all");
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const [pRes, cRes, vRes] = await Promise.all([
          fetch(`${API_URL}/api/v1/products?vendor_category=retail&limit=200`),
          fetch(`${API_URL}/api/v1/categories?active_only=true`),
          fetch(`${API_URL}/api/v1/vendors/public?category=retail&limit=100`),
        ]);
        const [p, c, v] = await Promise.all([
          pRes.json(),
          cRes.json(),
          vRes.json(),
        ]);
        setProducts(Array.isArray(p) ? p : []);
        setCategories(Array.isArray(c) ? c : []);
        setVendors(Array.isArray(v) ? v : []);
      } catch {
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
          p.description?.toLowerCase().includes(q) ||
          (p.tags || []).some((t) => t.toLowerCase().includes(q))
      );
    }
    return items;
  }, [products, categories, activeCategory, query]);

  function handleAdd(item) {
    addItem({
      cartId: `shop-${item.id}`,
      product_id: item.id,
      vendor_id: item.vendor_id,
      vendor_name: item.vendor_name,
      vendor_category: "retail",
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
        <div className="inline-flex items-center gap-1.5 text-brand-accent font-bold text-xs uppercase tracking-widest bg-brand-accent/10 px-3 py-1 rounded-full border border-brand-accent/20 mb-3">
          <ShoppingBag className="w-3.5 h-3.5" />
          Shop
        </div>
        <h1 className="font-heading text-4xl font-black text-white">
          Shop products
        </h1>
        <p className="text-gray-400 text-sm mt-1">
          {products.length} item{products.length === 1 ? "" : "s"} from{" "}
          {vendors.length} seller{vendors.length === 1 ? "" : "s"}
        </p>
      </div>

      {/* Search */}
      <div className="relative max-w-md mb-6">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search products, brands, categories…"
          className="w-full pl-9 pr-9 py-2.5 rounded-xl bg-surface-card border border-surface-border text-white text-sm focus:border-brand-accent focus:ring-2 focus:ring-brand-accent/40 outline-none"
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

      {/* Categories */}
      {!loading && categories.length > 0 && (
        <div className="flex gap-2 overflow-x-auto pb-2 mb-6 no-scrollbar">
          <button
            onClick={() => setActiveCategory("all")}
            className={`px-4 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition-colors ${
              activeCategory === "all"
                ? "bg-brand-accent text-white"
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
                    ? "bg-brand-accent text-white"
                    : "bg-surface-card border border-surface-border text-gray-300 hover:text-white"
                }`}
              >
                {c.name} ({count})
              </button>
            );
          })}
        </div>
      )}

      {/* Product grid */}
      {loading ? (
        <GridSkeleton count={8} />
      ) : visibleProducts.length === 0 ? (
        <EmptyState
          icon={ShoppingBag}
          title="No products found"
          message={query ? `Nothing matches "${query}"` : "No retail products listed yet."}
        />
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
          {visibleProducts.map((p) => (
            <ShopCard key={p.id} product={p} onAdd={() => handleAdd(p)} />
          ))}
        </div>
      )}
    </div>
  );
}

function ShopCard({ product, onAdd }) {
  return (
    <div className="bg-surface-card border border-surface-border rounded-2xl overflow-hidden flex flex-col hover:border-brand-accent/60 transition-colors">
      <Link
        href={`/shop/product/${product.slug}`}
        className="block relative aspect-square overflow-hidden bg-surface-dark"
      >
        {product.image_url ? (
          <img
            src={product.image_url}
            alt={product.name}
            className="w-full h-full object-cover"
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-600">
            <Store className="w-8 h-8" />
          </div>
        )}
      </Link>
      <div className="p-3 flex-1 flex flex-col">
        <Link href={`/shop/product/${product.slug}`}>
          <h3 className="font-bold text-white text-sm hover:text-brand-accent line-clamp-2 leading-snug">
            {product.name}
          </h3>
        </Link>
        {product.brand && (
          <div className="text-[10px] text-gray-500 mt-1 uppercase tracking-wider font-bold">
            {product.brand}
          </div>
        )}
        <div className="mt-auto pt-3 flex items-center justify-between gap-2">
          <div className="text-brand-accent font-bold text-sm">
            {formatGHS(product.price)}
          </div>
          <button
            onClick={onAdd}
            aria-label={`Add ${product.name} to cart`}
            className="w-8 h-8 rounded-lg bg-brand-accent hover:bg-brand-accentDark text-white flex items-center justify-center transition-colors"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}