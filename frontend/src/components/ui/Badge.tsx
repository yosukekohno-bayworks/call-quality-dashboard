"use client";

import { clsx } from "clsx";
import { HTMLAttributes } from "react";

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: "success" | "warning" | "error";
}

export function Badge({
  variant = "success",
  className,
  children,
  ...props
}: BadgeProps) {
  const baseStyles =
    "inline-flex items-center justify-center h-6 px-2.5 rounded-xl text-xs font-semibold";

  const variants = {
    success: "bg-[var(--status-success-bg)] text-[var(--status-success)]",
    warning: "bg-[var(--status-warning-bg)] text-[var(--status-warning)]",
    error: "bg-[var(--status-error-bg)] text-[var(--status-error)]",
  };

  return (
    <span className={clsx(baseStyles, variants[variant], className)} {...props}>
      {children}
    </span>
  );
}
