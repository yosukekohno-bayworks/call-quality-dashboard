"use client";

import { Button, SearchBar } from "@/components/ui";
import { Calendar, ChevronLeft, ChevronRight, Filter, Upload, User } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

interface CallRecord {
  id: string;
  date: string;
  operator: string;
  caller: string;
  category: string;
  duration: string;
  score: number;
  flowCompliance: "pass" | "warning" | "fail";
}

const mockCalls: CallRecord[] = [
  {
    id: "1",
    date: "01/21 14:32",
    operator: "山田 太郎",
    caller: "090-1234-5678",
    category: "製品サポート",
    duration: "5:23",
    score: 92,
    flowCompliance: "pass",
  },
  {
    id: "2",
    date: "01/21 13:15",
    operator: "鈴木 花子",
    caller: "03-9876-5432",
    category: "契約手続き",
    duration: "3:47",
    score: 78,
    flowCompliance: "warning",
  },
  {
    id: "3",
    date: "01/21 11:42",
    operator: "佐藤 一郎",
    caller: "080-5555-1234",
    category: "クレーム",
    duration: "8:12",
    score: 95,
    flowCompliance: "pass",
  },
  {
    id: "4",
    date: "01/21 10:05",
    operator: "田中 美咲",
    caller: "06-1111-2222",
    category: "料金問い合わせ",
    duration: "2:15",
    score: 65,
    flowCompliance: "fail",
  },
  {
    id: "5",
    date: "01/21 09:30",
    operator: "高橋 健一",
    caller: "070-3333-4444",
    category: "製品サポート",
    duration: "6:45",
    score: 88,
    flowCompliance: "pass",
  },
];

function getScoreColor(score: number) {
  if (score >= 85) return "var(--status-success)";
  if (score >= 70) return "var(--status-warning)";
  return "var(--status-error)";
}

function getFlowComplianceDisplay(status: "pass" | "warning" | "fail") {
  switch (status) {
    case "pass":
      return { symbol: "○", color: "var(--status-success)" };
    case "warning":
      return { symbol: "△", color: "var(--status-warning)" };
    case "fail":
      return { symbol: "×", color: "var(--status-error)" };
  }
}

export default function CallsPage() {
  const [currentPage, setCurrentPage] = useState(1);
  const totalItems = 1248;
  const itemsPerPage = 20;
  const totalPages = Math.ceil(totalItems / itemsPerPage);

  return (
    <div className="flex flex-col gap-6 p-8 h-full">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex flex-col gap-1">
          <h1 className="text-[28px] font-bold text-[var(--text-primary)]">
            通話一覧
          </h1>
          <p className="text-sm text-[var(--text-secondary)]">
            全{totalItems.toLocaleString()}件の通話記録
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/upload">
            <Button variant="primary" icon={Upload}>
              アップロード
            </Button>
          </Link>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex items-center gap-4">
        <SearchBar
          placeholder="通話ID、オペレーター名で検索..."
          className="w-[300px]"
        />
        <Button variant="secondary" icon={Calendar}>
          期間
        </Button>
        <Button variant="secondary" icon={User}>
          オペレーター
        </Button>
        <Button variant="secondary" icon={Filter}>
          種別
        </Button>
      </div>

      {/* Calls Table */}
      <div className="flex-1 flex flex-col rounded-[var(--radius-lg)] bg-[var(--bg-card)] border border-[var(--border)] overflow-hidden">
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
          <span className="w-[120px] text-[13px] font-semibold text-[var(--text-secondary)]">
            問い合わせ種別
          </span>
          <span className="w-[100px] text-[13px] font-semibold text-[var(--text-secondary)]">
            通話時間
          </span>
          <span className="w-20 text-[13px] font-semibold text-[var(--text-secondary)]">
            スコア
          </span>
          <span className="w-[100px] text-[13px] font-semibold text-[var(--text-secondary)]">
            フロー遵守
          </span>
          <span className="text-[13px] font-semibold text-[var(--text-secondary)]">
            &nbsp;
          </span>
        </div>

        {/* Table Body */}
        <div className="flex-1 overflow-auto">
          {mockCalls.map((call, index) => {
            const flowDisplay = getFlowComplianceDisplay(call.flowCompliance);
            return (
              <div
                key={call.id}
                className={`flex items-center h-14 px-6 ${
                  index < mockCalls.length - 1
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
                <span className="w-[120px] text-[13px] text-[var(--text-primary)]">
                  {call.category}
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
                <span
                  className="w-[100px] text-sm"
                  style={{ color: flowDisplay.color }}
                >
                  {flowDisplay.symbol}
                </span>
                <Link
                  href={`/calls/${call.id}`}
                  className="text-[13px] font-medium text-[var(--accent-primary)] hover:underline"
                >
                  詳細
                </Link>
              </div>
            );
          })}
        </div>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between pt-4">
        <span className="text-sm text-[var(--text-secondary)]">
          {((currentPage - 1) * itemsPerPage + 1).toLocaleString()}-
          {Math.min(currentPage * itemsPerPage, totalItems).toLocaleString()} /{" "}
          {totalItems.toLocaleString()}件を表示
        </span>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            disabled={currentPage === 1}
            className="flex items-center justify-center w-9 h-9 rounded-[var(--radius-md)] bg-[var(--bg-card)] border border-[var(--border)] text-[var(--text-muted)] hover:border-[var(--accent-primary)] disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronLeft className="w-[18px] h-[18px]" />
          </button>

          {[1, 2, 3].map((page) => (
            <button
              key={page}
              onClick={() => setCurrentPage(page)}
              className={`flex items-center justify-center w-9 h-9 rounded-[var(--radius-md)] text-sm font-semibold ${
                currentPage === page
                  ? "bg-[var(--accent-primary)] text-white"
                  : "bg-[var(--bg-card)] border border-[var(--border)] text-[var(--text-primary)] hover:border-[var(--accent-primary)]"
              }`}
            >
              {page}
            </button>
          ))}

          <button
            onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages}
            className="flex items-center justify-center w-9 h-9 rounded-[var(--radius-md)] bg-[var(--bg-card)] border border-[var(--border)] text-[var(--text-primary)] hover:border-[var(--accent-primary)] disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronRight className="w-[18px] h-[18px]" />
          </button>
        </div>
      </div>
    </div>
  );
}
