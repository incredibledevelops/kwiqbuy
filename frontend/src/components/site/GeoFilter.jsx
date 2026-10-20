// src/components/site/GeoFilter.jsx
"use client";

import { useState } from "react";
import { Navigation, Loader2 } from "lucide-react";
import { useToast } from "@/components/ui/Toast";

export default function GeoFilter({ onLocationChange }) {
  const toast = useToast();
  const [loading, setLoading] = useState(false);

  function detectLocation() {
    if (typeof navigator === "undefined" || !navigator.geolocation) {
      toast.error("Geolocation is not supported by your browser");
      return;
    }
    setLoading(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLoading(false);
        toast.success("Location found! Showing nearby vendors.");
        onLocationChange?.({
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
        });
      },
      (err) => {
        setLoading(false);
        if (err.code === err.PERMISSION_DENIED) {
          toast.error("Location permission denied. Enable it in your browser.");
        } else if (err.code === err.TIMEOUT) {
          toast.error("Location request timed out. Try again.");
        } else {
          toast.error("Could not get your location. Please try again.");
        }
      },
      { timeout: 10000, maximumAge: 60000 }
    );
  }

  return (
    <button
      onClick={detectLocation}
      disabled={loading}
      aria-busy={loading}
      className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-brand-primary/10 border border-brand-primary/30 text-brand-primary font-bold text-sm hover:bg-brand-primary/20 transition-colors disabled:opacity-60"
    >
      {loading ? (
        <Loader2 className="w-4 h-4 animate-spin" />
      ) : (
        <Navigation className="w-4 h-4" />
      )}
      {loading ? "Detecting..." : "Use my location"}
    </button>
  );
}