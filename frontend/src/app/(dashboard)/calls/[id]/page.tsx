"use client";

import { Button } from "@/components/ui";
import {
  ArrowLeft,
  CheckCircle,
  Download,
  HelpCircle,
  RefreshCw,
  Smile,
} from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const emotionData = [
  { time: "0:00", operator: 0.6, customer: 0.4 },
  { time: "0:30", operator: 0.7, customer: 0.5 },
  { time: "1:00", operator: 0.65, customer: 0.3 },
  { time: "1:30", operator: 0.8, customer: 0.6 },
  { time: "2:00", operator: 0.75, customer: 0.7 },
  { time: "2:30", operator: 0.85, customer: 0.8 },
  { time: "3:00", operator: 0.8, customer: 0.75 },
  { time: "3:30", operator: 0.9, customer: 0.85 },
  { time: "4:00", operator: 0.85, customer: 0.8 },
  { time: "4:30", operator: 0.9, customer: 0.9 },
  { time: "5:00", operator: 0.95, customer: 0.95 },
];

const transcript = [
  {
    speaker: "operator",
    name: "山田 太郎",
    time: "0:00",
    text: "お電話ありがとうございます。○○株式会社、山田でございます。",
  },
  {
    speaker: "customer",
    name: "お客様",
    time: "0:05",
    text: "あ、すみません。先日購入した製品についてお聞きしたいのですが。",
  },
  {
    speaker: "operator",
    name: "山田 太郎",
    time: "0:12",
    text: "はい、製品についてのお問い合わせですね。どのような内容でしょうか？",
  },
  {
    speaker: "customer",
    name: "お客様",
    time: "0:20",
    text: "設定の仕方がよくわからなくて...",
  },
  {
    speaker: "operator",
    name: "山田 太郎",
    time: "0:25",
    text: "かしこまりました。設定についてご案内いたします。まず、製品の型番を教えていただけますか？",
  },
];

const flowSteps = [
  { step: "1. 挨拶", status: "completed", note: "適切な挨拶" },
  { step: "2. 要件確認", status: "completed", note: "問い合わせ内容を確認" },
  { step: "3. 本人確認", status: "completed", note: "製品型番を確認" },
  { step: "4. 対応", status: "completed", note: "適切に案内" },
  { step: "5. クロージング", status: "completed", note: "丁寧に終話" },
];

