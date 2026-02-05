"use client";

import { clsx } from "clsx";
import { LucideIcon } from "lucide-react";
import { ButtonHTMLAttributes, forwardRef } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary";
  icon?: LucideIcon;
  iconPosition?: "left" | "right";
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = "primary",
      icon: Icon,
      iconPosition = "left",
      className,
      children,
      ...props
    },
    ref
  ) => {
    const baseStyles =
      "inline-flex items-center justify-center gap-2 h-10 px-4 rounded-[var(--radius-md)] font-semibold text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed";

    const variants = {
      primary:
        "bg-[var(--accent-primary)] text-white hover:bg-[var(--accent-primary-dark)] focus:ring-[var(--accent-primary)]",
      secondary:
        "bg-[var(--bg-card)] text-[var(--text-primary)] border border-[var(--border)] hover:bg-[var(--bg-muted)] focus:ring-[var(--border)]",
    };

    return (
      <button
        ref={ref}
        className={clsx(baseStyles, variants[variant], className)}
        {...props}
      >
        {Icon && iconPosition === "left" && <Icon className="w-[18px] h-[18px]" />}
        {children}
        {Icon && iconPosition === "right" && <Icon className="w-[18px] h-[18px]" />}
      </button>
    );
  }
);

Button.displayName = "Button";
