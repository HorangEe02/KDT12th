import { loadPOIsByStadium, loadStadiums } from "@/lib/data/loaders";
import { StadiumPicker } from "@/components/places/stadium-picker";
import { CategoryTabs } from "@/components/places/category-tabs";
import { ScatterPlaces } from "@/components/places/scatter-places";
import { PoiCard } from "@/components/places/poi-card";
import { PlacesMapShell } from "@/components/places/places-map-shell";
import { PlacesMobileView } from "@/components/places/places-mobile-view";

interface PlacesPageProps {
  searchParams: Promise<{
    s?: string;
    cat?: string;
    p?: string;
    q?: string;
    /** 모바일 POI 리스트 페이지네이션 limit (기본 12, 12씩 증가) */
    limit?: string;
  }>;
}

const DEFAULT_LIMIT = 12;
const MAX_LIMIT = 500;

type Category = "food" | "stay" | "tour";
const CAT_LABEL: Record<Category, string> = {
  food: "음식점",
  stay: "숙박",
  tour: "관광지",
};

export default async function PlacesPage({ searchParams }: PlacesPageProps) {
  const p = await searchParams;
  const stadiums = await loadStadiums();
  const shortNames = stadiums.map((s) => s.short_name);

  const short =
    p.s && shortNames.includes(p.s) ? p.s : stadiums[0].short_name;
  const category: Category =
    p.cat === "stay" || p.cat === "tour" ? p.cat : "food";
  const stadium = stadiums.find((s) => s.short_name === short)!;

  const [food, stay, tour] = await Promise.all([
    loadPOIsByStadium(`${short}_food`),
    loadPOIsByStadium(`${short}_stay`),
    loadPOIsByStadium(`${short}_tour`),
  ]);

  const byCat: Record<Category, typeof food> = { food, stay, tour };
  const active = byCat[category]
    .slice()
    .sort((a, b) => (a.dist_m ?? Infinity) - (b.dist_m ?? Infinity));

  const top10 = active.slice(0, 10);
  const selectedId =
    p.p && top10.some((poi) => poi.content_id === p.p) ? p.p : undefined;

  const parsedLimit = Number.parseInt(p.limit ?? "", 10);
  const mobileLimit =
    Number.isFinite(parsedLimit) && parsedLimit > 0
      ? Math.min(parsedLimit, MAX_LIMIT)
      : DEFAULT_LIMIT;

  return (
    <>
      {/* === Mobile === */}
      <PlacesMobileView
        stadium={stadium}
        allStadiums={stadiums}
        category={category}
        pois={active}
        counts={{ food: food.length, stay: stay.length, tour: tour.length }}
        searchQuery={p.q}
        limit={mobileLimit}
      />

      {/* === Desktop === */}
    <section className="hidden space-y-5 md:block">
      <header>
        <h1 className="font-display text-2xl font-extrabold text-se-primary">
          🍽️ 경기장 주변 맛집 · 숙소 · 관광지
        </h1>
        <p className="text-sm text-se-on-surface-variant">
          {stadium.stadium_name} · {stadium.city}
        </p>
      </header>

      <StadiumPicker stadiums={stadiums} selected={short} />

      <div className="grid grid-cols-3 gap-3">
        <Metric label="🍽️ 음식점" value={`${food.length}곳`} />
        <Metric label="🏨 숙박" value={`${stay.length}곳`} />
        <Metric label="🎡 관광지" value={`${tour.length}곳`} />
      </div>

      <CategoryTabs
        active={category}
        counts={{ food: food.length, stay: stay.length, tour: tour.length }}
      />

      <section>
        <div className="mb-3 flex items-end justify-between">
          <h3 className="font-display text-sm font-extrabold uppercase tracking-[0.12em] text-se-on-surface-variant">
            📍 TOP 10 위치 지도
          </h3>
          <span className="text-[0.7rem] text-se-on-surface-variant">
            점선 원 = 경기장 반경 500m · 마커 클릭 → 카드로 이동
          </span>
        </div>
        <PlacesMapShell
          stadium={stadium}
          pois={top10}
          category={category}
          selectedId={selectedId}
          height={380}
        />
      </section>

      <section>
        <h3 className="mb-3 font-display text-sm font-extrabold uppercase tracking-[0.12em] text-se-on-surface-variant">
          🧾 가까운 {CAT_LABEL[category]} TOP 10
        </h3>
        {top10.length === 0 ? (
          <div className="rounded-2xl border border-se-outline-variant bg-se-surface-container-low px-5 py-8 text-center text-sm text-se-on-surface-variant">
            POI 데이터가 없습니다.
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
            {top10.map((poi) => (
              <div
                key={poi.content_id}
                id={`poi-card-${poi.content_id}`}
                className="rounded-2xl transition-shadow"
              >
                <PoiCard poi={poi} />
              </div>
            ))}
          </div>
        )}
      </section>

      <section>
        <h3 className="mb-3 font-display text-sm font-extrabold uppercase tracking-[0.12em] text-se-on-surface-variant">
          📊 거리 × 평점 산점도
        </h3>
        <div className="rounded-2xl border border-se-outline-variant bg-se-surface-container-lowest p-3">
          <ScatterPlaces places={active} category={category} />
        </div>
        <p className="mt-2 text-xs text-se-on-surface-variant">
          💡 마커 크기는 경기장과의 가까운 정도를 표현합니다. 평점은 TourAPI
          실데이터 연동 전 재현 가능한 더미값(3.5~4.8)으로 표시됩니다.
        </p>
      </section>
    </section>
    </>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border-l-4 border-se-secondary-fixed bg-se-surface-container-low px-4 py-3">
      <div className="font-display text-[0.65rem] font-bold uppercase tracking-[0.12em] text-se-on-surface-variant">
        {label}
      </div>
      <div className="font-display text-xl font-extrabold text-se-primary">
        {value}
      </div>
    </div>
  );
}
