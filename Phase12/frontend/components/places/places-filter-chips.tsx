"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { cn } from "@/lib/utils";

/**
 * 모바일 전용 — 카테고리 필터 chips (horizontal scroll).
 * mockup: uiux/mobile_uiux/eats_stays_mobile/code.html § Filter Chips
 */
interface FilterChipsProps {
  active: "food" | "stay" | "tour";
  counts: { food: number; stay: number; tour: number };
}

const CHIPS: Array<{ key: "food" | "stay" | "tour"; label: string; emoji: string }> = [
  { key: "food", label: "음식점", emoji: "🍽️" },
  { key: "stay", label: "숙박", emoji: "🏨" },
  { key: "tour", label: "관광", emoji: "🎡" },
];

export function PlacesFilterChips({ active, counts }: FilterChipsProps) {
  const pathname = usePathname();
  const searchParams = useSearchParams();

  function buildHref(cat: string): string {
    const p = new URLSearchParams(searchParams.toString());
    p.set("cat", cat);
    return `${pathname}?${p.toString()}`;
  }

  return (
    <div className="-mx-4 flex gap-2 overflow-x-auto px-4 pb-1 [&::-webkit-scrollbar]:hidden">
      {CHIPS.map((c) => {
        const isActive = active === c.key;
        return (
          <Link
            key={c.key}
            href={buildHref(c.key)}
            scroll={false}
            className={cn(
              "inline-flex shrink-0 items-center gap-1.5 rounded-full px-4 py-2 font-display text-xs font-bold uppercase tracking-wider no-underline transition-colors",
              isActive
                ? "bg-se-secondary-fixed text-se-on-secondary-fixed shadow-[0_2px_8px_rgba(163,246,156,0.4)]"
                : "border border-se-outline-variant/30 bg-se-surface-container-lowest text-se-on-surface hover:bg-se-surface-container-low",
            )}
          >
            <span className="text-sm">{c.emoji}</span>
            {c.label}
            <span
              className={cn(
                "rounded-full px-1.5 py-0.5 text-[9px]",
                isActive
                  ? "bg-se-on-secondary-fixed/15"
                  : "bg-se-surface-container",
              )}
            >
              {counts[c.key]}
            </span>
          </Link>
        );
      })}
    </div>
  );
}
