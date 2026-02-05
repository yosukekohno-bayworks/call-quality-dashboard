"use client";

import { clsx } from "clsx";
import { Search } from "lucide-react";
import { InputHTMLAttributes, forwardRef } from "react";

interface SearchBarProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "type"> {}

export const SearchBar = forwardRef<HTMLInputElement, SearchBarProps>(
  ({ className, placeholder = "検索...", ...props }, ref) => {
    return (
      <div
        className={clsx(
          "flex items-center gap-2.5 h-11 px-3.5 rounded-[var(--radius-md)]",
          "bg-[var(--bg-card)] border border-[var(--border)]",
          "focus-within:ring-2 focus-within:ring-[var(--accent-primary)] focus-within:border-transparent",
          className
        )}
      >
        <Search className="w-[18px] h-[18px] text-[var(--text-muted)] shrink-0" />
        <input
          ref={ref}
          type="text"
          placeholder={placeholder}
          className="flex-1 bg-transparent text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none"
          {...props}
        />
      </div>
    );
  }
);

SearchBar.displayName = "SearchBar";
