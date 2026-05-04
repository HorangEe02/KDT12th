"use client";

import { useCallback, useRef } from "react";

/**
 * 반경 조절 컨트롤 — 슬라이더 + 프리셋 버튼 병행.
 *
 * - 슬라이더: 300m ~ 5000m 연속 조절 (step=100m)
 * - 프리셋:  300m / 500m / 1km / 2km / 5km 원클릭
 * - 슬라이더 드래그 중에는 debounce(300ms) 후 onChange 호출
 * - 프리셋 클릭 시 즉시 onChange
 */

const PRESETS = [
  { label: "300m", value: 300 },
  { label: "500m", value: 500 },
  { label: "1km", value: 1000 },
  { label: "2km", value: 2000 },
  { label: "5km", value: 5000 },
] as const;

const MIN = 300;
const MAX = 5000;
const STEP = 100;

function formatRadius(m: number): string {
  return m >= 1000 ? `${(m / 1000).toFixed(m % 1000 === 0 ? 0 : 1)}km` : `${m}m`;
}

interface RadiusControlProps {
  value: number;
  onChange: (radius: number) => void;
}

export default function RadiusControl({ value, onChange }: RadiusControlProps) {
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleSlider = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const v = Number(e.target.value);
      // debounce: 드래그 중 API 호출 폭주 방지
      if (timerRef.current) clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => onChange(v), 300);
    },
    [onChange],
  );

  // 슬라이더 놓았을 때 즉시 반영
  const handleSliderEnd = useCallback(
    (e: React.SyntheticEvent<HTMLInputElement>) => {
      if (timerRef.current) clearTimeout(timerRef.current);
      onChange(Number(e.currentTarget.value));
    },
    [onChange],
  );

  const pct = ((value - MIN) / (MAX - MIN)) * 100;

  return (
    <div className="flex flex-col gap-2">
      {/* 프리셋 버튼 */}
      <div className="flex items-center gap-1.5 flex-wrap">
        <span className="text-[10px] font-bold text-text-tertiary uppercase tracking-[0.08em] mr-1">
          반경
        </span>
        {PRESETS.map((p) => (
          <button
            key={p.value}
            type="button"
            onClick={() => onChange(p.value)}
            className={`px-2 py-0.5 text-[11px] font-bold rounded-sm border transition-colors ${
              value === p.value
                ? "bg-primary/10 border-primary/40 text-primary"
                : "border-outline/25 text-text-tertiary hover:border-outline/40 hover:text-text-secondary"
            }`}
          >
            {p.label}
          </button>
        ))}
        {/* 현재 값이 프리셋이 아니면 표시 */}
        {!PRESETS.some((p) => p.value === value) && (
          <span className="text-[11px] font-mono font-bold text-primary ml-1">
            {formatRadius(value)}
          </span>
        )}
      </div>

      {/* 슬라이더 */}
      <div className="flex items-center gap-2">
        <span className="text-[9px] text-text-tertiary font-mono w-8 text-right">
          300m
        </span>
        <div className="relative flex-1 h-5 flex items-center">
          <input
            type="range"
            min={MIN}
            max={MAX}
            step={STEP}
            defaultValue={value}
            onChange={handleSlider}
            onMouseUp={handleSliderEnd}
            onTouchEnd={handleSliderEnd}
            aria-label="검색 반경 조절"
            className="w-full h-1.5 appearance-none bg-transparent cursor-pointer
              [&::-webkit-slider-runnable-track]:h-1.5
              [&::-webkit-slider-runnable-track]:rounded-full
              [&::-webkit-slider-thumb]:appearance-none
              [&::-webkit-slider-thumb]:w-4
              [&::-webkit-slider-thumb]:h-4
              [&::-webkit-slider-thumb]:rounded-full
              [&::-webkit-slider-thumb]:bg-primary
              [&::-webkit-slider-thumb]:border-2
              [&::-webkit-slider-thumb]:border-background
              [&::-webkit-slider-thumb]:shadow-md
              [&::-webkit-slider-thumb]:-mt-[5px]
              [&::-webkit-slider-thumb]:relative
              [&::-webkit-slider-thumb]:z-10
              [&::-moz-range-track]:h-1.5
              [&::-moz-range-track]:rounded-full
              [&::-moz-range-track]:bg-surface-2
              [&::-moz-range-thumb]:w-4
              [&::-moz-range-thumb]:h-4
              [&::-moz-range-thumb]:rounded-full
              [&::-moz-range-thumb]:bg-primary
              [&::-moz-range-thumb]:border-2
              [&::-moz-range-thumb]:border-background"
            style={{
              background: `linear-gradient(to right, var(--color-primary) 0%, var(--color-primary) ${pct}%, var(--color-surface-2) ${pct}%, var(--color-surface-2) 100%)`,
              borderRadius: "9999px",
            }}
          />
        </div>
        <span className="text-[9px] text-text-tertiary font-mono w-7">
          5km
        </span>
      </div>
    </div>
  );
}

export { formatRadius };
