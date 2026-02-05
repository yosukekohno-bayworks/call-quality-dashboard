"use client";

import { clsx } from "clsx";
import { InputHTMLAttributes, forwardRef } from "react";

interface InputFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const InputField = forwardRef<HTMLInputElement, InputFieldProps>(
  ({ label, error, className, id, ...props }, ref) => {
    const inputId = id || props.name;

    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label
            htmlFor={inputId}
            className="text-sm font-medium text-[var(--text-primary)]"
          >
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={clsx(
            "h-11 px-3.5 rounded-[var(--radius-md)] bg-[var(--bg-card)] border border-[var(--border)]",
            "text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)]",
            "focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)] focus:border-transparent",
            "disabled:opacity-50 disabled:cursor-not-allowed",
            error && "border-[var(--status-error)] focus:ring-[var(--status-error)]",
            className
          )}
          {...props}
        />
        {error && (
          <span className="text-xs text-[var(--status-error)]">{error}</span>
        )}
      </div>
    );
  }
);

InputField.displayName = "InputField";
