import { NextResponse } from "next/server";
import { getLiveScore } from "@/lib/api/live-score";

/**
 * GET /api/live-score?date=2026-04-25&team=삼성
 * 모든 파라미터 선택. date 생략 시 오늘.
 */
export const runtime = "nodejs";

export async function GET(req: Request) {
  const url = new URL(req.url);
  const date = url.searchParams.get("date") ?? undefined;
  const team = url.searchParams.get("team") ?? undefined;
  try {
    const result = await getLiveScore({ date, team });
    return NextResponse.json(result);
  } catch (err) {
    const message = err instanceof Error ? err.message : "라이브 스코어 조회 실패";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
