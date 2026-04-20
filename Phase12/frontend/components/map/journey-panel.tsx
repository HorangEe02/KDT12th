"use client";

import { useMemo, useState, useTransition } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import type { Game, POI, RouteResult, Stadium, Waypoint } from "@/lib/types";
import { NavAppPicker } from "./nav-app-picker";
import { OriginPickerDialog } from "./origin-picker-dialog";
import { GamePickerDialog } from "./game-picker-dialog";
import { cn } from "@/lib/utils";
import { MAX_WAYPOINTS, serializeWaypoints } from "@/lib/map/waypoints-url";
import {
  annotateWaypointDistances,
  formatDistanceShort,
  FAR_WAYPOINT_THRESHOLD_M,
} from "@/lib/map/waypoint-distance";

interface JourneyPanelProps {
  origin: [number, number];
  originLabel: string;
  originKey: string;
  stadium: Stadium;
  waypoints: Waypoint[];
  route: RouteResult;
  pois: { food: POI[]; stay: POI[]; tour: POI[] };
  gameTime?: string;
  games: Game[];
  selectedGame: Game;
}

const SOURCE_META: Record<
  RouteResult["source"],
  { label: string; tone: string }
> = {
  kakao: { label: "정밀 (Kakao)", tone: "bg-se-primary text-white" },
  osrm: { label: "최적 (OSRM)", tone: "bg-purple-600 text-white" },
  haversine: { label: "직선", tone: "bg-se-outline text-white" },
};

function formatDistance(m: number | null): string {
  if (!m) return "—";
  return m >= 1000 ? `${(m / 1000).toFixed(1)} km` : `${Math.round(m)} m`;
}
function formatDuration(sec: number | null): string {
  if (!sec) return "—";
  const min = Math.round(sec / 60);
  if (min < 60) return `${min}분`;
  const h = Math.floor(min / 60);
  return `${h}시간 ${min % 60}분`;
}
function formatToll(krw: number | null): string {
  if (krw == null) return "—";
  return `${krw.toLocaleString()}원`;
}

