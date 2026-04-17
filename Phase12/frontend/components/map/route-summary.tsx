import type { RouteResult } from "@/lib/types";
import { cn } from "@/lib/utils";

const SOURCE_META: Record<
  RouteResult["source"],
  { label: string; tone: "brand" | "secondary" | "muted" }
> = {
  kakao: { label: "Kakao Mobility", tone: "brand" },
  osrm: { label: "OSM · OSRM", tone: "secondary" },
  haversine: { label: "직선 거리", tone: "muted" },
};

function formatDistance(m: number | null): string {
  if (!m) return "—";
  return m >= 1000 ? `${(m / 1000).toFixed(1)} km` : `${Math.round(m)} m`;
}
function formatDuration(sec: number | null): string {
  if (!sec) return "—";
  const min = Math.round(sec / 60);
  if (min < 60) return `${min} 분`;
  const h = Math.floor(min / 60);
  return `${h}시간 ${min % 60}분`;
}
function formatToll(krw: number | null): string {
  if (krw == null) return "—";
  return `${krw.toLocaleString()} 원`;
}

export function RouteSummary({ route }: { route: RouteResult | null }) {
  if (!route) {
    return (
      <div className="rounded-2xl border border-se-outline-variant bg-se-surface-container-low px-4 py-3 text-sm text-se-on-surface-variant">
        경기/출발지를 선택하면 경로가 계산됩니다.
      </div>
    );
  }
  const meta = SOURCE_META[route.source];
  const toneClass =
    meta.tone === "brand"
      ? "bg-se-primary text-white"
      : meta.tone === "secondary"
        ? "bg-purple-600 text-white"
        : "bg-se-outline text-white";

  return (
    <div className="rounded-2xl border border-se-outline-variant bg-se-surface-container-lowest p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span
            className={cn(
              "rounded-full px-2.5 py-1 font-display text-[0.65rem] font-extrabold uppercase tracking-wider",
              toneClass,
            )}
          >
            {meta.label}
          </span>
          {route.fallback ? (
            <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[0.65rem] font-bold text-amber-900">
              Fallback
            </span>
          ) : null}
        </div>
        <details className="text-[0.65rem] text-se-on-surface-variant">
          <summary className="cursor-pointer">attempts</summary>
          <ul className="mt-1 min-w-[180px] rounded-lg bg-se-surface-container-low px-2 py-1.5">
            {route.attempts.map((a, i) => (
              <li key={i} className="flex justify-between gap-2">
                <span>{a.provider}</span>
                <span className="font-mono">{a.status}</span>
                <span className="font-mono text-se-outline">{a.ms}ms</span>
              </li>
            ))}
          </ul>
        </details>
      </div>
      <div className="mt-3 grid grid-cols-3 gap-2">
        <Metric label="거리" value={formatDistance(route.distance_m)} />
        <Metric label="예상 소요" value={formatDuration(route.duration_sec)} />
        <Metric label="통행료" value={formatToll(route.toll_fare_krw)} />
      </div>
      {route.source === "haversine" ? (
        <p className="mt-3 rounded-lg bg-amber-50 px-3 py-2 text-[0.7rem] text-amber-900">
          ⚠️ Kakao · OSRM 모두 응답이 없어 <strong>직선 거리</strong>만 표시됩니다.
          실제 도로 경로와 다를 수 있어요.
        </p>
      ) : null}
      {route.source === "osrm" ? (
        <p className="mt-3 rounded-lg bg-purple-50 px-3 py-2 text-[0.7rem] text-purple-900">
          🌍 Kakao 키가 없어 <strong>OpenStreetMap · OSRM</strong> 공용 서버로 경로를
          계산했습니다. 교통정보는 반영되지 않아요.
        </p>
      ) : null}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border-l-4 border-se-secondary-fixed bg-se-surface-container-low px-3 py-2">
      <div className="font-display text-[0.6rem] font-bold uppercase tracking-wider text-se-on-surface-variant">
        {label}
      </div>
      <div className="font-display text-base font-extrabold text-se-primary">
        {value}
      </div>
    </div>
  );
}
