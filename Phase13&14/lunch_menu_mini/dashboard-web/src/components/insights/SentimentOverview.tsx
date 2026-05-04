"use client";

import {
  BarChart,
  Bar,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
  ResponsiveContainer,
} from "recharts";
import { Smile, RefreshCcw, Loader2 } from "lucide-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useSentimentTop } from "@/lib/queries";
import { apiFetchNLP } from "@/lib/api";

export default function SentimentOverview() {
  const { data, isLoading, error } = useSentimentTop(10);
  const queryClient = useQueryClient();

  const refresh = useMutation({
    mutationFn: () =>
      apiFetchNLP<unknown>("/nlp/sentiment/refresh", { method: "POST" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["nlp", "sentiment"] });
    },
  });

  const chartData = (data ?? []).map((s) => ({
    name: s.name || s.restaurant_id,
    score: Math.round((s.score || 0) * 100) / 100,
    reviews: s.review_count,
  }));

  return (
    <div className="bg-surface-1 border border-outline/15 rounded-sm p-5 h-full">
      <div className="flex items-center gap-2 mb-1">
        <Smile size={16} className="text-success" />
        <h3 className="text-base font-heading font-bold text-text-primary uppercase tracking-[0.04em]">
          Sentiment Top 10
        </h3>
      </div>
      <p
        className="text-[11px] text-text-tertiary mb-4"
        style={{ fontFamily: "var(--font-ko)" }}
      >
        A1 KcELECTRA — 리뷰 감성 점수 상위 10개
      </p>

      {isLoading && (
        <div className="text-xs text-text-tertiary py-8 text-center">
          분석 결과 로딩 중…
        </div>
      )}

      {!isLoading && error && (
        <div className="text-xs text-error py-6 font-mono">
          /nlp/sentiment/top 호출 실패
        </div>
      )}

      {!isLoading && !error && chartData.length === 0 && (
        <div className="text-center py-8 px-4">
          <Smile size={36} className="mx-auto text-text-tertiary/40 mb-3" />
          <p
            className="text-sm text-text-secondary mb-1"
            style={{ fontFamily: "var(--font-ko)" }}
          >
            아직 감성 데이터가 없습니다
          </p>
          <p
            className="text-[11px] text-text-tertiary mb-4"
            style={{ fontFamily: "var(--font-ko)" }}
          >
            식당 리뷰 → KcELECTRA 분석을 실행하면 상위 10개 식당의 감성 점수가
            <br />표시됩니다 (1–2분 소요).
          </p>
          <button
            type="button"
            onClick={() => refresh.mutate()}
            disabled={refresh.isPending}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-[11px] font-bold uppercase tracking-[0.08em] border border-primary/30 text-primary rounded-sm hover:bg-primary/10 disabled:opacity-50"
          >
            {refresh.isPending ? (
              <Loader2 size={13} className="animate-spin" />
            ) : (
              <RefreshCcw size={13} />
            )}
            {refresh.isPending ? "분석 중…" : "감성 분석 실행"}
          </button>
          {refresh.isError && (
            <p className="mt-2 text-[10px] text-error font-mono">
              {String(refresh.error)}
            </p>
          )}
          {refresh.isSuccess && !refresh.isPending && (
            <p className="mt-2 text-[10px] text-success font-mono">
              ✓ 분석 요청 완료 — 잠시 후 데이터가 갱신됩니다
            </p>
          )}
        </div>
      )}

      {chartData.length > 0 && (
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={chartData} layout="vertical" margin={{ left: 10 }}>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="var(--color-outline)"
              strokeOpacity={0.25}
            />
            <XAxis
              type="number"
              domain={[-1, 1]}
              tick={{ fill: "var(--color-text-secondary)", fontSize: 11 }}
            />
            <YAxis
              type="category"
              dataKey="name"
              tick={{ fill: "var(--color-text-secondary)", fontSize: 11 }}
              width={90}
            />
            <Tooltip
              contentStyle={{
                background: "var(--color-surface-2)",
                border: "1px solid var(--color-outline)",
                borderRadius: 6,
                fontSize: 12,
              }}
              formatter={(v: unknown, _k: unknown, entry: unknown) => {
                const val = typeof v === "number" ? v : Number(v) || 0;
                const pl = (entry as { payload?: { reviews?: number } })?.payload;
                return [
                  val.toFixed(2),
                  `score · ${pl?.reviews ?? 0} reviews`,
                ];
              }}
            />
            <Bar dataKey="score" radius={[0, 6, 6, 0]}>
              {chartData.map((d, i) => (
                <Cell
                  key={i}
                  fill={
                    d.score >= 0.3
                      ? "var(--color-success)"
                      : d.score >= -0.1
                      ? "var(--color-tertiary)"
                      : "var(--color-error)"
                  }
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
