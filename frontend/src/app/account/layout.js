"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import {
  User,
  MapPin,
  Heart,
  Wallet,
  Users,
  Package,
  LogOut,
  Loader2,
} from "lucide-react";
import { getCustomerToken, clearCustomerTokens } from "@/lib/customerAuth";

const NAV = [
  { href: "/account/orders", label: "Orders", icon: Package },
  { href: "/account/favorites", label: "Favorites", icon: Heart },
  { href: "/account/addresses", label: "Addresses", icon: MapPin },
  { href: "/account/wallet", label: "Wallet", icon: Wallet },
  { href: "/account/referrals", label: "Referrals", icon: Users },
  { href: "/account/profile", label: "Profile", icon: User },
];

export default function AccountLayout({ children }) {
  const pathname = usePathname() || "";
  const router = useRouter();
  const [ready, setReady] = useState(false);

  const isLoginPage = pathname === "/account";

  const ensureAuth = useCallback(() => {
    if (isLoginPage) {
      setReady(true);
      return;
    }
    if (!getCustomerToken()) {
      router.replace("/account");
      return;
    }
    setReady(true);
  }, [isLoginPage, router]);

  useEffect(() => {
    setReady(false);
    ensureAuth();
  }, [ensureAuth]);

  // Re-check auth when tab regains focus
  useEffect(() => {
    if (isLoginPage) return;
    function onFocus() {
      if (!getCustomerToken()) router.replace("/account");
    }
    window.addEventListener("focus", onFocus);
    return () => window.removeEventListener("focus", onFocus);
  }, [isLoginPage, router]);

  function logout() {
    clearCustomerTokens();
    router.replace("/account");
  }

  if (!ready && !isLoginPage) {
    return (
      <div className="py-20 text-center">
        <Loader2 className="w-8 h-8 text-brand-primary animate-spin mx-auto" />
      </div>
    );
  }

  if (isLoginPage) return children;

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 flex flex-col md:flex-row gap-8">
      <aside className="w-full md:w-56 shrink-0">
        <nav
          className="flex flex-row md:flex-col gap-1 overflow-x-auto pb-2 md:pb-0 no-scrollbar"
          aria-label="Account"
        >
          {NAV.map((item) => {
            const active =
              pathname === item.href || pathname.startsWith(item.href + "/");
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={`inline-flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-sm font-bold whitespace-nowrap transition-colors ${
                  active
                    ? "bg-brand-primary/15 text-brand-primary"
                    : "text-gray-400 hover:text-white hover:bg-white/5"
                }`}
              >
                <Icon className="w-4 h-4 shrink-0" />
                {item.label}
              </Link>
            );
          })}
          <button
            onClick={logout}
            className="inline-flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-sm font-bold text-red-400 hover:bg-red-500/10 transition-colors whitespace-nowrap"
          >
            <LogOut className="w-4 h-4 shrink-0" />
            Sign out
          </button>
        </nav>
      </aside>

      <main className="flex-1 min-w-0">{children}</main>
    </div>
  );
}