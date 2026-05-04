"use client";

import type { Restaurant } from "@/lib/types";
import { CATEGORY_COLORS } from "@/lib/mock";
import { useSentimentTop } from "@/lib/queries";

export default function TodaysTop5({
  items,
}: {
  items: (Restaurant & { score: number })[];
}) {
  // Overlay sentiment score from /nlp/sentiment/top if available
  const { data: top } = useSentimentTop(50);
  const sentimentMap = new Map<string, number>();
  (top ?? []).forEach((t) => sentimentMap.set(String(t.restaurant_id), t.score));

  return (
    <div className="bento-card">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-base font-heading font-bold text-text-primary uppercase tracking-[0.04em]">
            Today&apos;s Top 5
          </h3>
          <p className="text-[11px] text-text-tertiary uppercase tracking-[0.1em] mt-0.5">
            Composite Score Ranking
          </p>
          <p
            className="text-[10px] text-text-tertiary mt-0.5"
            style={{ fontFamily: "var(--font-ko)" }}
          >
            오늘의 추천 TOP 5
          </p>
        </div>
      </div>
      <div className="space-y-2">
        {items.slice(0, 5).map((r, i) => {
          const sentiment = sentimentMap.get(String(r.id));
          const categoryColor = CATEGORY_COLORS[r.category] || "#888";
          return (
            <div
              key={r.id}
              className="flex items-center gap-4 p-3 bg-surface-2 border border-outline/10 rounded-sm hover:border-primary/30 transition-colors"
            >
              <div
                className="w-8 h-8 flex items-center justify-center font-heading font-bold text-xs text-white rounded-sm"
                style={{ background: categoryColor }}
              >
                {i + 1}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-semibold text-text-primary truncate">
                  {r.name}
                </div>
                <div className="text-[11px] text-text-tertiary font-mono">
                  {r.category} · {r.distance}m · ₩{r.price.toLocaleString()}
                  {sentiment != null && (
                    <>
                      {" · "}
                      <span
                        className={
                          sentiment >= 0.3
                            ? "text-success"
                            : sentiment >= -0.1
                            ? "text-warning"
                            : "text-error"
                        }
                      >
                        {sentiment >= 0 ? "+" : ""}
                        {sentiment.toFixed(2)}
                      </span>
                    </>
                  )}
                </div>
              </div>
              <div className="text-right">
                <div
                  className="text-lg font-heading font-bold leading-none"
                  style={{
                    color:
                      r.score >= 70
                        ? "var(--color-success)"
                        : r.score >= 40
                        ? "var(--color-tertiary)"
                        : "var(--color-error)",
                  }}
                >
                  {r.score}
                </div>
                <div className="text-[9px] text-text-tertiary uppercase">Score</div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