export default function CallDetailPage() {
  const params = useParams();
  const callId = params.id;

  return (
    <div className="flex flex-col gap-6 p-8 h-full overflow-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/calls">
            <button className="flex items-center justify-center w-10 h-10 rounded-[var(--radius-md)] bg-[var(--bg-card)] border border-[var(--border)] text-[var(--text-primary)] hover:border-[var(--accent-primary)]">
              <ArrowLeft className="w-5 h-5" />
            </button>
          </Link>
          <div className="flex flex-col gap-1">
            <h1 className="text-2xl font-bold text-[var(--text-primary)]">
              通話詳細 #CALL-2024-0121-00{callId}
            </h1>
            <p className="text-sm text-[var(--text-secondary)]">
              2024年1月21日 14:32 • 山田 太郎 • 5分23秒
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="secondary" icon={RefreshCw}>
            再分析
          </Button>
          <Button variant="secondary" icon={Download}>
            音声DL
          </Button>
        </div>
      </div>

      {/* Score Cards */}
      <div className="flex gap-5">
        {/* Total Score */}
        <div className="flex flex-col items-center gap-2 p-5 rounded-[var(--radius-lg)] bg-[var(--bg-card)] border border-[var(--border)] w-[200px]">
          <span className="text-sm text-[var(--text-secondary)]">総合スコア</span>
          <span className="text-5xl font-bold font-mono text-[var(--status-success)]">
            92
          </span>
          <span className="text-sm text-[var(--text-muted)]">/ 100</span>
        </div>

        {/* Category */}
        <div className="flex flex-col items-center gap-2 p-5 rounded-[var(--radius-lg)] bg-[var(--bg-card)] border border-[var(--border)] w-[200px]">
          <span className="text-sm text-[var(--text-secondary)]">
            問い合わせ種別
          </span>
          <HelpCircle className="w-12 h-12 text-[var(--accent-primary)]" />
          <span className="text-base font-semibold text-[var(--accent-primary)]">
            製品サポート
          </span>
        </div>

        {/* Flow Compliance */}
        <div className="flex flex-col items-center gap-2 p-5 rounded-[var(--radius-lg)] bg-[var(--bg-card)] border border-[var(--border)] w-[200px]">
          <span className="text-sm text-[var(--text-secondary)]">フロー遵守</span>
          <CheckCircle className="w-12 h-12 text-[var(--status-success)]" />
          <span className="text-base font-semibold text-[var(--status-success)]">
            遵守
          </span>
        </div>

        {/* Emotion */}
        <div className="flex flex-col items-center gap-2 p-5 rounded-[var(--radius-lg)] bg-[var(--bg-card)] border border-[var(--border)] w-[200px]">
          <span className="text-sm text-[var(--text-secondary)]">感情傾向</span>
          <Smile className="w-12 h-12 text-[var(--status-success)]" />
          <span className="text-base font-semibold text-[var(--status-success)]">
            ポジティブ
          </span>
        </div>

        {/* Filler Count */}
        <div className="flex flex-col items-center gap-2 p-5 rounded-[var(--radius-lg)] bg-[var(--bg-card)] border border-[var(--border)] w-[200px]">
          <span className="text-sm text-[var(--text-secondary)]">フィラー数</span>
          <span className="text-5xl font-bold font-mono text-[var(--status-success)]">
            3
          </span>
          <span className="text-sm text-[var(--text-muted)]">回</span>
        </div>
      </div>

      {/* Content Row */}
      <div className="flex gap-5 flex-1 min-h-0">
        {/* Transcript */}
        <div className="flex-1 flex flex-col rounded-[var(--radius-lg)] bg-[var(--bg-card)] border border-[var(--border)] overflow-hidden">
          <div className="px-5 py-4 border-b border-[var(--border)]">
            <h2 className="text-base font-semibold text-[var(--text-primary)]">
              文字起こし
            </h2>
          </div>
          <div className="flex-1 overflow-auto p-5">
            <div className="flex flex-col gap-4">
              {transcript.map((msg, index) => (
                <div key={index} className="flex gap-3">
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${
                      msg.speaker === "operator"
                        ? "bg-[var(--accent-primary-light)] text-[var(--accent-primary)]"
                        : "bg-[var(--bg-muted)] text-[var(--text-muted)]"
                    }`}
                  >
                    <span className="text-xs font-semibold">
                      {msg.speaker === "operator" ? "OP" : "顧客"}
                    </span>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium text-[var(--text-primary)]">
                        {msg.name}
                      </span>
                      <span className="text-xs text-[var(--text-muted)] font-mono">
                        {msg.time}
                      </span>
                    </div>
                    <p className="text-sm text-[var(--text-secondary)]">
                      {msg.text}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Panel */}
        <div className="w-[400px] flex flex-col gap-5">
          {/* Emotion Graph */}
          <div className="flex flex-col rounded-[var(--radius-lg)] bg-[var(--bg-card)] border border-[var(--border)] overflow-hidden flex-1">
            <div className="px-5 py-4 border-b border-[var(--border)]">
              <h2 className="text-base font-semibold text-[var(--text-primary)]">
                感情推移
              </h2>
            </div>
            <div className="flex-1 p-5">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={emotionData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                  <XAxis
                    dataKey="time"
                    tick={{ fontSize: 10, fill: "var(--text-muted)" }}
                    axisLine={{ stroke: "var(--border)" }}
                  />
                  <YAxis
                    domain={[0, 1]}
                    tick={{ fontSize: 10, fill: "var(--text-muted)" }}
                    axisLine={{ stroke: "var(--border)" }}
                    tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "var(--bg-card)",
                      border: "1px solid var(--border)",
                      borderRadius: "var(--radius-md)",
                    }}
                    formatter={(value: number) => `${(value * 100).toFixed(0)}%`}
                  />
                  <Area
                    type="monotone"
                    dataKey="operator"
                    stroke="#3B82F6"
                    fill="#3B82F6"
                    fillOpacity={0.2}
                    name="オペレーター"
                  />
                  <Area
                    type="monotone"
                    dataKey="customer"
                    stroke="#10B981"
                    fill="#10B981"
                    fillOpacity={0.2}
                    name="顧客"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Flow Detail */}
          <div className="flex flex-col rounded-[var(--radius-lg)] bg-[var(--bg-card)] border border-[var(--border)] overflow-hidden">
            <div className="px-5 py-4 border-b border-[var(--border)]">
              <h2 className="text-base font-semibold text-[var(--text-primary)]">
                フロー遵守詳細
              </h2>
            </div>
            <div className="p-4">
              <div className="flex flex-col gap-3">
                {flowSteps.map((step, index) => (
                  <div
                    key={index}
                    className="flex items-center gap-3 p-3 rounded-[var(--radius-md)] bg-[var(--bg-muted)]"
                  >
                    <CheckCircle className="w-5 h-5 text-[var(--status-success)] shrink-0" />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-[var(--text-primary)]">
                        {step.step}
                      </p>
                      <p className="text-xs text-[var(--text-muted)]">
                        {step.note}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
