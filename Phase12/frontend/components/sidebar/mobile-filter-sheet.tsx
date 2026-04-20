"use client";

import { useEffect } from "react";
import { usePathname } from "next/navigation";
import { BottomSheet } from "@/components/ui/bottom-sheet";
import { FilterControls } from "./filter-controls";
import { SharePlanButton } from "@/components/badges/share-plan-button";
import { UserBadge } from "@/components/auth/user-badge";
import { useMobileSheet } from "@/lib/store/mobile-sheet";
import { useTripStore } from "@/lib/store/trip";

/**
 * 모바일 전용 — 사이드바 필터 BottomSheet.
 * (shell)/layout.tsx 에 한 번 mount, useMobileSheet 글로벌 store 로 제어.
 *
 * 페이지 navigate 시 자동 close (usePathname effect).
 */
export function MobileFilterSheet() {
  const open = useMobileSheet((s) => s.active === "filter");
  const close = useMobileSheet((s) => s.close);
  const openSheet = useMobileSheet((s) => s.open);
  const pathname = usePathname();
  const isMapPage = pathname === "/map";
  const waypointCount = useTripStore((s) => s.waypoints.length);

  // 페이지 이동 시 자동 close (sheet 가 stale 상태로 남지 않게)
  useEffect(() => {
    close();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pathname]);

  return (
    <BottomSheet
      open={open}
      onOpenChange={(o) => (o ? null : close())}
      title="🎽 원정 설정"
      snapPoints={["62%", "92%"]}
    >
      {/* 사용자 배지 (로그인/회원가입) */}
      <div className="mb-4 border-b border-se-outline-variant/40 pb-4">
        <UserBadge />
      </div>

      {/* 필터 폼 */}
      <FilterControls closeSheetOnGenerate />

      {/* /map 페이지 컨텍스트 — 길찾기 빠른 진입 */}
      {isMapPage ? (
        <>
          <hr className="my-4 border-se-outline-variant" />
          <h3 className="mb-3 font-display text-[0.72rem] font-bold uppercase tracking-[0.12em] text-se-on-surface-variant">
            🗺️ 길찾기 빠른 변경
          </h3>
          <div className="grid grid-cols-2 gap-2">
            <RouteQuickButton
              icon="my_location"
              label="출발지 변경"
              onClick={() => openSheet("origin")}
            />
            <RouteQuickButton
              icon="sports_baseball"
              label="경기/도착지"
              onClick={() => openSheet("game")}
            />
            <RouteQuickButton
              icon="add_location_alt"
              label="경유지 추가"
              badge={waypointCount > 0 ? `${waypointCount}` : undefined}
              onClick={() => openSheet("waypoint")}
            />
            <RouteQuickButton
              icon="navigation"
              label="길 안내 시작"
              variant="primary"
              onClick={() => openSheet("trip-confirm")}
            />
          </div>
        </>
      ) : null}

      {/* 공유 */}
      <hr className="my-4 border-se-outline-variant" />
      <SharePlanButton variant="sidebar" pathname="/" />
    </BottomSheet>
  );
}

function RouteQuickButton({
  icon,
  label,
  onClick,
  badge,
  variant = "default",
}: {
  icon: string;
  label: string;
  onClick: () => void;
  badge?: string;
  variant?: "default" | "primary";
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`relative flex flex-col items-center gap-1 rounded-xl border px-3 py-3 transition-all active:scale-95 ${
        variant === "primary"
          ? "border-se-primary bg-gradient-to-br from-se-primary to-se-primary-container text-white shadow-[0_4px_12px_rgba(0,25,60,0.2)]"
          : "border-se-outline-variant bg-white text-se-on-surface hover:border-se-primary"
      }`}
    >
      {badge ? (
        <span className="absolute right-2 top-2 flex h-5 w-5 items-center justify-center rounded-full bg-se-secondary text-[10px] font-bold text-white">
          {badge}
        </span>
      ) : null}
      <span className="material-symbols-outlined text-[22px]">{icon}</span>
      <span className="font-display text-[11px] font-bold">{label}</span>
    </button>
  );
}

