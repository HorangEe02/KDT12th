import { NextResponse } from "next/server";
import { getPlayerStats } from "@/lib/api/player-stats";

/**
 * GET /api/player-stats?team=LG&name=이정후&position=batter
 * 모든 파라미터 선택. 조합 가능.
 */
export const runtime = "nodejs";

export async function GET(req: Request) {
  const url = new URL(req.url);
  const team = url.searchParams.get("team") ?? undefined;
  const name = url.searchParams.get("name") ?? undefined;
  const positionRaw = url.searchParams.get("position");
  const position =
    positionRaw === "batter" || positionRaw === "pitcher"
      ? positionRaw
      : undefined;
  try {
    const result = await getPlayerStats({ team, name, position });
    return NextResponse.json(result);
  } catch (err) {
    const message = err instanceof Error ? err.message : "선수 스탯 조회 실패";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
