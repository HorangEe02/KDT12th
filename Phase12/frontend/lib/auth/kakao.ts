/**
 * Kakao OAuth + Firebase Custom Token 통합 (서버 전용).
 * Authorization Code flow:
 *   1) /api/auth/kakao/start    → kauth.kakao.com/oauth/authorize
 *   2) /api/auth/kakao/callback → exchangeCodeForToken → fetchKakaoUser
 *   3) mintFirebaseCustomToken  → HttpOnly cookie
 *   4) /login/complete          → signInWithCustomToken → /api/auth/session
 */
import "server-only";
import { getAdminAuth } from "@/lib/firebase/admin";

const AUTHORIZE_URL = "https://kauth.kakao.com/oauth/authorize";
const TOKEN_URL = "https://kauth.kakao.com/oauth/token";
const USERINFO_URL = "https://kapi.kakao.com/v2/user/me";

export interface KakaoUserInfo {
  id: number;
  nickname: string | null;
  profileImage: string | null;
  email: string | null;
}

export function buildAuthorizeUrl(params: {
  redirectUri: string;
  state: string;
}): string {
  const clientId = process.env.KAKAO_REST_API_KEY;
  if (!clientId) throw new Error("KAKAO_REST_API_KEY 미설정");
  const u = new URL(AUTHORIZE_URL);
  u.searchParams.set("client_id", clientId);
  u.searchParams.set("redirect_uri", params.redirectUri);
  u.searchParams.set("response_type", "code");
  u.searchParams.set("state", params.state);
  u.searchParams.set("scope", "profile_nickname,profile_image");
  return u.toString();
}

export async function exchangeCodeForToken(params: {
  code: string;
  redirectUri: string;
}): Promise<string> {
  const clientId = process.env.KAKAO_REST_API_KEY;
  if (!clientId) throw new Error("KAKAO_REST_API_KEY 미설정");
  const clientSecret = process.env.KAKAO_CLIENT_SECRET;

  const form = new URLSearchParams({
    grant_type: "authorization_code",
    client_id: clientId,
    redirect_uri: params.redirectUri,
    code: params.code,
  });
  if (clientSecret) form.set("client_secret", clientSecret);

  const res = await fetch(TOKEN_URL, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: form.toString(),
    signal: AbortSignal.timeout(5000),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Kakao 토큰 교환 실패 (${res.status}): ${text}`);
  }
  const json = (await res.json()) as { access_token?: string };
  if (!json.access_token) throw new Error("access_token 없음");
  return json.access_token;
}

export async function fetchKakaoUser(
  accessToken: string,
): Promise<KakaoUserInfo> {
  const res = await fetch(USERINFO_URL, {
    method: "GET",
    headers: { Authorization: `Bearer ${accessToken}` },
    signal: AbortSignal.timeout(5000),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Kakao userinfo 실패 (${res.status}): ${text}`);
  }
  const data = (await res.json()) as {
    id: number;
    kakao_account?: {
      email?: string;
      profile?: { nickname?: string; profile_image_url?: string };
    };
  };
  const profile = data.kakao_account?.profile;
  return {
    id: data.id,
    nickname: profile?.nickname ?? null,
    profileImage: profile?.profile_image_url ?? null,
    email: data.kakao_account?.email ?? null,
  };
}

/**
 * Firebase Auth 에 `kakao:{id}` uid 로 레코드 upsert → custom token 발급.
 * 이메일은 Firebase Auth 에 저장하지 않는다 (Google 계정과 uid 충돌 방지).
 * 프로필 정보는 /api/auth/session 단계에서 Firestore `users/{uid}` 에 저장됨.
 */
export async function mintFirebaseCustomToken(
  user: KakaoUserInfo,
): Promise<string> {
  const uid = `kakao:${user.id}`;
  const auth = getAdminAuth();
  const patch: { displayName?: string; photoURL?: string } = {};
  if (user.nickname) patch.displayName = user.nickname;
  if (user.profileImage) patch.photoURL = user.profileImage;

  try {
    await auth.getUser(uid);
    if (Object.keys(patch).length > 0) {
      await auth.updateUser(uid, patch);
    }
  } catch {
    await auth.createUser({ uid, ...patch });
  }

  return auth.createCustomToken(uid, {
    provider: "kakao",
    kakao_uid: user.id,
  });
}
