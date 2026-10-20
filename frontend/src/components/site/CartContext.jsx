"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

const CartContext = createContext(null);
const STORAGE_KEY = "kb_cart";

function normalizeItem(item) {
  return {
    ...item,
    cartId: item.cartId || `${item.vendor_id || "v"}:${item.id}`,
    quantity: Math.max(1, Number(item.quantity) || 1),
    unit_price: Number(item.unit_price) || 0,
  };
}

export function CartProvider({ children }) {
  const [cart, setCart] = useState([]);
  const [ready, setReady] = useState(false);

  // Hydrate from localStorage once
  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed)) {
          setCart(parsed.map(normalizeItem));
        }
      }
    } catch {
      // ignore corrupt storage
    }
    setReady(true);
  }, []);

  // Persist
  useEffect(() => {
    if (!ready) return;
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(cart));
    } catch {
      // quota / private mode
    }
  }, [cart, ready]);

  const addItem = useCallback((item) => {
    const normalized = normalizeItem(item);
    setCart((prev) => {
      const existing = prev.find((i) => i.cartId === normalized.cartId);
      if (existing) {
        return prev.map((i) =>
          i.cartId === normalized.cartId
            ? { ...i, quantity: i.quantity + normalized.quantity }
            : i
        );
      }
      return [...prev, normalized];
    });
  }, []);

  const updateQuantity = useCallback((cartId, quantity) => {
    const q = Number(quantity);
    if (!Number.isFinite(q) || q <= 0) {
      setCart((prev) => prev.filter((i) => i.cartId !== cartId));
      return;
    }
    setCart((prev) =>
      prev.map((i) => (i.cartId === cartId ? { ...i, quantity: q } : i))
    );
  }, []);

  const removeItem = useCallback((cartId) => {
    setCart((prev) => prev.filter((i) => i.cartId !== cartId));
  }, []);

  const clear = useCallback(() => setCart([]), []);

  const subtotal = useMemo(
    () =>
      cart.reduce(
        (sum, i) => sum + Number(i.unit_price || 0) * (Number(i.quantity) || 0),
        0
      ),
    [cart]
  );

  const count = useMemo(
    () => cart.reduce((sum, i) => sum + (Number(i.quantity) || 0), 0),
    [cart]
  );

  const vendorIds = useMemo(() => {
    const s = new Set();
    for (const i of cart) if (i.vendor_id) s.add(i.vendor_id);
    return [...s];
  }, [cart]);

  const vendorCategories = useMemo(() => {
    const s = new Set();
    for (const i of cart) if (i.vendor_category) s.add(i.vendor_category);
    return [...s];
  }, [cart]);

  const value = useMemo(
    () => ({
      cart,
      addItem,
      updateQuantity,
      removeItem,
      clear,
      subtotal,
      count,
      vendorIds,
      vendorCategories,
      ready,
    }),
    [
      cart,
      addItem,
      updateQuantity,
      removeItem,
      clear,
      subtotal,
      count,
      vendorIds,
      vendorCategories,
      ready,
    ]
  );

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export function useCart() {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error("useCart must be used inside <CartProvider>");
  return ctx;
}