"use client";

import Link from "next/link";
import { forwardRef } from "react";

const VARIANTS = {
  primary:
    "bg-brand-primary hover:bg-brand-primaryDark text-white shadow-lg shadow-brand-primary/20",
  secondary:
    "bg-surface-card hover:bg-surface-cardAlt border border-surface-border text-white",
  ghost: "text-gray-300 hover:text-white hover:bg-white/5",
  danger: "bg-brand-danger hover:bg-red-700 text-white",
  success: "bg-brand-success hover:bg-emerald-700 text-white",
  gold: "bg-brand-gold hover:bg-amber-500 text-surface-dark font-extrabold",
};

const SIZES = {
  sm: "px-3 py-1.5 text-xs rounded-lg",
  md: "px-4 py-2.5 text-sm rounded-xl",
  lg: "px-6 py-3.5 text-base rounded-2xl",
};

const Button = forwardRef(function Button(
  {
    children,
    variant = "primary",
    size = "md",
    href,
    disabled,
    loading,
    className = "",
    type = "button",
    ...props
  },
  ref
) {
  const cls = `inline-flex items-center justify-center gap-2 font-bold transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary/60 ${
    VARIANTS[variant] || VARIANTS.primary
  } ${SIZES[size] || SIZES.md} ${className}`;

  const isDisabled = disabled || loading;

  if (href && !isDisabled) {
    return (
      <Link href={href} className={cls} ref={ref} {...props}>
        {children}
      </Link>
    );
  }

  return (
    <button
      ref={ref}
      type={type}
      disabled={isDisabled}
      aria-busy={loading || undefined}
      className={cls}
      {...props}
    >
      {loading && (
        <span className="w-4 h-4 rounded-full border-2 border-current/40 border-t-current animate-spin" />
      )}
      {children}
    </button>
  );
});

export default Button;