import Image from "next/image";
import { getTeamPalette, getTeamLogoPath } from "@/lib/team-colors";
import type { Game } from "@/lib/types";

/**
 * 모바일 전용 — 다가오는 원정 경기 Hero VS 카드.
 * mockup: uiux/mobile_uiux/matches_predictions_mobile/code.html
 */
interface UpcomingFixtureHeroProps {
  game: Game;
  awayTeam: string;       // 사용자 응원팀 = 원정 팀
  homeTeamCode: string;   // 상대 = 홈 팀
  prob: number;           // 사용자 응원팀 (원정) 의 승률 0~1
}

export function UpcomingFixtureHero({
  game,
  awayTeam,
  homeTeamCode,
  prob,
}: UpcomingFixtureHeroProps) {
  const awayPalette = getTeamPalette(awayTeam);
  const homePalette = getTeamPalette(homeTeamCode);
  const awayPct = Math.round(prob * 100);
  const homePct = 100 - awayPct;

  return (
    <section>
      <div className="mb-3 flex items-center justify-between">
        <h2 className="font-display text-base font-bold tracking-tight text-se-on-surface">
          다가오는 경기
        </h2>
        <span className="flex items-center gap-1 font-display text-[0.65rem] font-bold uppercase tracking-widest text-se-secondary">
          <span className="h-2 w-2 animate-pulse rounded-full bg-se-secondary" />
          실시간 승률
        </span>
      </div>

      <div className="relative overflow-hidden rounded-[1.5rem] bg-se-surface-container-lowest p-5 shadow-[0_4px_24px_rgba(25,28,29,0.06)]">
        {/* Decorative gradients */}
        <div
          className="pointer-events-none absolute -right-10 -top-10 h-40 w-40 rounded-full blur-3xl"
          style={{ background: `${awayPalette.color}33` }}
        />
        <div
          className="pointer-events-none absolute -bottom-10 -left-10 h-40 w-40 rounded-full blur-3xl"
          style={{ background: `${homePalette.color}33` }}
        />

        <div className="relative z-10 flex flex-col items-center">
          <p className="mb-4 font-display text-[0.65rem] font-bold uppercase tracking-widest text-se-on-surface-variant">
            📍 {game.stadium}
          </p>

          {/* Team1 (Away) — VS — Team2 (Home) */}
          <div className="mb-6 flex w-full max-w-sm items-center justify-between">
            <TeamColumn
              name={awayPalette.nameKo}
              logoPath={getTeamLogoPath(awayTeam)}
              color={awayPalette.color}
              variant="away"
            />
            <div className="flex flex-col items-center px-2">
              <span className="font-display text-2xl font-black text-se-primary-container">
                VS
              </span>
              <span className="mt-1 font-body text-xs font-medium text-se-on-surface-variant">
                {game.start_time || game.time || "18:30"} KST
              </span>
            </div>
            <TeamColumn
              name={homePalette.nameKo}
              logoPath={getTeamLogoPath(homeTeamCode)}
              color={homePalette.color}
              variant="home"
            />
          </div>

          {/* Probability gauge (단순 progress bar) */}
          <div className="w-full max-w-sm rounded-2xl bg-se-surface-container-low p-3">
            <div className="mb-2 flex justify-between font-display text-[0.65rem] font-bold uppercase tracking-wider">
              <span style={{ color: awayPalette.color }}>
                {awayTeam} {awayPct}%
              </span>
              <span style={{ color: homePalette.color }}>
                {homeTeamCode} {homePct}%
              </span>
            </div>
            <div className="flex h-3 w-full overflow-hidden rounded-full bg-se-surface-variant">
              <div
                className="h-full"
                style={{ width: `${awayPct}%`, background: awayPalette.color }}
              />
              <div
                className="h-full"
                style={{ width: `${homePct}%`, background: homePalette.color }}
              />
            </div>
            <p className="mt-2 text-center font-body text-[0.65rem] text-se-on-surface-variant">
              로지스틱 회귀 · 5-피처 기반 예측
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

function TeamColumn({
  name,
  logoPath,
  color,
  variant,
}: {
  name: string;
  logoPath: string;
  color: string;
  variant: "away" | "home";
}) {
  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative flex h-16 w-16 items-center justify-center rounded-full border-4 border-se-surface-container-lowest bg-se-surface-container shadow-[0_4px_12px_rgba(0,0,0,0.08)]">
        <Image
          src={logoPath}
          alt={`${name} 로고`}
          width={40}
          height={40}
          className="object-contain"
        />
        <div
          className="absolute -bottom-2 rounded-full px-2 py-0.5 font-display text-[9px] font-bold uppercase tracking-wider text-white shadow-sm"
          style={{ background: variant === "home" ? color : "#43474f" }}
        >
          {variant === "home" ? "Home" : "Away"}
        </div>
      </div>
      <span className="font-display text-sm font-bold text-se-on-surface">
        {name}
      </span>
    </div>
  );
}
