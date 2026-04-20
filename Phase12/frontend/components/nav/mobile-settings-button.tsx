"use client";

import { useMobileSheet } from "@/lib/store/mobile-sheet";
import { cn } from "@/lib/utils";

/**
 * 모바일 페이지 우상단의 tune 버튼.
 * 클릭 시 MobileFilterSheet (글로벌 사이드바 BottomSheet) 열림.
 */
interface MobileSettingsButtonProps {
  /** 둥근 chip 스타일 (어두운 배경 위 floating) — false 면 단순 아이콘 버튼 */
  floating?: boolean;
  className?: string;
  ariaLabel?: string;
}

export function MobileSettingsButton({
  floating = false,
  className,
  ariaLabel = "원정 설정",
}: MobileSettingsButtonProps) {
  const open = useMobileSheet((s) => s.open);
  return (
    <button
      type="button"
      onClick={() => open("filter")}
      aria-label={ariaLabel}
      className={cn(
        floating
          ? "flex h-11 w-11 items-center justify-center rounded-full bg-white/95 text-se-on-surface shadow-[0_4px_24px_rgba(25,28,29,0.12)] backdrop-blur-md transition-colors hover:bg-se-surface active:scale-95"
          : "flex h-10 w-10 items-center justify-center rounded-full bg-se-surface-container-low text-se-primary shadow-[0_4px_24px_rgba(25,28,29,0.04)] active:scale-95",
        className,
      )}
    >
      <span className="material-symbols-outlined text-[22px]">tune</span>
    </button>
  );
}
