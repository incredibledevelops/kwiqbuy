"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import {
  Loader2,
  Bike,
  MapPin,
  Package,
  CheckCircle2,
  Wallet,
  Navigation,
} from "lucide-react";
import StatCard from "@/components/vendor/StatCard";
import Button from "@/components/ui/Button";
import { useToast } from "@/components/ui/Toast";
import { riderApi } from "@/lib/riderApi";
import { formatGHS, formatDateTime } from "@/lib/utils";

export default function RiderDashboard() {
  const toast = useToast();
  const [data, setData] = useState({
    assignable: [],
    active: [],
    earnings: { available: 0, total_earned: 0 },
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null);

  // Location Tracking State
  const [isTracking, setIsTracking] = useState(false);
  const geoWatchRef = useRef(null); // <-- FIXED: useRef is now imported

  const loadData = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const [assignable, active, earnings] = await Promise.all([
        riderApi.get("/api/v1/riders/assignable"),
        riderApi.get("/api/v1/riders/mine"),
        riderApi.get("/api/v1/riders/me/earnings"),
      ]);
      setData({
        assignable: Array.isArray(assignable) ? assignable : [],
        active: Array.isArray(active) ? active : [],
        earnings: earnings || { available: 0 },
      });
      setError("");
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial load + 30s polling for new orders
  useEffect(() => {
    loadData();
    const interval = setInterval(() => loadData(true), 30000);
    return () => clearInterval(interval);
  }, [loadData]);

  // Location tracking logic — stable across renders
  const pushLocation = useCallback(async (pos) => {
    try {
      const activeOrder = data.active.length > 0 ? data.active[0] : null;
      await riderApi.post("/api/v1/rider/location", {
        lat: pos.coords.latitude,
        lng: pos.coords.longitude,
        order_id: activeOrder?.id || null,
        heading: pos.coords.heading,
        speed_mps: pos.coords.speed,
        accuracy_meters: pos.coords.accuracy,
      });
    } catch (e) {
      console.error("Failed to update location:", e);
    }
  }, [data.active]);

  useEffect(() => {
    if (!isTracking) {
      if (geoWatchRef.current !== null) {
        navigator.geolocation.clearWatch(geoWatchRef.current);
        geoWatchRef.current = null;
      }
      return;
    }

    if (!navigator.geolocation) {
      toast.error("Geolocation is not supported by your browser.");
      setIsTracking(false);
      return;
    }

    // Get initial position immediately
    navigator.geolocation.getCurrentPosition(pushLocation, (err) => {
      console.error("Geo error:", err);
      toast.error("Could not get your location. Check permissions.");
      setIsTracking(false);
    });

    // Watch as they move
    geoWatchRef.current = navigator.geolocation.watchPosition(
      pushLocation,
      (err) => console.error("Geo error:", err),
      { enableHighAccuracy: true, maximumAge: 10000, timeout: 5000 }
    );

    return () => {
      if (geoWatchRef.current !== null) {
        navigator.geolocation.clearWatch(geoWatchRef.current);
        geoWatchRef.current = null;
      }
    };
  }, [isTracking, pushLocation, toast]);

  async function claimOrder(orderId) {
    setBusyId(orderId);
    try {
      await riderApi.post(`/api/v1/riders/claim/${orderId}`);
      toast.success("Order claimed! Please head to the vendors.");
      setIsTracking(true); // Turn on GPS automatically
      await loadData();
    } catch (e) {
      toast.error(e.message);
    } finally {
      setBusyId(null);
    }
  }

  async function markDelivered(orderId) {
    setBusyId(orderId);
    try {
      await riderApi.patch(`/api/v1/riders/orders/${orderId}/status`, {
        status: "delivered",
      });
      toast.success("Order delivered! Great job.");
      // Turn off GPS if this was the last active order
      if (data.active.length <= 1) {
        setIsTracking(false);
      }
      await loadData();
    } catch (e) {
      toast.error(e.message);
    } finally {
      setBusyId(null);
    }
  }

  if (loading) {
    return (
      <div className="py-16 text-center">
        <Loader2 className="w-8 h-8 text-brand-primary animate-spin mx-auto" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="font-heading text-3xl font-black text-white">
            Dashboard
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Manage your deliveries and track your earnings.
          </p>
        </div>
        
        <button
          onClick={() => setIsTracking(!isTracking)}
          className={`inline-flex items-center gap-2 px-4 py-2.5 rounded-xl border font-bold text-sm transition-colors ${
            isTracking 
              ? "bg-emerald-500/15 border-emerald-500/30 text-emerald-400 animate-pulse" 
              : "bg-surface-card border-surface-border text-gray-400 hover:text-white"
          }`}
        >
          <Navigation className="w-4 h-4" />
          {isTracking ? "Location Sharing ON" : "Location Sharing OFF"}
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
          {error}
        </div>
      )}

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
        <StatCard
          label="Available Balance"
          value={formatGHS(data.earnings.available || 0)}
          icon={Wallet}
          accent="success"
        />
        <StatCard
          label="Active Deliveries"
          value={data.active.length}
          icon={Bike}
          accent="primary"
        />
        <StatCard
          label="Available Orders"
          value={data.assignable.length}
          icon={Package}
          accent="warning"
        />
      </div>

      {/* ACTIVE DELIVERIES */}
      <section>
        <h2 className="font-heading text-xl font-bold text-white mb-3">
          Active Deliveries
        </h2>
        {data.active.length === 0 ? (
          <div className="bg-surface-card border border-surface-border rounded-2xl p-6 text-center text-sm text-gray-500">
            No active deliveries. Claim an order below to start.
          </div>
        ) : (
          <div className="space-y-4">
            {data.active.map((order) => (
              <div
                key={order.id}
                className="bg-surface-card border-2 border-brand-primary/30 rounded-2xl overflow-hidden"
              >
                <div className="bg-brand-primary/10 px-5 py-3 flex justify-between items-center border-b border-brand-primary/20">
                  <div className="font-mono text-sm font-bold text-brand-primary">
                    {order.reference}
                  </div>
                  <div className="text-xs font-bold text-white bg-brand-primary px-2 py-0.5 rounded-md">
                    DELIVERING
                  </div>
                </div>
                <div className="p-5 space-y-4">
                  <div className="flex items-start gap-4">
                    <div className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center shrink-0">
                      <MapPin className="w-5 h-5 text-gray-400" />
                    </div>
                    <div>
                      <div className="text-sm font-bold text-white">
                        {order.customer_name} · {order.customer_phone}
                      </div>
                      <div className="text-xs text-gray-400 mt-0.5">
                        {order.delivery_address} ({order.delivery_zone_name})
                      </div>
                    </div>
                  </div>

                  <div className="bg-surface-dark border border-surface-border rounded-xl p-3 space-y-2">
                    <div className="text-[10px] uppercase font-bold text-gray-500">
                      Pickup Locations
                    </div>
                    {order.vendor_pickups.map((v, i) => (
                      <div key={i} className="flex justify-between items-center text-sm">
                        <span className="text-white font-bold">{v.vendor_name}</span>
                        <span className="text-gray-500">{v.items_count} items</span>
                      </div>
                    ))}
                  </div>
                  
                  <div className="pt-2 flex gap-3">
                    <Button
                      variant="success"
                      size="lg"
                      className="w-full"
                      loading={busyId === order.id}
                      onClick={() => markDelivered(order.id)}
                    >
                      <CheckCircle2 className="w-5 h-5" />
                      Mark Delivered
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* AVAILABLE ORDERS */}
      <section>
        <h2 className="font-heading text-xl font-bold text-white mb-3">
          Available Orders
        </h2>
        {data.assignable.length === 0 ? (
          <div className="bg-surface-card border border-surface-border rounded-2xl p-6 text-center text-sm text-gray-500">
            No orders available for pickup right now. Check back soon.
          </div>
        ) : (
          <div className="grid sm:grid-cols-2 gap-4">
            {data.assignable.map((order) => (
              <div
                key={order.id}
                className="bg-surface-card border border-surface-border rounded-2xl p-5 flex flex-col"
              >
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <div className="font-mono text-xs text-brand-primary font-bold">
                      {order.reference}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {order.delivery_zone_name}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-[10px] text-gray-500 uppercase tracking-wider font-bold">
                      Earning
                    </div>
                    <div className="text-brand-primary font-bold">
                      {formatGHS(order.rider_earning)}
                    </div>
                  </div>
                </div>
                <div className="flex-1">
                  <div className="text-xs text-gray-400 flex items-center gap-3">
                    <span>{order.vendor_count} vendor{order.vendor_count !== 1 && 's'}</span>
                    <span>{order.items_count} item{order.items_count !== 1 && 's'}</span>
                  </div>
                </div>
                <Button
                  variant="secondary"
                  size="md"
                  className="w-full mt-4 border-brand-primary/30 text-brand-primary hover:bg-brand-primary/10"
                  loading={busyId === order.id}
                  onClick={() => claimOrder(order.id)}
                >
                  Claim Order
                </Button>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}