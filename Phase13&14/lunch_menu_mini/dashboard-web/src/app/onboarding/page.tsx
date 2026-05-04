"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  ChevronRight,
  ChevronLeft,
  Check,
  UtensilsCrossed,
  ShieldAlert,
  DollarSign,
  Sparkles,
} from "lucide-react";
import { BRAND } from "@/lib/brand";
import {
  COMMON_ALLERGENS,
  DEFAULT_PREFERENCES,
  savePreferences,
  type UserPreferences,
} from "@/lib/preferences";
import { CATEGORY_COLORS } from "@/lib/mock";

type Step = 0 | 1 | 2 | 3 | 4;

const STEPS: { key: Step; title: string; ko: string; icon: typeof Sparkles }[] = [
  { key: 0, title: "Welcome", ko: "시작하기", icon: Sparkles },
  { key: 1, title: "Favorites", ko: "선호 카테고리", icon: UtensilsCrossed },
  { key: 2, title: "Allergens", ko: "알레르기", icon: ShieldAlert },
  { key: 3, title: "Budget", ko: "예산", icon: DollarSign },
  { key: 4, title: "Done", ko: "완료", icon: Check },
];

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState<Step>(0);
  const [prefs, setPrefs] = useState<UserPreferences>({
    ...DEFAULT_PREFERENCES,
    enabled: true,
  });

  const categories = Object.keys(CATEGORY_COLORS);

  const toggleCategory = (c: string) =>
    setPrefs((p) => ({
      ...p,
      favoriteCategories: p.favoriteCategories.includes(c)
        ? p.favoriteCategories.filter((x) => x !== c)
        : [...p.favoriteCategories, c],
    }));

  const toggleAllergen = (a: string) =>
    setPrefs((p) => ({
      ...p,
      allergies: p.allergies.includes(a)
        ? p.allergies.filter((x) => x !== a)
        : [...p.allergies, a],
    }));

  const finish = () => {
    savePreferences({ ...prefs, onboardingComplete: true });
    router.replace("/");
  };

  const skip = () => {
    savePreferences({
      ...DEFAULT_PREFERENCES,
      enabled: false,
      onboardingComplete: true,
    });
    router.replace("/");
  };

  const next = () => setStep((s) => (Math.min(s + 1, 4) as Step));
  const prev = () => setStep((s) => (Math.max(s - 1, 0) as Step));

  return (
    <div className="max-w-xl mx-auto">
      {/* Progress bar */}
      <div className="flex items-center justify-between mb-8">
        {STEPS.map((s, i) => {
          const Active = s.key <= step;
          const Current = s.key === step;
          return (
            <div key={s.key} className="flex items-center flex-1">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center border-2 flex-shrink-0 transition-all ${
                  Current
                    ? "border-primary bg-primary text-background shadow-[0_0_12px_rgba(232,89,60,0.35)]"
                    : Active
                    ? "border-success bg-success/20 text-success"
                    : "border-outline/30 text-text-tertiary"
                }`}
              >
                {Active && !Current ? (
                  <Check size={14} strokeWidth={3} />
                ) : (
                  <s.icon size={14} />
                )}
              </div>
              {i < STEPS.length - 1 && (
                <div
                  className={`flex-1 h-[2px] mx-1 ${
                    s.key < step ? "bg-success/60" : "bg-outline/20"
                  }`}
                />
              )}
            </div>
          );
        })}
      </div>

      {/* Content */}
      <div className="bg-surface-1 border border-outline/15 rounded-sm p-6 min-h-[360px]">
        {step === 0 && (
          <div className="text-center">
            <img
              src={BRAND.logoSrc}
              alt={BRAND.logoAlt}
              className="w-20 h-20 mx-auto mb-3 rounded-md object-contain select-none"
              draggable={false}
            />
            <h1 className="text-2xl font-heading font-bold text-text-primary mb-1 tracking-tight">
              Welcome to Lunch Optimizer
            </h1>
            <p
              className="text-sm text-text-secondary mb-6"
              style={{ fontFamily: "var(--font-ko)" }}
            >
              2분만 투자해서 개인 취향을 설정하면, 매일 더 나은 점심 추천을 받을 수 있어요.
            </p>
            <div className="text-left bg-surface-2 rounded-sm p-4 space-y-2 text-xs text-text-secondary">
              <div className="flex items-center gap-2">
                <UtensilsCrossed size={14} className="text-primary" />
                선호 카테고리 선택
              </div>
              <div className="flex items-center gap-2">
                <ShieldAlert size={14} className="text-tertiary" />
                알레르기·기피 음식 제외
              </div>
              <div className="flex items-center gap-2">
                <DollarSign size={14} className="text-secondary" />
                예산 상한 설정
              </div>
            </div>
          </div>
        )}

        {step === 1 && (
          <div>
            <h2 className="text-xl font-heading font-bold text-text-primary mb-1">
              Favorite categories
            </h2>
            <p
              className="text-xs text-text-tertiary mb-5"
              style={{ fontFamily: "var(--font-ko)" }}
            >
              좋아하는 음식 카테고리를 선택하세요. 여러 개 선택 가능.
            </p>
            <div className="flex flex-wrap gap-2">
              {categories.map((c) => {
                const active = prefs.favoriteCategories.includes(c);
                return (
                  <button
                    key={c}
                    onClick={() => toggleCategory(c)}
                    className={`px-4 py-2.5 text-sm font-semibold border rounded-full transition-all ${
                      active
                        ? "border-primary bg-primary/10 text-primary scale-105"
                        : "border-outline/25 text-text-secondary hover:text-text-primary"
                    }`}
                  >
                    {c}
                  </button>
                );
              })}
            </div>
            <p className="text-[11px] text-text-tertiary mt-4">
              선택한 카테고리는 Discovery 탭에서 우선 노출됩니다.
            </p>
          </div>
        )}

        {step === 2 && (
          <div>
            <h2 className="text-xl font-heading font-bold text-text-primary mb-1">
              Allergens & dislikes
            </h2>
            <p
              className="text-xs text-text-tertiary mb-5"
              style={{ fontFamily: "var(--font-ko)" }}
            >
              알레르기나 피하고 싶은 재료를 선택하면 해당 식당이 자동으로 제외됩니다.
            </p>
            <div className="flex flex-wrap gap-2">
              {COMMON_ALLERGENS.map((a) => {
                const active = prefs.allergies.includes(a);
                return (
                  <button
                    key={a}
                    onClick={() => toggleAllergen(a)}
                    className={`px-3.5 py-2 text-sm font-semibold border rounded-full transition-all ${
                      active
                        ? "border-tertiary bg-tertiary/15 text-tertiary"
                        : "border-outline/25 text-text-secondary"
                    }`}
                    style={{ fontFamily: "var(--font-ko)" }}
                  >
                    {a}
                  </button>
                );
              })}
            </div>
            <p className="text-[11px] text-text-tertiary mt-4">
              이후 Settings → Personalization 에서 언제든 수정할 수 있어요.
            </p>
          </div>
        )}

        {step === 3 && (
          <div>
            <h2 className="text-xl font-heading font-bold text-text-primary mb-1">
              Budget
            </h2>
            <p
              className="text-xs text-text-tertiary mb-5"
              style={{ fontFamily: "var(--font-ko)" }}
            >
              점심 1끼 최대 예산을 설정하세요. 0원 = 제한 없음.
            </p>
            <div className="text-center mb-4">
              <div className="text-4xl font-heading font-bold text-primary font-mono">
                {prefs.maxPrice > 0
                  ? `₩${prefs.maxPrice.toLocaleString()}`
                  : "제한 없음"}
              </div>
            </div>
            <input
              type="range"
              min={0}
              max={25000}
              step={1000}
              value={prefs.maxPrice}
              onChange={(e) =>
                setPrefs((p) => ({ ...p, maxPrice: Number(e.target.value) }))
              }
              className="w-full accent-primary"
            />
            <div className="flex justify-between text-[10px] text-text-tertiary font-mono mt-1">
              <span>₩0</span>
              <span>₩25,000</span>
            </div>
          </div>
        )}

        {step === 4 && (
          <div className="text-center">
            <div className="text-5xl mb-3" aria-hidden>
              ✨
            </div>
            <h2 className="text-2xl font-heading font-bold text-text-primary mb-2">
              All set!
            </h2>
            <p
              className="text-sm text-text-secondary mb-6"
              style={{ fontFamily: "var(--font-ko)" }}
            >
              설정이 완료됐어요. 이제 개인화된 추천을 받을 수 있습니다.
            </p>
            <div className="bg-surface-2 rounded-sm p-4 text-left text-xs space-y-2">
              <div>
                <span className="text-text-tertiary">선호 카테고리: </span>
                <span className="text-text-primary font-semibold">
                  {prefs.favoriteCategories.length
                    ? prefs.favoriteCategories.join(", ")
                    : "없음"}
                </span>
              </div>
              <div>
                <span className="text-text-tertiary">알레르기: </span>
                <span className="text-text-primary font-semibold">
                  {prefs.allergies.length
                    ? prefs.allergies.join(", ")
                    : "없음"}
                </span>
              </div>
              <div>
                <span className="text-text-tertiary">최대 예산: </span>
                <span className="text-text-primary font-semibold font-mono">
                  {prefs.maxPrice > 0
                    ? `₩${prefs.maxPrice.toLocaleString()}`
                    : "제한 없음"}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between mt-6">
        <button
          onClick={skip}
          className="text-xs text-text-tertiary hover:text-text-secondary underline"
        >
          Skip for now
        </button>
        <div className="flex gap-2">
          {step > 0 && (
            <button
              onClick={prev}
              className="flex items-center gap-1 px-4 py-2 text-sm font-bold uppercase tracking-wider border border-outline/25 rounded-sm hover:text-primary hover:border-primary/40"
            >
              <ChevronLeft size={14} />
              Back
            </button>
          )}
          {step < 4 ? (
            <button
              onClick={next}
              className="flex items-center gap-1 px-5 py-2 text-sm font-bold uppercase tracking-wider bg-primary text-background rounded-sm hover:bg-primary-dark"
            >
              Next
              <ChevronRight size={14} />
            </button>
          ) : (
            <button
              onClick={finish}
              className="flex items-center gap-1 px-5 py-2 text-sm font-bold uppercase tracking-wider bg-success text-background rounded-sm hover:brightness-110"
            >
              <Check size={14} />
              Finish
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
