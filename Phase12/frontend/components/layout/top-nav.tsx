"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { cn } from "@/lib/utils";
import { getTeamPalette } from "@/lib/team-colors";

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
  const team = searchParams.get("team") ?? teamFromServer ?? "LG";
  const palette = getTeamPalette(team);

  const qs = (() => {
    const p = new URLSearchParams(searchParams.toString());
    return p.toString() ? `?${p.toString()}` : "";
  })();

  return (
    <nav className="sticky top-0 z-40 w-full border-b border-se-outline-variant bg-white/80 backdrop-blur-md">
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
      </div>
    </nav>
  );
}
