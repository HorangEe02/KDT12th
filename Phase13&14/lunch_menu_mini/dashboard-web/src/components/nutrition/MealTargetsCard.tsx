"use client";

import { useNutritionTargets } from "@/lib/queries";
import type { MealNutritionTarget } from "@/lib/types";

/**
 * 식사별 영양 목표 카드 — 아침/점심/저녁 권장량 분배 표시.
 *
 * 헤비 옵션(다중 식사 시간) 의 시각화 컴포넌트.
 * `/api/nutrition/targets/{userId}` 가 반환하는 식사별 분배 비율
 * (아침 25% / 점심 35% / 저녁 40%) 을 보여준다.
 */

interface MealTargetsCardProps {
  userId: string | number;
}

const MEAL_META: Array<{
  key: "breakfast" | "lunch" | "dinner";
  emoji: string;
  ko: string;
  color: string;
}> = [
  { key: "breakfast", emoji: "🌅", ko: "아침", color: "var(--color-primary)" },
  { key: "lunch", emoji: "🍱", ko: "점심", color: "var(--color-success, #22c55e)" },
  { key: "dinner", emoji: "🌙", ko: "저녁", color: "var(--color-tertiary, #8b5cf6)" },
];

export default function MealTargetsCard({ userId }: MealTargetsCardProps) {
  const { data, isLoading, error } = useNutritionTargets(userId);

  if (error) {
    return (
      <div className="bento-card">
        <h3 className="text-sm font-heading font-bold uppercase tracking-[0.04em] mb-1">
          식사별 영양 목표
        </h3>
        <p className="text-[11px] text-error">목표 조회 실패</p>
      </div>
    );
  }

  return (
    <div className="bento-card">
      <h3 className="text-base font-heading font-bold text-text-primary uppercase tracking-[0.04em] mb-1">
        Meal-Time Targets
      </h3>
      <p
        className="text-[11px] text-text-tertiary mb-4"
        style={{ fontFamily: "var(--font-ko)" }}
      >
        식사별 일일 권장 영양량 — 아침 25% / 점심 35% / 저녁 40%
      </p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {MEAL_META.map((m) => {
          const t: MealNutritionTarget | undefined = data?.by_meal[m.key];
          return (
            <div
              key={m.key}
              className="border border-outline/15 rounded-sm p-3 bg-surface-2"
              style={{ borderLeft: `3px solid ${m.color}` }}
            >
              <div className="flex items-baseline justify-between mb-2">
                <div className="flex items-center gap-1.5">
                  <span aria-hidden className="text-base">{m.emoji}</span>
                  <span
                    className="text-xs font-bold uppercase tracking-[0.06em]"
                    style={{ fontFamily: "var(--font-ko)" }}
                  >
                    {m.ko}
                  </span>
                </div>
                <span className="text-[10px] font-mono text-text-tertiary">
                  {t ? `${(t.ratio * 100).toFixed(0)}%` : "—"}
                </span>
              </div>
              {isLoading || !t ? (
                <div className="space-y-1">
                  <div className="h-3 bg-surface-1 rounded animate-pulse" />
                  <div className="h-3 bg-surface-1 rounded animate-pulse" />
                </div>
              ) : (
                <ul className="text-[11px] font-mono space-y-0.5 text-text-secondary">
                  <li>
                    <span className="text-text-tertiary">cal</span>{" "}
                    <span className="font-bold text-text-primary">{t.calories}</span>
                    <span className="text-text-tertiary"> kcal</span>
                  </li>
                  <li>
                    <span className="text-text-tertiary">탄수</span>{" "}
                    <span className="text-text-primary">{t.carbs_g}g</span>
                  </li>
                  <li>
                    <span className="text-text-tertiary">단백</span>{" "}
                    <span className="text-text-primary">{t.protein_g}g</span>
                  </li>
                  <li>
                    <span className="text-text-tertiary">지방</span>{" "}
                    <span className="text-text-primary">{t.fat_g}g</span>
                  </li>
                </ul>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
