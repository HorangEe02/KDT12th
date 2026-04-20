"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useRouter } from "next/navigation";
import { signOut } from "@/lib/firebase/auth";
import { cn } from "@/lib/utils";
import type { SessionUser } from "@/lib/firebase/server-session";

const NAV: Array<{ href: string; label: string; icon: string }> = [
  { href: "/admin", label: "대시보드", icon: "dashboard" },
  { href: "/admin/users", label: "회원 관리", icon: "group" },
  { href: "/admin/audit", label: "감사 로그", icon: "history" },
];

interface SideNavProps {
  user: SessionUser;
}

export function AdminSideNav({ user }: SideNavProps) {
  const pathname = usePathname();
  const router = useRouter();

  async function onSignOut() {
    try {
      await signOut();
      router.replace("/");
    } catch {
      /* ignore */
    }
  }

  return (
    <aside className="fixed left-0 top-0 z-40 hidden h-dvh w-64 flex-col gap-4 border-r border-se-outline-variant bg-se-surface-container-low p-6 md:flex">
      {/* Brand + Admin Portal badge */}
      <div className="mb-6">
        <Link
          href="/"
          className="mb-6 block font-display text-lg font-bold tracking-tight text-se-primary hover:text-se-secondary"
        >
          원정 응원 플래너
        </Link>
        <div className="flex items-center gap-3 rounded-xl bg-se-surface-container-lowest p-3 shadow-[0_4px_24px_0_rgba(0,0,0,0.04)]">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-se-primary-fixed-dim text-se-primary">
            <span
              className="material-symbols-outlined"
              style={{ fontVariationSettings: "'FILL' 1" }}
            >
              admin_panel_settings
            </span>
          </div>
          <div className="min-w-0 flex-1">
            <div className="truncate text-sm font-bold text-se-on-surface">
              관리자 콘솔
            </div>
            <div className="truncate text-xs text-se-on-surface-variant">
              {user.email}
            </div>
          </div>
        </div>
      </div>

      {/* Nav links */}
      <nav className="flex flex-1 flex-col gap-2">
        {NAV.map((item) => {
          const active =
            item.href === "/admin"
              ? pathname === "/admin"
              : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-4 py-3 transition-all",
                active
                  ? "bg-white font-display font-bold text-se-primary shadow-sm"
                  : "font-body font-medium text-se-on-surface-variant hover:translate-x-1 hover:bg-white/60",
              )}
            >
              <span
                className={cn("material-symbols-outlined", active && "fill")}
                style={active ? { fontVariationSettings: "'FILL' 1" } : undefined}
              >
                {item.icon}
              </span>
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Footer actions */}
      <div className="mt-auto space-y-2 border-t border-se-outline-variant pt-4">
        <Link
          href="/"
          className="flex w-full items-center justify-center gap-2 rounded-xl border border-se-outline-variant bg-white px-4 py-2.5 font-display text-xs font-bold text-se-on-surface hover:border-se-primary"
        >
          <span className="material-symbols-outlined text-[16px]">arrow_back</span>
          사용자 화면으로
        </Link>
        <button
          type="button"
          onClick={onSignOut}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-br from-se-primary to-se-primary-container px-4 py-2.5 font-display text-xs font-bold text-white shadow-[0_4px_14px_rgba(0,25,60,0.2)] active:scale-95"
        >
          <span className="material-symbols-outlined text-[16px]">logout</span>
          로그아웃
        </button>
      </div>
    </aside>
  );
}
