"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import AdminSidebar from "@/components/admin/AdminSidebar";
import { getAdminToken } from "@/lib/adminAuth";

const PUBLIC_ADMIN_ROUTES = ["/admin/login"];

export default function AdminLayout({ children }) {
  const pathname = usePathname() || "";
  const router = useRouter();
  const [ready, setReady] = useState(false);

  const isPublic = PUBLIC_ADMIN_ROUTES.some((p) => pathname.startsWith(p));

  useEffect(() => {
    if (isPublic) {
      setReady(true);
      return;
    }
    if (!getAdminToken()) {
      router.replace("/admin/login");
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
      <AdminSidebar />
      <main className="flex-1 min-w-0 pb-16">
        <div className="max-w-6xl mx-auto px-4 lg:px-8 py-6">{children}</div>
      </main>
    </div>
  );
}