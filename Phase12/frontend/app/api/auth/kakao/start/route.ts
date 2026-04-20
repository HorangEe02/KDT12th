/**
 * Kakao OAuth start — state cookie 발급 + kauth.kakao.com 으로 302.
 * next 파라미터를 쿠키에 저장해 콜백 후 원래 목적지로 복귀.
 */
import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { randomBytes } from "node:crypto";
import { buildAuthorizeUrl } from "@/lib/auth/kakao";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const STATE_COOKIE = "__kakao_oauth_state";
const NEXT_COOKIE = "__kakao_oauth_next";

export async function GET(req: Request) {
  const url = new URL(req.url);
  const nextParam = sanitizeNext(url.searchParams.get("next"));
  const redirectUri = `${url.origin}/api/auth/kakao/callback`;
  const state = randomBytes(16).toString("hex");

  const jar = await cookies();
  const opts = {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax" as const,
    path: "/",
    maxAge: 300,
  };
  jar.set(STATE_COOKIE, state, opts);
  jar.set(NEXT_COOKIE, nextParam, opts);

  try {
    return NextResponse.redirect(buildAuthorizeUrl({ redirectUri, state }));
  } catch (err) {
    const msg = err instanceof Error ? err.message : "kakao_start_failed";
    return NextResponse.redirect(
      new URL(`/login?kakao_error=${encodeURIComponent(msg)}`, url.origin),
    );
  }
}

function sanitizeNext(n: string | null): string {
  if (!n) return "/";
  if (!n.startsWith("/") || n.startsWith("//")) return "/";
  return n;
}
