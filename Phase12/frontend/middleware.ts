import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * 인증 게이트 — 미로그인 사용자는 /login?next=<원래경로> 로 리다이렉트.
 *
 * 규칙:
 *   - Public 경로(아래 배열): 통과 (로그인/가입/리셋/공유 링크)
 *   - 그 외 경로: `__session` 쿠키 없으면 /login 리다이렉트
 *   - 쿠키 유효성(세션 만료 등)은 middleware 에서 검증하지 않음 — 각 라우트 layout
 *     (getOptionalUser) 이 실제 검증. 이로써 Edge runtime 한계(Firebase Admin 미사용)를
 *     회피하며 빠른 1차 게이트만 수행.
 *
 * 매처 설정은 하단 `config.matcher` 참조 — API / 정적 에셋은 자동 제외.
 */

/** 로그인 없이 접근 가능한 경로 (접두사 매칭) */
const PUBLIC_PREFIXES = [
  "/login",
  "/signup",
  "/reset-password",
  "/share", // 공유 링크 — 친구가 로그인 없이 열람 가능
];

const SESSION_COOKIE = "__session";

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  // Public 경로 통과
  if (
    PUBLIC_PREFIXES.some(
      (p) => pathname === p || pathname.startsWith(p + "/"),
    )
  ) {
    return NextResponse.next();
  }

  // 세션 쿠키 있으면 통과 (layout 에서 실제 검증)
  if (req.cookies.has(SESSION_COOKIE)) {
    return NextResponse.next();
  }

  // 미인증 → /login 으로 리다이렉트, 원래 경로+쿼리를 next 에 보존
  const url = req.nextUrl.clone();
  const originalPath = pathname + req.nextUrl.search;
  url.pathname = "/login";
  url.search = "";
  url.searchParams.set("next", originalPath);
  return NextResponse.redirect(url);
}

export const config = {
  /**
   * 매처 — 다음은 자동 제외:
   *   - /api/* (API 라우트는 자체 401 처리)
   *   - /_next/* (Next.js 내부)
   *   - 정적 파일 (logos/, data/, favicon, .svg, .png, .ico, .json)
   */
  matcher: [
    "/((?!api|_next/static|_next/image|_next/data|favicon\\.ico|logos|data|manifest\\.json|.*\\.(?:svg|png|jpg|jpeg|webp|ico|json|xml|txt)).*)",
  ],
};
