#!/usr/bin/env node
/**
 * KBO 2026 시즌 전체 경기 데이터 크롤러.
 *
 * 소스: kbo-game@0.0.2 (MIT · https://github.com/vkehfdl1/kbo-game)
 * 대상: frontend/public/data/schedule.json
 *
 * 사용:
 *   npm install --prefix scripts
 *   node scripts/fetch_kbo_schedule.mjs
 *   (optional)  node scripts/fetch_kbo_schedule.mjs --start 2026-03-28 --end 2026-11-15
 */
import { getGame } from "kbo-game";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, "..");
const OUTPUT = path.join(
  REPO_ROOT,
  "frontend/public/data/schedule.json",
);
const BACKUP = path.join(
  REPO_ROOT,
  "frontend/public/data/schedule.prev.json",
);

const DEFAULT_START = "2026-03-28";
const DEFAULT_END = "2026-11-15";
const DELAY_MS = 200;
const RETRY = 3;
const DOW = ["일", "월", "화", "수", "목", "금", "토"];

const STADIUM_SHORT = {
  잠실: "잠실",
  "잠실 (낮)": "잠실",
  "잠실 (밤)": "잠실",
  고척: "고척",
  수원: "수원",
  인천: "문학",
  문학: "문학",
  대전: "대전",
  대구: "대구",
  광주: "광주",
  창원: "창원",
  부산: "사직",
  사직: "사직",
  한밭: "한밭",
};

function parseArgs() {
  const args = process.argv.slice(2);
  const out = { start: DEFAULT_START, end: DEFAULT_END };
  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--start" && args[i + 1]) out.start = args[++i];
    else if (args[i] === "--end" && args[i + 1]) out.end = args[++i];
  }
  return out;
}

function normalizeStadium(raw) {
  if (!raw) return "미정";
  const key = String(raw).trim();
  if (STADIUM_SHORT[key]) return STADIUM_SHORT[key];
  for (const [k, v] of Object.entries(STADIUM_SHORT)) {
    if (key.includes(k)) return v;
  }
  return key;
}

function normalizeGame(g) {
  const d = new Date(g.date);
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  const dateStr = `${yyyy}-${mm}-${dd}`;
  const isFinal =
    g.status === "FINISHED" || g.status === "IN_PROGRESS" || g.status === "CANCELED";

  return {
    game_id: g.id,
    date: dateStr,
    day_of_week: DOW[d.getDay()],
    home_team: g.homeTeam,
    away_team: g.awayTeam,
    stadium: normalizeStadium(g.stadium),
    start_time: g.startTime ?? "",
    home_pitcher: g.homePitcher?.trim() || null,
    away_pitcher: g.awayPitcher?.trim() || null,
    win_pitcher: g.winPitcher?.trim() || null,
    lose_pitcher: g.losePitcher?.trim() || null,
    save_pitcher: g.savePitcher?.trim() || null,
    score: isFinal && Number.isFinite(g.score?.home) && Number.isFinite(g.score?.away)
      ? { home: g.score.home, away: g.score.away }
      : null,
    status: g.status ?? "SCHEDULED",
    current_inning: g.currentInning ?? null,
    broadcast: Array.isArray(g.broadcastServices) ? g.broadcastServices : [],
    season: g.season ?? 2026,
  };
}

async function fetchDate(dateObj, attempt = 1) {
  try {
    const games = await getGame(dateObj);
    return games ?? [];
  } catch (err) {
    if (attempt >= RETRY) throw err;
    await new Promise((r) => setTimeout(r, 500 * attempt));
    return fetchDate(dateObj, attempt + 1);
  }
}

async function main() {
  const { start, end } = parseArgs();
  const startDate = new Date(`${start}T00:00:00+09:00`);
  const endDate = new Date(`${end}T00:00:00+09:00`);

  console.log(`🔍 Crawling KBO schedule: ${start} → ${end}`);

  // 기존 데이터 백업
  try {
    const existing = await fs.readFile(OUTPUT, "utf-8");
    await fs.writeFile(BACKUP, existing);
    console.log(`💾 Backed up existing → ${path.basename(BACKUP)}`);
  } catch {
    // no existing file · skip
  }

  const all = [];
  const stats = { days: 0, empty: 0, errors: 0 };

  for (
    const d = new Date(startDate);
    d <= endDate;
    d.setDate(d.getDate() + 1)
  ) {
    stats.days++;
    try {
      const games = await fetchDate(new Date(d));
      if (!games.length) {
        stats.empty++;
      } else {
        for (const g of games) all.push(normalizeGame(g));
      }
      process.stdout.write(
        `  ${d.toISOString().slice(0, 10)} — ${games.length.toString().padStart(2)} games\r`,
      );
    } catch (err) {
      stats.errors++;
      console.warn(
        `\n  ⚠️  ${d.toISOString().slice(0, 10)} failed: ${err.message}`,
      );
    }
    await new Promise((r) => setTimeout(r, DELAY_MS));
  }

  console.log(
    `\n📊 ${all.length} games · ${stats.days} days · ${stats.empty} empty · ${stats.errors} errors`,
  );

  // 정렬: date asc, then start_time
  all.sort(
    (a, b) =>
      a.date.localeCompare(b.date) ||
      (a.start_time || "").localeCompare(b.start_time || ""),
  );

  await fs.writeFile(OUTPUT, JSON.stringify(all, null, 2));
  const size = (await fs.stat(OUTPUT)).size;
  console.log(
    `✅ Wrote ${path.relative(REPO_ROOT, OUTPUT)} · ${(size / 1024).toFixed(1)} KB`,
  );

  // 요약 통계
  const byStatus = {};
  const byTeam = {};
  for (const g of all) {
    byStatus[g.status] = (byStatus[g.status] ?? 0) + 1;
    byTeam[g.home_team] = (byTeam[g.home_team] ?? 0) + 1;
    byTeam[g.away_team] = (byTeam[g.away_team] ?? 0) + 1;
  }
  console.log("\n📈 Status:", byStatus);
  console.log("📈 Games per team (home+away):");
  for (const [t, n] of Object.entries(byTeam).sort((a, b) => b[1] - a[1])) {
    console.log(`    ${t.padEnd(4)}  ${n}`);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
