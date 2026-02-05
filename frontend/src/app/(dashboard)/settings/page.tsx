"use client";

import { Badge, Button, InputField } from "@/components/ui";
import { clsx } from "clsx";
import {
  ArrowDown,
  ArrowRight,
  Check,
  Key,
  Link as LinkIcon,
  Play,
  Plus,
  Save,
  Trash2,
  Users,
} from "lucide-react";
import { useState } from "react";

type TabType = "flows" | "prompts" | "biztel" | "users";

interface OperationFlow {
  id: string;
  name: string;
  description: string;
  isActive: boolean;
  steps: FlowStep[];
  classificationCriteria: string;
}

interface FlowStep {
  id: string;
  name: string;
  description: string;
}

interface AnalysisPrompt {
  id: string;
  name: string;
  description: string;
  content: string;
}

const mockFlows: OperationFlow[] = [
  {
    id: "1",
    name: "標準サポートフロー",
    description: "一般的な問い合わせ対応用",
    isActive: true,
    classificationCriteria: "製品の使い方、設定方法、トラブルシューティングに関する問い合わせ",
    steps: [
      { id: "1", name: "挨拶", description: "会社名と担当者名を名乗る" },
      { id: "2", name: "要件確認", description: "お問い合わせ内容を確認" },
      { id: "3", name: "本人確認", description: "必要に応じて契約情報を確認" },
      { id: "4", name: "対応", description: "問い合わせ内容に対応" },
      { id: "5", name: "クロージング", description: "他に質問がないか確認し終話" },
    ],
  },
  {
    id: "2",
    name: "クレーム対応フロー",
    description: "クレーム・苦情対応用",
    isActive: true,
    classificationCriteria: "不満、苦情、クレームを含む問い合わせ",
    steps: [
      { id: "1", name: "挨拶・謝罪", description: "まず謝罪から始める" },
      { id: "2", name: "傾聴", description: "お客様の話を最後まで聞く" },
      { id: "3", name: "共感", description: "お客様の気持ちに寄り添う" },
      { id: "4", name: "解決策提示", description: "具体的な解決策を提示" },
      { id: "5", name: "再発防止", description: "今後の対応を説明" },
    ],
  },
  {
    id: "3",
    name: "契約手続きフロー",
    description: "新規契約・変更手続き用",
    isActive: false,
    classificationCriteria: "契約、申込、プラン変更、解約に関する問い合わせ",
    steps: [
      { id: "1", name: "挨拶", description: "会社名と担当者名を名乗る" },
      { id: "2", name: "本人確認", description: "契約者情報を確認" },
      { id: "3", name: "内容確認", description: "手続き内容を確認" },
      { id: "4", name: "手続き実施", description: "システムで手続きを実施" },
      { id: "5", name: "完了確認", description: "手続き完了を伝える" },
    ],
  },
];

