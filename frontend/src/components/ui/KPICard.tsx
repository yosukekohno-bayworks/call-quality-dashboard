"use client";

import { clsx } from "clsx";
import { LucideIcon, TrendingDown, TrendingUp } from "lucide-react";
import { HTMLAttributes } from "react";

interface KPICardProps extends HTMLAttributes<HTMLDivElement> {
  label: string;
  value: string | number;
  icon?: LucideIcon;
  delta?: number;
  deltaLabel?: string;
}

export function KPICard({
  label,
  value,
  icon: Icon,
  delta,
  deltaLabel = "前週比",
  className,
  ...props
}: KPICardProps) {
  const isPositive = delta !== undefined && delta >= 0;
  const DeltaIcon = isPositive ? TrendingUp : TrendingDown;

  return (
    <div
      className={clsx(
        "flex flex-col gap-3 p-6 rounded-[var(--radius-lg)]",
        "bg-[var(--bg-card)] border border-[var(--border)]",
        className
      )}
      {...props}
    >
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-[var(--text-secondary)]">
          {label}
        </span>
        {Icon && (
          <Icon className="w-5 h-5 text-[var(--text-muted)]" />
        )}
      </div>

      <span className="text-[32px] font-bold text-[var(--text-primary)] font-mono">
        {value}
      </span>

      {delta !== undefined && (
        <div className="flex items-center gap-1.5">
          <DeltaIcon
            className={clsx(
              "w-4 h-4",
              isPositive
                ? "text-[var(--status-success)]"
                : "text-[var(--status-error)]"
            )}
          />
          <span
            className={clsx(
              "text-[13px] font-medium",
              isPositive
                ? "text-[var(--status-success)]"
                : "text-[var(--status-error)]"
            )}
          >
            {isPositive ? "+" : ""}
            {delta}% {deltaLabel}
          </span>
        </div>
      )}
    </div>
  );
}
