"use client";

import { CartProvider } from "@/components/site/CartContext";
import { ToastProvider } from "@/components/ui/Toast";

export default function Providers({ children }) {
  return (
    <ToastProvider>
      <CartProvider>{children}</CartProvider>
    </ToastProvider>
  );
}