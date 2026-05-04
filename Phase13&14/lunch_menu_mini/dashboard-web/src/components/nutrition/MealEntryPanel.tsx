"use client";

import dynamic from "next/dynamic";
import { useMemo, useState } from "react";
import {
  AlertTriangle,
  Check,
  Loader2,
  MapPin,
  Plus,
  Save,
  Search,
  Trash2,
  Utensils,
  X,
} from "lucide-react";
import { SkeletonMap } from "@/components/common/Skeleton";
import type {
  MealType,
  NaturalMealAnalysisOut,
  NaturalMealItem,
  NaturalMealPayload,
  Restaurant,
  RestaurantSnapshot,
} from "@/lib/types";
import { useAnalyzeMealText, useNearbyRestaurants, useSaveNaturalMeal } from "@/lib/queries";
import { useGeolocation } from "@/lib/useGeolocation";

const KakaoMap = dynamic(() => import("@/components/map/KakaoMap"), {
  ssr: false,
  loading: () => <SkeletonMap height={280} />,
});

const MEAL_TYPES: Array<{ value: MealType; label: string }> = [
  { value: "breakfast", label: "아침" },
  { value: "lunch", label: "점심" },
  { value: "dinner", label: "저녁" },
  { value: "snack", label: "간식" },
  { value: "unknown", label: "미정" },
];

function todayLocal() {
  const d = new Date();
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
  return d.toISOString().slice(0, 10);
}

function numberOrNull(value: string): number | null {
  if (value.trim() === "") return null;
  const n = Number(value);
  return Number.isFinite(n) && n >= 0 ? n : null;
}

function restaurantSnapshot(r: Restaurant | null): RestaurantSnapshot | null {
  if (!r) return null;
  return {
    id: String(r.id),
    name: r.name,
    category: r.category,
    address: r.address ?? null,
    lat: r.lat ?? null,
    lng: r.lng ?? null,
    place_url: r.place_url ?? null,
  };
}

function toPayload(
  userId: string,
  analysis: NaturalMealAnalysisOut,
  selected: Restaurant | null,
): NaturalMealPayload {
  return {
    user_id: userId,
    raw_text: analysis.raw_text,
    meal_date: analysis.meal_date,
    meal_type: analysis.meal_type ?? "unknown",
    restaurant_id: selected ? String(selected.id) : analysis.restaurant_id ?? null,
    restaurant_snapshot: restaurantSnapshot(selected),
    satisfaction: analysis.satisfaction ?? null,
    items: analysis.items,
  };
}

