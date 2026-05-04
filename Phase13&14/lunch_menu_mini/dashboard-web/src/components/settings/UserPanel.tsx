"use client";

import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { LogOut, User as UserIcon } from "lucide-react";
import { useNLPHealth } from "@/lib/queries";
import { useAuth } from "@/lib/useAuth";
import { logout } from "@/lib/auth";

export default function UserPanel({ onClose }: { onClose: () => void }) {
  const panelRef = useRef<HTMLDivElement>(null);
  const router = useRouter();
  const user = useAuth();
  const { data: health } = useNLPHealth();

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        onClose();
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [onClose]);

  const ok = health?.status === "ok";

  const handleLogout = () => {
    logout();
    onClose();
    router.replace("/login");
  };

  return (
    <div
      ref={panelRef}
      className="absolute top-14 right-0 w-64 bg-surface-1 border border-outline/20 shadow-2xl shadow-background/60 z-50"
    >
      {/* User Info */}
      <div className="px-4 py-3 border-b border-outline/10">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary/15 border border-primary/25 rounded-full flex items-center justify-center text-xl">
            {user?.avatar_emoji ?? "🧑‍💻"}
          </div>
          <div className="flex-1 min-w-0">
            <div
              className="text-sm font-bold text-text-primary truncate"
              style={{ fontFamily: "var(--font-ko)" }}
            >
              {user?.name ?? "Guest"}
            </div>
            <div className="text-[10px] text-text-tertiary font-mono truncate">
              {user ? `${user.id} · ${user.team_id}` : "not signed in"}
            </div>
          </div>
        </div>
      </div>

      {/* System Info */}
      <div className="px-4 py-3 space-y-2 text-[10px]">
        <div className="flex justify-between">
          <span className="text-text-tertiary">NLP Status</span>
          <span className={ok ? "text-success font-bold" : "text-error font-bold"}>
            {ok ? "Connected" : "Disconnected"}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-text-tertiary">Modules OK</span>
          <span className="text-text-secondary font-mono">
            {Object.values(health?.modules ?? {}).filter((v) => v === "ok").length}
            {"/"}
            {Object.keys(health?.modules ?? {}).length}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-text-tertiary">Version</span>
          <span className="text-text-secondary font-mono">
            {health?.version ?? "—"}
          </span>
        </div>
      </div>

      {/* Actions */}
      <div className="px-2 py-2 border-t border-outline/10 space-y-1">
        {user ? (
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-2 px-3 py-2 text-[11px] font-bold uppercase tracking-wider text-text-secondary hover:text-error hover:bg-error/5 rounded-sm transition-colors"
          >
            <LogOut size={12} />
            Sign out
          </button>
        ) : (
          <button
            onClick={() => {
              onClose();
              router.replace("/login");
            }}
            className="w-full flex items-center gap-2 px-3 py-2 text-[11px] font-bold uppercase tracking-wider text-text-secondary hover:text-primary hover:bg-primary/5 rounded-sm transition-colors"
          >
            <UserIcon size={12} />
            Sign in
          </button>
        )}
      </div>

      <div className="px-4 py-2 border-t border-outline/10">
        <p className="text-[9px] text-text-tertiary font-mono">
          Mini Lunch Optimizer v0.5 · Local Session
        </p>
      </div>
    </div>
  );
}