export function JourneyPanel({
  origin,
  originLabel,
  originKey,
  stadium,
  waypoints,
  route,
  pois,
  gameTime,
  games,
  selectedGame,
}: JourneyPanelProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [, startTransition] = useTransition();
  const [addOpen, setAddOpen] = useState(false);
  const [navOpen, setNavOpen] = useState(false);
  const [originOpen, setOriginOpen] = useState(false);
  const [gameOpen, setGameOpen] = useState(false);

  const badge = SOURCE_META[route.source];
  const stopsCount = waypoints.length + 2;

  const annotated = useMemo(
    () => annotateWaypointDistances(waypoints, stadium),
    [waypoints, stadium],
  );
  const farCount = annotated.filter((a) => a.isFar).length;

  function commitWaypoints(next: Waypoint[]) {
    const p = new URLSearchParams(searchParams.toString());
    if (next.length === 0) p.delete("wps");
    else p.set("wps", serializeWaypoints(next));
    startTransition(() => {
      router.replace(`${pathname}?${p.toString()}`, { scroll: false });
    });
  }

  function removeAt(i: number) {
    commitWaypoints(waypoints.filter((_, idx) => idx !== i));
  }
  function move(i: number, dir: -1 | 1) {
    const j = i + dir;
    if (j < 0 || j >= waypoints.length) return;
    const next = [...waypoints];
    [next[i], next[j]] = [next[j], next[i]];
    commitWaypoints(next);
  }
  function addWaypoint(w: Waypoint) {
    if (waypoints.length >= MAX_WAYPOINTS) return;
    commitWaypoints([...waypoints, w]);
    setAddOpen(false);
  }
  function clearFarWaypoints() {
    commitWaypoints(annotated.filter((a) => !a.isFar).map((a) => a.waypoint));
  }

  const gameDate = new Date(`${selectedGame.date}T00:00:00+09:00`);
  const gameWd = ["일", "월", "화", "수", "목", "금", "토"][gameDate.getDay()];

  return (
    <aside className="relative overflow-hidden rounded-[1.5rem] border border-se-outline-variant bg-white p-5 shadow-[0_8px_32px_rgba(0,25,60,0.08)]">
      {/* Game card — clickable → GamePickerDialog */}
      <button
        type="button"
        onClick={() => setGameOpen(true)}
        className="mb-4 flex w-full items-center gap-3 rounded-xl border border-dashed border-se-outline-variant/60 bg-se-surface-container-lowest px-3 py-2.5 text-left transition-colors hover:border-se-primary hover:bg-white"
      >
        <div className="flex h-11 w-11 shrink-0 flex-col items-center justify-center rounded-lg bg-se-primary text-white">
          <span className="font-display text-[9px] font-bold">{gameWd}</span>
          <span className="font-display text-base font-extrabold leading-none">
            {gameDate.getDate()}
          </span>
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate font-display text-sm font-bold text-se-primary">
            {selectedGame.date} · vs {selectedGame.home_team}
          </p>
          <p className="truncate font-body text-[11px] text-se-on-surface-variant">
            {selectedGame.stadium}
            {gameTime ? ` · ${gameTime}` : ""} · 탭하여 변경
          </p>
        </div>
        <span className="material-symbols-outlined text-[18px] text-se-outline">
          edit
        </span>
      </button>

      {/* Header */}
      <div className="mb-3 flex items-start justify-between">
        <div>
          <h2 className="font-display text-base font-extrabold tracking-tight text-se-primary">
            경기일 동선
          </h2>
          <p className="mt-0.5 font-body text-xs text-se-on-surface-variant">
            {stopsCount} stops · 총 {formatDuration(route.duration_sec)} ·{" "}
            {formatDistance(route.distance_m)}
          </p>
        </div>
        <span
          className={cn(
            "shrink-0 rounded-full px-2.5 py-1 font-display text-[10px] font-bold uppercase tracking-wider shadow-sm",
            badge.tone,
          )}
        >
          {badge.label}
        </span>
      </div>

      {/* 경유지 거리 경고 배너 (Decision 3 D) */}
      {farCount > 0 ? (
        <div className="mb-3 flex items-start gap-2 rounded-xl border border-amber-400/60 bg-amber-50 px-3 py-2">
          <span className="material-symbols-outlined text-[18px] text-amber-700">
            warning
          </span>
          <div className="min-w-0 flex-1">
            <p className="font-display text-[11px] font-bold text-amber-900">
              경유지 {farCount}개가 현재 구장과 멀어요 (≥ {formatDistanceShort(FAR_WAYPOINT_THRESHOLD_M)})
            </p>
            <button
              type="button"
              onClick={clearFarWaypoints}
              className="mt-1 inline-flex items-center gap-1 rounded-full bg-amber-700 px-2.5 py-0.5 text-[10px] font-bold text-white hover:bg-amber-800"
            >
              먼 경유지 {farCount}개 삭제
            </button>
          </div>
        </div>
      ) : null}

      {/* Stops list */}
      <ol className="mb-4 flex flex-col gap-2.5">
        <StopRow
          icon="my_location"
          iconTone="muted"
          title={originLabel}
          subtitle={`출발 · ${origin[0].toFixed(3)}, ${origin[1].toFixed(3)} · 탭하여 변경`}
          onClick={() => setOriginOpen(true)}
        />
        {annotated.map(({ waypoint: wp, distance_m, isFar }, i) => (
          <StopRow
            key={`${wp.lat},${wp.lng},${i}`}
            icon="place"
            iconTone="secondary"
            badge={`${i + 1}`}
            far={isFar}
            title={wp.name ?? `경유지 ${i + 1}`}
            subtitle={`경유 · 구장까지 ${formatDistanceShort(distance_m)}${isFar ? " · 멀어요" : ""}`}
            legInfo={
              route.legs?.[i]
                ? `${formatDistance(route.legs[i].distance_m)}${
                    route.legs[i].duration_sec
                      ? ` · ${formatDuration(route.legs[i].duration_sec)}`
                      : ""
                  }`
                : undefined
            }
            actions={
              <>
                <IconBtn
                  icon="arrow_upward"
                  onClick={() => move(i, -1)}
                  disabled={i === 0}
                  label="위로"
                />
                <IconBtn
                  icon="arrow_downward"
                  onClick={() => move(i, 1)}
                  disabled={i === waypoints.length - 1}
                  label="아래로"
                />
                <IconBtn icon="close" onClick={() => removeAt(i)} label="삭제" />
              </>
            }
          />
        ))}
        <StopRow
          icon="sports_baseball"
          iconTone="primary"
          title={stadium.stadium_name}
          subtitle={`도착${gameTime ? ` · ${gameTime} 경기 시작` : ""}`}
        />
      </ol>

      {/* Add waypoint */}
      <button
        type="button"
        onClick={() => setAddOpen(true)}
        disabled={waypoints.length >= MAX_WAYPOINTS}
        className="mb-4 flex w-full items-center justify-center gap-1.5 rounded-xl border-2 border-dashed border-se-outline-variant/60 py-2.5 font-display text-xs font-bold text-se-on-surface-variant transition-colors hover:border-se-primary hover:text-se-primary disabled:opacity-40"
      >
        <span className="material-symbols-outlined text-[18px]">add</span>
        경유지 추가 ({waypoints.length}/{MAX_WAYPOINTS})
      </button>

      {/* Metrics */}
      <div className="mb-4 grid grid-cols-3 gap-2">
        <Metric label="거리" value={formatDistance(route.distance_m)} />
        <Metric label="소요" value={formatDuration(route.duration_sec)} />
        <Metric label="통행료" value={formatToll(route.toll_fare_krw)} />
      </div>

      {/* CTA */}
      <button
        type="button"
        onClick={() => setNavOpen(true)}
        className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-br from-se-primary to-se-primary-container py-4 font-display text-sm font-bold text-white shadow-[0_4px_16px_rgba(0,25,60,0.18)] transition-all hover:opacity-95 active:scale-[0.98]"
      >
        <span>길 안내 시작</span>
        <span className="material-symbols-outlined text-[18px]">navigation</span>
      </button>

      {route.source !== "kakao" ? (
        <p className="mt-3 rounded-lg bg-amber-50 px-3 py-2 text-[0.7rem] text-amber-900">
          {route.source === "osrm"
            ? "🌍 OSM · OSRM 경로로 계산됨 (실시간 교통 미반영)."
            : "⚠️ 직선 거리 fallback — 실제 도로와 다를 수 있어요."}
        </p>
      ) : null}

      {/* Dialogs (all z-[9999] to beat leaflet controls) */}
      {addOpen ? (
        <AddWaypointDialog
          pois={pois}
          onClose={() => setAddOpen(false)}
          onPick={addWaypoint}
        />
      ) : null}
      {navOpen ? (
        <NavAppDialog
          origin={origin}
          destination={[stadium.lat, stadium.lng]}
          destinationName={stadium.stadium_name}
          waypoints={waypoints}
          onClose={() => setNavOpen(false)}
        />
      ) : null}
      {originOpen ? (
        <OriginPickerDialog
          currentOrigin={originKey}
          onClose={() => setOriginOpen(false)}
        />
      ) : null}
      {gameOpen ? (
        <GamePickerDialog
          games={games}
          selectedGameId={selectedGame.game_id}
          currentStadiumShort={stadium.short_name}
          waypoints={waypoints}
          onClose={() => setGameOpen(false)}
        />
      ) : null}
    </aside>
  );
}

