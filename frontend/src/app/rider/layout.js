"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import RiderSidebar from "@/components/rider/RiderSidebar";

export default function RiderLayout({ children }) {
  const pathname = usePathname() || "";
  const router = useRouter();
  const [ready, setReady] = useState(false);

  const isPublic = pathname.startsWith("/rider/login");

  useEffect(() => {
    if (isPublic) {
      setReady(true);
      return;
    }
    const token = localStorage.getItem("kb_rider_token");
    if (!token) {
      router.replace("/rider/login");
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
      <RiderSidebar />
      <main className="flex-1 min-w-0 pb-16">
        <div className="max-w-4xl mx-auto px-4 lg:px-8 py-6">{children}</div>
      </main>
    </div>
  );
}