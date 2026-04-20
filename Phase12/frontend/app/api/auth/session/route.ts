/**
 * 세션 쿠키 발급/삭제 API.
 *
 * POST /api/auth/session  body: { idToken, profile? }   → __session 쿠키 + users/{uid} upsert
 * DELETE /api/auth/session                              → __session 쿠키 삭제
 *
 * 참고: docs/FIREBASE_DB_PLAN.md §2-3
 */
import { NextResponse } from "next/server";
import { z } from "zod";
import {
  createSessionCookie,
  clearSessionCookie,
} from "@/lib/firebase/server-session";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const PostBody = z.object({
  idToken: z.string().min(50, "idToken 누락"),
  profile: z
    .object({
      displayName: z.string().max(50).optional(),
      photoURL: z.string().nullable().optional(),
      favoriteTeam: z.string().nullable().optional(),
      consent: z
        .object({
          tos: z.boolean(),
          tosVersion: z.string().optional(),
          tosAt: z.union([z.number(), z.string()]).optional(),
          privacy: z.boolean(),
          privacyAt: z.union([z.number(), z.string()]).optional(),
          marketing: z.boolean(),
        })
        .optional(),
    })
    .optional(),
});

export async function POST(req: Request) {
  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "INVALID_JSON" }, { status: 400 });
  }
  const parsed = PostBody.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json(
      { error: "INVALID_BODY", issues: parsed.error.issues },
      { status: 400 },
    );
  }

  const result = await createSessionCookie(
    parsed.data.idToken,
    parsed.data.profile as Record<string, unknown> | undefined,
  );
  if (!result.ok) {
    const status = result.error.includes("미구성") ? 503 : 401;
    return NextResponse.json({ error: result.error }, { status });
  }
  return NextResponse.json({ ok: true, uid: result.uid });
}

export async function DELETE() {
  await clearSessionCookie();
  return NextResponse.json({ ok: true });
}
