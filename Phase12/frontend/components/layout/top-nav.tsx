"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { cn } from "@/lib/utils";
import { getTeamPalette, TEAM_COLORS } from "@/lib/team-colors";
import { useAuthUser, useAuthProfile, useIsAdmin } from "@/lib/store/auth";
import { useFilters } from "@/lib/store/filters";

const TABS = [
  { href: "/", label: "Home", icon: "home" },
  { href: "/matches", label: "Matches", icon: "sports_baseball" },
  { href: "/map", label: "Map", icon: "map" },
  { href: "/places", label: "Places", icon: "restaurant" },
  { href: "/ai", label: "AI", icon: "smart_toy" },
  { href: "/badges", label: "Badges", icon: "workspace_premium" },
] as const;

export function TopNav({ team: teamFromServer }: { team?: string }) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const authUser = useAuthUser();
  const profile = useAuthProfile();
  const isAdmin = useIsAdmin();
  const filtersTeam = useFilters((s) => s.team);

  /**
   * 팀 우선순위 (높음 → 낮음):
   *   1. URL ?team=XX       (공유 링크 · 명시적 의도)
   *   2. filters.team       (Zustand · useFavoriteTeamSync 로 profile.favoriteTeam hydrate됨)
   *   3. profile.favoriteTeam(Firestore · 백업용)
   *   4. teamFromServer     (서버 컴포넌트가 prop 으로 내려준 값)
   *   5. "LG"               (최종 fallback)
   *
   * 이전에는 URL → teamFromServer → "LG" 순이라 로그인 사용자가 삼성 설정해도
   * URL 에 team= 이 없으면 항상 "LG" 로 fallback 되던 문제 수정.
   */
  const candidates = [
    searchParams.get("team"),
    filtersTeam,
    profile?.favoriteTeam ?? undefined,
    teamFromServer,
    "LG",
  ];
  const team = candidates.find(
    (t): t is string => typeof t === "string" && t.length > 0 && t in TEAM_COLORS,
  ) ?? "LG";
  const palette = getTeamPalette(team);

  const qs = (() => {
    const p = new URLSearchParams(searchParams.toString());
    return p.toString() ? `?${p.toString()}` : "";
  })();

  return (
    <nav
      className="sticky top-0 z-40 w-full border-b border-se-outline-variant bg-white/80 backdrop-blur-md"
      style={{ paddingTop: "env(safe-area-inset-top)" }}
    >
      <div className="mx-auto flex h-16 max-w-[1240px] items-center justify-between px-4 md:px-8">
        <Link
          href={{ pathname: "/", query: Object.fromEntries(searchParams) }}
          className="flex items-center gap-2 no-underline"
          aria-label="홈"
        >
          <span className="material-symbols-outlined text-se-primary">
            sports_baseball
          </span>
          <span className="font-display text-base font-extrabold tracking-tight text-se-primary">
            원정 응원 플래너
          </span>
        </Link>

        <div className="flex items-center gap-2 md:gap-3">
          {/* 데스크톱 탭 */}
          <div className="hidden items-center gap-1 md:flex">
            {TABS.slice(1).map((t) => {
              const active =
                pathname === t.href ||
                (t.href !== "/" && pathname.startsWith(t.href));
              return (
                <Link
                  key={t.href}
                  href={`${t.href}${qs}`}
                  aria-current={active ? "page" : undefined}
                  className={cn(
                    "flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-semibold no-underline transition-colors",
                    active
                      ? "bg-se-primary text-white"
                      : "text-se-on-surface-variant hover:bg-se-surface-container-low hover:text-se-primary",
                  )}
                >
                  <span className="material-symbols-outlined text-[18px]">
                    {t.icon}
                  </span>
                  <span className="hidden lg:inline">{t.label}</span>
                </Link>
              );
            })}
          </div>

          {/* 팀 배지 (sm+) */}
          <div
            className="hidden items-center gap-2 rounded-full border border-se-outline-variant px-3 py-1 sm:flex"
            title={`응원팀: ${palette.nameKo}`}
          >
            <span
              className="h-3 w-3 rounded-full"
              style={{ background: palette.color }}
            />
            <span className="font-display text-xs font-bold text-se-primary">
              {team}
            </span>
          </div>

          {/* 모바일 전용 관리자 콘솔 바로가기 (< md · admin 만 표시) */}
          {authUser && isAdmin ? (
            <Link
              href="/admin"
              aria-label="관리자 콘솔"
              title="관리자 콘솔"
              className="flex h-10 w-10 items-center justify-center rounded-full border-2 border-se-secondary bg-white text-se-secondary shadow-[0_2px_6px_rgba(27,109,36,0.15)] md:hidden"
            >
              <span
                className="material-symbols-outlined text-[20px]"
                style={{ fontVariationSettings: "'FILL' 1" }}
              >
                admin_panel_settings
              </span>
            </Link>
          ) : null}

          {/* 모바일 전용 계정 진입 버튼 (< md) — 로그인 여부에 따라 /account or /login */}
          <Link
            href={authUser ? "/account" : "/login?next=/account"}
            aria-label={authUser ? "내 계정" : "로그인"}
            className="flex h-10 w-10 items-center justify-center rounded-full border border-se-outline-variant bg-white text-se-primary shadow-[0_2px_6px_rgba(0,0,0,0.04)] md:hidden"
          >
            <span
              className="material-symbols-outlined text-[20px]"
              style={authUser ? { fontVariationSettings: "'FILL' 1" } : undefined}
            >
              {authUser ? "person" : "login"}
            </span>
          </Link>
        </div>
      </div>
    </nav>
  );
}
