"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Tag,
  Award,
  Wallet,
  Loader2,
  AlertCircle,
  ArrowLeft,
  Lock,
  Sparkles,
} from "lucide-react";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import { useToast } from "@/components/ui/Toast";
import { useCart } from "@/components/site/CartContext";
import { API_URL, randomKey } from "@/lib/api";
import { getCustomerToken, customerFetch } from "@/lib/customerAuth";
import { formatGHS } from "@/lib/utils";

const FREE_DELIVERY_THRESHOLD = 100;

export default function CheckoutPage() {
  const router = useRouter();
  const toast = useToast();
  const { cart, subtotal, vendorIds, vendorCategories, clear } = useCart();

  const [zones, setZones] = useState([]);
  const [customer, setCustomer] = useState({ full_name: "", email: "", phone: "" });
  const [zoneId, setZoneId] = useState("");
  const [address, setAddress] = useState("");
  const [notes, setNotes] = useState("");

  const [promoInput, setPromoInput] = useState("");
  const [promoApplied, setPromoApplied] = useState(null);
  const [promoError, setPromoError] = useState("");
  const [promoLoading, setPromoLoading] = useState(false);

  const [loyalty, setLoyalty] = useState(null);
  const [redeemPoints, setRedeemPoints] = useState(0);

  const [wallet, setWallet] = useState(null);
  const [useWallet, setUseWallet] = useState(false);

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [stage, setStage] = useState("form");

  const idemKeyRef = useMemo(() => randomKey(), []);

  useEffect(() => {
    (async () => {
      try {
        const zRes = await fetch(`${API_URL}/api/v1/delivery-zones?active_only=true`);
        const zData = await zRes.json();
        const list = Array.isArray(zData) ? zData : [];
        setZones(list);
        if (list[0]) setZoneId(list[0].id);

        const token = getCustomerToken();
        if (token) {
          const [meRes, walletRes] = await Promise.all([
            customerFetch(`${API_URL}/api/v1/customer-account/me`),
            customerFetch(`${API_URL}/api/v1/wallet/me`),
          ]);
          if (meRes.ok) {
            const me = await meRes.json();
            setCustomer({
              full_name: me.full_name || "",
              email: me.email || "",
              phone: me.phone || "",
            });
          }
          if (walletRes.ok) setWallet(await walletRes.json());
        }
      } catch {
        setError("Couldn't load checkout data. Is the backend running?");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  useEffect(() => {
    const phone = (customer.phone || "").trim();
    if (phone.length < 9) {
      setLoyalty(null);
      return;
    }
    const t = setTimeout(async () => {
      try {
        const res = await fetch(`${API_URL}/api/v1/loyalty/balance/${phone}`);
        if (res.ok) setLoyalty(await res.json());
      } catch {}
    }, 500);
    return () => clearTimeout(t);
  }, [customer.phone]);

  const selectedZone = useMemo(
    () => zones.find((z) => z.id === zoneId),
    [zones, zoneId]
  );
  const zoneFee = selectedZone?.delivery_fee ?? 15;

  const cartOrderType = useMemo(() => {
    if (vendorCategories.length === 0) return "food";
    if (vendorCategories.length === 1) return vendorCategories[0];
    return "mixed";
  }, [vendorCategories]);

  const freeDeliveryReached =
    cartOrderType !== "retail" && subtotal >= FREE_DELIVERY_THRESHOLD;

  const deliveryFee =
    cartOrderType === "retail" ? 0 : freeDeliveryReached ? 0 : zoneFee;

  const promoDiscount = promoApplied?.discount_amount || 0;
  const loyaltyRate = typeof loyalty?.points_to_cash_rate === "number" ? loyalty.points_to_cash_rate : 0.01;
  const loyaltyDiscount = useMemo(() => {
    if (!redeemPoints) return 0;
    return Math.min(redeemPoints * loyaltyRate, subtotal + deliveryFee);
  }, [redeemPoints, loyaltyRate, subtotal, deliveryFee]);

  const totalBeforeWallet = Math.max(
    subtotal + deliveryFee - promoDiscount - loyaltyDiscount,
    0
  );

  const walletApplied = useMemo(() => {
    if (!useWallet || !wallet || wallet.balance <= 0) return 0;
    return Math.min(wallet.balance, totalBeforeWallet);
  }, [useWallet, wallet, totalBeforeWallet]);

  const total = Math.max(totalBeforeWallet - walletApplied, 0);

  async function applyPromo() {
    if (!promoInput.trim()) return;
    setPromoLoading(true);
    setPromoError("");
    try {
      const res = await fetch(`${API_URL}/api/v1/promo-codes/validate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          code: promoInput.trim(),
          phone: customer.phone || null,
          subtotal,
          vendor_ids: vendorIds,
        }),
      });
      const data = await res.json();
      if (data.valid) {
        setPromoApplied({
          code: data.code,
          discount_amount: data.discount_amount,
          message: data.message,
        });
        setPromoInput("");
        toast.success(data.message);
      } else {
        setPromoApplied(null);
        setPromoError(data.message || "Invalid code");
      }
    } catch (e) {
      setPromoError(e.message);
    } finally {
      setPromoLoading(false);
    }
  }

  async function submitOrder(e) {
    e?.preventDefault?.();

    if (cart.length === 0) {
      toast.error("Your cart is empty");
      return;
    }
    if (!zoneId) {
      toast.error("Please select a delivery zone");
      return;
    }
    if (!address.trim() || address.trim().length < 4) {
      toast.error("Please enter a delivery address");
      return;
    }
    if (!customer.email.includes("@")) {
      toast.error("Please enter a valid email");
      return;
    }
    if (!customer.full_name.trim()) {
      toast.error("Please enter your full name");
      return;
    }
    if (!customer.phone.trim() || customer.phone.trim().length < 9) {
      toast.error("Please enter a valid phone number");
      return;
    }

    const missingProduct = cart.find(item => !item.product_id);
    if (missingProduct) {
      toast.error(`Something went wrong. Please refresh and try again.`);
      return;
    }

    setSubmitting(true);
    setError("");
    setStage("form");

    let order = null;

    try {
      const orderRes = await fetch(`${API_URL}/api/v1/orders`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Idempotency-Key": idemKeyRef,
        },
        body: JSON.stringify({
          customer: {
            full_name: customer.full_name.trim(),
            email: customer.email.trim(),
            phone: customer.phone.trim(),
          },
          delivery_zone_id: zoneId,
          delivery_address: address.trim(),
          notes: notes.trim() || null,
          promo_code: promoApplied?.code || null,
          redeem_points: redeemPoints > 0 ? redeemPoints : null,
          apply_wallet: useWallet && walletApplied > 0,
          items: cart.map((i) => ({
            product_id: i.product_id,
            variant_sku: i.variant_sku || null,
            variant_selections: i.variant_selections || null,
            name: i.name,
            unit_price: i.unit_price,
            quantity: i.quantity,
            is_custom_bowl: i.is_custom_bowl || false,
            customizations: i.customizations || null,
          })),
        }),
      });

      if (!orderRes.ok) {
        const err = await orderRes.json().catch(() => ({}));
        throw new Error(
          err.detail || `Order creation failed (HTTP ${orderRes.status})`
        );
      }
      order = await orderRes.json();

      if (!order.amount_due_external || order.amount_due_external <= 0) {
        clear();
        toast.success("Order placed — fully covered by wallet credit!");
        router.push(`/order/${order.reference}`);
        return;
      }

      setStage("redirecting");

      const payRes = await fetch(`${API_URL}/api/v1/payments/initialize`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "X-Idempotency-Key": `pay-${idemKeyRef}`,
        },
        body: JSON.stringify({
          order_id: order.id,
          email: customer.email.trim(),
        }),
      });

      const payData = await payRes.json().catch(() => ({}));

      if (!payRes.ok) {
        const detail = typeof payData.detail === "string" ? payData.detail : JSON.stringify(payData.detail || payData);
        throw new Error(detail || `Payment init failed (HTTP ${payRes.status})`);
      }

      if (!payData.authorization_url) {
        throw new Error("Backend did not return a Paystack URL. Check the backend logs.");
      }

      clear();
      window.location.href = payData.authorization_url;
    } catch (e) {
      setStage("form");
      setError(e.message);
      toast.error("Payment couldn't start — see the message above.");
      setSubmitting(false);

      if (order?.reference) {
        setTimeout(() => {
          router.push(`/order/${order.reference}`);
        }, 4000);
      }
    }
  }

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-16 text-center">
        <Loader2 className="w-8 h-8 text-brand-primary animate-spin mx-auto" />
        <p className="text-gray-400 text-sm mt-4">Loading checkout…</p>
      </div>
    );
  }

  if (cart.length === 0) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-16 text-center">
        <h1 className="font-heading text-2xl font-black text-white">
          Your cart is empty
        </h1>
        <p className="text-gray-400 text-sm mt-2">
          Add products before checking out.
        </p>
        <Button href="/" variant="primary" className="mt-6">
          <ArrowLeft className="w-4 h-4" />
          Browse products
        </Button>
      </div>
    );
  }

  if (stage === "redirecting") {
    return (
      <div className="min-h-[70vh] flex items-center justify-center p-4">
        <div className="text-center max-w-sm">
          <div className="w-24 h-24 rounded-full bg-brand-primary/15 mx-auto flex items-center justify-center">
            <Loader2 className="w-12 h-12 text-brand-primary animate-spin" />
          </div>
          <h1 className="font-heading text-2xl font-black mt-6 text-white">
            Redirecting to Paystack…
          </h1>
          <p className="text-gray-400 text-sm mt-2">
            Choose your payment method on the next screen.
          </p>
          <div className="flex items-center justify-center gap-2 mt-6 text-[11px] text-gray-500">
            <Lock className="w-3 h-3" />
            Secure checkout powered by Paystack
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 pb-32">
      <Link
        href="/"
        className="inline-flex items-center gap-2 text-sm font-bold text-gray-400 hover:text-brand-primary mb-6"
      >
        <ArrowLeft className="w-4 h-4" />
        Continue shopping
      </Link>

      <div className="flex items-baseline justify-between gap-4 mb-6">
        <h1 className="font-heading text-3xl font-black text-white">
          Checkout
        </h1>
        <div className="text-right">
          <div className="text-[10px] uppercase tracking-wider text-gray-500 font-bold">
            Total
          </div>
          <div className="text-2xl font-black text-brand-primary">
            {formatGHS(total)}
          </div>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-300 text-sm flex items-start gap-3">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <div className="flex-1">
            <div className="font-bold">Payment couldn't start</div>
            <div className="text-xs text-red-400/90 mt-1 whitespace-pre-wrap">
              {error}
            </div>
          </div>
        </div>
      )}

      <form onSubmit={submitOrder} className="space-y-6">
        <section className="bg-surface-card border border-surface-border rounded-3xl p-6 space-y-4">
          <h2 className="font-heading text-lg font-bold text-white">
            Contact details
          </h2>
          <Input
            label="Full name"
            required
            value={customer.full_name}
            onChange={(e) =>
              setCustomer({ ...customer, full_name: e.target.value })
            }
            placeholder="Kwadwo Mensah"
          />
          <Input
            label="Email"
            type="email"
            required
            value={customer.email}
            onChange={(e) =>
              setCustomer({ ...customer, email: e.target.value })
            }
            placeholder="you@example.com"
          />
          <Input
            label="Phone"
            type="tel"
            required
            value={customer.phone}
            onChange={(e) =>
              setCustomer({ ...customer, phone: e.target.value })
            }
            placeholder="024XXXXXXX"
          />
        </section>

        <section className="bg-surface-card border border-surface-border rounded-3xl p-6 space-y-4">
          <h2 className="font-heading text-lg font-bold text-white">
            Delivery
          </h2>
          <div>
            <label className="block text-xs font-bold text-gray-300 mb-1.5">
              Delivery zone
            </label>
            <select
              value={zoneId}
              onChange={(e) => setZoneId(e.target.value)}
              className="w-full px-4 py-3 rounded-xl bg-surface-dark border border-surface-border text-white text-sm focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/40 outline-none"
            >
              {zones.length === 0 && <option value="">No zones available</option>}
              {zones.map((z) => (
                <option key={z.id} value={z.id}>
                  {z.name} — {formatGHS(z.delivery_fee)}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-bold text-gray-300 mb-1.5">
              Delivery address
            </label>
            <textarea
              required
              rows={2}
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder="e.g. Pent Block C Room 204, UG Legon"
              className="w-full px-4 py-3 rounded-xl bg-surface-dark border border-surface-border text-white text-sm focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/40 outline-none resize-none"
            />
          </div>
          <div>
            <label className="block text-xs font-bold text-gray-300 mb-1.5">
              Notes (optional)
            </label>
            <textarea
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Any special instructions?"
              className="w-full px-4 py-3 rounded-xl bg-surface-dark border border-surface-border text-white text-sm focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/40 outline-none resize-none"
            />
          </div>
        </section>

        <section className="bg-surface-card border border-surface-border rounded-3xl p-6 space-y-3">
          <h2 className="font-heading text-lg font-bold text-white flex items-center gap-2">
            <Tag className="w-5 h-5 text-brand-primary" />
            Promo code
          </h2>
          {promoApplied ? (
            <div className="flex items-center justify-between p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30">
              <div className="text-sm">
                <div className="font-mono font-bold text-emerald-400">
                  {promoApplied.code}
                </div>
                <div className="text-emerald-300 text-xs">
                  {promoApplied.message}
                </div>
              </div>
              <button
                type="button"
                onClick={() => setPromoApplied(null)}
                className="text-xs text-red-400 hover:underline"
              >
                Remove
              </button>
            </div>
          ) : (
            <div className="flex gap-2">
              <input
                value={promoInput}
                onChange={(e) => setPromoInput(e.target.value.toUpperCase())}
                placeholder="WELCOME10"
                className="flex-1 px-4 py-3 rounded-xl bg-surface-dark border border-surface-border text-white text-sm font-mono focus:border-brand-primary outline-none"
              />
              <Button
                type="button"
                variant="primary"
                onClick={applyPromo}
                loading={promoLoading}
                disabled={!promoInput.trim()}
              >
                Apply
              </Button>
            </div>
          )}
          {promoError && <p className="text-xs text-red-400">{promoError}</p>}
        </section>

        {loyalty && loyalty.points >= (loyalty.min_redeem_points || 100) && (
          <section className="bg-surface-card border border-surface-border rounded-3xl p-6 space-y-3">
            <h2 className="font-heading text-lg font-bold text-white flex items-center gap-2">
              <Award className="w-5 h-5 text-brand-gold" />
              Redeem loyalty points
            </h2>
            <label className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer">
              <input
                type="checkbox"
                checked={redeemPoints > 0}
                onChange={(e) =>
                  setRedeemPoints(
                    e.target.checked
                      ? Math.min(
                          loyalty.points,
                          loyalty.min_redeem_points || 100
                        )
                      : 0
                  )
                }
                className="accent-brand-primary"
              />
              Use my {loyalty.points} points (worth {formatGHS(loyalty.cash_value)})
            </label>
            {redeemPoints > 0 && (
              <div>
                <input
                  type="range"
                  min={loyalty.min_redeem_points || 100}
                  max={loyalty.points}
                  step={10}
                  value={redeemPoints}
                  onChange={(e) =>
                    setRedeemPoints(parseInt(e.target.value, 10))
                  }
                  className="w-full accent-brand-primary"
                />
                <div className="flex justify-between text-[10px] text-gray-400 mt-1">
                  <span>{loyalty.min_redeem_points} min</span>
                  <span className="text-brand-gold font-bold">
                    Using {redeemPoints} pts
                  </span>
                  <span>{loyalty.points} max</span>
                </div>
              </div>
            )}
          </section>
        )}

        {wallet && wallet.balance > 0 && (
          <section className="bg-surface-card border border-surface-border rounded-3xl p-6 space-y-3">
            <h2 className="font-heading text-lg font-bold text-white flex items-center gap-2">
              <Wallet className="w-5 h-5 text-brand-primary" />
              Wallet balance
            </h2>
            <div className="text-sm text-gray-300">
              You have{" "}
              <strong className="text-brand-primary">
                {formatGHS(wallet.balance)}
              </strong>{" "}
              in store credit.
            </div>
            <label className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer">
              <input
                type="checkbox"
                checked={useWallet}
                onChange={(e) => setUseWallet(e.target.checked)}
                className="accent-brand-primary"
              />
              Apply wallet balance to this order
            </label>
            {useWallet && walletApplied > 0 && (
              <p className="text-xs text-emerald-400">
                Applying {formatGHS(walletApplied)} from wallet
              </p>
            )}
          </section>
        )}

        <section className="bg-surface-card border border-surface-border rounded-3xl p-6 space-y-2 text-sm">
          <div className="flex justify-between text-gray-400">
            <span>Subtotal</span>
            <span className="text-white font-semibold">
              {formatGHS(subtotal)}
            </span>
          </div>
          {promoApplied && (
            <div className="flex justify-between text-emerald-400">
              <span className="inline-flex items-center gap-1">
                <Sparkles className="w-3.5 h-3.5" />
                {promoApplied.code}
              </span>
              <span>−{formatGHS(promoDiscount)}</span>
            </div>
          )}
          {redeemPoints > 0 && (
            <div className="flex justify-between text-emerald-400">
              <span>{redeemPoints} pts</span>
              <span>−{formatGHS(loyaltyDiscount)}</span>
            </div>
          )}
          <div className="flex justify-between text-gray-400">
            <span>Delivery</span>
            <span className="text-emerald-400">
              {freeDeliveryReached || cartOrderType === "retail"
                ? "FREE"
                : formatGHS(deliveryFee)}
            </span>
          </div>
          {walletApplied > 0 && (
            <div className="flex justify-between text-emerald-400">
              <span>Wallet</span>
              <span>−{formatGHS(walletApplied)}</span>
            </div>
          )}
          <div className="flex justify-between font-extrabold text-white pt-3 border-t border-surface-border text-base">
            <span>Total</span>
            <span className="text-brand-primary">{formatGHS(total)}</span>
          </div>
        </section>
      </form>

      <div className="fixed bottom-0 left-0 right-0 z-30 border-t border-surface-border bg-surface-dark/95 backdrop-blur-md">
        <div className="max-w-3xl mx-auto px-4 py-4 flex items-center gap-4">
          <div className="flex-1">
            <div className="text-[10px] uppercase tracking-wider text-gray-500 font-bold">
              Pay
            </div>
            <div className="text-xl font-black text-white">
              {formatGHS(total)}
            </div>
          </div>
          <Button
            type="button"
            variant="primary"
            size="lg"
            loading={submitting}
            disabled={submitting || zones.length === 0}
            onClick={submitOrder}
            className="min-w-[200px]"
          >
            <Lock className="w-4 h-4" />
            {total <= 0 ? "Place order" : `Pay ${formatGHS(total)}`}
          </Button>
        </div>
        <div className="max-w-3xl mx-auto px-4 pb-3 text-[10px] text-gray-500 text-center flex items-center justify-center gap-1.5">
          <Lock className="w-3 h-3" />
          Secure payments by Paystack · MoMo, card, bank accepted
        </div>
      </div>
    </div>
  );
}