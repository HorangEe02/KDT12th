"use client";

/**
 * 데스크톱 좌측 sticky 사이드바.
 * 모바일은 MobileFilterSheet (BottomSheet) 가 같은 FilterControls 를 사용.
 *
 * 반응형 너비:
 *   - md  (768–1023, iPad portrait): 216px + px-4     → 본문 공간 최대화
 *   - lg  (1024–1279, 노트북):        248px + px-5
 *   - xl  (1280+, 데스크톱):          280px + px-6
 *
 * 이전 고정 260px 는 iPad portrait 구간에서 본문을 508px 이내로 조여
 * 카드 그리드와 테이블이 붙어 보이는 문제가 있었음.
 */
import { SharePlanButton } from "@/components/badges/share-plan-button";
import { UserBadge } from "@/components/auth/user-badge";
import { FilterControls } from "./filter-controls";

export function FilterSidebar() {
  return (
    <aside className="sticky top-20 hidden h-[calc(100vh-5rem)] w-[216px] shrink-0 overflow-y-auto border-r border-se-outline-variant bg-se-surface-container-low px-4 py-6 md:block lg:w-[248px] lg:px-5 xl:w-[280px] xl:px-6">
      <div className="mb-5 border-b border-se-outline-variant pb-4">
        <UserBadge />
      </div>

      <h2 className="mb-4 font-display text-sm font-extrabold uppercase tracking-[0.14em] text-se-primary">
        🎽 원정 설정
      </h2>

      <FilterControls />

      <hr className="my-4 border-se-outline-variant" />

      <SharePlanButton variant="sidebar" pathname="/" />
    </aside>
  );
}
