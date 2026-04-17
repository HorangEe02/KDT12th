/**
 * POST /api/plans  — shared_plans 생성 (Firestore 가능 시)
 *   body: { filters: {...}, title?: string }
 *   200:  { id: string, storage: "firestore" } | 503 { error: "unavailable" }
 */
import { NextResponse } from "next/server";
import { z } from "zod";
import { createSharedPlan } from "@/lib/firebase/shared-plans";

export const runtime = "nodejs";

const Body = z.object({
  filters: z.record(z.string(), z.unknown()),
  title: z.string().max(120).optional(),
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
  const id = await createSharedPlan(parsed.filters, parsed.title);
  if (!id) {
    return NextResponse.json(
      { error: "unavailable", detail: "Firestore 미구성 — URL 쿼리 방식 사용" },
      { status: 503 },
    );
  }
  return NextResponse.json({ id, storage: "firestore" });
}
