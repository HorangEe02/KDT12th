"use client";

import { useRouter } from "next/navigation";
import { MobileSettingsButton } from "@/components/nav/mobile-settings-button";

/**
 * 모바일 전용 — 풀스크린 지도 위에 floating 되는 top action bar.
 * mockup: uiux/mobile_uiux/itinerary_route_map_mobile/code.html § Top Action Bar
 */
interface FloatingTopBarProps {
  title: string;
}

export function FloatingTopBar({ title }: FloatingTopBarProps) {
  const router = useRouter();

  return (
    <div className="pointer-events-none fixed top-16 left-0 right-0 z-40 flex items-center justify-between px-4 pt-2 md:hidden">
      <button
        type="button"
        onClick={() => router.back()}
        className="pointer-events-auto flex h-11 w-11 items-center justify-center rounded-full bg-white/95 shadow-[0_4px_24px_rgba(25,28,29,0.12)] backdrop-blur-md transition-colors hover:bg-se-surface active:scale-95"
        aria-label="뒤로 가기"
      >
        <span className="material-symbols-outlined text-se-on-surface">
          arrow_back
        </span>
      </button>

      <div className="pointer-events-auto flex items-center gap-2 rounded-full bg-white/95 px-4 py-2 shadow-[0_4px_24px_rgba(25,28,29,0.12)] backdrop-blur-md">
        <span className="material-symbols-outlined text-sm text-se-primary">
          my_location
        </span>
        <span className="font-display text-sm font-bold tracking-tight text-se-primary">
          {title}
        </span>
      </div>

      <div className="pointer-events-auto">
        <MobileSettingsButton floating ariaLabel="원정 설정 열기" />
      </div>
    </div>
  );
}
