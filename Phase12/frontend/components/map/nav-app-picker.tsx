"use client";

import { useState } from "react";
import {
  NAV_APP_META,
  detectOS,
  isAppAvailable,
  launchNavigation,
  setPreferredNavApp,
  type NavApp,
  type TravelMode,
} from "@/lib/nav-deeplink";
import { cn } from "@/lib/utils";

/**
 * 길안내 앱 선택 chip grid + 실행.
 * Trip Confirmation Sheet 안에 임베드되거나 단독 sub-sheet 으로 사용 가능.
 */
interface NavAppPickerProps {
  origin: [number, number];
  destination: [number, number];
  destinationName?: string;
  mode?: TravelMode;
  waypoints?: Array<{ lat: number; lng: number; name?: string }>;
  onLaunched?: (app: NavApp) => void;
}

const ORDER: NavApp[] = ["kakao", "naver", "google", "apple", "tmap"];

export function NavAppPicker({
  origin,
  destination,
  destinationName,
  mode = "transit",
  waypoints,
  onLaunched,
}: NavAppPickerProps) {
  const [busy, setBusy] = useState<NavApp | null>(null);
  const os = detectOS();

  function handleLaunch(app: NavApp) {
    setBusy(app);
    setPreferredNavApp(app);
    launchNavigation(app, { origin, destination, destinationName, mode, waypoints });
    onLaunched?.(app);
    // busy 자동 해제 (사용자가 돌아왔을 때)
    setTimeout(() => setBusy(null), 2000);
  }

  return (
    <div>
      <h3 className="mb-3 font-display text-sm font-bold uppercase tracking-wider text-se-on-surface-variant">
        어떤 앱으로 길 안내?
      </h3>
      <div className="grid grid-cols-2 gap-2">
        {ORDER.map((app) => {
          const meta = NAV_APP_META[app];
          const available = isAppAvailable(app);
          const active = busy === app;
          return (
            <button
              key={app}
              type="button"
              onClick={() => available && handleLaunch(app)}
              disabled={!available || busy !== null}
              className={cn(
                "flex items-center gap-2 rounded-xl border-2 px-3 py-3 text-left transition-all",
                available
                  ? "border-se-outline-variant bg-white hover:border-se-primary active:scale-95"
                  : "cursor-not-allowed border-se-outline-variant/40 bg-se-surface-container-low opacity-50",
                active && "border-se-primary bg-se-primary/5",
              )}
            >
              <div
                className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm"
                style={{ background: `${meta.brandColor}33` }}
              >
                {meta.emoji}
              </div>
              <div className="min-w-0 flex-1">
                <div className="font-display text-sm font-bold text-se-on-surface">
                  {meta.label}
                </div>
                {!available ? (
                  <div className="font-body text-[10px] text-se-outline">
                    {os === "android" && app === "apple"
                      ? "iOS 전용"
                      : "앱 미지원"}
                  </div>
                ) : active ? (
                  <div className="font-body text-[10px] text-se-secondary">
                    실행 중...
                  </div>
                ) : null}
              </div>
            </button>
          );
        })}
      </div>
      <p className="mt-3 text-[0.65rem] text-se-on-surface-variant">
        앱 미설치 시 1.5초 후 Google Maps 웹으로 자동 전환됩니다.
      </p>
    </div>
  );
}
