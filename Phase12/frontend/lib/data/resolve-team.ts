import "server-only";
import { cookies } from "next/headers";
import {
  SESSION_COOKIE_NAME,
} from "@/lib/firebase/server-session";
import {
  getAdminAuth,
  getAdminFirestore,
  isAdminConfigured,
} from "@/lib/firebase/admin";
import { TEAM_COLORS } from "@/lib/team-colors";

const DEFAULT_TEAM = "LG";

/**
 * 서버 컴포넌트에서 "현재 응원팀" 을 해결.
 *
 * 우선순위:
 *   1. URL `?team=XX`        (공유 링크 · 최우선)
 *   2. Firestore users/{uid}.favoriteTeam  (로그인 사용자 프로필)
 *   3. "LG"                   (fallback)
 *
 * Hero · TeamSelector · 각 라우트 페이지에서 이 함수를 호출해 팀 기본값을 통일.
 * 클라이언트 `useFavoriteTeamSync` 훅은 filters.team 을 함께 갱신하여 SSR·CSR 동기.
 */
export async function resolveTeam(
  urlTeam?: string | undefined,
): Promise<string> {
  if (urlTeam && urlTeam in TEAM_COLORS) return urlTeam;
  if (!isAdminConfigured()) return DEFAULT_TEAM;
  try {
    const cookieStore = await cookies();
    const session = cookieStore.get(SESSION_COOKIE_NAME)?.value;
    if (!session) return DEFAULT_TEAM;
    const decoded = await getAdminAuth().verifySessionCookie(session, false);
    const snap = await getAdminFirestore()
      .collection("users")
      .doc(decoded.uid)
      .get();
    const fav = snap.data()?.favoriteTeam;
    if (typeof fav === "string" && fav in TEAM_COLORS) return fav;
  } catch {
    // 쿠키 만료 · 세션 무효 · Firestore 오류 등 — 기본값 반환
  }
  return DEFAULT_TEAM;
}
