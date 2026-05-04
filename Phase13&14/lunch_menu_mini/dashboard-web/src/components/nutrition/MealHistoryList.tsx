"use client";

import { AlertTriangle, Loader2, Trash2, Utensils } from "lucide-react";
import { useDeleteMeal, useMealHistory } from "@/lib/queries";

function fmtDate(value?: string | null) {
  if (!value) return "-";
  return value.slice(0, 10);
}

function fmtNum(value?: number | null, unit = "") {
  if (value == null) return "-";
  return `${Math.round(value)}${unit}`;
}

function mealTypeLabel(value?: string | null) {
  switch (value) {
    case "breakfast":
      return "아침";
    case "lunch":
      return "점심";
    case "dinner":
      return "저녁";
    case "snack":
      return "간식";
    default:
      return "기록";
  }
}

export default function MealHistoryList({ userId }: { userId: string | number }) {
  const { data: meals = [], isLoading } = useMealHistory(userId, 12);
  const deleteMeal = useDeleteMeal();

  return (
    <div className="border border-outline/15 bg-surface-1 rounded-sm p-4 mb-6">
      <div className="flex items-center justify-between gap-3 mb-3">
        <div className="flex items-center gap-2">
          <Utensils size={16} className="text-primary" />
          <div>
            <div className="text-sm font-heading font-bold text-text-primary uppercase tracking-[0.04em]">
              Recent Meals
            </div>
            <div className="text-[10px] text-text-tertiary" style={{ fontFamily: "var(--font-ko)" }}>
              최근 식단 {meals.length}건
            </div>
          </div>
        </div>
        {isLoading && <Loader2 size={14} className="animate-spin text-text-tertiary" />}
      </div>

      {meals.length === 0 ? (
        <div className="text-xs text-text-tertiary border border-outline/10 bg-surface-2 rounded-sm px-3 py-4" style={{ fontFamily: "var(--font-ko)" }}>
          저장된 식단 기록이 없습니다.
        </div>
      ) : (
        <div className="space-y-2">
          {meals.map((meal) => (
            <div
              key={meal.id ?? `${meal.meal_date}-${meal.menu_name}`}
              className="grid grid-cols-1 md:grid-cols-[1fr_auto] gap-3 border border-outline/15 bg-surface-2 rounded-sm p-3"
            >
              <div className="min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-[10px] font-bold uppercase tracking-[0.08em] text-primary border border-primary/25 bg-primary/5 rounded-sm px-1.5 py-0.5">
                    {mealTypeLabel(meal.meal_type)}
                  </span>
                  <span className="text-[11px] text-text-tertiary font-mono">
                    {fmtDate(meal.meal_date)}
                  </span>
                  {meal.needs_review && (
                    <span className="inline-flex items-center gap-1 text-[10px] text-warning border border-warning/30 bg-warning/10 rounded-sm px-1.5 py-0.5">
                      <AlertTriangle size={10} />
                      확인 필요
                    </span>
                  )}
                </div>
                <div className="mt-1 text-sm font-bold text-text-primary truncate" style={{ fontFamily: "var(--font-ko)" }}>
                  {meal.menu_name || meal.raw_text || "식단 기록"}
                </div>
                <div className="mt-1 text-[11px] text-text-tertiary truncate" style={{ fontFamily: "var(--font-ko)" }}>
                  {meal.restaurant_name_snapshot || "식당 미연결"} · {meal.nutrition_source || "unverified"}
                </div>
                <div className="mt-2 flex gap-2 flex-wrap text-[11px] font-mono text-text-secondary">
                  <span>{fmtNum(meal.calories, "kcal")}</span>
                  <span>P {fmtNum(meal.protein, "g")}</span>
                  <span>C {fmtNum(meal.carbs, "g")}</span>
                  <span>F {fmtNum(meal.fat, "g")}</span>
                  <span>Na {fmtNum(meal.sodium, "mg")}</span>
                </div>
              </div>

              <div className="flex md:flex-col items-end justify-between gap-2">
                <div className="text-[10px] text-text-tertiary font-mono">
                  #{meal.id ?? "-"}
                </div>
                {meal.id != null && (
                  <button
                    type="button"
                    disabled={deleteMeal.isPending}
                    onClick={() => deleteMeal.mutate({ mealId: meal.id!, userId })}
                    className="inline-flex items-center gap-1.5 px-2 py-1.5 text-[11px] font-bold uppercase border border-outline/25 rounded-sm text-text-secondary hover:text-error hover:border-error/40 disabled:opacity-50"
                  >
                    {deleteMeal.isPending ? <Loader2 size={12} className="animate-spin" /> : <Trash2 size={12} />}
                    삭제
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {deleteMeal.isError && (
        <div className="mt-3 text-[11px] text-error font-mono">
          삭제 실패: {String(deleteMeal.error)}
        </div>
      )}
    </div>
  );
}
