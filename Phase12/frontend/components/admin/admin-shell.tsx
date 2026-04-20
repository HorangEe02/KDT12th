"use client";

import type { ReactNode } from "react";
import { AdminSideNav } from "./admin-side-nav";
import { AdminMobileNav } from "./admin-mobile-nav";
import type { SessionUser } from "@/lib/firebase/server-session";

interface AdminShellProps {
  user: SessionUser;
  children: ReactNode;
}

export function AdminShell({ user, children }: AdminShellProps) {
  return (
    <div className="flex min-h-dvh bg-se-surface">
      <AdminSideNav user={user} />

      <main className="flex-1 px-4 py-6 pb-24 md:ml-64 md:px-10 md:py-10 md:pb-10">
        {children}
      </main>

      <AdminMobileNav />
    </div>
  );
}
