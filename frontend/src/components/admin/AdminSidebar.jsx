"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  LayoutDashboard,
  Store,
  FileCheck2,
  Wallet,
  History,
  Banknote,
  Star,
  AlertTriangle,
  Settings as SettingsIcon,
  ShieldCheck,
  BarChart3,
  LogOut,
  Menu as MenuIcon,
  X,
  Bike,
} from "lucide-react";
import { clearAdminSession, getAdminUser } from "@/lib/adminAuth";

const NAV = [
  { href: "/admin", label: "Overview", icon: LayoutDashboard },
  { href: "/admin/applications", label: "Applications", icon: FileCheck2 },
  { href: "/admin/vendors", label: "Vendors", icon: Store },
  { href: "/admin/riders", label: "Riders", icon: Bike },
  { href: "/admin/payouts", label: "Payouts", icon: Banknote },
  { href: "/admin/wallet", label: "Wallet", icon: Wallet },
  { href: "/admin/reviews", label: "Reviews", icon: Star },
  { href: "/admin/disputes", label: "Disputes", icon: AlertTriangle },
  { href: "/admin/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/admin/audit", label: "Audit log", icon: History },
  { href: "/admin/settings", label: "Settings", icon: SettingsIcon },
  { href: "/admin/2fa", label: "Security (2FA)", icon: ShieldCheck },
];

function NavList({ pathname, onNavigate, onLogout }) {
  return (
    <nav className="flex flex-col gap-1 p-3 overflow-y-auto h-full pb-20">
      {NAV.map((item) => {
        const active =
          item.href === "/admin"
            ? pathname === "/admin"
            : pathname === item.href || pathname.startsWith(item.href + "/");
        const Icon = item.icon;
        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={onNavigate}
            aria-current={active ? "page" : undefined}
            className={`inline-flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-bold transition-colors ${
              active
                ? "bg-brand-primary/15 text-brand-primary"
                : "text-gray-300 hover:text-white hover:bg-white/5"
            }`}
          >
            <Icon className="w-4 h-4 shrink-0" />
            {item.label}
          </Link>
        );
      })}
      <button
        onClick={onLogout}
        className="mt-2 inline-flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-bold text-red-400 hover:bg-red-500/10 transition-colors"
      >
        <LogOut className="w-4 h-4 shrink-0" />
        Sign out
      </button>
    </nav>
  );
}

export default function AdminSidebar() {
  const pathname = usePathname() || "";
  const router = useRouter();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [user, setUser] = useState(null);

  useEffect(() => {
    setUser(getAdminUser());
  }, []);

  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  function logout() {
    clearAdminSession();
    router.replace("/admin/login");
  }

  return (
    <>
      <aside className="hidden lg:flex flex-col w-64 shrink-0 border-r border-surface-border bg-surface-card/40">
        <div className="p-5 border-b border-surface-border">
          <Link href="/admin" className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl gradient-brand flex items-center justify-center text-white font-black">
              K
            </div>
            <div className="min-w-0">
              <div className="text-[10px] font-black uppercase tracking-wider text-brand-primary">
                Admin
              </div>
              <div className="font-heading font-bold text-white text-sm truncate max-w-[140px]">
                {user?.email || "Console"}
              </div>
            </div>
          </Link>
        </div>
        <NavList pathname={pathname} onLogout={logout} />
      </aside>

      <div className="lg:hidden sticky top-0 z-30 flex items-center justify-between px-4 py-3 border-b border-surface-border bg-surface-dark/95 backdrop-blur">
        <Link href="/admin" className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg gradient-brand flex items-center justify-center text-white font-black">
            K
          </div>
          <span className="font-bold text-white text-sm">Admin</span>
        </Link>
        <button
          onClick={() => setMobileOpen((v) => !v)}
          aria-label={mobileOpen ? "Close menu" : "Open menu"}
          aria-expanded={mobileOpen}
          className="p-2 rounded-lg bg-surface-card border border-surface-border text-white"
        >
          {mobileOpen ? <X className="w-5 h-5" /> : <MenuIcon className="w-5 h-5" />}
        </button>
      </div>

      {mobileOpen && (
        <div className="lg:hidden fixed inset-0 z-40">
          <div
            className="absolute inset-0 bg-black/60"
            onClick={() => setMobileOpen(false)}
          />
          <div className="absolute left-0 top-0 h-full w-64 bg-surface-dark border-r border-surface-border flex flex-col">
            <div className="p-4 border-b border-surface-border flex items-center justify-between">
              <span className="font-bold text-white">Menu</span>
              <button
                onClick={() => setMobileOpen(false)}
                aria-label="Close menu"
                className="p-1.5 rounded-lg text-gray-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <NavList
              pathname={pathname}
              onNavigate={() => setMobileOpen(false)}
              onLogout={logout}
            />
          </div>
        </div>
      )}
    </>
  );
}