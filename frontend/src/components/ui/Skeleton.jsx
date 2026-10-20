"use client";

export function SkeletonLine({ className = "" }) {
  return (
    <div
      aria-hidden="true"
      className={`animate-pulse motion-reduce:animate-none bg-white/10 rounded ${className}`}
    />
  );
}

export function SkeletonBlock({ className = "" }) {
  return (
    <div
      aria-hidden="true"
      className={`animate-pulse motion-reduce:animate-none bg-white/5 rounded-2xl ${className}`}
    />
  );
}

export function CardSkeleton() {
  return (
    <div className="bg-surface-card border border-surface-border rounded-2xl overflow-hidden">
      <SkeletonBlock className="h-40 rounded-none" />
      <div className="p-4 space-y-3">
        <SkeletonLine className="h-4 w-3/4" />
        <SkeletonLine className="h-3 w-full" />
        <SkeletonLine className="h-4 w-20" />
      </div>
    </div>
  );
}

export function GridSkeleton({ count = 6 }) {
  return (
    <div
      role="status"
      aria-label="Loading"
      className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"
    >
      {Array.from({ length: count }).map((_, i) => (
        <CardSkeleton key={i} />
      ))}
    </div>
  );
}