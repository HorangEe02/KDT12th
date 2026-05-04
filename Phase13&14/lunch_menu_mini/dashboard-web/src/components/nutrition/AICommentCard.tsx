"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Sparkles, RefreshCw, AlertTriangle, Loader2 } from "lucide-react";
import { apiFetchNLP, NLPPendingError } from "@/lib/api";
import { useWeeklyReport } from "@/lib/queries";
import type { WeeklyReportOut } from "@/lib/types";

export default function AICommentCard({ userId }: { userId: string | number }) {
  const uid = String(userId);
  const { data, isLoading, error, refetch } = useWeeklyReport(userId);
  const queryClient = useQueryClient();

  const regenerate = useMutation({
    mutationFn: () =>
      apiFetchNLP<WeeklyReportOut>(
        `/nlp/reports/weekly/${encodeURIComponent(uid)}/regenerate`,
        { method: "POST" }
      ),
    onSuccess: (fresh) => {
      queryClient.setQueryData(["nlp", "reports", "weekly", uid], fresh);
    },
  });

  const isPending = error instanceof NLPPendingError;
  const errMsg =
    error && !isPending
      ? error instanceof Error
        ? error.message
        : String(error)
      : null;

  const busy = isLoading || regenerate.isPending;

  return (
    <div
      className="rounded-sm border border-primary/25 p-5 mb-6 relative overflow-hidden"
      style={{
        background:
          "linear-gradient(135deg, color-mix(in srgb, var(--color-primary) 8%, transparent), var(--color-surface-1))",
      }}
    >
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex items-center gap-2">
          <Sparkles size={18} className="text-primary" />
          <div>
            <div className="text-sm font-heading font-bold text-text-primary uppercase tracking-[0.04em]">
              AI Weekly Comment
            </div>
            <div
              className="text-[10px] text-text-tertiary"
              style={{ fontFamily: "var(--font-ko)" }}
            >
              {data
                ? `${data.week_label || data.week_start} · ${data.generation_method}`
                : "주간 영양 패턴 분석 (NLP D5 NLG)"}
            </div>
          </div>
        </div>
        <button
          onClick={() => {
            regenerate.reset();
            regenerate.mutate();
          }}
          disabled={busy}
          className="flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-bold uppercase bg-surface-1 border border-outline/25 rounded-sm hover:border-primary/40 hover:text-primary transition-colors disabled:opacity-50"
        >
          {busy ? (
            <Loader2 size={12} className="animate-spin" />
          ) : (
            <RefreshCw size={12} />
          )}
          다시 생성
        </button>
      </div>

      <div
        className="text-sm text-text-primary whitespace-pre-wrap leading-relaxed min-h-[48px]"
        style={{ fontFamily: "var(--font-ko)" }}
      >
        {isLoading && (
          <span className="text-text-tertiary">
            ⏳ AI 가 이번 주 영양 데이터를 분석하는 중입니다…
          </span>
        )}
        {!isLoading && isPending && (
          <span className="text-text-tertiary">
            🤖 AI 모듈 준비 중입니다. 잠시 후 다시 시도해주세요.
          </span>
        )}
        {!isLoading && errMsg && (
          <div className="flex items-start gap-2 text-error text-xs">
            <AlertTriangle size={14} className="flex-shrink-0 mt-0.5" />
            <div>
              <div>리포트 로드 실패</div>
              <div className="text-text-tertiary font-mono text-[11px] mt-1">
                {errMsg}
              </div>
              <button
                onClick={() => refetch()}
                className="mt-2 underline text-primary"
              >
                다시 시도
              </button>
            </div>
          </div>
        )}
        {!isLoading && data && data.text}
      </div>

      {data?.generated_at && (
        <div className="text-[10px] text-text-tertiary font-mono mt-3 text-right">
          생성: {data.generated_at}
        </div>
      )}
      {regenerate.isError && (
        <div className="text-[10px] text-error font-mono mt-2">
          재생성 실패: {String(regenerate.error)}
        </div>
      )}
    </div>
  );
}
