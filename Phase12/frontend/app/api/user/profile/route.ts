import { NextResponse } from "next/server";
import { getOptionalUser } from "@/lib/firebase/server-session";
import { getAdminFirestore, isAdminConfigured } from "@/lib/firebase/admin";
import { profileUpdateSchema } from "@/lib/validators/profile";

/**
 * PATCH /api/user/profile
 * 본인 프로필(닉네임·응원팀) 수정.
 *
 * - 인증: __session 쿠키 (세션 검증)
 * - graceful: Firebase Admin 미구성 시 503
 * - 타 사용자 편집은 불가 (admin 전용 엔드포인트는 별도)
 */
export const runtime = "nodejs";

export async function PATCH(req: Request) {
  if (!isAdminConfigured()) {
    return NextResponse.json(
      { error: "Firebase Admin SDK 미구성 — 로그인 기능 비활성" },
      { status: 503 },
    );
  }

  const user = await getOptionalUser({ checkRevoked: true });
  if (!user) {
    return NextResponse.json(
      { error: "로그인이 필요합니다." },
      { status: 401 },
    );
  }
  if (user.isDisabled) {
    return NextResponse.json(
      { error: "비활성화된 계정입니다." },
      { status: 403 },
    );
  }

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json(
      { error: "잘못된 JSON 바디" },
      { status: 400 },
    );
  }

  const parsed = profileUpdateSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json(
      {
        error: "유효성 검증 실패",
        issues: parsed.error.issues.map((i) => ({
          path: i.path.join("."),
          message: i.message,
        })),
      },
      { status: 400 },
    );
  }

  const db = getAdminFirestore();
  const ref = db.collection("users").doc(user.uid);
  const now = new Date();
  const updates: Record<string, unknown> = { lastActiveAt: now };
  if (parsed.data.displayName !== undefined) {
    updates.displayName = parsed.data.displayName;
  }
  if (parsed.data.favoriteTeam !== undefined) {
    updates.favoriteTeam = parsed.data.favoriteTeam;
  }

  try {
    await ref.set(updates, { merge: true });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Firestore 업데이트 실패";
    return NextResponse.json({ error: message }, { status: 500 });
  }

  const snap = await ref.get();
  const data = snap.data() ?? {};
  return NextResponse.json({
    uid: user.uid,
    displayName: typeof data.displayName === "string" ? data.displayName : null,
    favoriteTeam:
      typeof data.favoriteTeam === "string" ? data.favoriteTeam : null,
    updatedAt: now.toISOString(),
  });
}
