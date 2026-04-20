"use client";

import { useState, useTransition } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

/**
 * 모바일 전용 — Search bar (rounded full + tune button).
 * mockup: uiux/mobile_uiux/eats_stays_mobile/code.html § Header & Search
 */
interface PlacesSearchBarProps {
  placeholder?: string;
  initialValue?: string;
}

export function PlacesSearchBar({
  placeholder = "주변 가볼 만한 곳 검색",
  initialValue = "",
}: PlacesSearchBarProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [, startTransition] = useTransition();
  const [value, setValue] = useState(initialValue);

  function pushSearch(q: string) {
    const p = new URLSearchParams(searchParams.toString());
    if (q.trim()) p.set("q", q.trim());
    else p.delete("q");
    startTransition(() => {
      router.replace(`${pathname}?${p.toString()}`, { scroll: false });
    });
  }

  return (
    <div className="relative flex items-center gap-2 rounded-full border border-se-outline-variant/15 bg-se-surface-container-lowest px-4 py-3 shadow-[0_4px_24px_rgba(0,0,0,0.06)]">
      <span className="material-symbols-outlined text-se-outline">search</span>
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") pushSearch(value);
        }}
        placeholder={placeholder}
        className="flex-1 border-none bg-transparent p-0 font-body text-sm font-medium text-se-on-surface placeholder:text-se-outline focus:outline-none focus:ring-0"
      />
      <button
        type="button"
        onClick={() => pushSearch(value)}
        className="rounded-full bg-se-surface-container-low p-2 text-se-on-surface transition-colors hover:bg-se-surface-variant"
        aria-label="필터"
      >
        <span className="material-symbols-outlined text-[20px]">tune</span>
      </button>
    </div>
  );
}
