"use client";

import { usePathname } from "next/navigation";
import Header from "./Header";
import Footer from "./Footer";
import CartDrawer from "./CartDrawer";
import CommandPalette from "./CommandPalette";

const HIDE_CHROME_ON = ["/vendor", "/admin", "/rider"];

export default function SiteShell({ children }) {
  const pathname = usePathname() || "";
  const hideChrome = HIDE_CHROME_ON.some((p) => pathname.startsWith(p));

  if (hideChrome) return children;

  return (
    <div className="min-h-screen bg-surface-dark text-gray-100 font-body flex flex-col">
      <Header />
      <main className="flex-1">{children}</main>
      <Footer />
      <CartDrawer />
      <CommandPalette />
    </div>
  );
}