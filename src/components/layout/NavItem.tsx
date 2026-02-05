"use client";

import { clsx } from "clsx";
import { LucideIcon } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

interface NavItemProps {
  href: string;
  icon: LucideIcon;
  label: string;
}

export function NavItem({ href, icon: Icon, label }: NavItemProps) {
  const pathname = usePathname();
  const isActive = pathname === href || pathname.startsWith(`${href}/`);

  return (
    <Link
      href={href}
      className={clsx(
        "flex items-center gap-3 h-11 px-3 rounded-[var(--radius-md)] transition-colors",
        isActive
          ? "bg-[var(--accent-primary)] text-white font-semibold"
          : "text-[var(--text-muted)] hover:bg-white/5 hover:text-white"
      )}
    >
      <Icon className="w-5 h-5 shrink-0" />
      <span className="text-sm">{label}</span>
    </Link>
  );
}
