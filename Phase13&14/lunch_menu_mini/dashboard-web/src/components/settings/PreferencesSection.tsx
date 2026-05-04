"use client";

import { useEffect, useState } from "react";
import { Heart, Ban, ShieldAlert, DollarSign, X } from "lucide-react";
import {
  COMMON_ALLERGENS,
  DEFAULT_PREFERENCES,
  loadPreferences,
  savePreferences,
  type UserPreferences,
} from "@/lib/preferences";
import { CATEGORY_COLORS } from "@/lib/mock";

/**
 * Preferences editor — lives inside SettingsPanel.
 *
 * - Favorite / disliked category chips (multi-select)
 * - Allergen chips (common list + custom add)
 * - Max price slider
 * - Recency penalty slider
 * - Enable toggle
 */
export default function PreferencesSection() {
  const [prefs, setPrefs] = useState<UserPreferences>(DEFAULT_PREFERENCES);
  const [mounted, setMounted] = useState(false);
  const [customAllergen, setCustomAllergen] = useState("");

  useEffect(() => {
    setMounted(true);
    setPrefs(loadPreferences());
  }, []);

  const update = (patch: Partial<UserPreferences>) => {
    const next = { ...prefs, ...patch };
    setPrefs(next);
    savePreferences(next);
  };

  const toggleInArray = (field: "favoriteCategories" | "dislikedCategories" | "allergies", v: string) => {
    const cur = prefs[field];
    const next = cur.includes(v) ? cur.filter((x) => x !== v) : [...cur, v];
    update({ [field]: next } as Partial<UserPreferences>);
  };

  const removeAllergen = (v: string) =>
    update({ allergies: prefs.allergies.filter((a) => a !== v) });

  const addCustomAllergen = () => {
    const v = customAllergen.trim();
    if (!v || prefs.allergies.includes(v)) {
      setCustomAllergen("");
      return;
    }
    update({ allergies: [...prefs.allergies, v] });
    setCustomAllergen("");
  };

  if (!mounted) return null;

  const categories = Object.keys(CATEGORY_COLORS);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="text-[10px] font-bold text-text-secondary uppercase tracking-[0.1em]">
            Personalization{" "}
            <span
              className="text-[9px] font-normal normal-case tracking-normal text-text-tertiary opacity-80"
              style={{ fontFamily: "var(--font-ko)" }}
            >
              개인화
            </span>
          </h4>
        </div>
        <button
          onClick={() => update({ enabled: !prefs.enabled })}
          className={`px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider border rounded-sm transition-colors ${
            prefs.enabled
              ? "border-success/40 bg-success/10 text-success"
              : "border-outline/25 text-text-tertiary"
          }`}
        >
          {prefs.enabled ? "ON" : "OFF"}
        </button>
      </div>

      {/* Favorites */}
      <div>
        <div className="flex items-center gap-1.5 mb-2">
          <Heart size={11} className="text-primary" />
          <span className="text-[10px] font-bold uppercase tracking-wider text-text-secondary">
            Favorite categories
          </span>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {categories.map((c) => {
            const active = prefs.favoriteCategories.includes(c);
            return (
              <button
                key={c}
                onClick={() => toggleInArray("favoriteCategories", c)}
                className={`px-2.5 py-1 text-[11px] font-semibold border rounded-full transition-colors ${
                  active
                    ? "border-primary/40 bg-primary/10 text-primary"
                    : "border-outline/20 text-text-tertiary hover:text-text-secondary"
                }`}
              >
                {c}
              </button>
            );
          })}
        </div>
      </div>

      {/* Dislikes */}
      <div>
        <div className="flex items-center gap-1.5 mb-2">
          <Ban size={11} className="text-error" />
          <span className="text-[10px] font-bold uppercase tracking-wider text-text-secondary">
            Disliked categories
          </span>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {categories.map((c) => {
            const active = prefs.dislikedCategories.includes(c);
            return (
              <button
                key={c}
                onClick={() => toggleInArray("dislikedCategories", c)}
                className={`px-2.5 py-1 text-[11px] font-semibold border rounded-full transition-colors ${
                  active
                    ? "border-error/40 bg-error/10 text-error"
                    : "border-outline/20 text-text-tertiary hover:text-text-secondary"
                }`}
              >
                {c}
              </button>
            );
          })}
        </div>
      </div>

      {/* Allergies */}
      <div>
        <div className="flex items-center gap-1.5 mb-2">
          <ShieldAlert size={11} className="text-tertiary" />
          <span className="text-[10px] font-bold uppercase tracking-wider text-text-secondary">
            Allergens to avoid
          </span>
        </div>
        <div className="flex flex-wrap gap-1.5 mb-2">
          {COMMON_ALLERGENS.map((a) => {
            const active = prefs.allergies.includes(a);
            return (
              <button
                key={a}
                onClick={() => toggleInArray("allergies", a)}
                className={`px-2.5 py-1 text-[11px] font-semibold border rounded-full transition-colors ${
                  active
                    ? "border-tertiary/40 bg-tertiary/10 text-tertiary"
                    : "border-outline/20 text-text-tertiary hover:text-text-secondary"
                }`}
                style={{ fontFamily: "var(--font-ko)" }}
              >
                {a}
              </button>
            );
          })}
        </div>
        {/* Custom allergens */}
        <div className="flex gap-1.5">
          <input
            value={customAllergen}
            onChange={(e) => setCustomAllergen(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                addCustomAllergen();
              }
            }}
            placeholder="직접 추가..."
            className="flex-1 bg-surface-2 border border-outline/20 px-2.5 py-1.5 text-xs text-text-primary rounded-sm outline-none focus:border-primary/40"
            style={{ fontFamily: "var(--font-ko)" }}
          />
          <button
            onClick={addCustomAllergen}
            className="px-3 py-1.5 text-[10px] font-bold uppercase bg-surface-2 border border-outline/25 rounded-sm hover:text-primary hover:border-primary/40"
          >
            Add
          </button>
        </div>
        {prefs.allergies.filter((a) => !COMMON_ALLERGENS.includes(a)).length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-2">
            {prefs.allergies
              .filter((a) => !COMMON_ALLERGENS.includes(a))
              .map((a) => (
                <span
                  key={a}
                  className="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] border border-tertiary/40 bg-tertiary/10 text-tertiary rounded-full"
                  style={{ fontFamily: "var(--font-ko)" }}
                >
                  {a}
                  <button
                    onClick={() => removeAllergen(a)}
                    className="hover:text-error"
                    aria-label={`Remove ${a}`}
                  >
                    <X size={10} />
                  </button>
                </span>
              ))}
          </div>
        )}
      </div>

      {/* Max price */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-1.5">
            <DollarSign size={11} className="text-secondary" />
            <span className="text-[10px] font-bold uppercase tracking-wider text-text-secondary">
              Max price
            </span>
          </div>
          <span className="text-xs font-mono text-text-primary">
            {prefs.maxPrice > 0 ? `₩${prefs.maxPrice.toLocaleString()}` : "제한 없음"}
          </span>
        </div>
        <input
          type="range"
          min={0}
          max={25000}
          step={1000}
          value={prefs.maxPrice}
          onChange={(e) => update({ maxPrice: Number(e.target.value) })}
          className="w-full accent-primary"
        />
      </div>

      {/* Recency penalty */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-[10px] font-bold uppercase tracking-wider text-text-secondary">
            Recency penalty
          </span>
          <span className="text-xs font-mono text-text-primary">
            {(prefs.recencyPenalty * 100).toFixed(0)}%
          </span>
        </div>
        <input
          type="range"
          min={0}
          max={1}
          step={0.1}
          value={prefs.recencyPenalty}
          onChange={(e) => update({ recencyPenalty: Number(e.target.value) })}
          className="w-full accent-primary"
        />
        <p
          className="text-[9px] text-text-tertiary mt-1"
          style={{ fontFamily: "var(--font-ko)" }}
        >
          최근 방문한 식당의 점수를 낮춥니다
        </p>
      </div>

      {/* Reset */}
      <button
        onClick={() => {
          const reset = { ...DEFAULT_PREFERENCES, onboardingComplete: true };
          setPrefs(reset);
          savePreferences(reset);
        }}
        className="w-full py-2 text-[10px] font-bold uppercase border border-outline/20 text-text-tertiary hover:text-error hover:border-error/40 rounded-sm transition-colors"
      >
        Reset preferences
      </button>
    </div>
  );
}
