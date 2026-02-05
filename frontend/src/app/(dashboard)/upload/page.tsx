"use client";

import { Button, FileDropzone, UploadProgress } from "@/components/ui";
import type { UploadStatus } from "@/components/ui";
import { apiClient } from "@/lib/api-client";
import { Upload } from "lucide-react";
import { useCallback, useState } from "react";

interface UploadHistory {
  id: string;
  uploadedAt: string;
  fileName: string;
  recordCount: number;
}

const mockHistory: UploadHistory[] = [
  {
    id: "1",
    uploadedAt: "2024/01/20 15:30",
    fileName: "calls_20240120.zip",
    recordCount: 48,
  },
  {
    id: "2",
    uploadedAt: "2024/01/19 14:15",
    fileName: "calls_20240119.zip",
    recordCount: 52,
  },
  {
    id: "3",
    uploadedAt: "2024/01/18 16:45",
    fileName: "calls_20240118.zip",
    recordCount: 45,
  },
];

interface ValidationErrors {
  audio?: string;
  csv?: string;
  general?: string;
}

export default function UploadPage() {
  const [audioFiles, setAudioFiles] = useState<File[]>([]);
  const [csvFiles, setCsvFiles] = useState<File[]>([]);
  const [uploadStatus, setUploadStatus] = useState<UploadStatus>("idle");
  const [uploadProgress, setUploadProgress] = useState(0);
  const [errors, setErrors] = useState<ValidationErrors>({});
  const [history] = useState<UploadHistory[]>(mockHistory);

  const validateFiles = useCallback((): boolean => {
    const newErrors: ValidationErrors = {};

    if (audioFiles.length === 0) {
      newErrors.audio = "音声ファイルを選択してください";
    }

    if (csvFiles.length === 0) {
      newErrors.csv = "CSVファイルを選択してください";
    }

    if (csvFiles.length > 1) {
      newErrors.csv = "CSVファイルは1つのみ選択できます";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [audioFiles, csvFiles]);

  const handleUpload = useCallback(async () => {
    if (!validateFiles()) return;

    setUploadStatus("uploading");
    setUploadProgress(0);
    setErrors({});

    try {
      const formData = new FormData();

      audioFiles.forEach((file) => {
        formData.append("audio_files", file);
      });

      if (csvFiles[0]) {
        formData.append("csv_file", csvFiles[0]);
      }

      // シミュレーション用の進捗更新
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return prev;
          }
          return prev + 10;
        });
      }, 500);

      await apiClient.upload("/api/calls/upload", formData);

      clearInterval(progressInterval);
      setUploadProgress(100);
      setUploadStatus("success");

      // 成功後、フォームをリセット
      setTimeout(() => {
        setAudioFiles([]);
        setCsvFiles([]);
        setUploadStatus("idle");
        setUploadProgress(0);
      }, 2000);
    } catch (error) {
      setUploadStatus("error");
      setErrors({
        general:
          error instanceof Error
            ? error.message
            : "アップロード中にエラーが発生しました",
      });
    }
  }, [audioFiles, csvFiles, validateFiles]);

  const handleCancel = useCallback(() => {
    setAudioFiles([]);
    setCsvFiles([]);
    setErrors({});
    setUploadStatus("idle");
    setUploadProgress(0);
  }, []);

  const isUploading = uploadStatus === "uploading";

  return (
    <div className="flex flex-col gap-6 p-8 h-full">
      {/* Header */}
      <div className="flex flex-col gap-1">
        <h1 className="text-[28px] font-bold text-[var(--text-primary)]">
          データアップロード
        </h1>
        <p className="text-sm text-[var(--text-secondary)]">
          音声ファイルとメタデータをアップロードして分析を開始
        </p>
      </div>

      {/* Upload Areas */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Audio Upload */}
        <div className="flex flex-col gap-4 p-6 rounded-[var(--radius-lg)] bg-[var(--bg-card)] border border-[var(--border)]">
          <h2 className="text-base font-semibold text-[var(--text-primary)]">
            音声ファイル
          </h2>
          <FileDropzone
            accept=".mp3,.wav,.m4a,audio/mpeg,audio/wav,audio/mp4"
            multiple
            maxSize={100}
            onFilesChange={setAudioFiles}
            files={audioFiles}
            type="audio"
            error={errors.audio}
          />
        </div>

        {/* CSV Upload */}
        <div className="flex flex-col gap-4 p-6 rounded-[var(--radius-lg)] bg-[var(--bg-card)] border border-[var(--border)]">
          <h2 className="text-base font-semibold text-[var(--text-primary)]">
            メタデータ（CSV）
          </h2>
          <FileDropzone
            accept=".csv,text/csv"
            multiple={false}
            maxSize={10}
            onFilesChange={setCsvFiles}
            files={csvFiles}
            type="csv"
            error={errors.csv}
          />
        </div>
      </div>

      {/* Upload Progress */}
      {uploadStatus !== "idle" && (
        <UploadProgress
          status={uploadStatus}
          progress={uploadProgress}
          fileName={
            audioFiles.length > 0
              ? `${audioFiles.length}件のファイル`
              : undefined
          }
          error={errors.general}
        />
      )}

      {/* Action Buttons */}
      <div className="flex justify-end gap-3">
        <Button
          variant="secondary"
          onClick={handleCancel}
          disabled={isUploading}
        >
          キャンセル
        </Button>
        <Button
          variant="primary"
          icon={Upload}
          onClick={handleUpload}
          disabled={isUploading || (audioFiles.length === 0 && csvFiles.length === 0)}
        >
          {isUploading ? "アップロード中..." : "アップロード開始"}
        </Button>
      </div>

      {/* Upload History */}
      <div className="flex-1 flex flex-col rounded-[var(--radius-lg)] bg-[var(--bg-card)] border border-[var(--border)] overflow-hidden">
        <div className="px-5 py-4 border-b border-[var(--border)]">
          <h2 className="text-base font-semibold text-[var(--text-primary)]">
            アップロード履歴
          </h2>
        </div>

        {/* Table Header */}
        <div className="flex items-center h-11 px-5 bg-[var(--bg-muted)]">
          <span className="w-[180px] text-[13px] font-semibold text-[var(--text-secondary)]">
            アップロード日時
          </span>
          <span className="flex-1 text-[13px] font-semibold text-[var(--text-secondary)]">
            ファイル名
          </span>
          <span className="w-20 text-[13px] font-semibold text-[var(--text-secondary)]">
            件数
          </span>
        </div>

        {/* Table Body */}
        <div className="flex-1 overflow-auto">
          {history.map((item, index) => (
            <div
              key={item.id}
              className={`flex items-center h-[52px] px-5 ${
                index < history.length - 1
                  ? "border-b border-[var(--border-light)]"
                  : ""
              }`}
            >
              <span className="w-[180px] text-[13px] font-mono text-[var(--text-primary)]">
                {item.uploadedAt}
              </span>
              <span className="flex-1 text-sm text-[var(--text-primary)]">
                {item.fileName}
              </span>
              <span className="w-20 text-[13px] font-mono text-[var(--text-primary)]">
                {item.recordCount}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
