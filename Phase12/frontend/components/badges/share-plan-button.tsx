"use client";

import { useState } from "react";
import { useFilters } from "@/lib/store/filters";
import { buildShareUrl } from "@/lib/share/serialize";
import { cn } from "@/lib/utils";

interface ShareButtonProps {
  pathname?: string;
  variant?: "sidebar" | "block";
}

export function SharePlanButton({
  pathname = "/",
  variant = "block",
}: ShareButtonProps) {
  const f = useFilters();
  const [state, setState] = useState<"idle" | "copied" | "error">("idle");
  const [url, setUrl] = useState<string | null>(null);

  async function share() {
    const origin =
      typeof window !== "undefined" ? window.location.origin : "";
    const built = buildShareUrl(origin, pathname, {
      team: f.team,
      start: f.dateStart,
      end: f.dateEnd,
      budget: f.budget,
      party: f.party,
      transport: f.transport,
    });
    setUrl(built);

    // Firestore 단축 링크 시도 (선택적 · 실패 시 long URL 유지)
    let shortUrl: string | null = null;
    try {
      const resp = await fetch("/api/plans", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          filters: {
            team: f.team,
            dateRange: [f.dateStart, f.dateEnd],
            budget: f.budget,
            party: f.party,
            transport: f.transport,
          },
        }),
      });
      if (resp.ok) {
        const data = (await resp.json()) as { id?: string };
        if (data.id) shortUrl = `${origin}/share/${data.id}`;
      }
    } catch {
      // 무시 — long URL 사용
    }

    const finalUrl = shortUrl ?? built;
    setUrl(finalUrl);

    try {
      await navigator.clipboard.writeText(finalUrl);
      setState("copied");
      setTimeout(() => setState("idle"), 2500);
    } catch {
      setState("error");
    }
  }

  const isSidebar = variant === "sidebar";

  return (
    <div className={isSidebar ? "space-y-1.5" : "flex flex-col gap-2"}>
      <button
        onClick={share}
        className={cn(
          "flex items-center justify-center gap-1.5 rounded-xl bg-se-primary text-white font-display font-bold shadow-[0_4px_12px_rgba(0,25,60,0.18)] transition-transform hover:-translate-y-0.5",
          isSidebar ? "w-full px-3 py-2 text-xs" : "px-4 py-2 text-sm",
        )}
      >
        <span className="material-symbols-outlined text-[16px]">share</span>
        {state === "copied" ? "✅ 복사됨" : "🔗 원정 계획 공유"}
      </button>
      {url ? (
        <div
          className={cn(
            "rounded-lg bg-se-surface-container-low px-2 py-1 font-mono text-[0.6rem] text-se-on-surface-variant",
            isSidebar ? "truncate" : "break-all",
          )}
          title={url}
        >
          {url}
        </div>
      ) : null}
      {state === "error" ? (
        <p className="text-[0.65rem] text-red-700">
          클립보드 접근 권한이 없어요. 위 링크를 수동으로 복사하세요.
        </p>
      ) : null}
    </div>
  );
}
