/**
 * 서버 측 세션 헬퍼 — Firebase Admin SDK 사용.
 * 사용처: app/api/auth/session/route.ts, app/admin/layout.tsx, RSC 인증 검증
 *
 * 쿠키 이름은 `__session` 으로 고정 — Firebase App Hosting 캐시 우회 동작.
 * 참고: docs/FIREBASE_DB_PLAN.md §2-3
 */
import "server-only";
import { cookies } from "next/headers";
import type { DecodedIdToken } from "firebase-admin/auth";
import { getAdminAuth, getAdminFirestore, isAdminConfigured } from "./admin";

export const SESSION_COOKIE_NAME = "__session";
export const SESSION_DURATION_DAYS = Number.parseInt(
  process.env.SESSION_COOKIE_DAYS ?? "5",
  10,
);
const SESSION_MS = SESSION_DURATION_DAYS * 24 * 60 * 60 * 1000;

// ────────────────────────────────────────────────────────────
// Cookie helpers
// ────────────────────────────────────────────────────────────

export interface SessionUser {
  uid: string;
  email: string;
  displayName: string | null;
  photoURL: string | null;
  emailVerified: boolean;
  isAdmin: boolean;
  isDisabled: boolean;
}

/**
 * idToken 으로 5일짜리 session cookie 생성 + Set-Cookie.
 * 회원가입 시 initialProfile 을 받아 users/{uid} 도큐먼트도 동시에 생성.
 */
export async function createSessionCookie(
  idToken: string,
  initialProfile?: Record<string, unknown>,
): Promise<{ ok: true; uid: string } | { ok: false; error: string }> {
  if (!isAdminConfigured()) {
    return { ok: false, error: "Firebase Admin SDK 미구성 (서버)" };
  }
  try {
    const decoded = await getAdminAuth().verifyIdToken(idToken, /* checkRevoked */ true);
    const sessionCookie = await getAdminAuth().createSessionCookie(idToken, {
      expiresIn: SESSION_MS,
    });
    const cookieStore = await cookies();
    cookieStore.set(SESSION_COOKIE_NAME, sessionCookie, {
      maxAge: SESSION_MS / 1000,
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      path: "/",
    });
    await upsertUserDocument(decoded, initialProfile);
    return { ok: true, uid: decoded.uid };
  } catch (err) {
    const message =
      err instanceof Error ? err.message : "session cookie 발급 실패";
    return { ok: false, error: message };
  }
}

/** 세션 쿠키 삭제 (로그아웃) */
export async function clearSessionCookie(): Promise<void> {
  const cookieStore = await cookies();
  cookieStore.delete(SESSION_COOKIE_NAME);
}

// ────────────────────────────────────────────────────────────
// Verification
// ────────────────────────────────────────────────────────────

/**
 * 서버 컴포넌트/RSC 에서 호출 — 로그인 안돼 있으면 null.
 * checkRevoked=false (성능 우선). admin 페이지에서는 true 권장.
 */
export async function getOptionalUser(opts?: {
  checkRevoked?: boolean;
}): Promise<SessionUser | null> {
  if (!isAdminConfigured()) return null;
  const cookieStore = await cookies();
  const session = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  if (!session) return null;
  try {
    const decoded = await getAdminAuth().verifySessionCookie(
      session,
      opts?.checkRevoked ?? false,
    );
    return decodedToSessionUser(decoded);
  } catch {
    return null;
  }
}

/** 로그인 필수 — 미인증 시 throw */
export async function requireUser(): Promise<SessionUser> {
  const user = await getOptionalUser({ checkRevoked: true });
  if (!user) throw new Error("UNAUTHENTICATED");
  if (user.isDisabled) throw new Error("USER_DISABLED");
  return user;
}

/** 관리자 필수 — 미인증/비-admin 시 throw */
export async function requireAdmin(): Promise<SessionUser> {
  const user = await requireUser();
  if (!user.isAdmin) throw new Error("FORBIDDEN");
  return user;
}

function decodedToSessionUser(d: DecodedIdToken): SessionUser {
  return {
    uid: d.uid,
    email: typeof d.email === "string" ? d.email : "",
    displayName: typeof d.name === "string" ? d.name : null,
    photoURL: typeof d.picture === "string" ? d.picture : null,
    emailVerified: Boolean(d.email_verified),
    isAdmin: d.admin === true,
    isDisabled: d.disabled === true,
  };
}

// ────────────────────────────────────────────────────────────
// users/{uid} 도큐먼트 upsert
// ────────────────────────────────────────────────────────────

async function upsertUserDocument(
  decoded: DecodedIdToken,
  initialProfile?: Record<string, unknown>,
): Promise<void> {
  const db = getAdminFirestore();
  const ref = db.collection("users").doc(decoded.uid);
  const snap = await ref.get();
  const now = new Date();

  if (!snap.exists) {
    await ref.set({
      uid: decoded.uid,
      email: decoded.email ?? "",
      displayName:
        (initialProfile?.displayName as string | undefined) ??
        decoded.name ??
        "사용자",
      photoURL:
        (initialProfile?.photoURL as string | undefined) ??
        decoded.picture ??
        null,
      role: "user",
      status: "active",
      favoriteTeam:
        (initialProfile?.favoriteTeam as string | null | undefined) ?? null,
      createdAt: now,
      lastSignInAt: now,
      lastActiveAt: now,
      stats: {
        visitedCount: 0,
        planCount: 0,
        chatSessionCount: 0,
        lastPlanAt: null,
      },
      consent: initialProfile?.consent ?? {
        tos: true,
        tosVersion: "v1",
        tosAt: now,
        privacy: true,
        privacyAt: now,
        marketing: false,
      },
    });
  } else {
    await ref.update({ lastSignInAt: now, lastActiveAt: now });
  }
}

// ────────────────────────────────────────────────────────────
// Admin actions (audit 포함)
// ────────────────────────────────────────────────────────────

export async function logAuditEvent(input: {
  adminUid: string;
  adminEmail: string;
  action: string;
  targetUid: string;
  targetEmail: string;
  reason: string;
  ip?: string | null;
}): Promise<void> {
  if (!isAdminConfigured()) return;
  await getAdminFirestore()
    .collection("admin_audit")
    .add({ ...input, createdAt: new Date() });
}
