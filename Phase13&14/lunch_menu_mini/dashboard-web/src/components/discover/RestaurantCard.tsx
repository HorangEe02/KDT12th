"use client";

import { memo } from "react";
import type { Restaurant, SentimentOut } from "@/lib/types";
import { CATEGORY_COLORS } from "@/lib/mock";
import SentimentBadge from "./SentimentBadge";

interface Props {
  r: Restaurant;
  score: number;
  rank: number;
  selected: boolean;
  sentiment: SentimentOut | null;
  onClick: () => void;
}

function RestaurantCardImpl({
  r,
  score,
  rank,
  selected,
  sentiment,
  onClick,
}: Props) {
  const categoryColor = CATEGORY_COLORS[r.category] || "#888";
  const scoreColor =
    score >= 70
      ? "var(--color-success)"
      : score >= 40
      ? "var(--color-tertiary)"
      : "var(--color-error)";

  return (
    <button
      type="button"
      onClick={onClick}
      className={`w-full text-left flex items-center gap-4 p-4 border rounded-sm transition-all ${
        selected
          ? "bg-primary/5 border-primary/40"
          : "bg-surface-1 border-outline/15 hover:border-outline/35 hover:bg-surface-2"
      }`}
    >
      {/* Rank chip */}
      <div
        className="w-9 h-9 flex items-center justify-center font-heading font-bold text-sm text-white rounded-sm flex-shrink-0"
        style={{ background: categoryColor }}
      >
        {rank}
      </div>

      {/* Body */}
      <div className="flex-1 min-w-0">
        <div className="flex items-baseline gap-2">
          <span className="text-sm font-bold text-text-primary truncate">
            {r.name}
          </span>
          <span className="text-[10px] font-mono text-text-tertiary">
            ★ {r.rating.toFixed(1)}
          </span>
        </div>
        <div className="text-[11px] text-text-tertiary font-mono mt-0.5">
          {r.category} · {r.distance}m · ₩{r.price.toLocaleString()}
        </div>
        <div className="mt-1.5">
          <SentimentBadge sentiment={sentiment} compact />
        </div>
      </div>

      {/* Score */}
      <div className="text-right flex-shrink-0">
        <div
          className="text-2xl font-heading font-bold leading-none"
          style={{ color: scoreColor }}
        >
          {score}
        </div>
        <div className="text-[9px] uppercase text-text-tertiary tracking-wider mt-0.5">
          Score
        </div>
      </div>
    </button>
  );
}

/**
 * Memoized — only re-renders when the composite shape actually changes.
 * Prevents streaming/sentiment-loading updates from thrashing the whole list.
 */
export default memo(RestaurantCardImpl, (prev, next) => {
  return (
    prev.r.id === next.r.id &&
    prev.score === next.score &&
    prev.rank === next.rank &&
    prev.selected === next.selected &&
    prev.sentiment === next.sentiment
  );
});
