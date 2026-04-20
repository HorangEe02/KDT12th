"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { cn } from "@/lib/utils";

/**
 * 모바일 전용 하단 BottomNav (5탭).
 * 모바일 mockup 의 핵심 패턴: 활성 탭은 secondary-fixed 녹색 pill + scale-110.
 * 출처: uiux/mobile_uiux/{matches,map,places,ai,badges}_mobile/
 */

interface Tab {
  href: string;
  label: string;
  icon: string;
}

const TABS: Tab[] = [
  { href: "/matches", label: "경기", icon: "sports_baseball" },
  { href: "/map", label: "지도", icon: "explore" },
  { href: "/places", label: "주변", icon: "restaurant" },
  { href: "/ai", label: "AI", icon: "auto_awesome" },
  { href: "/badges", label: "뱃지", icon: "military_tech" },
];

export function MobileBottomNav() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const qs = searchParams.toString() ? `?${searchParams.toString()}` : "";

  return (
    <nav
      role="navigation"
      aria-label="모바일 메인 메뉴"
      className="fixed bottom-0 left-0 right-0 z-50 flex items-end justify-around rounded-t-[2rem] bg-white/95 px-2 pb-6 pt-2 shadow-[0_-4px_20px_0_rgba(0,0,0,0.06)] backdrop-blur-xl md:hidden"
      style={{ paddingBottom: "max(1.5rem, env(safe-area-inset-bottom))" }}
    >
      {TABS.map((t) => {
        const active =
          pathname === t.href ||
          (t.href !== "/" && pathname.startsWith(t.href));
        return (
          <Link
            key={t.href}
            href={`${t.href}${qs}`}
            aria-current={active ? "page" : undefined}
            aria-label={t.label}
            className={cn(
              "no-underline transition-all duration-300 ease-out active:scale-90",
              active
                ? "-mt-2 flex h-14 w-14 flex-col items-center justify-center rounded-full bg-se-secondary-fixed text-se-primary shadow-[0_4px_12px_rgba(163,246,156,0.4)] scale-110"
                : "flex flex-col items-center justify-center px-2 py-2 text-slate-400 hover:text-se-secondary",
            )}
          >
            <span
              className="material-symbols-outlined mb-0.5 text-[22px]"
              style={
                active ? { fontVariationSettings: "'FILL' 1" } : undefined
              }
            >
              {t.icon}
            </span>
            <span className="font-body text-[10px] font-bold uppercase tracking-widest">
              {t.label}
            </span>
          </Link>
        );
      })}
    </nav>
  );
}
