"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  ShoppingBag,
  X,
  Minus,
  Plus,
  Trash2,
  ArrowRight,
} from "lucide-react";
import { useCart } from "./CartContext";
import { formatGHS } from "@/lib/utils";

export default function CartDrawer() {
  const { cart, updateQuantity, removeItem, subtotal, count, clear } = useCart();
  const [open, setOpen] = useState(false);
  const panelRef = useRef(null);
  const lastActiveRef = useRef(null);

  const openDrawer = useCallback(() => setOpen(true), []);
  const closeDrawer = useCallback(() => setOpen(false), []);

  // Expose global controls for Header
  useEffect(() => {
    if (typeof window === "undefined") return;
    window.__openCart = openDrawer;
    window.__closeCart = closeDrawer;
    return () => {
      delete window.__openCart;
      delete window.__closeCart;
    };
  }, [openDrawer, closeDrawer]);

  // Keyboard: ESC closes + focus management
  useEffect(() => {
    if (!open) return;
    lastActiveRef.current = document.activeElement;

    function onKey(e) {
      if (e.key === "Escape") {
        e.stopPropagation();
        setOpen(false);
        return;
      }
      if (e.key !== "Tab" || !panelRef.current) return;
      const focusables = panelRef.current.querySelectorAll(
        'a[href], button:not([disabled]), input:not([disabled]), [tabindex]:not([tabindex="-1"])'
      );
      if (!focusables.length) return;
      const first = focusables[0];
      const last = focusables[focusables.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }

    window.addEventListener("keydown", onKey);
    const t = setTimeout(() => {
      const first = panelRef.current?.querySelector(
        'button, a[href], input, [tabindex]:not([tabindex="-1"])'
      );
      first?.focus?.();
    }, 50);

    return () => {
      window.removeEventListener("keydown", onKey);
      clearTimeout(t);
      lastActiveRef.current?.focus?.();
    };
  }, [open]);

  // Lock scroll
  useEffect(() => {
    if (!open) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, [open]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50" role="dialog" aria-modal="true" aria-label="Shopping cart">
      <div
        onClick={() => setOpen(false)}
        className="absolute inset-0 bg-black/70 backdrop-blur-sm animate-fade-in"
      />
      <div
        ref={panelRef}
        className="absolute right-0 top-0 h-full w-full max-w-md bg-surface-dark border-l border-surface-border flex flex-col animate-slide-in"
      >
        <div className="p-5 border-b border-surface-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShoppingBag className="w-5 h-5 text-brand-primary" />
            <h2 className="font-heading text-lg font-bold text-white">
              Your cart
            </h2>
            {count > 0 && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-brand-primary/20 text-brand-primary font-bold">
                {count}
              </span>
            )}
          </div>
          <button
            onClick={() => setOpen(false)}
            aria-label="Close cart"
            className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          {cart.length === 0 ? (
            <div className="text-center py-16 px-6">
              <div className="w-20 h-20 rounded-full bg-surface-card border border-surface-border flex items-center justify-center mx-auto mb-4">
                <ShoppingBag className="w-8 h-8 text-gray-600" />
              </div>
              <h3 className="text-white font-bold mb-1">Your cart is empty</h3>
              <p className="text-gray-500 text-sm mb-6">
                Add items from a vendor to get started.
              </p>
              <Link
                href="/food"
                onClick={() => setOpen(false)}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-brand-primary hover:bg-brand-primaryDark text-white font-bold text-xs transition-colors"
              >
                Browse food
              </Link>
            </div>
          ) : (
            <ul className="p-5 space-y-3">
              {cart.map((item) => (
                <li
                  key={item.cartId}
                  className="p-3 rounded-2xl bg-surface-card border border-surface-border"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="font-bold text-sm text-white truncate">
                        {item.name}
                      </div>
                      {item.vendor_name && (
                        <div className="text-[10px] text-gray-500 mt-0.5">
                          {item.vendor_name}
                        </div>
                      )}
                      <div className="text-xs text-brand-primary font-bold mt-1">
                        {formatGHS((item.unit_price || 0) * (item.quantity || 0))}
                      </div>
                    </div>
                    <button
                      onClick={() => removeItem(item.cartId)}
                      aria-label={`Remove ${item.name} from cart`}
                      className="p-1.5 rounded-lg text-gray-500 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  <div className="inline-flex items-center gap-1 mt-3 bg-surface-dark px-1 py-1 rounded-xl border border-surface-border">
                    <button
                      onClick={() =>
                        updateQuantity(item.cartId, item.quantity - 1)
                      }
                      aria-label="Decrease quantity"
                      className="w-7 h-7 rounded-lg flex items-center justify-center text-gray-400 hover:text-white hover:bg-white/5 transition-colors"
                    >
                      <Minus className="w-3.5 h-3.5" />
                    </button>
                    <span
                      className="text-xs font-bold text-white w-6 text-center tabular-nums"
                      aria-live="polite"
                    >
                      {item.quantity}
                    </span>
                    <button
                      onClick={() =>
                        updateQuantity(item.cartId, item.quantity + 1)
                      }
                      aria-label="Increase quantity"
                      className="w-7 h-7 rounded-lg flex items-center justify-center text-gray-400 hover:text-white hover:bg-white/5 transition-colors"
                    >
                      <Plus className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </li>
              ))}
              <li>
                <button
                  onClick={clear}
                  className="text-xs text-red-400 hover:underline mt-2"
                >
                  Clear cart
                </button>
              </li>
            </ul>
          )}
        </div>

        {cart.length > 0 && (
          <div className="border-t border-surface-border bg-surface-card/40 p-5 space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Subtotal</span>
              <span className="text-white font-bold">{formatGHS(subtotal)}</span>
            </div>
            <Link
              href="/checkout"
              onClick={() => setOpen(false)}
              className="w-full py-3.5 rounded-2xl gradient-brand hover:opacity-90 text-white font-extrabold inline-flex items-center justify-center gap-2 transition-opacity"
            >
              Continue to checkout
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}