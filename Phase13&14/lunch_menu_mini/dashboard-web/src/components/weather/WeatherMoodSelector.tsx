"use client";

import type { MoodOption } from "@/lib/types";

interface Props {
  options: MoodOption[];
  selected: string | null;
  onSelect: (id: string) => void;
  weatherSummary: string;
}

export default function WeatherMoodSelector({
  options,
  selected,
  onSelect,
  weatherSummary,
}: Props) {
  return (
    <div className="bento-card mb-5">
      <div className="flex items-center gap-2 mb-3">
        <h3 className="text-base font-heading font-bold text-text-primary uppercase tracking-[0.04em]">
          Today&apos;s Mood
        </h3>
        <span className="text-xs text-text-tertiary font-mono">
          {weatherSummary}
        </span>
      </div>
      <p
        className="text-[11px] text-text-tertiary mb-4"
        style={{ fontFamily: "var(--font-ko)" }}
      >
        오늘 기분에 맞는 옵션을 선택하면 맞춤 추천을 받을 수 있어요
      </p>

      <div className="flex flex-wrap gap-2">
        {options.map((opt) => {
          const isActive = selected === opt.id;
          return (
            <button
              key={opt.id}
              onClick={() => onSelect(opt.id)}
              className={`
                group flex items-center gap-2 px-4 py-2.5 rounded-sm border
                transition-all duration-150 cursor-pointer
                ${
                  isActive
                    ? "bg-primary/10 border-primary/60 ring-1 ring-primary/30"
                    : "bg-surface-2 border-outline/20 hover:border-primary/40 hover:bg-primary/5"
                }
              `}
            >
              <span className="text-xl" aria-hidden>
                {opt.emoji}
              </span>
              <div className="text-left">
                <div
                  className={`text-sm font-bold ${
                    isActive ? "text-primary" : "text-text-primary"
                  }`}
                  style={{ fontFamily: "var(--font-ko)" }}
                >
                  {opt.label}
                </div>
                <div
                  className="text-[10px] text-text-tertiary"
                  style={{ fontFamily: "var(--font-ko)" }}
                >
                  {opt.description}
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
