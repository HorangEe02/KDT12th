"use client";

import { useTransition } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { cn } from "@/lib/utils";

const CATS = [
  { key: "food" as const, label: "🍽️ 음식점" },
  { key: "stay" as const, label: "🏨 숙박" },
  { key: "tour" as const, label: "🎡 관광지" },
];

export function CategoryTabs({
  active,
  counts,
}: {
  active: "food" | "stay" | "tour";
  counts: Record<"food" | "stay" | "tour", number>;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [, startTransition] = useTransition();

  function pick(cat: string) {
    const p = new URLSearchParams(searchParams.toString());
    p.set("cat", cat);
    startTransition(() => {
      router.replace(`${pathname}?${p.toString()}`, { scroll: false });
    });
  }

  return (
    <div className="flex gap-1 border-b border-se-outline-variant">
      {CATS.map((c) => {
        const selected = active === c.key;
        return (
          <button
            key={c.key}
            onClick={() => pick(c.key)}
            aria-selected={selected}
            className={cn(
              "-mb-px rounded-t-xl border-b-2 px-4 py-2 font-display text-sm font-bold transition-colors",
              selected
                ? "border-se-primary text-se-primary"
                : "border-transparent text-se-on-surface-variant hover:text-se-primary",
            )}
          >
            {c.label}
            <span className="ml-1.5 rounded-full bg-se-surface-container-low px-1.5 py-0.5 text-[0.65rem] text-se-on-surface-variant">
              {counts[c.key]}
            </span>
          </button>
        );
      })}
    </div>
  );
}
