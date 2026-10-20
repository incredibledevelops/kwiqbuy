"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import VendorSidebar from "@/components/vendor/VendorSidebar";
import { getVendorToken } from "@/lib/vendorAuth";

const PUBLIC_VENDOR_ROUTES = ["/vendor/login", "/vendor/apply"];

export default function VendorLayout({ children }) {
  const pathname = usePathname() || "";
  const router = useRouter();
  const [ready, setReady] = useState(false);

  const isPublic = PUBLIC_VENDOR_ROUTES.some((p) => pathname.startsWith(p));

  useEffect(() => {
    if (isPublic) {
      setReady(true);
      return;
    }
    const token = getVendorToken();
    if (!token) {
      router.replace("/vendor/login");
      return;
    }
    setReady(true);
  }, [isPublic, pathname, router]);

  if (!ready && !isPublic) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface-dark">
        <div className="text-gray-400 text-sm">Loading…</div>
      </div>
    );
  }

  if (isPublic) {
    return <div className="min-h-screen bg-surface-dark text-gray-100">{children}</div>;
  }

  return (
    <div className="min-h-screen bg-surface-dark text-gray-100 flex">
      <VendorSidebar />
      <main className="flex-1 min-w-0 pb-16">
        <div className="max-w-6xl mx-auto px-4 lg:px-8 py-6">{children}</div>
      </main>
    </div>
  );
}