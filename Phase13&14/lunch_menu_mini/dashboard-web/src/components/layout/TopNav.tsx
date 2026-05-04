"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Search, Settings, User, Sun, Moon } from "lucide-react";
import { useTheme } from "next-themes";
import { useNLPHealth, useNLPSettings } from "@/lib/queries";
import { isNLPHealthy } from "@/lib/types";
import SettingsPanel from "@/components/settings/SettingsPanel";
import UserPanel from "@/components/settings/UserPanel";
import { BRAND } from "@/lib/brand";

export default function TopNav() {
  const [showSettings, setShowSettings] = useState(false);
  const [showUser, setShowUser] = useState(false);
  const [mounted, setMounted] = useState(false);
  const { resolvedTheme, setTheme } = useTheme();
  useEffect(() => setMounted(true), []);
  const isDark = mounted && resolvedTheme === "dark";

  const { data: health } = useNLPHealth();
  const { data: settings } = useNLPSettings();
  const isConnected = isNLPHealthy(health);
  const modelName = settings?.chat_model || "N/A";

  return (
    <>
      <header className="glass-panel fixed top-0 left-0 right-0 z-50 h-16 border-b border-outline/15 flex items-center justify-between px-4 md:px-6">
        {/* Left: Brand */}
        <Link
          href="/"
          className="flex items-center gap-2.5 hover:opacity-80 transition-opacity"
        >
          <img
            src={BRAND.logoSrc}
            alt={BRAND.logoAlt}
            className="h-9 sm:h-11 w-auto select-none"
            draggable={false}
          />
          <span className="font-heading text-[13px] sm:text-[15px] font-extrabold text-text-primary tracking-tight whitespace-nowrap">
            {BRAND.name}
          </span>
        </Link>

        {/* Center: Global Search (desktop only) */}
        <div className="hidden md:flex flex-1 max-w-[500px] mx-6">
          <div className="w-full flex items-center gap-2 bg-surface-2 border border-outline/15 px-4 py-[7px] rounded-sm">
            <Search size={14} className="text-text-tertiary" />
            <span className="text-xs text-text-tertiary font-body">
              음식점·메뉴 검색...
            </span>
          </div>
        </div>

        {/* Right: Status */}
        <div className="flex items-center gap-2 md:gap-4">
          <span className="hidden lg:inline text-[10px] text-text-tertiary font-mono uppercase tracking-wider">
            {BRAND.tagline}
          </span>

          {/* Ollama model pill (desktop only — mobile hides to save space) */}
          <div
            className={`hidden md:flex items-center gap-2 text-[11px] font-mono px-3 py-[3px] border rounded-sm ${
              isConnected
                ? "bg-primary/8 border-primary/25 text-primary"
                : "bg-surface-2 border-outline/15 text-text-tertiary"
            }`}
          >
            <div
              className={`w-[5px] h-[5px] rounded-full ${
                isConnected
                  ? "bg-primary shadow-[0_0_4px_rgba(232,89,60,0.6)]"
                  : "bg-text-tertiary"
              }`}
            />
            <span>Ollama: {modelName}</span>
          </div>

          {/* Connected badge — 모바일은 dot만, 데스크톱은 풀 라벨 */}
          <div
            className={`flex items-center gap-[6px] py-1 rounded-sm border
                        px-1.5 sm:px-3
                        ${
                          isConnected
                            ? "bg-primary/10 border-primary/25"
                            : "bg-error/10 border-error/25"
                        }`}
            title={isConnected ? "Connected" : "Disconnected"}
          >
            <div
              className={`w-[7px] h-[7px] rounded-full ${
                isConnected
                  ? "bg-primary shadow-[0_0_6px_rgba(232,89,60,0.5)]"
                  : "bg-error shadow-[0_0_6px_rgba(255,113,108,0.5)]"
              }`}
            />
            <span
              className={`hidden sm:inline text-[10px] font-semibold font-mono ${
                isConnected ? "text-primary" : "text-error"
              }`}
            >
              {isConnected ? "Connected" : "Disconnected"}
            </span>
          </div>

          {/* Theme toggle (Light/Dark) */}
          <button
            onClick={() => setTheme(isDark ? "light" : "dark")}
            className="p-1.5 text-text-tertiary hover:text-text-secondary transition-colors"
            aria-label={isDark ? "라이트 모드로" : "다크 모드로"}
            title={isDark ? "라이트 모드로" : "다크 모드로"}
          >
            {mounted ? (
              isDark ? <Sun size={16} /> : <Moon size={16} />
            ) : (
              <Moon size={16} />
            )}
          </button>

          {/* Settings */}
          <button
            onClick={() => {
              setShowSettings(true);
              setShowUser(false);
            }}
            className="p-1.5 text-text-tertiary hover:text-text-secondary transition-colors"
            aria-label="Settings"
          >
            <Settings size={16} />
          </button>

          {/* User */}
          <div className="relative">
            <button
              onClick={() => {
                setShowUser(!showUser);
                setShowSettings(false);
              }}
              className="p-1.5 text-text-tertiary hover:text-text-secondary transition-colors"
              aria-label="User"
            >
              <User size={16} />
            </button>
            {showUser && <UserPanel onClose={() => setShowUser(false)} />}
          </div>
        </div>
      </header>

      {showSettings && (
        <SettingsPanel onClose={() => setShowSettings(false)} />
      )}
    </>
  );
}
