"use client";

export type DiscoverSortKey =
  | "composite"
  | "sentiment"
  | "distance"
  | "rating"
  | "price";

const OPTIONS: { value: DiscoverSortKey; label: string; ko: string }[] = [
  { value: "composite", label: "Composite", ko: "종합 점수" },
  { value: "sentiment", label: "Sentiment", ko: "😊 감성 점수" },
  { value: "distance", label: "Distance", ko: "가까운 순" },
  { value: "rating", label: "Rating", ko: "평점 순" },
  { value: "price", label: "Price", ko: "가격 낮은 순" },
];

export default function SortDropdown({
  value,
  onChange,
}: {
  value: DiscoverSortKey;
  onChange: (v: DiscoverSortKey) => void;
}) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-[10px] font-bold uppercase tracking-[0.1em] text-text-tertiary">
        Sort
      </span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value as DiscoverSortKey)}
        className="bg-surface-1 border border-outline/15 rounded-sm text-xs text-text-secondary px-3 py-1.5 outline-none focus:border-primary/40 font-mono"
      >
        {OPTIONS.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label} — {o.ko}
          </option>
        ))}
      </select>
    </div>
  );
}
