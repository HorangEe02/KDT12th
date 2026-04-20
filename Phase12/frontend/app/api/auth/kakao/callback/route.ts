/**
 * Kakao OAuth callback — code → token → userinfo → Firebase custom token.
 * Custom token 은 2분짜리 HttpOnly 쿠키로 저장 → /login/complete 가 소진.
 */
import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import {
  exchangeCodeForToken,
  fetchKakaoUser,
  mintFirebaseCustomToken,
} from "@/lib/auth/kakao";
import { isAdminConfigured } from "@/lib/firebase/admin";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const STATE_COOKIE = "__kakao_oauth_state";
const NEXT_COOKIE = "__kakao_oauth_next";
const TOKEN_COOKIE = "__kakao_custom_token";

export async function GET(req: Request) {
  const url = new URL(req.url);
  const code = url.searchParams.get("code");
  const state = url.searchParams.get("state");
  const error = url.searchParams.get("error");

  const jar = await cookies();
  const savedState = jar.get(STATE_COOKIE)?.value ?? null;
  const savedNext = jar.get(NEXT_COOKIE)?.value ?? "/";
  jar.delete(STATE_COOKIE);
  jar.delete(NEXT_COOKIE);

  const fail = (reason: string) =>
    NextResponse.redirect(
      new URL(`/login?kakao_error=${encodeURIComponent(reason)}`, url.origin),
    );

  if (error) return fail(error);
  if (!code || !state) return fail("missing_code");
  if (!savedState || savedState !== state) return fail("state_mismatch");
  if (!isAdminConfigured()) return fail("firebase_admin_unavailable");

  try {
    const redirectUri = `${url.origin}/api/auth/kakao/callback`;
    const accessToken = await exchangeCodeForToken({ code, redirectUri });
    const kakaoUser = await fetchKakaoUser(accessToken);
    const customToken = await mintFirebaseCustomToken(kakaoUser);

    jar.set(TOKEN_COOKIE, customToken, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      path: "/",
      maxAge: 120,
    });

    const dest = new URL("/login/complete", url.origin);
    dest.searchParams.set("next", savedNext);
    return NextResponse.redirect(dest);
  } catch (err) {
    const msg = err instanceof Error ? err.message : "unknown";
    return fail(msg);
  }
}