const mockPrompts: AnalysisPrompt[] = [
  {
    id: "1",
    name: "品質スコア評価",
    description: "通話の品質を0-100で評価",
    content: `以下の観点で通話品質を0-100のスコアで評価してください：

1. 挨拶・名乗り (10点)
2. 傾聴姿勢 (20点)
3. 説明のわかりやすさ (25点)
4. 問題解決力 (25点)
5. クロージング (10点)
6. 言葉遣い・敬語 (10点)

各項目の評価理由と、総合スコアを出力してください。`,
  },
  {
    id: "2",
    name: "通話要約",
    description: "通話内容を簡潔に要約",
    content: `通話内容を以下の形式で要約してください：

【問い合わせ内容】
お客様が何について問い合わせたか

【対応内容】
オペレーターがどう対応したか

【結果】
問題が解決したかどうか

【特記事項】
フォローアップが必要な事項など`,
  },
  {
    id: "3",
    name: "感情分析",
    description: "通話中の感情変化を分析",
    content: `通話中の顧客とオペレーターの感情変化を分析してください：

1. 通話開始時の顧客感情
2. 通話中の感情変化ポイント
3. 通話終了時の顧客感情
4. オペレーターの対応が感情に与えた影響`,
  },
];

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<TabType>("flows");
  const [selectedFlowId, setSelectedFlowId] = useState<string>("1");
  const [selectedPromptId, setSelectedPromptId] = useState<string>("1");

  const selectedFlow = mockFlows.find((f) => f.id === selectedFlowId);
  const selectedPrompt = mockPrompts.find((p) => p.id === selectedPromptId);

  const tabs: { id: TabType; label: string }[] = [
    { id: "flows", label: "オペレーションフロー" },
    { id: "prompts", label: "分析プロンプト" },
    { id: "biztel", label: "Biztel API" },
    { id: "users", label: "ユーザー管理" },
  ];

  return (
    <div className="flex flex-col gap-6 p-8 h-full">
      {/* Header */}
      <div className="flex flex-col gap-1">
        <h1 className="text-[28px] font-bold text-[var(--text-primary)]">
          設定
        </h1>
        <p className="text-sm text-[var(--text-secondary)]">
          分析設定とAPI連携の管理
        </p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-[var(--border)]">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={clsx(
              "px-5 h-11 text-sm font-medium transition-colors",
              activeTab === tab.id
                ? "text-[var(--accent-primary)] border-b-2 border-[var(--accent-primary)]"
                : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="flex-1 min-h-0">
        {activeTab === "flows" && (
          <div className="flex gap-6 h-full">
            {/* Flow List */}
            <div className="w-[360px] flex flex-col rounded-[var(--radius-lg)] bg-[var(--bg-card)] border border-[var(--border)] overflow-hidden">
              <div className="flex items-center justify-between px-5 py-4 border-b border-[var(--border)]">
                <h2 className="text-base font-semibold text-[var(--text-primary)]">
                  フロー一覧
                </h2>
                <Button variant="primary" icon={Plus} className="h-8 text-sm">
                  新規
                </Button>
              </div>
              <div className="flex-1 overflow-auto">
                {mockFlows.map((flow, index) => (
                  <button
                    key={flow.id}
                    onClick={() => setSelectedFlowId(flow.id)}
                    className={clsx(
                      "w-full flex items-center justify-between px-5 h-14",
                      index < mockFlows.length - 1 &&
                        "border-b border-[var(--border-light)]",
                      selectedFlowId === flow.id
                        ? "bg-[var(--accent-primary-light)]"
                        : "hover:bg-[var(--bg-muted)]"
                    )}
                  >
                    <div className="flex flex-col items-start gap-0.5">
                      <span className="text-sm font-medium text-[var(--text-primary)]">
                        {flow.name}
                      </span>
                      <span className="text-xs text-[var(--text-muted)]">
                        {flow.description}
                      </span>
                    </div>
                    {flow.isActive && <Badge variant="success">有効</Badge>}
                  </button>
                ))}
              </div>
            </div>

            {/* Flow Editor */}
            {selectedFlow && (
              <div className="flex-1 flex flex-col rounded-[var(--radius-lg)] bg-[var(--bg-card)] border border-[var(--border)] overflow-hidden">
                <div className="flex items-center justify-between px-5 py-4 border-b border-[var(--border)]">
                  <h2 className="text-base font-semibold text-[var(--text-primary)]">
                    {selectedFlow.name}
                  </h2>
                  <div className="flex items-center gap-3">
                    <Button variant="secondary" icon={Trash2} className="h-8 text-sm">
                      削除
                    </Button>
                    <Button variant="primary" icon={Save} className="h-8 text-sm">
                      保存
                    </Button>
                  </div>
                </div>
                <div className="flex-1 overflow-auto p-6">
                  <div className="flex flex-col gap-5">
                    <InputField
                      label="フロー名"
                      defaultValue={selectedFlow.name}
                    />
                    <div className="flex flex-col gap-1.5">
                      <label className="text-sm font-medium text-[var(--text-primary)]">
                        分類条件
                      </label>
                      <textarea
                        className="h-24 p-3 rounded-[var(--radius-md)] bg-[var(--bg-card)] border border-[var(--border)] text-sm resize-none focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)]"
                        defaultValue={selectedFlow.classificationCriteria}
                        placeholder="このフローが適用される条件を記述..."
                      />
                    </div>
                    <div className="flex flex-col gap-3">
                      <label className="text-sm font-medium text-[var(--text-primary)]">
                        フローステップ
                      </label>
                      <div className="flex flex-col gap-2">
                        {selectedFlow.steps.map((step, index) => (
                          <div key={step.id}>
                            <div className="flex items-center gap-3 p-3 rounded-[var(--radius-md)] bg-[var(--bg-muted)] border border-[var(--border)]">
                              <div className="w-8 h-8 rounded-full bg-[var(--accent-primary)] text-white flex items-center justify-center text-sm font-semibold">
                                {index + 1}
                              </div>
                              <div className="flex-1">
                                <p className="text-sm font-medium text-[var(--text-primary)]">
                                  {step.name}
                                </p>
                                <p className="text-xs text-[var(--text-muted)]">
                                  {step.description}
                                </p>
                              </div>
                            </div>
                            {index < selectedFlow.steps.length - 1 && (
                              <div className="flex justify-center py-1">
                                <ArrowDown className="w-4 h-4 text-[var(--text-muted)]" />
                              </div>
                            )}
                          </div>
                        ))}
                        <button className="flex items-center justify-center gap-2 h-10 rounded-[var(--radius-md)] border-2 border-dashed border-[var(--border)] text-sm text-[var(--text-muted)] hover:border-[var(--accent-primary)] hover:text-[var(--accent-primary)]">
                          <Plus className="w-4 h-4" />
                          ステップを追加
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === "prompts" && (
          <div className="flex gap-6 h-full">
            {/* Prompt List */}
            <div className="w-[320px] flex flex-col rounded-[var(--radius-lg)] bg-[var(--bg-card)] border border-[var(--border)] overflow-hidden">
              <div className="px-5 py-4 border-b border-[var(--border)]">
                <h2 className="text-base font-semibold text-[var(--text-primary)]">
                  プロンプト一覧
                </h2>
              </div>
              <div className="flex-1 overflow-auto">
                {mockPrompts.map((prompt, index) => (
                  <button
                    key={prompt.id}
                    onClick={() => setSelectedPromptId(prompt.id)}
                    className={clsx(
                      "w-full flex items-center justify-between px-5 h-16",
                      index < mockPrompts.length - 1 &&
                        "border-b border-[var(--border-light)]",
                      selectedPromptId === prompt.id
                        ? "bg-[var(--accent-primary-light)]"
                        : "hover:bg-[var(--bg-muted)]"
                    )}
                  >
                    <div className="flex flex-col items-start gap-0.5">
                      <span className="text-sm font-medium text-[var(--text-primary)]">
                        {prompt.name}
                      </span>
                      <span className="text-xs text-[var(--text-muted)]">
                        {prompt.description}
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Prompt Editor */}
            {selectedPrompt && (
              <div className="flex-1 flex flex-col rounded-[var(--radius-lg)] bg-[var(--bg-card)] border border-[var(--border)] overflow-hidden">
                <div className="flex items-center justify-between px-5 py-4 border-b border-[var(--border)]">
                  <h2 className="text-base font-semibold text-[var(--text-primary)]">
                    {selectedPrompt.name}
                  </h2>
                  <div className="flex items-center gap-3">
                    <Button variant="secondary" icon={Play} className="h-8 text-sm">
                      テスト
                    </Button>
                    <Button variant="primary" icon={Save} className="h-8 text-sm">
                      保存
                    </Button>
                  </div>
                </div>
                <div className="flex-1 overflow-auto p-6">
                  <div className="flex flex-col gap-5 h-full">
                    <InputField
                      label="説明"
                      defaultValue={selectedPrompt.description}
                    />
                    <div className="flex flex-col gap-1.5 flex-1">
                      <label className="text-sm font-medium text-[var(--text-primary)]">
                        プロンプト内容
                      </label>
                      <textarea
                        className="flex-1 p-3 rounded-[var(--radius-md)] bg-[var(--bg-card)] border border-[var(--border)] text-sm font-mono resize-none focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)]"
                        defaultValue={selectedPrompt.content}
                      />
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === "biztel" && (
          <div className="flex flex-col gap-6 max-w-2xl">
            <div className="flex flex-col rounded-[var(--radius-lg)] bg-[var(--bg-card)] border border-[var(--border)] overflow-hidden">
              <div className="px-5 py-4 border-b border-[var(--border)]">
                <h2 className="text-base font-semibold text-[var(--text-primary)]">
                  Biztel API 接続設定
                </h2>
              </div>
              <div className="p-6 flex flex-col gap-5">
                <div className="flex items-center gap-3 p-4 rounded-[var(--radius-md)] bg-[var(--status-success-bg)]">
                  <Check className="w-5 h-5 text-[var(--status-success)]" />
                  <span className="text-sm text-[var(--status-success)]">
                    API接続が正常に確立されています
                  </span>
                </div>
                <InputField
                  label="APIホスト"
                  defaultValue="your-biztel-server.biztel.jp"
                  placeholder="your-server.biztel.jp"
                />
                <InputField
                  label="APIトークン"
                  type="password"
                  defaultValue="••••••••••••••••"
                  placeholder="APIトークンを入力"
                />
                <div className="flex items-center gap-3 pt-4">
                  <Button variant="secondary" icon={LinkIcon}>
                    接続テスト
                  </Button>
                  <Button variant="primary" icon={Save}>
                    保存
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "users" && (
          <div className="flex flex-col gap-6">
            <div className="flex flex-col rounded-[var(--radius-lg)] bg-[var(--bg-card)] border border-[var(--border)] overflow-hidden">
              <div className="flex items-center justify-between px-5 py-4 border-b border-[var(--border)]">
                <h2 className="text-base font-semibold text-[var(--text-primary)]">
                  ユーザー一覧
                </h2>
                <Button variant="primary" icon={Plus} className="h-8 text-sm">
                  ユーザーを招待
                </Button>
              </div>
              <div className="flex items-center h-12 px-6 bg-[var(--bg-muted)]">
                <span className="w-[200px] text-[13px] font-semibold text-[var(--text-secondary)]">
                  名前
                </span>
                <span className="w-[240px] text-[13px] font-semibold text-[var(--text-secondary)]">
                  メールアドレス
                </span>
                <span className="w-[120px] text-[13px] font-semibold text-[var(--text-secondary)]">
                  権限
                </span>
                <span className="text-[13px] font-semibold text-[var(--text-secondary)]">
                  &nbsp;
                </span>
              </div>
              {[
                { name: "山田 太郎", email: "yamada@example.com", role: "admin" },
                { name: "鈴木 花子", email: "suzuki@example.com", role: "sv" },
                { name: "佐藤 一郎", email: "sato@example.com", role: "qa" },
                { name: "田中 美咲", email: "tanaka@example.com", role: "operator" },
              ].map((user, index) => (
                <div
                  key={index}
                  className={`flex items-center h-14 px-6 ${
                    index < 3 ? "border-b border-[var(--border-light)]" : ""
                  }`}
                >
                  <span className="w-[200px] text-sm text-[var(--text-primary)]">
                    {user.name}
                  </span>
                  <span className="w-[240px] text-sm text-[var(--text-secondary)]">
                    {user.email}
                  </span>
                  <span className="w-[120px]">
                    <Badge
                      variant={user.role === "admin" ? "warning" : "success"}
                    >
                      {user.role}
                    </Badge>
                  </span>
                  <button className="text-[13px] font-medium text-[var(--accent-primary)] hover:underline">
                    編集
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
