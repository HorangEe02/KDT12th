import { cn } from "@/lib/utils";
import type { POI } from "@/lib/types";

/**
 * 모바일 전용 — Hotel-style 카드 (썸네일 1/3 + 정보 2/3).
 * mockup: uiux/mobile_uiux/eats_stays_mobile/code.html § Hotel Card
 */
interface PoiCardMobileProps {
  poi: POI;
  category: "food" | "stay" | "tour";
  recommended?: boolean;  // 반경 500m 이내 = 추천
  stadiumName: string;
}

const CATEGORY_GRADIENT: Record<string, string> = {
  food: "from-orange-200 to-red-300",
  stay: "from-blue-200 to-indigo-300",
  tour: "from-emerald-200 to-teal-300",
};

const CATEGORY_ICON: Record<string, string> = {
  food: "restaurant",
  stay: "hotel",
  tour: "landscape",
};

const CATEGORY_LABEL: Record<string, string> = {
  food: "음식점",
  stay: "숙박",
  tour: "관광",
};

function formatDistance(m?: number): string {
  if (!m) return "—";
  return m >= 1000 ? `${(m / 1000).toFixed(1)}km` : `${Math.round(m)}m`;
}

function pseudoRating(contentId: string): string {
  // 결정적 더미 평점 3.5~4.8
  let h = 0;
  for (let i = 0; i < contentId.length; i++) h = (h * 31 + contentId.charCodeAt(i)) >>> 0;
  return (3.5 + ((h % 130) / 100)).toFixed(1);
}

export function PoiCardMobile({
  poi,
  category,
  recommended,
  stadiumName,
}: PoiCardMobileProps) {
  const rating = pseudoRating(poi.content_id);
  const distance = formatDistance(poi.dist_m);
  const kakaoUrl = `https://map.kakao.com/link/map/${encodeURIComponent(poi.title)},${poi.lat},${poi.lng}`;

  return (
    <a
      href={kakaoUrl}
      target="_blank"
      rel="noreferrer"
      className="relative flex h-32 overflow-hidden rounded-xl border border-se-outline-variant/15 bg-se-surface-container-lowest no-underline shadow-[0_4px_24px_rgba(0,0,0,0.04)] transition-shadow hover:shadow-[0_8px_24px_rgba(0,0,0,0.08)]"
    >
      {recommended ? (
        <div className="absolute left-0 top-0 bottom-0 z-10 w-1 bg-se-secondary-fixed" />
      ) : null}

      {/* Thumbnail (1/3) */}
      <div className="relative h-full w-1/3 shrink-0">
        {poi.first_image ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={poi.first_image.replace(/^http:\/\//, "https://")}
            alt=""
            className="h-full w-full object-cover"
            loading="lazy"
          />
        ) : (
          <div
            className={cn(
              "flex h-full w-full items-center justify-center bg-gradient-to-br",
              CATEGORY_GRADIENT[category] ?? "from-slate-200 to-slate-300",
            )}
          >
            <span className="material-symbols-outlined text-[36px] text-white/80">
              {CATEGORY_ICON[category] ?? "place"}
            </span>
          </div>
        )}
        {/* Rating badge */}
        <div className="absolute left-2 top-2 flex items-center gap-1 rounded bg-white/90 px-1.5 py-0.5 shadow-sm backdrop-blur-sm">
          <span
            className="material-symbols-outlined text-[12px] text-amber-500"
            style={{ fontVariationSettings: "'FILL' 1" }}
          >
            star
          </span>
          <span className="font-display text-[10px] font-bold text-se-on-surface">
            {rating}
          </span>
        </div>
      </div>

      {/* Info (2/3) */}
      <div className="flex w-2/3 flex-col justify-between p-3">
        <div>
          <div className="mb-1 flex items-start justify-between gap-2">
            <h3 className="line-clamp-1 font-display text-sm font-bold leading-tight text-se-on-surface">
              {poi.title}
            </h3>
            <span
              className="material-symbols-outlined text-[18px] text-se-outline"
              aria-hidden
            >
              chevron_right
            </span>
          </div>
          <p className="mb-1 flex items-center gap-1 font-body text-[11px] text-se-on-surface-variant">
            <span className="material-symbols-outlined text-[12px]">
              location_on
            </span>
            {stadiumName}에서 {distance}
          </p>
          <div className="mt-1 flex flex-wrap items-center gap-1">
            <span className="rounded bg-se-surface-container-low px-1.5 py-0.5 font-display text-[9px] font-bold uppercase text-se-on-surface-variant">
              {CATEGORY_LABEL[category] ?? "장소"}
            </span>
            {recommended ? (
              <span className="rounded bg-se-secondary-container/50 px-1.5 py-0.5 font-display text-[9px] font-bold uppercase text-se-on-secondary-container">
                추천
              </span>
            ) : null}
          </div>
        </div>
        {poi.tel ? (
          <p className="font-body text-[10px] text-se-outline">☎ {poi.tel}</p>
        ) : null}
      </div>
    </a>
  );
}
