import { filterAwayGames, loadPOIsByStadium, loadStadiums } from "@/lib/data/loaders";
import { requestRoute } from "@/lib/api/route";
import { TEAM_COLORS, getTeamPalette } from "@/lib/team-colors";
import { MapShell } from "@/components/map/map-shell";
import { MapControls } from "@/components/map/map-controls";
import { RouteSummary } from "@/components/map/route-summary";
import { ORIGIN_PRESETS } from "@/lib/map/origins";
import type { Stadium } from "@/lib/types";

interface MapPageProps {
  searchParams: Promise<{
    team?: string;
    start?: string;
    end?: string;
    game?: string;
    origin?: string;
  }>;
}

export default async function MapPage({ searchParams }: MapPageProps) {
  const p = await searchParams;
  const team = p.team && p.team in TEAM_COLORS ? p.team : "LG";
  const start = p.start ?? "2026-03-28";
  const end = p.end ?? "2026-09-30";
  const originKey =
    p.origin && p.origin in ORIGIN_PRESETS ? p.origin : "seoul";
  const origin = ORIGIN_PRESETS[originKey];
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

  const route = await requestRoute(origin, [stadium.lat, stadium.lng]);

  return (
    <section className="space-y-4">
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

      <RouteSummary route={route} />

      <MapShell
        stadium={stadium}
        places={{ food, stay, tour }}
        route={route}
        height={560}
      />

      <p className="text-[0.7rem] text-se-on-surface-variant">
        © OpenStreetMap contributors{route.source === "osrm" ? " · Routing by OSRM" : ""}
        {route.source === "kakao" ? " · 지도 데이터 © Kakao" : ""}
      </p>
    </section>
  );
}
