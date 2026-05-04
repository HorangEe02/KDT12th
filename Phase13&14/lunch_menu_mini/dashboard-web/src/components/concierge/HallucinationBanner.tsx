"use client";

import { AlertTriangle, X } from "lucide-react";

export default function HallucinationBanner({
  onDismiss,
}: {
  onDismiss: () => void;
}) {
  return (
    <div className="mb-3 flex items-start gap-3 p-3 border border-warning/40 bg-warning/10 rounded-sm">
      <AlertTriangle size={16} className="text-warning flex-shrink-0 mt-0.5" />
      <div className="flex-1">
        <div className="text-xs font-bold text-warning uppercase tracking-wider">
          Hallucination Warning
        </div>
        <div
          className="text-[11px] text-text-secondary mt-0.5"
          style={{ fontFamily: "var(--font-ko)" }}
        >
          응답에 실제 DB 에 없는 식당이 포함되었을 수 있습니다. AI가 추천한
          식당의 실존 여부를 직접 확인해주세요.
        </div>
      </div>
      <button
        onClick={onDismiss}
        className="text-text-tertiary hover:text-text-primary transition-colors"
        aria-label="Dismiss warning"
      >
        <X size={14} />
      </button>
    </div>
  );
}
