/**
 * Kakao custom token 소진 — /login/complete 클라이언트가 호출.
 * 쿠키는 반환 즉시 삭제 (단발).
 */
import { NextResponse } from "next/server";
import { cookies } from "next/headers";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const TOKEN_COOKIE = "__kakao_custom_token";

export async function GET() {
  const jar = await cookies();
  const token = jar.get(TOKEN_COOKIE)?.value;
  if (!token) {
    return NextResponse.json({ error: "NO_TOKEN" }, { status: 404 });
  }
  jar.delete(TOKEN_COOKIE);
  return NextResponse.json({ token });
}
