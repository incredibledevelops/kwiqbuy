"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Store, MapPin, Star, Utensils, ShoppingBag, ArrowRight } from "lucide-react";
import { API_URL } from "@/lib/api";
import { GridSkeleton } from "@/components/ui/Skeleton";
import EmptyState from "@/components/ui/EmptyState";

export default function VendorsPage() {
  const [vendors, setVendors] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`${API_URL}/api/v1/vendors/public?limit=100`);
        const data = await res.json();
        setVendors(Array.isArray(data) ? data : []);
      } catch {
        setVendors([]);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header Section */}
      <div className="mb-8">
        <h1 className="font-heading text-4xl font-black text-white">
          Vendors
        </h1>
        <p className="text-gray-400 text-sm mt-1">
          Every business selling on KwiqBuy
        </p>
      </div>

      {/* Vendor Grid */}
      {loading ? (
        <GridSkeleton count={6} />
      ) : vendors.length === 0 ? (
        <EmptyState icon={Store} title="No vendors yet" />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {vendors.map((v) => {
            const isFood = v.business_category === "food";
            const themeColor = isFood ? "text-brand-primary" : "text-brand-accent";
            const themeBg = isFood ? "bg-brand-primary/10" : "bg-brand-accent/10";
            const themeBorder = isFood ? "border-brand-primary/30" : "border-brand-accent/30";
            const hoverBorder = isFood ? "hover:border-brand-primary/60" : "hover:border-brand-accent/60";
            const buttonBg = isFood ? "gradient-brand text-white" : "bg-brand-accent hover:bg-brand-accentDark text-white";
            const ThemeIcon = isFood ? Utensils : ShoppingBag;
            
            // Route correctly based on category
            const href = isFood ? `/food/${v.slug}` : `/shop/${v.slug}`;

            return (
              <Link
                key={v.id}
                href={href}
                className={`group flex flex-col bg-surface-card border border-surface-border rounded-2xl p-5 ${hoverBorder} transition-all`}
              >
                <div className="flex items-start gap-3">
                  <div className={`w-14 h-14 rounded-xl ${themeBg} border ${themeBorder} flex items-center justify-center shrink-0 overflow-hidden`}>
                    {v.logo_url ? (
                      <img src={v.logo_url} alt="" className="w-full h-full object-cover" />
                    ) : (
                      <ThemeIcon className={`w-6 h-6 ${themeColor}`} />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-bold text-white text-lg truncate group-hover:text-white">
                      {v.business_name}
                    </div>
                    <div className="flex items-center gap-1.5 mt-1">
                      <span className={`text-[9px] uppercase tracking-wider font-bold ${themeColor} ${themeBg} px-2 py-0.5 rounded-md border ${themeBorder}`}>
                        {v.business_category}
                      </span>
                      {v.business_subtype && (
                        <span className="text-[10px] text-gray-500 uppercase tracking-wider font-bold">
                          · {v.business_subtype}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                
                {v.description && (
                  <p className="text-xs text-gray-400 mt-4 line-clamp-2 flex-1">
                    {v.description}
                  </p>
                )}
                
                <div className="flex items-center justify-between mt-5 pt-4 border-t border-surface-border">
                  <div className="flex items-center gap-3 text-[11px] text-gray-500">
                    {v.average_rating > 0 && (
                      <span className="inline-flex items-center gap-1">
                        <Star className="w-3 h-3 text-brand-gold fill-brand-gold" />
                        {v.average_rating.toFixed(1)} ({v.total_reviews})
                      </span>
                    )}
                    {v.prep_minutes && (
                      <span className="inline-flex items-center gap-1">
                        <MapPin className="w-3 h-3" />
                        ~{v.prep_minutes} min
                      </span>
                    )}
                  </div>
                  <div className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-bold transition-transform group-hover:translate-x-0.5 ${buttonBg}`}>
                    Visit
                    <ArrowRight className="w-3 h-3" />
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}