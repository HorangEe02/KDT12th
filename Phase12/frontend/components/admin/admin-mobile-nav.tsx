"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const TABS = [
  { href: "/admin", label: "대시보드", icon: "dashboard" },
  { href: "/admin/users", label: "회원", icon: "group" },
  { href: "/admin/audit", label: "감사", icon: "history" },
  { href: "/", label: "나가기", icon: "exit_to_app" },
];

export function AdminMobileNav() {
  const pathname = usePathname();
  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 flex items-center justify-around rounded-t-3xl bg-white/90 px-2 pb-6 pt-3 shadow-[0_-4px_24px_rgba(0,0,0,0.08)] backdrop-blur-lg md:hidden">
      {TABS.map((t) => {
        const active =
          t.href === "/admin"
            ? pathname === "/admin"
            : pathname.startsWith(t.href) && t.href !== "/";
        return (
          <Link
            key={t.href}
            href={t.href}
            className={cn(
              "flex flex-col items-center gap-1 rounded-2xl px-3 py-2 text-[10px] font-bold uppercase tracking-tight transition-transform active:scale-90",
              active
                ? "bg-se-secondary-container/30 text-se-secondary"
                : "text-se-on-surface-variant hover:text-se-primary",
            )}
          >
            <span
              className={cn("material-symbols-outlined text-[22px]")}
              style={active ? { fontVariationSettings: "'FILL' 1" } : undefined}
            >
              {t.icon}
            </span>
            <span>{t.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
