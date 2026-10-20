"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Search, Loader2, ArrowRight } from "lucide-react";
import { API_URL } from "@/lib/api";
import { formatGHS } from "@/lib/utils";

export default function CommandPalette() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const inputRef = useRef(null);
  const abortRef = useRef(null);

  // Cmd/Ctrl+K toggle
  useEffect(() => {
    function onKeyDown(e) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((v) => !v);
      }
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, []);

  // Reset on open/close
  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 50);
    } else {
      setQuery("");
      setResults([]);
      setActiveIndex(-1);
    }
  }, [open]);

  // Debounced search with abort
  useEffect(() => {
    if (query.trim().length < 2) {
      setResults([]);
      setLoading(false);
      return;
    }
    const t = setTimeout(async () => {
      abortRef.current?.abort?.();
      const controller = new AbortController();
      abortRef.current = controller;
      setLoading(true);
      try {
        const res = await fetch(
          `${API_URL}/api/v1/search?q=${encodeURIComponent(query)}&limit=6`,
          { signal: controller.signal }
        );
        if (res.ok) {
          const data = await res.json();
          setResults(Array.isArray(data.items) ? data.items : []);
        } else {
          setResults([]);
        }
      } catch (err) {
        if (err?.name !== "AbortError") setResults([]);
      } finally {
        setLoading(false);
      }
    }, 300);
    return () => clearTimeout(t);
  }, [query]);

  function goToItem(item) {
    if (!item) return;
    setOpen(false);
    const base = item.vendor_category === "retail" ? "/shop" : "/food";
    const slug = item.slug || item.id;
    router.push(`${base}/${slug}`);
  }

  function onInputKeyDown(e) {
    if (!results.length) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIndex((i) => (i + 1) % results.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIndex((i) => (i - 1 + results.length) % results.length);
    } else if (e.key === "Enter" && activeIndex >= 0) {
      e.preventDefault();
      goToItem(results[activeIndex]);
    }
  }

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-[100] flex items-start justify-center pt-[15vh] px-4"
      role="dialog"
      aria-modal="true"
      aria-label="Search"
    >
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={() => setOpen(false)}
      />

      <div className="relative w-full max-w-xl bg-surface-card border border-surface-border rounded-2xl shadow-2xl overflow-hidden animate-slide-down">
        <div className="flex items-center px-4 py-3 border-b border-surface-border">
          <Search className="w-5 h-5 text-gray-400 mr-3" />
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={onInputKeyDown}
            placeholder="Search products, restaurants..."
            className="flex-1 bg-transparent text-white outline-none text-lg placeholder:text-gray-500"
            aria-label="Search"
            autoComplete="off"
          />
          {loading && (
            <Loader2 className="w-4 h-4 text-brand-primary animate-spin" />
          )}
          <div className="hidden sm:block ml-3 px-2 py-1 bg-surface-dark border border-surface-border rounded text-[10px] text-gray-500 font-mono">
            ESC
          </div>
        </div>

        {query.length > 0 && (
          <div className="max-h-[60vh] overflow-y-auto p-2" role="listbox">
            {results.length === 0 && !loading && query.length >= 2 && (
              <div className="py-12 text-center text-sm text-gray-500">
                No results found for "{query}"
              </div>
            )}
            {results.map((item, idx) => (
              <button
                key={item.id}
                role="option"
                aria-selected={idx === activeIndex}
                onMouseEnter={() => setActiveIndex(idx)}
                onClick={() => goToItem(item)}
                className={`w-full text-left flex items-center gap-3 p-2 rounded-xl transition-colors ${
                  idx === activeIndex ? "bg-white/10" : "hover:bg-white/5"
                }`}
              >
                <div className="w-10 h-10 rounded-lg bg-surface-dark border border-surface-border overflow-hidden shrink-0">
                  {item.image_url ? (
                    <img
                      src={item.image_url}
                      alt=""
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <Search className="w-4 h-4 text-gray-600 m-auto mt-3" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-bold text-white truncate">
                    {item.name}
                  </div>
                  <div className="text-xs text-gray-500 truncate">
                    {item.vendor_name}
                  </div>
                </div>
                <div className="text-brand-primary font-bold text-sm">
                  {formatGHS(item.price)}
                </div>
                <ArrowRight className="w-4 h-4 text-gray-600" />
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}