import type { POI } from "@/lib/types";

const CATEGORY_ICON: Record<string, string> = {
  food: "restaurant",
  stay: "hotel",
  tour: "camera_alt",
};

export function PoiCard({ poi }: { poi: POI }) {
  const icon = CATEGORY_ICON[poi.category] ?? "place";
  const mapHref = `https://map.kakao.com/link/map/${encodeURIComponent(
    poi.title,
  )},${poi.lat},${poi.lng}`;

  return (
    <article className="rounded-2xl border border-se-outline-variant bg-se-surface-container-lowest p-4 transition-shadow hover:shadow-[0_8px_18px_rgba(0,25,60,0.08)]">
      <div className="flex items-start gap-3">
        <span className="material-symbols-outlined flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-se-surface-container-low text-se-primary">
          {icon}
        </span>
        <div className="min-w-0 flex-1">
          <h4 className="truncate font-display text-sm font-extrabold text-se-primary">
            {poi.title}
          </h4>
          {poi.addr ? (
            <p className="mt-0.5 truncate text-xs text-se-on-surface-variant">
              📍 {poi.addr}
            </p>
          ) : null}
          <div className="mt-1.5 flex flex-wrap items-center gap-2 text-[0.7rem] text-se-on-surface-variant">
            {typeof poi.dist_m === "number" ? (
              <span className="rounded-full bg-se-secondary-fixed/40 px-2 py-0.5 font-bold text-se-on-secondary-container">
                🏟️ {poi.dist_m.toLocaleString()}m
              </span>
            ) : null}
            {poi.tel ? <span>☎️ {poi.tel}</span> : null}
          </div>
        </div>
      </div>
      <div className="mt-3 flex gap-2">
        <a
          href={mapHref}
          target="_blank"
          rel="noopener noreferrer"
          className="rounded-full border border-se-outline-variant px-3 py-1 text-[0.7rem] font-bold text-se-primary no-underline hover:border-se-primary"
        >
          🗺️ 카카오맵
        </a>
      </div>
    </article>
  );
}
