"use client";

import { forwardRef, useId } from "react";

const Input = forwardRef(function Input(
  { label, error, hint, className = "", containerClassName = "", id, ...props },
  ref
) {
  const reactId = useId();
  const inputId = id || props.name || `kb-input-${reactId}`;
  const errorId = `${inputId}-error`;
  const hintId = `${inputId}-hint`;

  return (
    <div className={containerClassName}>
      {label && (
        <label
          htmlFor={inputId}
          className="block text-xs font-bold text-gray-300 mb-1.5"
        >
          {label}
        </label>
      )}
      <input
        id={inputId}
        ref={ref}
        aria-invalid={error ? "true" : undefined}
        aria-describedby={error ? errorId : hint ? hintId : undefined}
        {...props}
        className={`w-full px-4 py-3 rounded-xl bg-surface-dark border text-white text-sm outline-none transition-colors focus:ring-2 disabled:opacity-60 ${
          error
            ? "border-red-500/60 focus:border-red-500 focus:ring-red-500/30"
            : "border-surface-border focus:border-brand-primary focus:ring-brand-primary/40"
        } ${className}`}
      />
      {error && (
        <p id={errorId} className="text-[11px] text-red-400 mt-1">
          {error}
        </p>
      )}
      {!error && hint && (
        <p id={hintId} className="text-[10px] text-gray-500 mt-1">
          {hint}
        </p>
      )}
    </div>
  );
});

export default Input;