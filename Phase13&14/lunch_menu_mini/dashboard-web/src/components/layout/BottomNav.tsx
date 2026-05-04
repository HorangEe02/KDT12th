"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import {
  LayoutDashboard,
  UtensilsCrossed,
  CloudSun,
  Salad,
  Vote,
  Users,
  MessageSquare,
  BrainCircuit,
  MoreHorizontal,
  X,
  Shield,
  LogOut,
} from "lucide-react";

/**
 * Apple App Store iOS 26 "Liquid Glass" 스타일 모바일 하단 네비.
 *
 * - 5 primary tabs + More 시트 (총 6 슬롯)
 * - 캡슐형 떠 있는 컨테이너 (`fixed bottom-3 mx-3 rounded-full`)
 * - `backdrop-blur` + 반투명 배경 = Liquid Glass
 * - 활성 탭: 펠릿 배경 + fill 아이콘 + scale-in 애니메이션
 * - 비활성: outline 아이콘
 *
 * 탭 순서 (사용자 결정):
 *   Dashboard → Discovery → Weather → Nutrition → AI Concierge → More
 *
 * More 시트: Vote · Buddy · NLP Insights · Admin · Logout
 */

const MOBILE_NAV = [
  { href: "/", icon: LayoutDashboard, label: "Home" },
  { href: "/discover", icon: UtensilsCrossed, label: "Discover" },
  { href: "/weather", icon: CloudSun, label: "Weather" },
  { href: "/nutrition", icon: Salad, label: "Nutri" },
  { href: "/concierge", icon: MessageSquare, label: "AI" },
];

const MORE_LINKS = [
  { href: "/vote", icon: Vote, label: "Team Vote", ko: "팀 투표" },
  { href: "/buddy", icon: Users, label: "Buddy", ko: "밥친구 찾기" },
  { href: "/insights", icon: BrainCircuit, label: "NLP Insights", ko: "AI 인사이트" },
  { href: "/admin", icon: Shield, label: "Admin", ko: "관리자 콘솔" },
];

export default function BottomNav() {
  const pathname = usePathname();
  const [moreOpen, setMoreOpen] = useState(false);
  const moreActive = MORE_LINKS.some((m) => pathname.startsWith(m.href));

  const handleLogout = () => {
    if (typeof window === "undefined") return;
    localStorage.removeItem("p11_auth_token");
    localStorage.removeItem("p11_current_user");
    window.dispatchEvent(new CustomEvent("p11_auth_updated"));
    setMoreOpen(false);
    window.location.href = "/login";
  };

  return (
    <>
      <nav
        className="
          md:hidden
          fixed bottom-3 left-3 right-3 z-40
          flex justify-around items-stretch gap-1
          px-2 py-2
          rounded-full
          backdrop-blur-2xl
          bg-white/70 dark:bg-black/40
          ring-1 ring-black/5 dark:ring-white/10
          shadow-[0_8px_30px_rgba(0,0,0,0.12)]
        "
        style={{
          paddingBottom: "calc(env(safe-area-inset-bottom, 0px) * 0.25 + 0.5rem)",
          marginBottom: "calc(env(safe-area-inset-bottom, 0px) * 0.5)",
        }}
        aria-label="Mobile navigation"
      >
        {MOBILE_NAV.map((item) => {
          const isActive =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              aria-current={isActive ? "page" : undefined}
              className={`
                flex flex-col items-center justify-center
                flex-1 min-w-0 min-h-[48px]
                px-1 py-1 rounded-full
                transition-all duration-150 active:scale-90
                ${isActive
                  ? "bg-primary/15 ring-1 ring-primary/30 text-primary"
                  : "text-text-tertiary hover:text-text-secondary"}
              `}
            >
              <item.icon
                size={20}
                strokeWidth={isActive ? 2.4 : 1.7}
                fill={isActive ? "currentColor" : "none"}
                fillOpacity={isActive ? 0.18 : 0}
              />
              <span className="text-[9px] font-bold uppercase tracking-[0.04em] mt-0.5 w-full text-center truncate whitespace-nowrap">
                {item.label}
              </span>
            </Link>
          );
        })}

        {/* More tab — opens bottom sheet */}
        <button
          type="button"
          onClick={() => setMoreOpen(true)}
          aria-expanded={moreOpen}
          aria-label="더보기"
          className={`
            flex flex-col items-center justify-center
            flex-1 min-w-0 min-h-[48px]
            px-1 py-1 rounded-full
            transition-all duration-150 active:scale-90
            ${moreActive || moreOpen
              ? "bg-primary/15 ring-1 ring-primary/30 text-primary"
              : "text-text-tertiary hover:text-text-secondary"}
          `}
        >
          <MoreHorizontal size={20} strokeWidth={moreActive || moreOpen ? 2.4 : 1.7} />
          <span className="text-[9px] font-bold uppercase tracking-[0.04em] mt-0.5 w-full text-center truncate whitespace-nowrap">
            More
          </span>
        </button>
      </nav>

      {/* Bottom sheet for secondary routes */}
      {moreOpen && (
        <div
          className="md:hidden fixed inset-0 z-50 flex flex-col justify-end"
          role="dialog"
          aria-modal="true"
          aria-label="더보기 메뉴"
        >
          <button
            type="button"
            aria-label="닫기"
            className="absolute inset-0 bg-black/40 backdrop-blur-sm"
            onClick={() => setMoreOpen(false)}
          />
          <div className="relative bg-surface-1 border-t border-outline/20 rounded-t-3xl shadow-2xl pb-[max(env(safe-area-inset-bottom),1.5rem)] animate-slide-up">
            <div className="flex items-center justify-between px-5 py-3 border-b border-outline/10">
              <span
                className="text-[12px] font-bold uppercase tracking-[0.1em] text-text-tertiary"
                style={{ fontFamily: "var(--font-ko)" }}
              >
                더보기
              </span>
              <button
                type="button"
                onClick={() => setMoreOpen(false)}
                aria-label="닫기"
                className="p-1.5 rounded-full hover:bg-surface-2 active:scale-95"
              >
                <X size={16} />
              </button>
            </div>
            <div className="grid grid-cols-2 gap-2 p-4">
              {MORE_LINKS.map((m) => {
                const isActive = pathname.startsWith(m.href);
                return (
                  <Link
                    key={m.href}
                    href={m.href}
                    onClick={() => setMoreOpen(false)}
                    className={`
                      flex items-center gap-3 p-3 rounded-2xl
                      transition-colors duration-150 active:scale-[0.98]
                      ${isActive
                        ? "bg-primary/10 text-primary border border-primary/30"
                        : "bg-surface-2 text-text-secondary border border-outline/10"}
                    `}
                  >
                    <m.icon size={18} strokeWidth={isActive ? 2.2 : 1.8} />
                    <div className="flex flex-col min-w-0">
                      <span className="text-[12px] font-bold uppercase tracking-[0.04em]">
                        {m.label}
                      </span>
                      <span
                        className="text-[10px] text-text-tertiary truncate"
                        style={{ fontFamily: "var(--font-ko)" }}
                      >
                        {m.ko}
                      </span>
                    </div>
                  </Link>
                );
              })}
            </div>
            <div className="border-t border-outline/10 p-3">
              <button
                type="button"
                onClick={handleLogout}
                className="w-full flex items-center justify-center gap-2 p-3 rounded-2xl bg-surface-2 text-error hover:bg-error/5 active:scale-[0.98]"
              >
                <LogOut size={16} />
                <span
                  className="text-[12px] font-bold"
                  style={{ fontFamily: "var(--font-ko)" }}
                >
                  로그아웃
                </span>
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
