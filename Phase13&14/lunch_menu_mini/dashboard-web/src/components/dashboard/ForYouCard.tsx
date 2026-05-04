"use client";

import { Sparkles, AlertCircle, Loader2 } from "lucide-react";
import { useV2Recommendations } from "@/lib/queries";

/**
 * ML-backed personal recommendations from the Phase 6 E1 Embedding CF
 * endpoint (`/nlp/v2/recommend`).
 *
 * Graceful degradation:
 *  - 503 / network error → show an "AI 추천 준비 중" card
 *  - empty array → "아직 추천할 메뉴가 없어요"
 *  - backend="dummy" badge when no trained weights
 */
export default function ForYouCard({ userId }: { userId: number | string }) {
  const { data, isLoading, error } = useV2Recommendations(userId, 5);

  return (
    <div className="bento-card">
      <div className="flex items-center justify-between mb-4">
        <div>
          <div className="flex items-center gap-2">
            <Sparkles size={16} className="text-tertiary" />
            <h3 className="text-base font-heading font-bold text-text-primary uppercase tracking-[0.04em]">
              For You
            </h3>
            {data?.backend && (
              <span
                className={`text-[9px] font-mono font-semibold px-2 py-0.5 border rounded-sm ${
                  data.backend === "embedding_cf"
                    ? "text-success border-success/40"
                    : "text-warning border-warning/40"
                }`}
              >
                {data.backend}
              </span>
            )}
          </div>
          <p className="text-[11px] text-text-tertiary uppercase tracking-[0.1em] mt-0.5">
            ML Personalized Recommendations
          </p>
          <p
            className="text-[10px] text-text-tertiary mt-0.5"
            style={{ fontFamily: "var(--font-ko)" }}
          >
            유사 사용자 기반 개인화 추천 (E1 Embedding CF)
          </p>
        </div>
      </div>

      {isLoading && (
        <div className="flex items-center gap-2 text-sm text-text-tertiary py-6">
          <Loader2 size={14} className="animate-spin" />
          AI가 유사 취향 사용자를 찾는 중…
        </div>
      )}

      {!isLoading && error && (
        <div className="flex items-start gap-2 text-[11px] text-text-tertiary font-mono py-4">
          <AlertCircle size={12} className="flex-shrink-0 mt-0.5" />
          <div>
            /nlp/v2/recommend 호출 실패. NLP API(8001) 실행 중인지 확인하세요.
          </div>
        </div>
      )}

      {!isLoading && !error && data && data.recommendations.length === 0 && (
        <div
          className="text-xs text-text-tertiary py-6 text-center"
          style={{ fontFamily: "var(--font-ko)" }}
        >
          아직 추천할 메뉴가 없어요.
          <br />
          식사 이력을 몇 건 더 기록해보세요.
        </div>
      )}

      {!isLoading && data && data.recommendations.length > 0 && (
        <div className="space-y-2">
          {data.recommendations.map((rec, i) => (
            <div
              key={`${rec.menu}-${i}`}
              className="flex items-center gap-3 p-3 bg-surface-2 border border-outline/10 rounded-sm hover:border-tertiary/40 transition-colors"
            >
              <div className="w-7 h-7 flex items-center justify-center bg-tertiary/15 border border-tertiary/30 rounded-sm text-tertiary font-heading font-bold text-xs">
                {i + 1}
              </div>
              <div className="flex-1 min-w-0">
                <div
                  className="text-sm font-bold text-text-primary truncate"
                  style={{ fontFamily: "var(--font-ko)" }}
                >
                  {rec.menu}
                </div>
                {rec.reason && (
                  <div
                    className="text-[10px] text-text-tertiary truncate"
                    style={{ fontFamily: "var(--font-ko)" }}
                  >
                    {rec.reason}
                  </div>
                )}
              </div>
              <div className="text-right flex-shrink-0">
                <div className="text-sm font-heading font-bold text-tertiary font-mono">
                  {rec.score.toFixed(2)}
                </div>
                <div className="text-[9px] text-text-tertiary uppercase tracking-wider">
                  {rec.similar_user_count} users
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