export default function MealEntryPanel({ userId }: { userId: string }) {
  const [text, setText] = useState("");
  const [baseDate, setBaseDate] = useState(todayLocal());
  const [analysis, setAnalysis] = useState<NaturalMealAnalysisOut | null>(null);
  const [selectedRestaurant, setSelectedRestaurant] = useState<Restaurant | null>(null);
  const [showMap, setShowMap] = useState(false);
  const [savedId, setSavedId] = useState<number | null>(null);

  const analyze = useAnalyzeMealText();
  const saveMeal = useSaveNaturalMeal();
  const { position, loading: geoLoading } = useGeolocation();
  const { data: nearby = [], isLoading: nearbyLoading } = useNearbyRestaurants(
    position?.lat,
    position?.lng,
    800,
    80,
  );

  const selectedId = selectedRestaurant ? String(selectedRestaurant.id) : null;
  const busy = analyze.isPending || saveMeal.isPending;

  const totals = useMemo(() => {
    if (!analysis) return null;
    return [
      { label: "kcal", value: analysis.calories },
      { label: "P", value: analysis.protein },
      { label: "C", value: analysis.carbs },
      { label: "F", value: analysis.fat },
      { label: "Na", value: analysis.sodium },
    ];
  }, [analysis]);

  const updateAnalysis = (patch: Partial<NaturalMealAnalysisOut>) => {
    setAnalysis((prev) => (prev ? { ...prev, ...patch } : prev));
  };

  const updateItem = (index: number, patch: Partial<NaturalMealItem>) => {
    setAnalysis((prev) => {
      if (!prev) return prev;
      const items = prev.items.map((item, i) =>
        i === index ? { ...item, ...patch, source: "user_adjusted" } : item,
      );
      return { ...prev, items };
    });
  };

  const removeItem = (index: number) => {
    setAnalysis((prev) => {
      if (!prev) return prev;
      const items = prev.items.filter((_, i) => i !== index);
      return { ...prev, items };
    });
  };

  const addItem = () => {
    setAnalysis((prev) => {
      const blank: NaturalMealItem = {
        raw_name: "",
        normalized_name: null,
        quantity: 1,
        unit: "serving",
        calories: null,
        protein: null,
        carbs: null,
        fat: null,
        sugar: null,
        sodium: null,
        match_type: "user_added",
        match_confidence: null,
        needs_review: true,
        source: "user_adjusted",
        food_code: null,
        serving_size: null,
      };
      if (!prev) {
        return {
          user_id: userId,
          raw_text: text,
          meal_date: baseDate,
          meal_type: "unknown" as MealType,
          satisfaction: null,
          restaurant_id: null,
          restaurant_name_snapshot: null,
          restaurant_place_url: null,
          menu_name: null,
          calories: null,
          protein: null,
          carbs: null,
          fat: null,
          sugar: null,
          sodium: null,
          nutrition_source: "manual",
          match_confidence: null,
          needs_review: true,
          items: [blank],
        } as NaturalMealAnalysisOut;
      }
      return { ...prev, items: [...prev.items, blank] };
    });
  };

  const handleAnalyze = () => {
    setSavedId(null);
    analyze.mutate(
      {
        user_id: userId,
        text,
        base_date: baseDate,
        restaurant_id: selectedRestaurant ? String(selectedRestaurant.id) : null,
        restaurant_snapshot: restaurantSnapshot(selectedRestaurant),
      },
      {
        onSuccess: ({ analysis: next }) => {
          setAnalysis(next);
        },
      },
    );
  };

  const handleSave = () => {
    if (!analysis) return;
    // 빈 raw_name 항목 필터 (사용자가 ➕ 추가만 하고 안 채운 행 제외)
    const cleaned: NaturalMealAnalysisOut = {
      ...analysis,
      items: analysis.items.filter(
        (it) => (it.raw_name ?? "").trim() !== "" || (it.normalized_name ?? "").trim() !== "",
      ),
    };
    if (cleaned.items.length === 0) {
      alert("저장할 음식이 없습니다. 자연어로 분석하거나 직접 음식을 추가해 주세요.");
      return;
    }
    saveMeal.mutate(toPayload(userId, cleaned, selectedRestaurant), {
      onSuccess: (saved) => {
        setAnalysis(saved);
        setSavedId(saved.id ?? null);
      },
    });
  };

  return (
    <div className="border border-outline/20 bg-surface-1 rounded-sm p-4 mb-6">
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2 text-sm font-heading font-bold text-text-primary uppercase tracking-[0.04em]">
            <Utensils size={16} className="text-primary" />
            Meal Log
          </div>
          <div className="text-[11px] text-text-tertiary mt-0.5" style={{ fontFamily: "var(--font-ko)" }}>
            자연어 식단 입력과 식당 연결
          </div>
        </div>
        <button
          type="button"
          onClick={() => setShowMap((v) => !v)}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-bold uppercase border border-outline/25 rounded-sm hover:border-primary/40 hover:text-primary transition-colors"
        >
          {showMap ? <X size={13} /> : <MapPin size={13} />}
          식당 연결
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-3">
        <div className="lg:col-span-3">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={4}
            placeholder="오늘 점심에 김치찌개랑 공기밥 먹었어. 만족도는 4점."
            className="w-full bg-surface-2 border border-outline/25 rounded-sm px-3 py-2 text-sm text-text-primary resize-none focus:outline-none focus:border-primary/50"
            style={{ fontFamily: "var(--font-ko)" }}
          />
        </div>
        <div className="lg:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-2 content-start">
          <label className="min-w-0 text-[10px] uppercase tracking-[0.08em] text-text-tertiary">
            Date
            <input
              type="date"
              value={analysis?.meal_date ?? baseDate}
              onChange={(e) => {
                setBaseDate(e.target.value);
                updateAnalysis({ meal_date: e.target.value });
              }}
              className="mt-1 block w-full max-w-full bg-surface-2 border border-outline/25 rounded-sm px-2 py-1.5 text-xs text-text-primary"
            />
          </label>
          <label className="min-w-0 text-[10px] uppercase tracking-[0.08em] text-text-tertiary">
            Type
            <select
              value={analysis?.meal_type ?? "unknown"}
              onChange={(e) => updateAnalysis({ meal_type: e.target.value as MealType })}
              className="mt-1 block w-full max-w-full bg-surface-2 border border-outline/25 rounded-sm px-2 py-1.5 text-xs text-text-primary"
            >
              {MEAL_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </label>
          <button
            type="button"
            disabled={busy || text.trim().length === 0}
            onClick={handleAnalyze}
            className="sm:col-span-2 inline-flex items-center justify-center gap-2 px-3 py-2 text-xs font-bold uppercase bg-primary text-white rounded-sm disabled:opacity-50"
          >
            {analyze.isPending ? <Loader2 size={14} className="animate-spin" /> : <Search size={14} />}
            분석
          </button>
        </div>
      </div>

      {selectedRestaurant && (
        <div className="mt-3 flex items-center justify-between gap-3 border border-primary/25 bg-primary/5 rounded-sm px-3 py-2 text-xs">
          <div className="min-w-0">
            <div className="font-bold text-text-primary truncate">{selectedRestaurant.name}</div>
            <div className="text-text-tertiary truncate" style={{ fontFamily: "var(--font-ko)" }}>
              {selectedRestaurant.category} · {selectedRestaurant.address ?? "주소 없음"}
            </div>
          </div>
          <button
            type="button"
            onClick={() => setSelectedRestaurant(null)}
            className="p-1 border border-outline/25 rounded-sm hover:text-error"
            aria-label="식당 연결 해제"
          >
            <X size={14} />
          </button>
        </div>
      )}

      {showMap && (
        <div className="mt-4 grid grid-cols-1 lg:grid-cols-5 gap-3">
          <div className="lg:col-span-3">
            {position ? (
              <KakaoMap
                userLat={position.lat}
                userLng={position.lng}
                restaurants={nearby}
                selectedId={selectedId}
                onSelect={(id) => {
                  const found = nearby.find((r) => String(r.id) === String(id));
                  if (found) setSelectedRestaurant(found);
                }}
                height="280px"
                showRadius={800}
              />
            ) : (
              <SkeletonMap height={280} />
            )}
          </div>
          <div className="lg:col-span-2 max-h-[280px] overflow-auto border border-outline/15 rounded-sm">
            <div className="px-3 py-2 text-[10px] uppercase tracking-[0.08em] text-text-tertiary border-b border-outline/15">
              {geoLoading || nearbyLoading ? "검색 중" : `주변 식당 ${nearby.length}개`}
            </div>
            {nearby.slice(0, 20).map((r) => (
              <button
                key={String(r.id)}
                type="button"
                onClick={() => setSelectedRestaurant(r)}
                className={`w-full text-left px-3 py-2 border-b border-outline/10 hover:bg-surface-2 ${
                  selectedId === String(r.id) ? "bg-primary/5 text-primary" : "text-text-primary"
                }`}
              >
                <div className="text-xs font-bold truncate">{r.name}</div>
                <div className="text-[11px] text-text-tertiary truncate" style={{ fontFamily: "var(--font-ko)" }}>
                  {r.category} · {r.distance_m ?? r.distance}m
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {analysis && (
        <div className="mt-4 border-t border-outline/15 pt-4">
          <div className="flex items-center justify-between gap-3 mb-3">
            <div>
              <div className="text-sm font-bold text-text-primary" style={{ fontFamily: "var(--font-ko)" }}>
                {analysis.menu_name ?? "분석 결과"}
              </div>
              <div className="text-[11px] text-text-tertiary">
                {analysis.nutrition_source ?? "unverified"}
                {analysis.match_confidence != null && ` · ${(analysis.match_confidence * 100).toFixed(0)}%`}
              </div>
            </div>
            <button
              type="button"
              disabled={busy || analysis.items.length === 0}
              onClick={handleSave}
              className="inline-flex items-center gap-2 px-3 py-2 text-xs font-bold uppercase bg-secondary text-white rounded-sm disabled:opacity-50"
            >
              {saveMeal.isPending ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
              저장
            </button>
          </div>

          {analysis.needs_review && (
            <div className="mb-3 flex items-start gap-2 text-xs text-warning border border-warning/25 bg-warning/5 rounded-sm px-3 py-2">
              <AlertTriangle size={14} className="flex-shrink-0 mt-0.5" />
              <span style={{ fontFamily: "var(--font-ko)" }}>
                일부 항목은 검증된 영양값을 찾지 못했습니다. 저장 전에 값을 확인해 주세요.
              </span>
            </div>
          )}

          {totals && (
            <div className="grid grid-cols-5 gap-2 mb-3">
              {totals.map((t) => (
                <div key={t.label} className="bg-surface-2 border border-outline/15 rounded-sm px-2 py-2">
                  <div className="text-[10px] text-text-tertiary uppercase">{t.label}</div>
                  <div className="text-sm font-heading font-bold text-text-primary">
                    {t.value == null ? "-" : Math.round(t.value)}
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="space-y-2">
            {analysis.items.map((item, idx) => (
              <div key={`item-${idx}`} className="grid grid-cols-2 md:grid-cols-9 gap-2 items-end bg-surface-2 border border-outline/15 rounded-sm p-2">
                <label className="md:col-span-2 text-[10px] uppercase tracking-[0.08em] text-text-tertiary">
                  Food
                  <input
                    value={item.normalized_name ?? item.raw_name}
                    placeholder="음식 이름"
                    onChange={(e) => updateItem(idx, { normalized_name: e.target.value, raw_name: e.target.value })}
                    className="mt-1 w-full bg-surface-1 border border-outline/25 rounded-sm px-2 py-1.5 text-xs text-text-primary"
                  />
                </label>
                <label className="text-[10px] uppercase tracking-[0.08em] text-text-tertiary">
                  Qty
                  <input
                    type="number"
                    min="0.1"
                    step="0.1"
                    value={item.quantity}
                    onChange={(e) => updateItem(idx, { quantity: Number(e.target.value) || 1 })}
                    className="mt-1 w-full bg-surface-1 border border-outline/25 rounded-sm px-2 py-1.5 text-xs text-text-primary"
                  />
                </label>
                {(["calories", "protein", "carbs", "fat", "sodium"] as const).map((key) => (
                  <label key={key} className="text-[10px] uppercase tracking-[0.08em] text-text-tertiary">
                    {key === "calories" ? "kcal" : key.slice(0, 1).toUpperCase()}
                    <input
                      type="number"
                      min="0"
                      value={item[key] ?? ""}
                      onChange={(e) => updateItem(idx, { [key]: numberOrNull(e.target.value) })}
                      className="mt-1 w-full bg-surface-1 border border-outline/25 rounded-sm px-2 py-1.5 text-xs text-text-primary"
                    />
                  </label>
                ))}
                <button
                  type="button"
                  onClick={() => removeItem(idx)}
                  title="이 음식 삭제"
                  aria-label="삭제"
                  className="md:justify-self-center w-9 h-9 inline-flex items-center justify-center rounded-sm border border-outline/25 text-text-tertiary hover:text-error hover:border-error/40 hover:bg-error/5 transition-colors"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
            <button
              type="button"
              onClick={addItem}
              className="w-full inline-flex items-center justify-center gap-2 py-2.5 border border-dashed border-outline/30 text-text-tertiary text-xs font-bold uppercase tracking-[0.08em] rounded-sm hover:text-primary hover:border-primary/40 hover:bg-primary/5 transition-colors"
            >
              <Plus size={14} />
              음식 추가
            </button>
          </div>
        </div>
      )}
      {!analysis && (
        <button
          type="button"
          onClick={addItem}
          className="mt-3 w-full inline-flex items-center justify-center gap-2 py-2.5 border border-dashed border-outline/30 text-text-tertiary text-xs font-bold uppercase tracking-[0.08em] rounded-sm hover:text-primary hover:border-primary/40 hover:bg-primary/5 transition-colors"
        >
          <Plus size={14} />
          분석 없이 직접 음식 입력
        </button>
      )}

      {(analyze.isError || saveMeal.isError) && (
        <div className="mt-3 text-xs text-error font-mono">
          {String(analyze.error || saveMeal.error)}
        </div>
      )}
      {savedId != null && (
        <div className="mt-3 inline-flex items-center gap-1.5 text-xs text-success">
          <Check size={14} />
          저장됨 #{savedId}
        </div>
      )}
    </div>
  );
}
