"use client";

import { clsx } from "clsx";
import { FileAudio, FileSpreadsheet, Upload, X } from "lucide-react";
import { DragEvent, useCallback, useRef, useState } from "react";

interface FileDropzoneProps {
  accept: string;
  multiple?: boolean;
  maxSize?: number; // MB
  onFilesChange: (files: File[]) => void;
  files: File[];
  type: "audio" | "csv";
  error?: string;
}

export function FileDropzone({
  accept,
  multiple = true,
  maxSize = 100,
  onFilesChange,
  files,
  type,
  error,
}: FileDropzoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateFile = useCallback(
    (file: File): string | null => {
      const maxSizeBytes = maxSize * 1024 * 1024;
      if (file.size > maxSizeBytes) {
        return `ファイルサイズが${maxSize}MBを超えています`;
      }

      const acceptTypes = accept.split(",").map((t) => t.trim());
      const fileExt = `.${file.name.split(".").pop()?.toLowerCase()}`;
      const fileMime = file.type;

      const isValid = acceptTypes.some((acceptType) => {
        if (acceptType.startsWith(".")) {
          return fileExt === acceptType.toLowerCase();
        }
        if (acceptType.endsWith("/*")) {
          return fileMime.startsWith(acceptType.replace("/*", "/"));
        }
        return fileMime === acceptType;
      });

      if (!isValid) {
        return "対応していないファイル形式です";
      }

      return null;
    },
    [accept, maxSize]
  );

  const handleFiles = useCallback(
    (newFiles: FileList | File[]) => {
      const fileArray = Array.from(newFiles);
      const validFiles = fileArray.filter((file) => !validateFile(file));

      if (multiple) {
        onFilesChange([...files, ...validFiles]);
      } else {
        onFilesChange(validFiles.slice(0, 1));
      }
    },
    [files, multiple, onFilesChange, validateFile]
  );

  const handleDragOver = useCallback((e: DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      handleFiles(e.dataTransfer.files);
    },
    [handleFiles]
  );

  const handleClick = useCallback(() => {
    inputRef.current?.click();
  }, []);

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files) {
        handleFiles(e.target.files);
      }
    },
    [handleFiles]
  );

  const removeFile = useCallback(
    (index: number) => {
      const newFiles = files.filter((_, i) => i !== index);
      onFilesChange(newFiles);
    },
    [files, onFilesChange]
  );

  const Icon = type === "audio" ? FileAudio : FileSpreadsheet;

  return (
    <div className="flex flex-col gap-3">
      <div
        onClick={handleClick}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={clsx(
          "flex flex-col items-center justify-center gap-3 h-[200px] rounded-[var(--radius-md)] border-2 border-dashed cursor-pointer transition-colors",
          isDragging
            ? "bg-[var(--accent-primary-light)] border-[var(--accent-primary)]"
            : "bg-[var(--bg-muted)] border-[var(--border)] hover:border-[var(--accent-primary)]",
          error && "border-[var(--status-error)]"
        )}
      >
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          multiple={multiple}
          onChange={handleInputChange}
          className="hidden"
        />

        <div
          className={clsx(
            "w-12 h-12 rounded-full flex items-center justify-center",
            isDragging
              ? "bg-[var(--accent-primary)] text-white"
              : "bg-[var(--bg-card)] text-[var(--text-muted)]"
          )}
        >
          {isDragging ? (
            <Upload className="w-6 h-6" />
          ) : (
            <Icon className="w-6 h-6" />
          )}
        </div>

        <div className="text-center">
          <p className="text-sm font-medium text-[var(--text-primary)]">
            {isDragging
              ? "ここにドロップ"
              : "ドラッグ&ドロップ、またはクリックして選択"}
          </p>
          <p className="text-xs text-[var(--text-muted)] mt-1">
            {type === "audio"
              ? `対応形式: MP3, WAV, M4A（最大${maxSize}MB）`
              : `対応形式: CSV（最大${maxSize}MB）`}
          </p>
        </div>
      </div>

      {error && (
        <p className="text-xs text-[var(--status-error)]">{error}</p>
      )}

      {files.length > 0 && (
        <div className="flex flex-col gap-2">
          {files.map((file, index) => (
            <div
              key={`${file.name}-${index}`}
              className="flex items-center justify-between gap-3 p-3 rounded-[var(--radius-md)] bg-[var(--bg-muted)]"
            >
              <div className="flex items-center gap-2 min-w-0">
                <Icon className="w-4 h-4 text-[var(--text-muted)] shrink-0" />
                <span className="text-sm text-[var(--text-primary)] truncate">
                  {file.name}
                </span>
                <span className="text-xs text-[var(--text-muted)] shrink-0">
                  ({(file.size / 1024 / 1024).toFixed(2)} MB)
                </span>
              </div>
              <button
                type="button"
                onClick={() => removeFile(index)}
                className="p-1 rounded hover:bg-[var(--bg-card)] text-[var(--text-muted)] hover:text-[var(--status-error)] transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
