import Link from "next/link";
import { PlacesSearchBar } from "./places-search-bar";
import { PlacesFilterChips } from "./places-filter-chips";
import { PoiCardMobile } from "./poi-card-mobile";
import { MobileStadiumPicker } from "./mobile-stadium-picker";
import { LoadMoreButton } from "./load-more-button";
import { MobileSettingsButton } from "@/components/nav/mobile-settings-button";
import type { POI, Stadium } from "@/lib/types";

/**
 * 모바일 전용 — Places 페이지 view.
 * mockup: uiux/mobile_uiux/eats_stays_mobile/code.html
 *
 * 페이지네이션: URL `?limit=N` (기본 12, 12개씩 증가) 기반.
 * LoadMoreButton 이 server component 를 재검증 → slice 범위 확장.
 */
interface PlacesMobileViewProps {
  stadium: Stadium;
  /** 모든 구장 (chip selector 용) */
  allStadiums: Stadium[];
  category: "food" | "stay" | "tour";
  pois: POI[];
  counts: { food: number; stay: number; tour: number };
  searchQuery?: string;
  /** 표시할 POI 최대 개수 (기본 12, URL `?limit=` 에서 파생) */
  limit?: number;
}

const CAT_KO: Record<"food" | "stay" | "tour", string> = {
  food: "음식점",
  stay: "숙박",
  tour: "관광지",
};

export function PlacesMobileView({
  stadium,
  allStadiums,
  category,
  pois,
  counts,
  searchQuery,
  limit = 12,
}: PlacesMobileViewProps) {
  const q = searchQuery?.toLowerCase() ?? "";
  const filtered = q
    ? pois.filter((p) => p.title.toLowerCase().includes(q))
    : pois;
  const visible = filtered.slice(0, limit);

  return (
    <div className="space-y-5 md:hidden">
      {/* Header */}
      <header className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <h1 className="font-display text-2xl font-black tracking-tight text-se-primary">
            가볼 만한 곳
          </h1>
          <p className="mt-0.5 font-body text-xs text-se-on-surface-variant">
            {stadium.stadium_name} 주변 · {filtered.length}건
          </p>
        </div>
        <MobileSettingsButton ariaLabel="원정 설정 열기" />
      </header>

      {/* Stadium picker chip — 구장 변경 */}
      <MobileStadiumPicker stadiums={allStadiums} selected={stadium.short_name} />

      {/* Search bar */}
      <PlacesSearchBar initialValue={searchQuery ?? ""} />

      {/* Filter chips */}
      <PlacesFilterChips active={category} counts={counts} />

      {/* POI list */}
      <section>
        <h2 className="mb-3 font-display text-base font-bold tracking-tight text-se-on-surface">
          가까운 {CAT_KO[category]}
        </h2>
        {filtered.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-se-outline-variant bg-se-surface-container-low p-8 text-center text-sm text-se-on-surface-variant">
            검색 결과가 없습니다.
          </div>
        ) : (
          <>
            <div className="flex flex-col gap-3">
              {visible.map((poi) => (
                <PoiCardMobile
                  key={poi.content_id}
                  poi={poi}
                  category={category}
                  recommended={typeof poi.dist_m === "number" && poi.dist_m <= 500}
                  stadiumName={stadium.short_name}
                />
              ))}
            </div>
            <LoadMoreButton currentLimit={limit} total={filtered.length} />
          </>
        )}
      </section>

      {/* Floating Map FAB */}
      <Link
        href={`/map?team=&stadium=${encodeURIComponent(stadium.short_name)}`}
        className="fixed bottom-28 right-4 z-40 flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-se-primary to-se-primary-container text-white shadow-[0_8px_24px_rgba(0,25,60,0.25)] transition-transform hover:scale-105 active:scale-95"
        aria-label="지도 보기"
      >
        <span className="material-symbols-outlined text-[24px]">map</span>
      </Link>
    </div>
  );
}
