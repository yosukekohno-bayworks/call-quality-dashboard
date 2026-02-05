"use client";

import { clsx } from "clsx";
import { CheckCircle, Loader2, XCircle } from "lucide-react";

export type UploadStatus = "idle" | "uploading" | "success" | "error";

interface UploadProgressProps {
  status: UploadStatus;
  progress: number;
  fileName?: string;
  error?: string;
}

export function UploadProgress({
  status,
  progress,
  fileName,
  error,
}: UploadProgressProps) {
  if (status === "idle") return null;

  return (
    <div className="flex flex-col gap-3 p-4 rounded-[var(--radius-md)] bg-[var(--bg-card)] border border-[var(--border)]">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {status === "uploading" && (
            <Loader2 className="w-4 h-4 text-[var(--accent-primary)] animate-spin" />
          )}
          {status === "success" && (
            <CheckCircle className="w-4 h-4 text-[var(--status-success)]" />
          )}
          {status === "error" && (
            <XCircle className="w-4 h-4 text-[var(--status-error)]" />
          )}
          <span className="text-sm font-medium text-[var(--text-primary)]">
            {status === "uploading" && "アップロード中..."}
            {status === "success" && "アップロード完了"}
            {status === "error" && "アップロード失敗"}
          </span>
        </div>
        {status === "uploading" && (
          <span className="text-sm text-[var(--text-muted)]">{progress}%</span>
        )}
      </div>

      {fileName && (
        <p className="text-xs text-[var(--text-muted)]">{fileName}</p>
      )}

      {status === "uploading" && (
        <div className="h-2 rounded-full bg-[var(--bg-muted)] overflow-hidden">
          <div
            className={clsx(
              "h-full rounded-full transition-all duration-300",
              "bg-[var(--accent-primary)]"
            )}
            style={{ width: `${progress}%` }}
          />
        </div>
      )}

      {status === "error" && error && (
        <p className="text-xs text-[var(--status-error)]">{error}</p>
      )}
    </div>
  );
}
