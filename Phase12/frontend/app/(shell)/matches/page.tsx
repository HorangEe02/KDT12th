import { awayWinRateRanking, filterAwayGames } from "@/lib/data/loaders";
import { predictWinRate } from "@/lib/predict";
import { TEAM_COLORS, getTeamPalette } from "@/lib/team-colors";
import { MatchList } from "@/components/matches/match-list";
import { WinGauge } from "@/components/matches/win-gauge";
import { WinRateBar } from "@/components/matches/win-rate-bar";
import { formatWinRate } from "@/lib/utils";

interface MatchesPageProps {
  searchParams: Promise<{
    team?: string;
    start?: string;
    end?: string;
    game?: string;
    device?: string;
  }>;
}

export default async function MatchesPage({
  searchParams,
}: MatchesPageProps) {
  const p = await searchParams;
  const team = p.team && p.team in TEAM_COLORS ? p.team : "LG";
  const palette = getTeamPalette(team);
  const start = p.start ?? "2026-03-28";
  const end = p.end ?? "2026-09-30";

  const [games, ranking] = await Promise.all([
    filterAwayGames(team, start, end),
    awayWinRateRanking(3),
  ]);

  const selected = games.find((g) => g.game_id === p.game) ?? games[0];
  const prediction = selected
    ? await predictWinRate(team, selected.home_team)
    : null;

  const teamAvg =
    ranking.find((r) => r.team === team)?.away_win_rate ?? undefined;
  const top = ranking[0];

  return (
    <div className="space-y-6">
      {/* Header */}
      <header className="flex flex-col gap-1">
        <h1 className="font-display text-2xl font-extrabold text-se-primary">
          ⚾ 원정 경기 & 승률 예측
        </h1>
        <p className="text-sm text-se-on-surface-variant">
          {palette.nameKo} · {start} ~ {end} ·{" "}
          <strong className="text-se-primary">{games.length}</strong>건
        </p>
      </header>

      {/* Metrics */}
      <div className="grid grid-cols-3 gap-3">
        <Metric label="응원팀" value={team} />
        <Metric label="원정 경기" value={`${games.length}건`} />
        <Metric
          label="기간"
          value={`${start.slice(5)} ~ ${end.slice(5)}`}
          small
        />
      </div>

      {/* Selected game + gauge */}
      {selected && prediction ? (
        <section className="grid grid-cols-1 gap-4 md:grid-cols-5">
          <div className="rounded-2xl border border-se-outline-variant bg-se-surface-container-lowest p-5 md:col-span-3">
            <h2 className="font-display text-lg font-extrabold text-se-primary">
              🆚 vs {selected.home_team} @ {selected.stadium}
            </h2>
            <p className="mt-2 text-sm">
              📅 <strong>{selected.date}</strong> ({selected.day_of_week})
            </p>
            <p className="mt-1 text-sm">
              🕐 경기 시작:{" "}
              <strong>{selected.start_time || selected.time || "미정"}</strong>
            </p>
            {selected.status === "FINISHED" && selected.score ? (
              <p className="mt-1 text-sm">
                🏁 최종 스코어:{" "}
                <strong className="tabular-nums">
                  {team === selected.away_team
                    ? `${selected.score.away} - ${selected.score.home}`
                    : `${selected.score.home} - ${selected.score.away}`}
                </strong>
                {selected.win_pitcher ? ` · 승 ${selected.win_pitcher}` : ""}
                {selected.lose_pitcher ? ` · 패 ${selected.lose_pitcher}` : ""}
                {selected.save_pitcher ? ` · 세 ${selected.save_pitcher}` : ""}
              </p>
            ) : null}
            {selected.status === "IN_PROGRESS" && selected.score ? (
              <p className="mt-1 text-sm text-red-700">
                🔴 LIVE{" "}
                {selected.current_inning
                  ? `${selected.current_inning}회 · `
                  : ""}
                {selected.score.away}-{selected.score.home}
              </p>
            ) : null}
            {selected.status === "SCHEDULED" &&
            (selected.home_pitcher || selected.away_pitcher) ? (
              <p className="mt-1 text-sm text-se-on-surface-variant">
                🧤 선발: {selected.away_pitcher ?? "미정"} (원정) vs{" "}
                {selected.home_pitcher ?? "미정"} (홈)
              </p>
            ) : null}
            {selected.broadcast ? (
              <p className="mt-1 text-sm text-se-on-surface-variant">
                📺 중계:{" "}
                {Array.isArray(selected.broadcast)
                  ? selected.broadcast.join(", ")
                  : selected.broadcast}
              </p>
            ) : null}
            <p className="mt-4 text-xs text-se-on-surface-variant">
              💡 로지스틱 회귀 모델(5-피처)로 예측되며, 더미 데이터로 학습되어
              극단적 확률이 나올 수 있습니다. 실제 KBO 기록 연동 시 개선됩니다.
            </p>
            <p className="mt-1 text-xs text-se-on-surface-variant">
              🔮 예측 소스: <strong>{prediction.source}</strong>
              {prediction.detail ? ` · ${prediction.detail}` : ""}
            </p>
          </div>
          <div className="rounded-2xl border border-se-outline-variant bg-se-surface-container-lowest p-3 md:col-span-2">
            <WinGauge prob={prediction.prob} team={team} />
            <p className="-mt-2 px-2 pb-1 text-center text-xs text-se-on-surface-variant">
              원정 승률 예측 · {formatWinRate(prediction.prob)}
            </p>
          </div>
        </section>
      ) : null}

      {/* Match list */}
      <section>
        <h3 className="mb-2 font-display text-sm font-extrabold uppercase tracking-[0.12em] text-se-on-surface-variant">
          📋 기간 내 원정 경기
        </h3>
        <MatchList
          games={games}
          team={team}
          selectedGameId={selected?.game_id}
          baseQuery={Object.fromEntries(
            Object.entries(p).filter(([, v]) => typeof v === "string"),
          ) as Record<string, string>}
        />
      </section>

      {/* Ranking bar */}
      <section>
        <h3 className="mb-2 font-display text-sm font-extrabold uppercase tracking-[0.12em] text-se-on-surface-variant">
          📊 구단별 최근 3년 원정 승률
        </h3>
        <div className="rounded-2xl border border-se-outline-variant bg-se-surface-container-lowest p-3">
          <WinRateBar rows={ranking} highlight={team} />
        </div>
        <p className="mt-2 text-xs text-se-on-surface-variant">
          💡 최근 3년 원정 승률 1위는 <strong>{top?.team}</strong> (
          {top?.away_win_rate.toFixed(3)}). {team}의 평균 원정 승률:{" "}
          <strong>{teamAvg ? teamAvg.toFixed(3) : "N/A"}</strong>. 회색은
          비교군, 컬러는 선택 팀.
        </p>
      </section>
    </div>
  );
}

function Metric({
  label,
  value,
  small = false,
}: {
  label: string;
  value: string;
  small?: boolean;
}) {
  return (
    <div className="rounded-xl border-l-4 border-se-secondary-fixed bg-se-surface-container-low px-4 py-3">
      <div className="font-display text-[0.65rem] font-bold uppercase tracking-[0.12em] text-se-on-surface-variant">
        {label}
      </div>
      <div
        className={`font-display font-extrabold text-se-primary ${
          small ? "text-sm" : "text-xl"
        }`}
      >
        {value}
      </div>
    </div>
  );
}
