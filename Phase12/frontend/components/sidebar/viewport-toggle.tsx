"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { cn } from "@/lib/utils";

/**
 * 사이드바 상단에 표시하는 데스크톱/모바일 뷰포트 토글.
 * URL `?device=mobile|web` 쿼리 동기화.
 */
export function ViewportToggle() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const current = searchParams.get("device") === "mobile" ? "mobile" : "web";

  function set(device: "web" | "mobile") {
    const p = new URLSearchParams(searchParams.toString());
    if (device === "mobile") p.set("device", "mobile");
    else p.delete("device");
    const q = p.toString();
    router.replace(`${pathname}${q ? `?${q}` : ""}`, { scroll: false });
  }

  return (
    <div className="flex items-center gap-1 rounded-full border border-se-outline-variant bg-white p-0.5">
      {(["web", "mobile"] as const).map((d) => (
        <button
          key={d}
          onClick={() => set(d)}
          aria-pressed={current === d}
          className={cn(
            "flex items-center gap-1 rounded-full px-2.5 py-1 text-[0.65rem] font-bold uppercase tracking-wider transition-colors",
            current === d
              ? "bg-se-primary text-white"
              : "text-se-on-surface-variant",
          )}
        >
          <span className="material-symbols-outlined text-[14px]">
            {d === "web" ? "desktop_windows" : "smartphone"}
          </span>
          {d}
        </button>
      ))}
    </div>
  );
}
