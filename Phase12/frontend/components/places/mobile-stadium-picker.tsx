"use client";

import Link from "next/link";
import { useSearchParams, usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import type { Stadium } from "@/lib/types";

/**
 * 모바일 전용 — 구장 선택 chip horizontal scroll.
 * mockup: uiux/mobile_uiux/eats_stays_mobile/code.html § Filter Chips 패턴
 *
 * URL `?s=잠실` 갱신.
 */
interface MobileStadiumPickerProps {
  stadiums: Stadium[];
  selected: string;
}

export function MobileStadiumPicker({
  stadiums,
  selected,
}: MobileStadiumPickerProps) {
  const pathname = usePathname();
  const searchParams = useSearchParams();

  function buildHref(short: string): string {
    const p = new URLSearchParams(searchParams.toString());
    p.set("s", short);
    return `${pathname}?${p.toString()}`;
  }

  return (
    <div className="-mx-4 flex gap-2 overflow-x-auto px-4 pb-1 [&::-webkit-scrollbar]:hidden">
      {stadiums.map((s) => {
        const active = s.short_name === selected;
        return (
          <Link
            key={s.short_name}
            href={buildHref(s.short_name)}
            scroll={false}
            className={cn(
              "inline-flex shrink-0 items-center gap-1.5 rounded-full px-4 py-2 font-display text-xs font-bold no-underline transition-colors",
              active
                ? "bg-se-primary text-white shadow-[0_2px_8px_rgba(0,25,60,0.2)]"
                : "border border-se-outline-variant/30 bg-se-surface-container-lowest text-se-on-surface hover:bg-se-surface-container-low",
            )}
            aria-current={active ? "page" : undefined}
          >
            <span className="text-sm">⚾</span>
            {s.short_name}
          </Link>
        );
      })}
    </div>
  );
}
