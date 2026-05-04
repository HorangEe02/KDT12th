"use client";

import Link from "next/link";
import { MessageSquare, AlertCircle, ArrowRight } from "lucide-react";
import { useChatbotStats } from "@/lib/queries";

function pickNumber(obj: Record<string, unknown>, key: string): number {
  const v = obj[key];
  if (typeof v === "number") return v;
  const n = Number(v);
  return Number.isFinite(n) ? n : 0;
}

export default function RAGStatsCard() {
  const { data, isLoading, error } = useChatbotStats();
  const obj = (data ?? {}) as Record<string, unknown>;

  const totalCalls = pickNumber(obj, "total_calls");
  const avgLatency = pickNumber(obj, "avg_latency_ms");
  const warnings = pickNumber(obj, "hallucination_warnings");
  const sessions = pickNumber(obj, "active_sessions");
  const lastError = typeof obj.last_error === "string" ? obj.last_error : null;

  const cells: { label: string; ko: string; value: string; tone?: string }[] = [
    {
      label: "Total Calls",
      ko: "총 호출",
      value: totalCalls.toLocaleString(),
    },
    {
      label: "Avg Latency",
      ko: "평균 지연",
      value: `${avgLatency}ms`,
      tone:
        avgLatency > 5000
          ? "var(--color-error)"
          : avgLatency > 2000
          ? "var(--color-tertiary)"
          : "var(--color-success)",
    },
    {
      label: "Hallucinations",
      ko: "환각 경고",
      value: String(warnings),
      tone:
        warnings === 0 ? "var(--color-success)" : "var(--color-tertiary)",
    },
    {
      label: "Active Sessions",
      ko: "활성 세션",
      value: String(sessions),
    },
  ];

  return (
    <div className="bg-surface-1 border border-outline/15 rounded-sm p-5 h-full">
      <div className="flex items-center gap-2 mb-1">
        <MessageSquare size={16} className="text-primary" />
        <h3 className="text-base font-heading font-bold text-text-primary uppercase tracking-[0.04em]">
          RAG Concierge Stats
        </h3>
      </div>
      <p
        className="text-[11px] text-text-tertiary mb-4"
        style={{ fontFamily: "var(--font-ko)" }}
      >
        D3 챗봇 · 누적 호출 통계
      </p>

      {isLoading && (
        <div className="text-xs text-text-tertiary py-4">로딩 중…</div>
      )}

      {!isLoading && error && (
        <div className="text-xs text-error font-mono">
          /nlp/chatbot/stats 호출 실패
        </div>
      )}

      {!isLoading && !error && (
        <>
          <div className="grid grid-cols-2 gap-2">
            {cells.map((c) => (
              <div
                key={c.label}
                className="bg-surface-2 border border-outline/10 rounded-sm p-3"
                style={
                  c.tone
                    ? { borderLeft: `2px solid ${c.tone}` }
                    : undefined
                }
              >
                <div className="text-[10px] text-text-tertiary uppercase tracking-[0.08em] font-bold">
                  {c.label}
                </div>
                <div
                  className="text-[9px] text-text-tertiary"
                  style={{ fontFamily: "var(--font-ko)" }}
                >
                  {c.ko}
                </div>
                <div className="text-xl font-heading font-bold text-text-primary font-mono mt-1">
                  {c.value}
                </div>
              </div>
            ))}
          </div>

          {lastError && (
            <div className="mt-3 flex items-start gap-2 text-[10px] text-error font-mono p-2 bg-error/10 border border-error/25 rounded-sm">
              <AlertCircle size={11} className="flex-shrink-0 mt-0.5" />
              <div>
                <div className="font-bold uppercase tracking-wider">
                  Last error
                </div>
                <div className="break-all mt-0.5">{lastError}</div>
              </div>
            </div>
          )}

          {totalCalls === 0 && (
            <div className="mt-3 p-3 border border-dashed border-outline/30 rounded-sm">
              <p
                className="text-[11px] text-text-secondary mb-2"
                style={{ fontFamily: "var(--font-ko)" }}
              >
                아직 챗봇 사용 이력이 없습니다. AI 상담 페이지에서 첫 질문을 시작해 보세요.
              </p>
              <Link
                href="/concierge"
                className="inline-flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-[0.08em] text-primary hover:underline"
              >
                Concierge 열기
                <ArrowRight size={12} />
              </Link>
            </div>
          )}
        </>
      )}
    </div>
  );
}
