"use client";

import { useEffect, useState } from "react";
import type { MealType } from "@/lib/types";

/**
 * 식사 시간 칩 — 아침/점심/저녁/자유 4 개 토글.
 *
 * - 시각 기반 자동 추천(07-10 → 아침, 10-15 → 점심, 15-23 → 저녁)
 * - 선택 상태 localStorage 영속화 (`omw_meal_type`)
 * - Concierge / Dashboard 양쪽에서 재사용
 *
 * 참고: lib/types 의 MealType 은 호환성을 위해 "snack"/"unknown" 도 포함하지만,
 * 본 컴포넌트는 4개 칩(breakfast/lunch/dinner/any)만 노출한다.
 */

const STORAGE_KEY = "omw_meal_type";

type SelectableMealType = "breakfast" | "lunch" | "dinner" | "any";

interface Option {
  value: SelectableMealType;
  emoji: string;
  ko: string;
  en: string;
}

const OPTIONS: Option[] = [
  { value: "breakfast", emoji: "🌅", ko: "아침", en: "Breakfast" },
  { value: "lunch", emoji: "🍱", ko: "점심", en: "Lunch" },
  { value: "dinner", emoji: "🌙", ko: "저녁", en: "Dinner" },
  { value: "any", emoji: "🍽️", ko: "자유", en: "Any" },
];

export function inferMealTypeFromHour(hour: number): SelectableMealType {
  if (hour >= 6 && hour < 10) return "breakfast";
  if (hour >= 10 && hour < 15) return "lunch";
  return "dinner"; // 15-05 시 모두 저녁/야식
}

export function loadStoredMealType(): SelectableMealType {
  if (typeof window === "undefined") return "any";
  const v = localStorage.getItem(STORAGE_KEY);
  if (v === "breakfast" || v === "lunch" || v === "dinner" || v === "any") {
    return v;
  }
  return inferMealTypeFromHour(new Date().getHours());
}

interface MealTimeSelectorProps {
  /** lib/types 의 MealType (snack/unknown 포함). UI 는 칩 4개만 활성화 표시. */
  value: MealType;
  onChange: (next: MealType) => void;
  /** 컴팩트 모드 — 작은 칩 (Dashboard 등) */
  compact?: boolean;
}

export default function MealTimeSelector({
  value,
  onChange,
  compact = false,
}: MealTimeSelectorProps) {
  // 자동 추천 — 한 번만 시도 (사용자 선택 없을 때)
  const [autoApplied, setAutoApplied] = useState(false);

  useEffect(() => {
    if (autoApplied) return;
    if (typeof window === "undefined") return;
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) {
      const inferred = inferMealTypeFromHour(new Date().getHours());
      if (inferred !== value) onChange(inferred);
    }
    setAutoApplied(true);
  }, [autoApplied, value, onChange]);

  const handleClick = (next: SelectableMealType) => {
    if (typeof window !== "undefined") {
      localStorage.setItem(STORAGE_KEY, next);
    }
    onChange(next);
  };

  const padX = compact ? "px-2" : "px-3";
  const padY = compact ? "py-1" : "py-1.5";
  const fontSz = compact ? "text-[10px]" : "text-[11px]";

  return (
    <div
      role="radiogroup"
      aria-label="식사 시간 선택"
      className="flex items-center gap-1.5 flex-wrap"
    >
      {OPTIONS.map((o) => {
        const active = value === o.value;
        return (
          <button
            key={o.value}
            type="button"
            role="radio"
            aria-checked={active}
            onClick={() => handleClick(o.value)}
            className={`flex items-center gap-1 ${padX} ${padY} ${fontSz} font-bold uppercase tracking-[0.04em] rounded-sm border transition-colors ${
              active
                ? "bg-primary/10 border-primary/40 text-primary"
                : "border-outline/25 text-text-tertiary hover:border-outline/40 hover:text-text-secondary"
            }`}
          >
            <span aria-hidden>{o.emoji}</span>
            <span>{o.ko}</span>
          </button>
        );
      })}
    </div>
  );
}
