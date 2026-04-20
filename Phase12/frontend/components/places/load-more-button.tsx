"use client";

import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { useTransition } from "react";
import { cn } from "@/lib/utils";

/**
 * /places 모바일 — POI 리스트 "더 보기" 버튼.
 * URL `?limit=N` 을 `N + step` 으로 갱신하여 서버 컴포넌트가 slice 범위를 확장.
 *
 * - `useTransition` 으로 페이지 재검증 중 버튼 pending 표시.
 * - 기존 query (s/cat/q/team/...) 보존.
 */
interface LoadMoreButtonProps {
  currentLimit: number;
  total: number;
  step?: number;
}

export function LoadMoreButton({
  currentLimit,
  total,
  step = 12,
}: LoadMoreButtonProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [pending, startTransition] = useTransition();

  const shown = Math.min(currentLimit, total);
  const remaining = total - shown;
  if (remaining <= 0) return null;

  const nextLimit = Math.min(currentLimit + step, total);
  const nextStep = Math.min(step, remaining);

  function handleClick() {
    const params = new URLSearchParams(searchParams.toString());
    params.set("limit", String(nextLimit));
    startTransition(() => {
      router.replace(`${pathname}?${params.toString()}`, { scroll: false });
    });
  }

  return (
    <div className="mt-4 flex flex-col items-center gap-1.5">
      <button
        type="button"
        onClick={handleClick}
        disabled={pending}
        className={cn(
          "flex h-11 min-w-[200px] items-center justify-center gap-2 rounded-full border border-se-outline-variant bg-white px-5 font-display text-sm font-bold text-se-primary shadow-[0_2px_8px_rgba(0,0,0,0.04)] transition-all active:scale-95",
          pending && "opacity-60",
        )}
        aria-label={`${nextStep}개 더 불러오기`}
      >
        {pending ? (
          <>
            <span className="h-2 w-2 animate-pulse rounded-full bg-se-primary" />
            <span>불러오는 중…</span>
          </>
        ) : (
          <>
            <span className="material-symbols-outlined text-[18px]">
              expand_more
            </span>
            <span>
              {nextStep}개 더 보기 ({shown}/{total})
            </span>
          </>
        )}
      </button>
    </div>
  );
}
