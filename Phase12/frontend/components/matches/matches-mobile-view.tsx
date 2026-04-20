import { UpcomingFixtureHero } from "./upcoming-fixture-hero";
import { AwayMatrixCard } from "./away-matrix-card";
import { MobileSettingsButton } from "@/components/nav/mobile-settings-button";
import type { Game } from "@/lib/types";

/**
 * 모바일 전용 매치 페이지 뷰.
 * mockup: uiux/mobile_uiux/matches_predictions_mobile/code.html
 *
 * 데스크톱 (md+) 에서는 hidden, 모바일 (< md) 에서만 표시.
 */
interface MatchesMobileViewProps {
  team: string;
  teamNameKo: string;
  games: Game[];
  selected: Game | null;
  prediction: { prob: number } | null;
  baseQuery: Record<string, string>;
}

export function MatchesMobileView({
  team,
  teamNameKo,
  games,
  selected,
  prediction,
  baseQuery,
}: MatchesMobileViewProps) {
  const upcoming = selected ?? games[0];
  const otherGames = games.filter((g) => g.game_id !== upcoming?.game_id).slice(0, 6);

  return (
    <div className="space-y-6 md:hidden">
      {/* Mobile Header */}
      <header className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-black tracking-tight text-se-primary">
            원정 경기
          </h1>
          <p className="mt-0.5 font-body text-xs text-se-on-surface-variant">
            {teamNameKo} · 총 {games.length}건
          </p>
        </div>
        <MobileSettingsButton ariaLabel="원정 설정 열기" />
      </header>

      {/* Upcoming Fixture Hero */}
      {upcoming && prediction ? (
        <UpcomingFixtureHero
          game={upcoming}
          awayTeam={team}
          homeTeamCode={inferHomeCode(upcoming.home_team)}
          prob={prediction.prob}
        />
      ) : (
        <EmptyState />
      )}

      {/* Away Matrix */}
      {otherGames.length > 0 ? (
        <section>
          <h2 className="mb-3 font-display text-base font-bold tracking-tight text-se-on-surface">
            원정 일정
          </h2>
          <div className="grid grid-cols-1 gap-3">
            {otherGames.map((g, i) => (
              <AwayMatrixCard
                key={g.game_id}
                game={g}
                highlight={i === 0}
                baseQuery={baseQuery}
              />
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}

function EmptyState() {
  return (
    <div className="rounded-2xl border border-dashed border-se-outline-variant bg-se-surface-container-low px-5 py-10 text-center">
      <span className="material-symbols-outlined block text-3xl text-se-outline">
        sports_baseball
      </span>
      <p className="mt-2 font-display text-sm font-bold text-se-on-surface">
        예정된 원정 경기가 없습니다
      </p>
      <p className="mt-1 text-xs text-se-on-surface-variant">
        사이드바에서 기간을 넓혀보세요.
      </p>
    </div>
  );
}

/** "두산 베어스" → "두산" 코드 매핑 (간단 휴리스틱) */
function inferHomeCode(homeTeamFull: string): string {
  const map: Record<string, string> = {
    LG: "LG",
    KT: "KT",
    SSG: "SSG",
    KIA: "KIA",
    NC: "NC",
    두산: "두산",
    삼성: "삼성",
    롯데: "롯데",
    한화: "한화",
    키움: "키움",
  };
  for (const k of Object.keys(map)) {
    if (homeTeamFull.includes(k)) return map[k];
  }
  return "LG";
}
