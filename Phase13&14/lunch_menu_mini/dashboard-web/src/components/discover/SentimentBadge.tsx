"use client";

import type { SentimentOut } from "@/lib/types";

/**
 * Compact / full sentiment indicator.
 * Ported from legacy jsx (Mini Step 5 Discovery card).
 */
export default function SentimentBadge({
  sentiment,
  compact = false,
}: {
  sentiment: SentimentOut | null | undefined;
  compact?: boolean;
}) {
  if (!sentiment || sentiment.review_count < 1 || sentiment.score == null) {
    return (
      <span
        title="리뷰 데이터 없음"
        className="inline-flex items-center px-2 py-0.5 rounded-full border border-dashed border-outline/30 text-[10px] text-text-tertiary"
      >
        · AI 분석 대기 ·
      </span>
    );
  }

  const pos = Math.round((sentiment.pos_ratio || 0) * 100);
  const neu = Math.round((sentiment.neu_ratio || 0) * 100);
  const neg = Math.round((sentiment.neg_ratio || 0) * 100);

  const tone =
    sentiment.score >= 0.3
      ? "var(--color-success)"
      : sentiment.score >= -0.1
      ? "var(--color-warning)"
      : "var(--color-error)";

  if (compact) {
    return (
      <span
        title={`리뷰 ${sentiment.review_count}건 기반 · score ${sentiment.score.toFixed(2)}`}
        className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full border font-mono text-[10px] font-semibold"
        style={{
          color: tone,
          borderColor: `color-mix(in srgb, ${tone} 35%, transparent)`,
          background: `color-mix(in srgb, ${tone} 10%, transparent)`,
        }}
      >
        <span>😊 {pos}</span>
        <span className="opacity-50">/</span>
        <span>😐 {neu}</span>
        <span className="opacity-50">/</span>
        <span>😞 {neg}</span>
      </span>
    );
  }

  return (
    <div
      title={`리뷰 ${sentiment.review_count}건 기반`}
      className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold"
      style={{
        color: tone,
        background: `color-mix(in srgb, ${tone} 12%, transparent)`,
      }}
    >
      <span>😊 {pos}%</span>
      <span className="opacity-40">|</span>
      <span>😐 {neu}%</span>
      <span className="opacity-40">|</span>
      <span>😞 {neg}%</span>
    </div>
  );
}
