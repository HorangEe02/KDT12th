"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import {
  LayoutDashboard,
  UtensilsCrossed,
  CloudSun,
  Salad,
  Vote,
  MessageSquare,
  BrainCircuit,
  Users,
  FileText,
  HelpCircle,
  Shield,
} from "lucide-react";
import { getRole, isTokenValid } from "@/lib/auth";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", ko: "대시보드", icon: LayoutDashboard },
  { href: "/discover", label: "Discovery", ko: "음식점 탐색", icon: UtensilsCrossed },
  { href: "/weather", label: "Weather", ko: "날씨 추천", icon: CloudSun },
  { href: "/nutrition", label: "Nutrition", ko: "영양 리포트", icon: Salad },
  { href: "/concierge", label: "Concierge", ko: "AI 상담", icon: MessageSquare },
  { href: "/vote", label: "Team Vote", ko: "팀 투표", icon: Vote },
  { href: "/buddy", label: "Buddy", ko: "밥친구 찾기", icon: Users },
  { href: "/insights", label: "NLP Insights", ko: "AI 인사이트", icon: BrainCircuit },
];

const ADMIN_NAV = {
  href: "/admin",
  label: "Admin",
  ko: "관리자 콘솔",
  icon: Shield,
};

export default function Sidebar() {
  const pathname = usePathname();
  const [isAdmin, setIsAdmin] = useState(false);

  // 클라이언트에서만 role 검사 (정적 export 환경)
  useEffect(() => {
    const updateRole = () => {
      setIsAdmin(isTokenValid() && getRole() === "admin");
    };
    updateRole();
    window.addEventListener("storage", updateRole);
    window.addEventListener("p11_auth_updated", updateRole as EventListener);
    return () => {
      window.removeEventListener("storage", updateRole);
      window.removeEventListener("p11_auth_updated", updateRole as EventListener);
    };
  }, []);

  return (
    <aside className="glass-panel hidden md:flex fixed left-0 top-16 bottom-10 w-64 border-r border-outline/15 flex-col z-40">
      {/* Navigation */}
      <nav className="flex-1 py-3 px-3 space-y-0.5 overflow-y-auto">
        {NAV_ITEMS.map((item) => {
          const isActive =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-sm text-[13px] font-medium transition-all duration-150 ${
                isActive
                  ? "bg-primary/10 text-primary border-l-[3px] border-primary pl-[9px]"
                  : "text-text-secondary hover:bg-surface-2 hover:text-text-primary"
              }`}
            >
              <item.icon size={16} strokeWidth={isActive ? 2.2 : 1.5} />
              <div className="flex flex-col">
                <span className="uppercase tracking-[0.04em]">{item.label}</span>
                <span
                  className="text-[10px] font-normal tracking-normal opacity-60"
                  style={{ fontFamily: "var(--font-ko)" }}
                >
                  {item.ko}
                </span>
              </div>
            </Link>
          );
        })}

        {/* Admin 전용 — role==admin 사용자에게만 표시 */}
        {isAdmin && (
          <>
            <div className="pt-3 pb-1 px-3 text-[9px] font-bold uppercase tracking-[0.15em] text-text-tertiary">
              관리자 영역
            </div>
            <Link
              href={ADMIN_NAV.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-sm text-[13px] font-medium transition-all duration-150 ${
                pathname.startsWith(ADMIN_NAV.href)
                  ? "bg-primary/10 text-primary border-l-[3px] border-primary pl-[9px]"
                  : "text-text-secondary hover:bg-surface-2 hover:text-text-primary"
              }`}
            >
              <ADMIN_NAV.icon
                size={16}
                strokeWidth={pathname.startsWith(ADMIN_NAV.href) ? 2.2 : 1.5}
              />
              <div className="flex flex-col">
                <span className="uppercase tracking-[0.04em]">{ADMIN_NAV.label}</span>
                <span
                  className="text-[10px] font-normal tracking-normal opacity-60"
                  style={{ fontFamily: "var(--font-ko)" }}
                >
                  {ADMIN_NAV.ko}
                </span>
              </div>
            </Link>
          </>
        )}
      </nav>

      {/* Quick Vote Button */}
      <div className="px-3 pb-3">
        <Link
          href="/vote"
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-primary text-background text-xs font-bold uppercase tracking-wider rounded-sm hover:bg-primary-dark transition-colors"
        >
          <Vote size={14} />
          Quick Vote
        </Link>
      </div>

      {/* Footer Links */}
      <div className="px-5 py-3 border-t border-outline/10 space-y-2">
        <Link
          href="#"
          className="flex items-center gap-2 text-[11px] text-text-tertiary hover:text-text-secondary transition-colors"
        >
          <FileText size={12} />
          Documentation
        </Link>
        <Link
          href="#"
          className="flex items-center gap-2 text-[11px] text-text-tertiary hover:text-text-secondary transition-colors"
        >
          <HelpCircle size={12} />
          Support
        </Link>
      </div>
    </aside>
  );
}
