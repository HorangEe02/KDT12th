import { filterAwayGames, loadPOIsByStadium, loadStadiums } from "@/lib/data/loaders";
import { requestRoute } from "@/lib/api/route";
import { getTeamPalette } from "@/lib/team-colors";
import { resolveTeam } from "@/lib/data/resolve-team";
import { MapShell } from "@/components/map/map-shell";
import { MapControls } from "@/components/map/map-controls";
import { FloatingTopBar } from "@/components/map/floating-top-bar";
import { JourneySummaryCard } from "@/components/map/journey-summary-card";
import { JourneyPanel } from "@/components/map/journey-panel";
import { MobileGamePicker } from "@/components/map/mobile-game-picker";
import { MobileOriginPicker } from "@/components/map/mobile-origin-picker";
import { TripConfirmationSheet } from "@/components/map/trip-confirmation-sheet";
import { WaypointPicker } from "@/components/map/waypoint-picker";
import { TripBridge } from "@/components/map/trip-bridge";
import { ORIGIN_PRESETS, CUSTOM_ORIGIN_KEY, ORIGIN_LABEL } from "@/lib/map/origins";
import { parseWaypointsParam } from "@/lib/map/waypoints-url";
import type { Stadium } from "@/lib/types";

interface MapPageProps {
  searchParams: Promise<{
    team?: string;
    start?: string;
    end?: string;
    game?: string;
    origin?: string;
    lat?: string;
    lng?: string;
    wps?: string;
  }>;
}

export default async function MapPage({ searchParams }: MapPageProps) {
  const p = await searchParams;
  const team = await resolveTeam(p.team);
  const start = p.start ?? "2026-03-28";
  const end = p.end ?? "2026-09-30";

  let originKey: string;
  let origin: [number, number];
  if (p.origin === CUSTOM_ORIGIN_KEY && p.lat && p.lng) {
    const lat = Number.parseFloat(p.lat);
    const lng = Number.parseFloat(p.lng);
    if (Number.isFinite(lat) && Number.isFinite(lng)) {
      originKey = CUSTOM_ORIGIN_KEY;
      origin = [lat, lng];
    } else {
      originKey = "seoul";
      origin = ORIGIN_PRESETS.seoul;
    }
  } else if (p.origin && p.origin in ORIGIN_PRESETS) {
    originKey = p.origin;
    origin = ORIGIN_PRESETS[p.origin];
  } else {
    originKey = "seoul";
    origin = ORIGIN_PRESETS.seoul;
  }
  const palette = getTeamPalette(team);

  const [games, stadiums] = await Promise.all([
    filterAwayGames(team, start, end),
    loadStadiums(),
  ]);
  const selectedGame = games.find((g) => g.game_id === p.game) ?? games[0];

  if (!selectedGame) {
    return (
      <section className="space-y-4">
        <h1 className="font-display text-2xl font-extrabold text-se-primary">
          🗺️ 원정 동선 지도
        </h1>
        <div className="rounded-2xl border border-se-outline-variant bg-se-surface-container-low px-5 py-8 text-center text-sm text-se-on-surface-variant">
          {palette.nameKo}의 {start} ~ {end} 기간에 원정 경기가 없습니다.
          사이드바에서 기간을 넓혀보세요.
        </div>
      </section>
    );
  }

  const stadium =
    stadiums.find((s) => s.short_name === selectedGame.stadium) ??
    (stadiums[0] as Stadium);

  const [food, stay, tour] = await Promise.all([
    loadPOIsByStadium(`${stadium.short_name}_food`),
    loadPOIsByStadium(`${stadium.short_name}_stay`),
    loadPOIsByStadium(`${stadium.short_name}_tour`),
  ]);

  const waypoints = parseWaypointsParam(p.wps);
  const route = await requestRoute(origin, [stadium.lat, stadium.lng], {
    waypoints,
  });
  const originLabel =
    originKey === CUSTOM_ORIGIN_KEY
      ? "내 위치"
      : (ORIGIN_LABEL[originKey] ?? "출발지");

  // 가까운 음식점 1개를 mid stop 으로 (Stops list 풍성)
  const midStop = food[0]
    ? {
        label: food[0].title,
        time: undefined,
        icon: "restaurant",
      }
    : undefined;

  // 오늘 경기 여부
  const today = new Date().toISOString().slice(0, 10);
  const isToday = selectedGame.date === today;

  return (
    <>
      {/* === Mobile (< md) — 풀스크린 지도 + Floating cards ===
          - top:    TopNav(h-16=64px) + safe-area-inset-top (notch)
          - bottom: MobileBottomNav(~80px) + safe-area-inset-bottom (home indicator)
          - fill 모드: 부모 컨테이너가 실제 가용 높이를 잡고 MapShell 은 100% 채움.
            (이전 `window.innerHeight - 64` 는 SSR 시 window 미정의 → 항상 700px 하드코딩)
      */}
      <div
        className="fixed inset-x-0 z-10 md:hidden"
        style={{
          top: "calc(4rem + env(safe-area-inset-top))",
          bottom: "calc(5rem + env(safe-area-inset-bottom))",
        }}
      >
        <MapShell
          stadium={stadium}
          places={{ food: food.slice(0, 8), stay: stay.slice(0, 5), tour: tour.slice(0, 5) }}
          route={route}
          waypoints={waypoints}
          fill
        />
      </div>
      <FloatingTopBar title={`${palette.nameKo} 원정`} />
      <JourneySummaryCard
        origin={{ label: originLabel }}
        stadium={stadium}
        route={route}
        midStop={midStop}
        isToday={isToday}
        gameTime={selectedGame.start_time || selectedGame.time || undefined}
      />
      {/* Mobile sub-sheets */}
      <MobileGamePicker games={games} selectedGameId={selectedGame.game_id} />
      <MobileOriginPicker currentOrigin={originKey} />
      <TripBridge
        origin={{ label: originLabel, coords: origin }}
        stadium={stadium}
        selectedGame={selectedGame}
        route={route}
        pois={{ food, stay, tour }}
      />
      <WaypointPicker pois={{ food, stay, tour }} />

      {/* === Desktop (md+) — 기존 layout === */}
      <section className="hidden space-y-4 md:block">
        <header>
          <h1 className="font-display text-2xl font-extrabold text-se-primary">
            🗺️ 원정 동선 지도
          </h1>
          <p className="text-sm text-se-on-surface-variant">
            {palette.nameKo} · {selectedGame.date} @{" "}
            <strong>{stadium.stadium_name}</strong> · vs {selectedGame.home_team}
          </p>
        </header>

        <MapControls
          games={games}
          selectedGameId={selectedGame.game_id}
          origin={originKey}
        />

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_360px]">
          <MapShell
            stadium={stadium}
            places={{ food, stay, tour }}
            route={route}
            waypoints={waypoints}
            height={600}
          />
          <JourneyPanel
            origin={origin}
            originLabel={originLabel}
            stadium={stadium}
            waypoints={waypoints}
            route={route}
            pois={{ food, stay, tour }}
            gameTime={selectedGame.start_time || selectedGame.time || undefined}
          />
        </div>

        <p className="text-[0.7rem] text-se-on-surface-variant">
          © OpenStreetMap contributors{route.source === "osrm" ? " · Routing by OSRM" : ""}
          {route.source === "kakao" ? " · 지도 데이터 © Kakao" : ""}
        </p>
      </section>
    </>
  );
}
