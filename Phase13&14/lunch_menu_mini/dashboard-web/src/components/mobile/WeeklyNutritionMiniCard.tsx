"use client";

import Link from "next/link";
import { ChevronRight } from "lucide-react";
import type { WeeklyNutritionDay } from "@/lib/types";

/**
 * 주간 영양 미니 카드 — App Store "위젯"-style 컴팩트 표시.
 *
 * 평균 칼로리 vs 목표 + 일별 막대 시각화.
 * Recharts 없이 순수 CSS bar 로 가벼움 유지.
 */
interface WeeklyNutritionMiniCardProps {
  weekly: WeeklyNutritionDay[];
}

const DAYS_KO = ["월", "화", "수", "목", "금", "토", "일"];

export default function WeeklyNutritionMiniCard({
  weekly,
}: WeeklyNutritionMiniCardProps) {
  // 7일 정렬된 배열 보장 — 누락 일자는 0칼로리로 채움
  const padded = DAYS_KO.map((d, i) => weekly[i] ?? { day: d, calories: 0, target: 2000, protein: 0, carbs: 0, fat: 0 });

  const logged = padded.filter((d) => d.calories > 0);
  const avgCal =
    logged.length > 0
      ? Math.round(logged.reduce((s, d) => s + d.calories, 0) / logged.length)
      : 0;
  const target = padded[0]?.target ?? 2000;
  const ratio = target > 0 ? Math.min(100, Math.round((avgCal / target) * 100)) : 0;

  return (
    <Link
      href="/nutrition"
      className="appstore-card block p-5 active:scale-[0.99] transition-transform"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="min-w-0">
          <p className="text-[11px] font-bold uppercase tracking-widest text-secondary">
            평균 섭취
          </p>
          <p className="text-3xl font-extrabold text-text-primary mt-0.5">
            {avgCal.toLocaleString()}
            <span className="text-base font-bold text-text-tertiary ml-1">
              kcal
            </span>
          </p>
          <p className="text-[12px] text-text-tertiary font-mono mt-1">
            목표 {target.toLocaleString()}kcal · {ratio}% · {logged.length}/7일 기록
          </p>
        </div>
        <ChevronRight className="text-text-tertiary mt-1" size={18} />
      </div>

      {/* 일별 막대 */}
      <div className="flex items-end justify-between gap-1.5 h-16 mt-2">
        {padded.map((d, i) => {
          const h = target > 0 ? Math.min(100, (d.calories / target) * 100) : 0;
          const filled = d.calories > 0;
          return (
            <div key={i} className="flex-1 flex flex-col items-center gap-1">
              <div
                className={`w-full rounded-md transition-all ${
                  filled
                    ? "bg-gradient-to-t from-primary to-tertiary"
                    : "bg-surface-2"
                }`}
                style={{ height: `${Math.max(filled ? 8 : 4, h)}%` }}
                aria-label={`${DAYS_KO[i]}: ${d.calories}kcal`}
              />
              <span className="text-[9px] font-mono text-text-tertiary">
                {DAYS_KO[i]}
              </span>
            </div>
          );
        })}
      </div>
    </Link>
  );
}
