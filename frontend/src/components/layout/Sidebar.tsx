"use client";

import {
  FileText,
  LayoutDashboard,
  LogOut,
  Settings,
  Upload,
  Users,
} from "lucide-react";
import { NavItem } from "./NavItem";

interface SidebarProps {
  onLogout?: () => void;
}

const navItems = [
  { href: "/dashboard", icon: LayoutDashboard, label: "ダッシュボード" },
  { href: "/calls", icon: FileText, label: "通話一覧" },
  { href: "/operators", icon: Users, label: "オペレーター" },
  { href: "/upload", icon: Upload, label: "アップロード" },
  { href: "/settings", icon: Settings, label: "設定" },
];

export function Sidebar({ onLogout }: SidebarProps) {
  return (
    <aside className="flex flex-col w-[260px] h-screen bg-[var(--bg-sidebar)] p-4">
      {/* Logo */}
      <div className="flex items-center gap-3 h-12 px-2 mb-6">
        <div className="w-8 h-8 rounded-[var(--radius-md)] bg-[var(--accent-primary)] flex items-center justify-center">
          <span className="text-white font-bold text-sm">CQ</span>
        </div>
        <span className="text-xl font-bold text-[var(--text-on-dark)]">
          Call QA
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex flex-col gap-1 flex-1">
        {navItems.map((item) => (
          <NavItem
            key={item.href}
            href={item.href}
            icon={item.icon}
            label={item.label}
          />
        ))}
      </nav>

      {/* Logout */}
      {onLogout && (
        <button
          onClick={onLogout}
          className="flex items-center gap-3 h-11 px-3 rounded-[var(--radius-md)] text-[var(--text-muted)] hover:bg-white/5 hover:text-white transition-colors"
        >
          <LogOut className="w-5 h-5 shrink-0" />
          <span className="text-sm">ログアウト</span>
        </button>
      )}
    </aside>
  );
}
