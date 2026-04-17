/**
 * POST /api/predict
 * body: { team: string, opponent: string }
 * 200:  { team, opponent, prob: 0~1, source: "logreg"|"neutral-fallback"|"error" }
 */
import { NextResponse } from "next/server";
import { z } from "zod";
import { predictWinRate } from "@/lib/predict";

export const runtime = "nodejs"; // fs 접근 위해 node 런타임 강제

const Body = z.object({
  team: z.string().min(1),
  opponent: z.string().min(1),
});

export async function POST(request: Request) {
  let parsed;
  try {
    parsed = Body.parse(await request.json());
  } catch (err) {
    return NextResponse.json(
      { error: "invalid-body", detail: String(err) },
      { status: 400 },
    );
  }
  const result = await predictWinRate(parsed.team, parsed.opponent);
  return NextResponse.json(result);
}

/** GET 편의: ?team=LG&opponent=KT */
export async function GET(request: Request) {
  const url = new URL(request.url);
  const team = url.searchParams.get("team");
  const opponent = url.searchParams.get("opponent");
  if (!team || !opponent) {
    return NextResponse.json(
      { error: "missing-params", expected: ["team", "opponent"] },
      { status: 400 },
    );
  }
  const result = await predictWinRate(team, opponent);
  return NextResponse.json(result);
}
