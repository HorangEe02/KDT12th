"use client";

import { useState } from "react";
import {
  NAV_APP_META,
  detectOS,
  isAppAvailable,
  getWaypointSupport,
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
  const hasWaypoints = (waypoints?.length ?? 0) > 0;

  function handleLaunch(app: NavApp) {
    setBusy(app);
    setPreferredNavApp(app);
    launchNavigation(app, { origin, destination, destinationName, mode, waypoints });
    onLaunched?.(app);
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
          const wpSupport = getWaypointSupport(app);
          const wpWarn = hasWaypoints && wpSupport === "none";

          const subLabel = !available
            ? os === "android" && app === "apple"
              ? "iOS 전용"
              : "앱 미지원"
            : os === "desktop" && (app === "kakao" || app === "naver")
              ? "웹 지도 새 탭"
              : active
                ? "실행 중..."
                : undefined;

          return (
            <button
              key={app}
              type="button"
              onClick={() => available && handleLaunch(app)}
              disabled={!available || busy !== null}
              className={cn(
                "relative flex items-center gap-2 rounded-xl border-2 px-3 py-3 text-left transition-all",
                available
                  ? "border-se-outline-variant bg-white hover:border-se-primary active:scale-95"
                  : "cursor-not-allowed border-se-outline-variant/40 bg-se-surface-container-low opacity-50",
                active && "border-se-primary bg-se-primary/5",
              )}
              aria-label={
                wpWarn
                  ? `${meta.label} — 경유지 미지원, 출발지-도착지만 전달됩니다`
                  : meta.label
              }
              title={
                wpWarn
                  ? `${meta.label} 은 경유지 미지원 — 출발/도착만 전달됨`
                  : meta.label
              }
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
                {subLabel ? (
                  <div
                    className={cn(
                      "font-body text-[10px]",
                      active
                        ? "text-se-secondary"
                        : available
                          ? "text-se-on-surface-variant"
                          : "text-se-outline",
                    )}
                  >
                    {subLabel}
                  </div>
                ) : null}
              </div>
              {wpWarn && available ? (
                <span
                  aria-hidden
                  className="absolute right-1.5 top-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-amber-500 text-[9px] font-extrabold text-white shadow"
                  title="경유지 미지원"
                >
                  !
                </span>
              ) : null}
            </button>
          );
        })}
      </div>

      {hasWaypoints ? (
        <p className="mt-3 rounded-lg bg-amber-50 px-3 py-2 text-[0.65rem] leading-relaxed text-amber-900">
          <strong>⚠️ 경유지 {waypoints?.length}개 포함</strong> — 카카오맵/네이버지도/Apple Maps/T맵은
          경유지 미지원. <strong>Google Maps</strong> 만 경유지를 그대로 전달합니다.
          다른 앱 선택 시 <strong>출발지 → 도착지만</strong> 전달됩니다.
        </p>
      ) : null}

      <p className="mt-2 text-[0.65rem] text-se-on-surface-variant">
        {os === "desktop"
          ? "데스크톱: 카카오/네이버/구글은 새 탭으로 웹 지도 열림. T맵은 앱 전용."
          : "앱 미설치 시 1.5초 후 Google Maps 웹으로 자동 전환됩니다."}
      </p>
    </div>
  );
}
