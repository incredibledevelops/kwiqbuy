"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import {
  ShoppingBag,
  User,
  Menu as MenuIcon,
  X,
  Utensils,
  Store,
} from "lucide-react";
import { useCart } from "./CartContext";
import { getCustomerToken } from "@/lib/customerAuth";
import { formatGHS } from "@/lib/utils";

const NAV = [
  { href: "/food", label: "Food", icon: Utensils },
  { href: "/shop", label: "Shop", icon: Store },
  { href: "/vendors", label: "Vendors" },
  { href: "/about", label: "About" },
  { href: "/contact", label: "Contact" },
];

export default function Header() {
  const pathname = usePathname() || "";
  const { count, subtotal } = useCart();
  const [loggedIn, setLoggedIn] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    setLoggedIn(!!getCustomerToken());
  }, [pathname]);

  useEffect(() => {
    function onStorage(e) {
      if (!e.key || !e.key.startsWith("kb_customer")) return;
      setLoggedIn(!!getCustomerToken());
    }
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  function openCart() {
    if (typeof window !== "undefined" && typeof window.__openCart === "function") {
      window.__openCart();
    }
  }

  return (
    <header className="sticky top-0 z-40 bg-surface-dark/95 backdrop-blur-md border-b border-surface-border">
      <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between gap-4">
        <Link href="/" className="flex items-center gap-2.5 shrink-0">
          <div className="w-9 h-9 rounded-xl gradient-brand flex items-center justify-center text-white font-black text-lg">
            K
          </div>
          <span className="font-heading text-lg font-black text-white hidden sm:inline">
            KwiqBuy
          </span>
        </Link>

        <nav className="hidden lg:flex items-center gap-1 text-sm" aria-label="Primary">
          {NAV.map((item) => {
            const active =
              pathname === item.href ||
              (item.href !== "/" && pathname.startsWith(item.href + "/"));
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`inline-flex items-center gap-1.5 px-3 py-2 rounded-lg transition-colors ${
                  active
                    ? "text-brand-primary font-bold bg-brand-primary/10"
                    : "text-gray-300 hover:text-white hover:bg-white/5"
                }`}
              >
                {Icon && <Icon className="w-4 h-4" />}
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="flex items-center gap-2">
          <Link
            href="/account"
            className="hidden sm:inline-flex items-center gap-2 px-3 py-2 rounded-xl bg-surface-card border border-surface-border text-xs font-bold text-white hover:border-brand-primary transition-colors"
          >
            <User className="w-4 h-4" />
            <span>{loggedIn ? "Account" : "Sign in"}</span>
          </Link>

          <button
            onClick={openCart}
            aria-label={`Open cart${count > 0 ? ` (${count} items)` : ""}`}
            className="relative inline-flex items-center gap-2 px-3 py-2 rounded-xl bg-surface-card border border-surface-border text-brand-primary hover:border-brand-primary transition-colors"
          >
            <ShoppingBag className="w-5 h-5" />
            {count > 0 && (
              <>
                <span className="absolute -top-1 -right-1 bg-brand-danger text-white text-[10px] font-bold rounded-full min-w-[20px] h-5 px-1 flex items-center justify-center border-2 border-surface-dark">
                  {count}
                </span>
                <span className="hidden sm:inline font-bold text-sm text-white">
                  {formatGHS(subtotal)}
                </span>
              </>
            )}
          </button>

          <button
            onClick={() => setMobileOpen((v) => !v)}
            aria-label={mobileOpen ? "Close menu" : "Open menu"}
            aria-expanded={mobileOpen}
            className="lg:hidden p-2.5 rounded-xl bg-surface-card border border-surface-border text-white"
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <MenuIcon className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {mobileOpen && (
        <div className="lg:hidden border-t border-surface-border bg-surface-card/50 animate-slide-down">
          <nav className="max-w-7xl mx-auto px-4 py-3 flex flex-col gap-1" aria-label="Mobile">
            {NAV.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className="px-4 py-3 rounded-xl text-sm font-bold text-gray-300 hover:bg-white/5 hover:text-white inline-flex items-center gap-2"
                >
                  {Icon && <Icon className="w-4 h-4" />}
                  {item.label}
                </Link>
              );
            })}
            <Link
              href="/account"
              className="mt-1 px-4 py-3 rounded-xl bg-surface-card border border-surface-border text-sm font-bold text-white hover:border-brand-primary transition-colors inline-flex items-center gap-2"
            >
              <User className="w-4 h-4" />
              {loggedIn ? "My account" : "Sign in"}
            </Link>
          </nav>
        </div>
      )}
    </header>
  );
}