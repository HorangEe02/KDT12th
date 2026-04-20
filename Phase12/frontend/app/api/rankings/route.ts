import { NextResponse } from "next/server";
import { getTeamRankings } from "@/lib/api/rankings";

/**
 * GET /api/rankings?team=삼성  ← team 은 선택
 * 현재 KBO 시즌 팀 순위 조회.
 *
 * 향후 확장:
 *   - Cloud Scheduler 가 /api/rankings/refresh 를 일 1회 호출 → Firestore 캐시 갱신
 *   - 실제 크롤링 (Naver 스포츠 · KBO 공식) 로직 추가 시 내부 orchestrator 만 교체
 */
export const runtime = "nodejs";

export async function GET(req: Request) {
  const url = new URL(req.url);
  const team = url.searchParams.get("team") ?? undefined;
  try {
    const result = await getTeamRankings(team);
    return NextResponse.json(result);
  } catch (err) {
    const message = err instanceof Error ? err.message : "순위 조회 실패";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
