"use client";

import { AlertTriangle, RefreshCw, Loader2, WifiOff } from "lucide-react";
import { useEffect, useState } from "react";
import { cn } from "@/lib/cn";

export type ErrorBannerVariant = "error" | "warming" | "offline";

interface ErrorBannerProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  variant?: ErrorBannerVariant;
  retryAfter?: number; // seconds — used by warming variant for countdown
  className?: string;
}

/**
 * Unified error surface for query failures across the app.
 *
 * - `error`   : plain failure with retry button
 * - `warming` : NLP module warming up (503) — spinner + auto-countdown hint
 * - `offline` : fetch-level network failure
 */
export default function ErrorBanner({
  title,
  message,
  onRetry,
  variant = "error",
  retryAfter,
  className,
}: ErrorBannerProps) {
  const [countdown, setCountdown] = useState(retryAfter ?? 0);

  useEffect(() => {
    if (variant !== "warming" || !retryAfter) return;
    setCountdown(retryAfter);
    const id = setInterval(() => {
      setCountdown((c) => (c > 0 ? c - 1 : 0));
    }, 1000);
    return () => clearInterval(id);
  }, [variant, retryAfter]);

  const palette =
    variant === "warming"
      ? "border-primary/30 bg-primary/5 text-primary"
      : variant === "offline"
      ? "border-warning/40 bg-warning/5 text-warning"
      : "border-error/40 bg-error/5 text-error";

  const Icon =
    variant === "warming"
      ? Loader2
      : variant === "offline"
      ? WifiOff
      : AlertTriangle;

  const defaultTitle =
    variant === "warming"
      ? "AI 모듈 준비 중"
      : variant === "offline"
      ? "네트워크 연결 실패"
      : "데이터 로드 실패";

  const defaultMessage =
    variant === "warming"
      ? "NLP 서비스가 워밍업 중입니다. 잠시 후 자동으로 다시 시도합니다."
      : variant === "offline"
      ? "백엔드에 연결할 수 없습니다. 연결 상태를 확인해주세요."
      : "요청을 완료하지 못했습니다. 다시 시도해주세요.";

  return (
    <div
      role="alert"
      className={cn(
        "flex items-start gap-3 border rounded-sm p-4",
        palette,
        className,
      )}
    >
      <Icon
        size={18}
        className={cn(
          "flex-shrink-0 mt-0.5",
          variant === "warming" && "animate-spin",
        )}
      />
      <div className="flex-1 min-w-0">
        <div className="text-sm font-bold uppercase tracking-[0.04em]">
          {title ?? defaultTitle}
        </div>
        <div
          className="text-xs text-text-secondary mt-0.5"
          style={{ fontFamily: "var(--font-ko)" }}
        >
          {message ?? defaultMessage}
          {variant === "warming" && countdown > 0 && (
            <span className="ml-1 font-mono text-text-tertiary">
              ({countdown}s)
            </span>
          )}
        </div>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-bold uppercase border border-current rounded-sm hover:bg-current/10 transition-colors flex-shrink-0"
        >
          <RefreshCw size={12} />
          재시도
        </button>
      )}
    </div>
  );
}
