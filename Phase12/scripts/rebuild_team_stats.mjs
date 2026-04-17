#!/usr/bin/env node
/**
 * 실제 FINISHED 경기 결과로 team-stats.json 의 현재 시즌 엔트리를 재계산.
 *
 * 소스: frontend/public/data/schedule.json (fetch_kbo_schedule.mjs 산출물)
 * 대상: frontend/public/data/team-stats.json (기존 2015~2025 보존 + 2026 추가/갱신)
 *
 * 사용:
 *   node scripts/rebuild_team_stats.mjs [--season 2026]
 */
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, "..");
const SCHEDULE = path.join(REPO_ROOT, "frontend/public/data/schedule.json");
const STATS = path.join(REPO_ROOT, "frontend/public/data/team-stats.json");

function parseArgs() {
  const args = process.argv.slice(2);
  let season = 2026;
  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--season" && args[i + 1]) season = Number(args[++i]);
  }
  return { season };
}

function makeEmptyRecord(team, season) {
  return {
    year: season,
    team,
    games_played: 0,
    wins: 0,
    losses: 0,
    draws: 0,
    win_rate: 0,
    home_win_rate: 0,
    away_win_rate: 0,
    final_rank: 0,
    _home_games: 0,
    _home_wins: 0,
    _home_losses: 0,
    _away_games: 0,
    _away_wins: 0,
    _away_losses: 0,
  };
}

function finalize(rec) {
  const { games_played, wins, losses, draws } = rec;
  const decided = wins + losses; // KBO 전통: 무승부 제외한 승률
  rec.win_rate = decided > 0 ? Number((wins / decided).toFixed(3)) : 0;
  rec.home_win_rate =
    rec._home_games > 0
      ? Number(
          (rec._home_wins / (rec._home_wins + rec._home_losses || 1)).toFixed(3),
        )
      : 0;
  rec.away_win_rate =
    rec._away_games > 0
      ? Number(
          (rec._away_wins / (rec._away_wins + rec._away_losses || 1)).toFixed(3),
        )
      : 0;
  // 내부 필드 제거
  delete rec._home_games;
  delete rec._home_wins;
  delete rec._home_losses;
  delete rec._away_games;
  delete rec._away_wins;
  delete rec._away_losses;
  return rec;
}

async function main() {
  const { season } = parseArgs();
  console.log(`🔍 Rebuilding team stats for ${season} season`);

  const [scheduleRaw, statsRaw] = await Promise.all([
    fs.readFile(SCHEDULE, "utf-8"),
    fs.readFile(STATS, "utf-8"),
  ]);
  const schedule = JSON.parse(scheduleRaw);
  const stats = JSON.parse(statsRaw);

  const finished = schedule.filter(
    (g) => g.status === "FINISHED" && g.score && g.season === season,
  );
  console.log(`  📊 ${finished.length} FINISHED games for season ${season}`);

  const records = new Map();

  function rec(team) {
    if (!records.has(team)) records.set(team, makeEmptyRecord(team, season));
    return records.get(team);
  }

  for (const g of finished) {
    const home = rec(g.home_team);
    const away = rec(g.away_team);
    home.games_played++;
    away.games_played++;
    home._home_games++;
    away._away_games++;

    const { home: hs, away: as } = g.score;
    if (hs > as) {
      home.wins++;
      home._home_wins++;
      away.losses++;
      away._away_losses++;
    } else if (hs < as) {
      home.losses++;
      home._home_losses++;
      away.wins++;
      away._away_wins++;
    } else {
      home.draws++;
      away.draws++;
    }
  }

  // 최종 계산 + 순위 (win_rate desc)
  const finalized = [...records.values()].map(finalize);
  finalized.sort((a, b) => b.win_rate - a.win_rate);
  finalized.forEach((r, i) => {
    r.final_rank = i + 1;
  });

  // 기존 2026 엔트리 제거 후 덮어쓰기
  const cleaned = stats.filter((r) => r.year !== season);
  const merged = [...cleaned, ...finalized];

  await fs.writeFile(STATS, JSON.stringify(merged, null, 2));
  console.log(`✅ Wrote ${path.relative(REPO_ROOT, STATS)}`);
  console.log(`\n📈 ${season} 시즌 현재 순위:`);
  console.log(
    "  순위 | 팀   | 경기 | 승 | 패 | 무 | 승률  | 홈    | 원정");
  console.log(
    "  ---- | ---- | ---- | -- | -- | -- | ----- | ----- | -----");
  for (const r of finalized) {
    console.log(
      `  ${String(r.final_rank).padStart(4)} | ${r.team.padEnd(4)} | ${String(r.games_played).padStart(4)} | ${String(r.wins).padStart(2)} | ${String(r.losses).padStart(2)} | ${String(r.draws).padStart(2)} | ${r.win_rate.toFixed(3)} | ${r.home_win_rate.toFixed(3)} | ${r.away_win_rate.toFixed(3)}`,
    );
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