// ────────────────────────────────────────────────────────────
// Sub-components
// ────────────────────────────────────────────────────────────

function StopRow({
  icon,
  iconTone,
  badge,
  far,
  title,
  subtitle,
  legInfo,
  actions,
  onClick,
}: {
  icon: string;
  iconTone: "primary" | "secondary" | "muted";
  badge?: string;
  far?: boolean;
  title: string;
  subtitle: string;
  legInfo?: string;
  actions?: React.ReactNode;
  onClick?: () => void;
}) {
  const iconCls =
    iconTone === "primary"
      ? "bg-gradient-to-br from-se-primary to-se-primary-container text-white"
      : iconTone === "secondary"
        ? far
          ? "bg-amber-100 text-amber-700 ring-2 ring-amber-400"
          : "bg-se-secondary-fixed/40 text-se-secondary"
        : "bg-se-surface-container-low text-se-on-surface-variant";

  const row = (
    <div className="flex items-start gap-3">
      <div
        className={cn(
          "relative flex h-9 w-9 shrink-0 items-center justify-center rounded-full",
          iconCls,
        )}
      >
        <span
          className="material-symbols-outlined text-[18px]"
          style={
            iconTone === "primary"
              ? { fontVariationSettings: "'FILL' 1" }
              : undefined
          }
        >
          {icon}
        </span>
        {badge ? (
          <span
            className={cn(
              "absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-white font-display text-[9px] font-extrabold ring-2",
              far
                ? "text-amber-700 ring-amber-400"
                : "text-se-secondary ring-se-secondary-fixed/40",
            )}
          >
            {badge}
          </span>
        ) : null}
      </div>
      <div className="min-w-0 flex-1">
        <p
          className={cn(
            "truncate font-display text-sm font-bold",
            far ? "text-amber-900" : "text-se-on-surface",
          )}
        >
          {title}
        </p>
        <p
          className={cn(
            "truncate font-body text-[11px]",
            far ? "text-amber-700" : "text-se-outline",
          )}
        >
          {subtitle}
          {legInfo ? (
            <span className="ml-1 text-se-secondary">· {legInfo}</span>
          ) : null}
        </p>
      </div>
      {actions ? (
        <div className="flex shrink-0 items-center gap-1">{actions}</div>
      ) : null}
    </div>
  );

  if (onClick) {
    return (
      <li>
        <button
          type="button"
          onClick={onClick}
          className="w-full rounded-xl border border-dashed border-transparent p-0.5 text-left transition-colors hover:border-se-primary/60 hover:bg-se-surface-container-low/60"
        >
          {row}
        </button>
      </li>
    );
  }
  return <li>{row}</li>;
}

