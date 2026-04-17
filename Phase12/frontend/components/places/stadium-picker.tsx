"use client";

import { useTransition } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import type { Stadium } from "@/lib/types";
import { cn } from "@/lib/utils";

interface StadiumPickerProps {
  stadiums: Stadium[];
  selected: string;
}

export function StadiumPicker({ stadiums, selected }: StadiumPickerProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [, startTransition] = useTransition();

  function pick(short: string) {
    const p = new URLSearchParams(searchParams.toString());
    p.set("s", short);
    startTransition(() => {
      router.replace(`${pathname}?${p.toString()}`, { scroll: false });
    });
  }

  return (
    <div className="flex flex-wrap gap-1.5">
      {stadiums.map((s) => {
        const active = s.short_name === selected;
        return (
          <button
            key={s.short_name}
            onClick={() => pick(s.short_name)}
            className={cn(
              "rounded-full border px-3 py-1 text-xs font-bold transition-colors",
              active
                ? "border-se-primary bg-se-primary text-white"
                : "border-se-outline-variant bg-white text-se-on-surface hover:border-se-primary",
            )}
            title={s.stadium_name}
          >
            {s.short_name}
          </button>
        );
      })}
    </div>
  );
}
