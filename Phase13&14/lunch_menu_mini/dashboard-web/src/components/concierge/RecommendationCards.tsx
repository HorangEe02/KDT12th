"use client";

import type { ChatRecommendation } from "@/lib/types";
import { CATEGORY_COLORS } from "@/lib/mock";

export default function RecommendationCards({
  items,
}: {
  items: ChatRecommendation[];
}) {
  if (!items.length) return null;
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
      {items.slice(0, 6).map((rec, i) => {
        const color =
          (rec.category && CATEGORY_COLORS[rec.category]) || "var(--color-primary)";
        return (
          <div
            key={`${rec.name}-${i}`}
            className="bg-surface-2 border border-outline/15 rounded-sm p-3 hover:border-primary/30 transition-colors"
          >
            <div className="flex items-center gap-2 mb-1">
              <span
                className="w-2 h-2 rounded-full"
                style={{ background: color }}
              />
              <div className="text-xs font-bold text-text-primary truncate flex-1">
                {rec.name}
              </div>
            </div>
            {rec.category && (
              <div className="text-[10px] text-text-tertiary font-mono uppercase tracking-wider">
                {rec.category}
              </div>
            )}
            {rec.reason && (
              <div
                className="text-[11px] text-text-secondary mt-1.5 line-clamp-3"
                style={{ fontFamily: "var(--font-ko)" }}
              >
                {rec.reason}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