function IconBtn({
  icon,
  onClick,
  disabled,
  label,
}: {
  icon: string;
  onClick: () => void;
  disabled?: boolean;
  label: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-label={label}
      title={label}
      className="flex h-7 w-7 items-center justify-center rounded-full text-se-on-surface-variant transition-colors hover:bg-se-surface-container-low disabled:opacity-30"
    >
      <span className="material-symbols-outlined text-[16px]">{icon}</span>
    </button>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border-l-4 border-se-secondary-fixed bg-se-surface-container-low px-3 py-2">
      <div className="font-display text-[10px] font-bold uppercase tracking-wider text-se-on-surface-variant">
        {label}
      </div>
      <div className="font-display text-sm font-extrabold text-se-primary">
        {value}
      </div>
    </div>
  );
}

// ────────────────────────────────────────────────────────────
// Add Waypoint Dialog — POI picker (food / stay / tour)
// ────────────────────────────────────────────────────────────

type Cat = "food" | "stay" | "tour";
const CAT_LABEL: Record<Cat, string> = {
  food: "🍽️ 음식점",
  stay: "🏨 숙박",
  tour: "🎡 관광지",
};

function AddWaypointDialog({
  pois,
  onClose,
  onPick,
}: {
  pois: { food: POI[]; stay: POI[]; tour: POI[] };
  onClose: () => void;
  onPick: (w: Waypoint) => void;
}) {
  const [cat, setCat] = useState<Cat>("food");
  const [query, setQuery] = useState("");
  const list = useMemo(() => {
    const src = pois[cat] ?? [];
    const q = query.trim();
    if (!q) return src.slice(0, 40);
    return src.filter((p) => p.title.includes(q)).slice(0, 40);
  }, [pois, cat, query]);

  return (
    <div
      className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/55 p-6 backdrop-blur-sm"
      role="dialog"
      aria-modal
      aria-label="경유지 선택"
      onClick={onClose}
    >
      <div
        className="relative max-h-[80dvh] w-full max-w-lg overflow-hidden rounded-3xl bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="flex items-center justify-between border-b border-se-outline-variant/50 px-5 py-4">
          <h3 className="font-display text-base font-bold text-se-primary">
            경유지 선택
          </h3>
          <button
            type="button"
            onClick={onClose}
            aria-label="닫기"
            className="flex h-8 w-8 items-center justify-center rounded-full hover:bg-se-surface-container-low"
          >
            <span className="material-symbols-outlined text-[20px]">close</span>
          </button>
        </header>
        <div className="flex gap-1 px-5 pt-4">
          {(Object.keys(CAT_LABEL) as Cat[]).map((c) => (
            <button
              key={c}
              type="button"
              onClick={() => setCat(c)}
              className={cn(
                "rounded-full px-3 py-1 font-display text-xs font-bold transition-colors",
                cat === c
                  ? "bg-se-primary text-white"
                  : "bg-se-surface-container-low text-se-on-surface-variant hover:bg-se-surface-container",
              )}
            >
              {CAT_LABEL[c]} ({pois[c]?.length ?? 0})
            </button>
          ))}
        </div>
        <div className="px-5 pt-3">
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="이름으로 검색..."
            className="w-full rounded-xl border border-se-outline-variant bg-se-surface-container-low px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-se-primary"
          />
        </div>
        <ul className="max-h-[50dvh] overflow-y-auto px-5 py-3">
          {list.length === 0 ? (
            <li className="py-8 text-center text-sm text-se-on-surface-variant">
              일치하는 항목이 없어요.
            </li>
          ) : (
            list.map((p) => (
              <li key={p.content_id}>
                <button
                  type="button"
                  onClick={() =>
                    onPick({ lat: p.lat, lng: p.lng, name: p.title })
                  }
                  className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left transition-colors hover:bg-se-surface-container-low"
                >
                  <span className="material-symbols-outlined text-[18px] text-se-secondary">
                    place
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-display text-sm font-bold text-se-on-surface">
                      {p.title}
                    </p>
                    {p.addr ? (
                      <p className="truncate text-[11px] text-se-outline">
                        {p.addr}
                      </p>
                    ) : null}
                  </div>
                  {typeof p.dist_m === "number" ? (
                    <span className="shrink-0 rounded-full bg-se-surface-container-low px-2 py-0.5 font-mono text-[10px] text-se-on-surface-variant">
                      {p.dist_m.toLocaleString()}m
                    </span>
                  ) : null}
                </button>
              </li>
            ))
          )}
        </ul>
      </div>
    </div>
  );
}

// ────────────────────────────────────────────────────────────
// Nav App Dialog — wraps NavAppPicker in modal
// ────────────────────────────────────────────────────────────

function NavAppDialog({
  origin,
  destination,
  destinationName,
  waypoints,
  onClose,
}: {
  origin: [number, number];
  destination: [number, number];
  destinationName: string;
  waypoints: Waypoint[];
  onClose: () => void;
}) {
  return (
    <div
      className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/55 p-6 backdrop-blur-sm"
      role="dialog"
      aria-modal
      aria-label="길 안내 앱 선택"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-md overflow-hidden rounded-3xl bg-white p-6 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          type="button"
          onClick={onClose}
          aria-label="닫기"
          className="absolute right-3 top-3 flex h-8 w-8 items-center justify-center rounded-full hover:bg-se-surface-container-low"
        >
          <span className="material-symbols-outlined text-[20px]">close</span>
        </button>
        <NavAppPicker
          origin={origin}
          destination={destination}
          destinationName={destinationName}
          mode="car"
          waypoints={waypoints.map((w) => ({
            lat: w.lat,
            lng: w.lng,
            name: w.name,
          }))}
          onLaunched={() => setTimeout(onClose, 300)}
        />
      </div>
    </div>
  );
}
