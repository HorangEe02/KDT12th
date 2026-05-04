"use client";

/**
 * A2 ABSA Radar — 측면별 감성 (taste / service / price / hygiene / ambience).
 *
 * Data source: `/nlp/v2/sentiment/{restaurant_id}` → restaurant_absa 시드.
 * Backend badges:
 *   - "seeded"  : DB 시드 (현재 default)
 *   - "trained" : 학습된 KoELECTRA 가중치 (Phase 16-B 본 학습 시)
 *   - "dummy"   : 폴백 (시드/가중치 모두 없는 경우)
 */
import { useMemo, useState } from "react";
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { Activity, Loader2, AlertCircle } from "lucide-react";
import { useSentimentTop, useV2Sentiment } from "@/lib/queries";

const ASPECT_KO: Record<string, string> = {
  taste: "맛",
  service: "서비스",
  price: "가격",
  hygiene: "위생",
  ambience: "분위기",
};

export default function ABSARadarPanel() {
  const { data: top, isLoading: loadingTop } = useSentimentTop(20);

  // Restaurant selector defaults to the first sentiment-top item
  const [selectedRid, setSelectedRid] = useState<string>("");
  const effectiveRid =
    selectedRid || (top && top.length > 0 ? String(top[0].restaurant_id) : "");

  const {
    data,
    isLoading,
    error,
  } = useV2Sentiment(effectiveRid, !!effectiveRid);

  const chartData = useMemo(() => {
    if (!data) return [];
    return data.aspects.map((a) => ({
      // recharts radar axis label
      aspect: ASPECT_KO[a.aspect] ?? a.aspect,
      // 0–100 scale for visual clarity (score in [-1,1] → [0,100])
      value: Math.round(((a.score + 1) / 2) * 100),
      sentiment: a.sentiment,
      raw: a.score,
      confidence: a.confidence,
    }));
  }, [data]);

  const selectedName =
    top?.find((t) => String(t.restaurant_id) === effectiveRid)?.name ??
    effectiveRid;

  return (
    <div className="bg-surface-1 border border-outline/15 rounded-sm p-5 h-full">
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2">
          <Activity size={16} className="text-tertiary" />
          <h3 className="text-base font-heading font-bold text-text-primary uppercase tracking-[0.04em]">
            ABSA Radar
          </h3>
          {data?.backend && (
            <span
              className={`text-[9px] font-mono font-semibold px-2 py-0.5 border rounded-sm ${
                data.backend === "trained"
                  ? "text-success border-success/40"
                  : data.backend === "seeded"
                    ? "text-tertiary border-tertiary/40"
                    : "text-warning border-warning/40"
              }`}
            >
              {data.backend}
            </span>
          )}
        </div>
        <select
          value={effectiveRid}
          onChange={(e) => setSelectedRid(e.target.value)}
          disabled={loadingTop || !top || top.length === 0}
          className="text-[11px] font-mono bg-surface-2 border border-outline/20 rounded-sm px-2 py-1 text-text-secondary focus:outline-none focus:border-tertiary/50 max-w-[180px]"
        >
          {(top ?? []).map((t) => (
            <option key={t.restaurant_id} value={String(t.restaurant_id)}>
              {t.name || t.restaurant_id}
            </option>
          ))}
        </select>
      </div>
      <p
        className="text-[11px] text-text-tertiary mb-4"
        style={{ fontFamily: "var(--font-ko)" }}
      >
        A2 ABSA · 측면별 감성 — {selectedName || "식당 선택"}
      </p>

      {(isLoading || loadingTop) && (
        <div className="flex items-center gap-2 text-xs text-text-tertiary py-12 justify-center">
          <Loader2 size={14} className="animate-spin" />
          측면별 감성 분석 로딩 중…
        </div>
      )}

      {!isLoading && error && (
        <div className="flex items-start gap-2 text-[11px] text-error font-mono py-6">
          <AlertCircle size={12} className="flex-shrink-0 mt-0.5" />
          <div>/nlp/v2/sentiment 호출 실패</div>
        </div>
      )}

      {!isLoading && !error && chartData.length === 0 && effectiveRid && (
        <div
          className="text-xs text-text-tertiary py-12 text-center"
          style={{ fontFamily: "var(--font-ko)" }}
        >
          이 식당은 아직 측면별 감성 데이터가 없습니다.
          <br />
          <code className="text-[10px]">scripts/seed_absa.py</code> 실행 후
          새로고침하세요.
        </div>
      )}

      {!isLoading && chartData.length > 0 && (
        <>
          <ResponsiveContainer width="100%" height={260}>
            <RadarChart data={chartData} outerRadius="78%">
              <PolarGrid stroke="var(--color-outline)" strokeOpacity={0.3} />
              <PolarAngleAxis
                dataKey="aspect"
                tick={{
                  fill: "var(--color-text-secondary)",
                  fontSize: 12,
                }}
              />
              <PolarRadiusAxis
                domain={[0, 100]}
                tick={{
                  fill: "var(--color-text-tertiary)",
                  fontSize: 9,
                }}
                stroke="var(--color-outline)"
                strokeOpacity={0.4}
                axisLine={false}
              />
              <Radar
                name="감성"
                dataKey="value"
                stroke="var(--color-tertiary)"
                fill="var(--color-tertiary)"
                fillOpacity={0.35}
              />
              <Tooltip
                contentStyle={{
                  background: "var(--color-surface-2)",
                  border: "1px solid var(--color-outline)",
                  borderRadius: 6,
                  fontSize: 12,
                }}
                formatter={(_v: unknown, _k: unknown, entry: unknown) => {
                  const pl = (entry as { payload?: { raw?: number; sentiment?: string; confidence?: number } })
                    ?.payload;
                  const raw = pl?.raw ?? 0;
                  return [
                    `${raw.toFixed(2)} · ${pl?.sentiment ?? "-"} (conf ${(pl?.confidence ?? 0).toFixed(2)})`,
                    "",
                  ];
                }}
              />
            </RadarChart>
          </ResponsiveContainer>

          <div className="grid grid-cols-5 gap-1.5 mt-2">
            {chartData.map((d) => (
              <div
                key={d.aspect}
                className="text-center px-1 py-1.5 rounded-sm border border-outline/10 bg-surface-2"
              >
                <div
                  className="text-[10px] text-text-tertiary uppercase tracking-wider"
                  style={{ fontFamily: "var(--font-ko)" }}
                >
                  {d.aspect}
                </div>
                <div
                  className={`text-xs font-mono font-bold ${
                    d.sentiment === "positive"
                      ? "text-success"
                      : d.sentiment === "negative"
                        ? "text-error"
                        : "text-text-secondary"
                  }`}
                >
                  {d.raw >= 0 ? "+" : ""}
                  {d.raw.toFixed(2)}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
