"use client";

import { Button, KPICard, SearchBar } from "@/components/ui";
import {
  Calendar,
  CheckCircle,
  Clock,
  Download,
  Phone,
  Star,
} from "lucide-react";
import Link from "next/link";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";

const scoreData = [
  { date: "1/15", score: 82 },
  { date: "1/16", score: 85 },
  { date: "1/17", score: 84 },
  { date: "1/18", score: 88 },
  { date: "1/19", score: 86 },
  { date: "1/20", score: 89 },
  { date: "1/21", score: 87 },
];

const categoryData = [
  { name: "製品サポート", value: 420, color: "#3B82F6" },
  { name: "契約手続き", value: 280, color: "#10B981" },
  { name: "クレーム", value: 180, color: "#EF4444" },
  { name: "料金問い合わせ", value: 220, color: "#F59E0B" },
  { name: "その他", value: 148, color: "#64748B" },
];

const recentCalls = [
  {
    id: "1",
    date: "01/21 14:32",
    operator: "山田 太郎",
    caller: "090-1234-5678",
    duration: "5:23",
    score: 92,
    category: "製品サポート",
  },
  {
    id: "2",
    date: "01/21 13:15",
    operator: "鈴木 花子",
    caller: "03-9876-5432",
    duration: "3:47",
    score: 78,
    category: "契約手続き",
  },
  {
    id: "3",
    date: "01/21 11:42",
    operator: "佐藤 一郎",
    caller: "080-5555-1234",
    duration: "8:12",
    score: 95,
    category: "クレーム",
  },
];

function getScoreColor(score: number) {
  if (score >= 85) return "var(--status-success)";
  if (score >= 70) return "var(--status-warning)";
  return "var(--status-error)";
}

export default function DashboardPage() {
  return (
    <div className="flex flex-col gap-6 p-8 h-full">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex flex-col gap-1">
          <h1 className="text-[28px] font-bold text-[var(--text-primary)]">
            ダッシュボード
          </h1>
          <p className="text-sm text-[var(--text-secondary)]">
            2024年1月15日 - 2024年1月21日
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="secondary" icon={Download}>
            エクスポート
          </Button>
          <Button variant="secondary" icon={Calendar}>
            期間選択
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        <KPICard
          label="総通話数"
          value="1,248"
          icon={Phone}
          delta={8.2}
        />
        <KPICard
          label="平均通話時間"
          value="4:32"
          icon={Clock}
          delta={-2.1}
        />
        <KPICard
          label="平均品質スコア"
          value="87.5"
          icon={Star}
          delta={3.4}
        />
        <KPICard
          label="フロー遵守率"
          value="92.3%"
          icon={CheckCircle}
          delta={1.8}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_400px] gap-5 h-[320px]">
        {/* Score Trend Chart */}
        <div className="flex flex-col gap-4 p-6 rounded-[var(--radius-lg)] bg-[var(--bg-card)] border border-[var(--border)]">
          <h2 className="text-base font-semibold text-[var(--text-primary)]">
            品質スコア推移
          </h2>
          <div className="flex-1">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={scoreData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 12, fill: "var(--text-muted)" }}
                  axisLine={{ stroke: "var(--border)" }}
                />
                <YAxis
                  domain={[70, 100]}
                  tick={{ fontSize: 12, fill: "var(--text-muted)" }}
                  axisLine={{ stroke: "var(--border)" }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "var(--bg-card)",
                    border: "1px solid var(--border)",
                    borderRadius: "var(--radius-md)",
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="score"
                  stroke="var(--accent-primary)"
                  strokeWidth={2}
                  dot={{ fill: "var(--accent-primary)", r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Category Distribution */}
        <div className="flex flex-col gap-4 p-6 rounded-[var(--radius-lg)] bg-[var(--bg-card)] border border-[var(--border)]">
          <h2 className="text-base font-semibold text-[var(--text-primary)]">
            問い合わせ種別
          </h2>
          <div className="flex-1">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={categoryData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {categoryData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: "var(--bg-card)",
                    border: "1px solid var(--border)",
                    borderRadius: "var(--radius-md)",
                  }}
                />
                <Legend
                  verticalAlign="bottom"
                  height={36}
                  formatter={(value) => (
                    <span style={{ color: "var(--text-secondary)", fontSize: 12 }}>
                      {value}
                    </span>
                  )}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent Calls Table */}
      <div className="flex-1 flex flex-col rounded-[var(--radius-lg)] bg-[var(--bg-card)] border border-[var(--border)] overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border)]">
          <h2 className="text-base font-semibold text-[var(--text-primary)]">
            最近の通話
          </h2>
          <div className="flex items-center gap-3">
            <SearchBar placeholder="通話を検索..." className="w-60" />
            <Link
              href="/calls"
              className="text-sm font-medium text-[var(--accent-primary)] hover:underline"
            >
              すべて表示 →
            </Link>
          </div>
        </div>

        {/* Table Header */}
        <div className="flex items-center h-12 px-6 bg-[var(--bg-muted)]">
          <span className="w-[140px] text-[13px] font-semibold text-[var(--text-secondary)]">
            日時
          </span>
          <span className="w-[140px] text-[13px] font-semibold text-[var(--text-secondary)]">
            オペレーター
          </span>
          <span className="w-[140px] text-[13px] font-semibold text-[var(--text-secondary)]">
            発信元
          </span>
          <span className="w-[100px] text-[13px] font-semibold text-[var(--text-secondary)]">
            通話時間
          </span>
          <span className="w-20 text-[13px] font-semibold text-[var(--text-secondary)]">
            スコア
          </span>
          <span className="w-[100px] text-[13px] font-semibold text-[var(--text-secondary)]">
            種別
          </span>
          <span className="text-[13px] font-semibold text-[var(--text-secondary)]">
            &nbsp;
          </span>
        </div>

        {/* Table Body */}
        <div className="flex-1 overflow-auto">
          {recentCalls.map((call, index) => (
            <div
              key={call.id}
              className={`flex items-center h-14 px-6 ${
                index < recentCalls.length - 1
                  ? "border-b border-[var(--border-light)]"
                  : ""
              }`}
            >
              <span className="w-[140px] text-[13px] font-mono text-[var(--text-primary)]">
                {call.date}
              </span>
              <span className="w-[140px] text-sm text-[var(--text-primary)]">
                {call.operator}
              </span>
              <span className="w-[140px] text-[13px] font-mono text-[var(--text-secondary)]">
                {call.caller}
              </span>
              <span className="w-[100px] text-[13px] font-mono text-[var(--text-primary)]">
                {call.duration}
              </span>
              <span
                className="w-20 text-sm font-semibold font-mono"
                style={{ color: getScoreColor(call.score) }}
              >
                {call.score}
              </span>
              <span className="w-[100px] text-[13px] text-[var(--text-primary)]">
                {call.category}
              </span>
              <Link
                href={`/calls/${call.id}`}
                className="text-[13px] font-medium text-[var(--accent-primary)] hover:underline"
              >
                詳細
              </Link>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
