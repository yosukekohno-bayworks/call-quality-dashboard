"use client";

import { KPICard } from "@/components/ui";
import { Phone, Star, TrendingUp, Users } from "lucide-react";

export default function DashboardPage() {
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-[var(--text-primary)] mb-6">
        ダッシュボード
      </h1>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <KPICard
          label="総通話数"
          value="1,234"
          icon={Phone}
          delta={12.5}
        />
        <KPICard
          label="平均品質スコア"
          value="87.3"
          icon={Star}
          delta={3.2}
        />
        <KPICard
          label="フロー遵守率"
          value="94.5%"
          icon={TrendingUp}
          delta={1.8}
        />
        <KPICard
          label="アクティブオペレーター"
          value="24"
          icon={Users}
          delta={-2}
        />
      </div>

      {/* Placeholder for charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-[var(--radius-lg)] p-6">
          <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
            スコア推移
          </h2>
          <div className="h-64 flex items-center justify-center text-[var(--text-muted)]">
            グラフ表示エリア
          </div>
        </div>
        <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-[var(--radius-lg)] p-6">
          <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
            オペレーターランキング
          </h2>
          <div className="h-64 flex items-center justify-center text-[var(--text-muted)]">
            ランキング表示エリア
          </div>
        </div>
      </div>
    </div>
  );
}
