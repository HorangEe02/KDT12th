"use client";

/**
 * 브라우저 Geolocation API hook.
 *
 * 3단계 위치 확인:
 * 1. 브라우저 Geolocation API (GPS/Wi-Fi)
 * 2. IP 기반 Geolocation API fallback (ipapi.co)
 * 3. 하드코딩 fallback (대구 중구)
 */
import { useCallback, useEffect, useRef, useState } from "react";

import { DEFAULT_LAT, DEFAULT_LNG, DEFAULT_LOCATION_LABEL } from "./api";

export type GeoPosition = {
  lat: number;
  lng: number;
  /**
   * "gps"     = 브라우저 GPS/Wi-Fi
   * "ip"      = IP 기반 추정 (ipapi.co)
   * "default" = GPS + IP 모두 실패 시 사용하는 하드코딩 폴백 (기본: 대구 중구)
   */
  source: "gps" | "ip" | "default";
  /** 정확도 (미터, GPS 소스일 때만 제공) */
  accuracy?: number;
  /** 위치 라벨 (IP 기반·default 일 때 도시명 등) */
  label?: string;
};

export type GeoHookResult = {
  /** 위치가 아직 확정되지 않으면 null */
  position: GeoPosition | null;
  loading: boolean;
  error: string | null;
  /** 사용자가 명시적으로 위치를 다시 요청 (브라우저 권한 캐시를 우회) */
  refresh: () => void;
};

/**
 * IP 기반 위치 확인 (브라우저 Geolocation 실패 시 fallback).
 * 무료 API: ipapi.co — 키 없이 하루 1000회.
 */
async function fetchIPLocation(): Promise<GeoPosition | null> {
  try {
    const resp = await fetch("https://ipapi.co/json/", { signal: AbortSignal.timeout(5000) });
    if (!resp.ok) return null;
    const data = await resp.json();
    if (data.latitude && data.longitude) {
      return {
        lat: data.latitude,
        lng: data.longitude,
        source: "ip",
        label: data.city
          ? `${data.city}, ${data.region || data.country_name || ""}`
          : undefined,
      };
    }
  } catch {
    // timeout or network error
  }
  return null;
}

// localStorage cache key — shared across all pages and tabs.
// Storing the last GPS-resolved position prevents Discover/Weather/etc.
// from disagreeing on user location when one page's detection happens to fail.
const CACHE_KEY = "p11_geo_position_v1";
const CACHE_TTL_MS = 30 * 60 * 1000; // 30 minutes

type CachedPosition = {
  pos: GeoPosition;
  ts: number;
};

function loadCachedPosition(): GeoPosition | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(CACHE_KEY);
    if (!raw) return null;
    const parsed: CachedPosition = JSON.parse(raw);
    if (!parsed?.pos || typeof parsed.ts !== "number") return null;
    if (Date.now() - parsed.ts > CACHE_TTL_MS) return null;
    return parsed.pos;
  } catch {
    return null;
  }
}

function saveCachedPosition(pos: GeoPosition) {
  if (typeof window === "undefined") return;
  // 캐시는 GPS / IP 위치만 저장 — default 폴백은 캐시하지 않는다.
  // (default 가 캐시되면 다음 방문 시 GPS 시도조차 안 하고 default 가 뜸.)
  if (pos.source === "default") return;
  try {
    window.localStorage.setItem(
      CACHE_KEY,
      JSON.stringify({ pos, ts: Date.now() } satisfies CachedPosition)
    );
  } catch {
    // localStorage quota exceeded — silently ignore
  }
}

export function useGeolocation(): GeoHookResult {
  // Initial state: hydrate from cache so all pages start with the same value.
  // Note: SSR returns null; the useEffect below re-reads cache on mount.
  const [position, setPosition] = useState<GeoPosition | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // Ref guards against stale callbacks on refresh — each call increments tick.
  const tickRef = useRef(0);

  const runDetection = useCallback((silent = false) => {
    if (typeof window === "undefined") {
      setLoading(false);
      return;
    }

    const myTick = ++tickRef.current;
    const isStale = () => tickRef.current !== myTick;
    // silent=true 인 경우 캐시 값으로 이미 화면이 표시된 상태이므로
    // loading 스피너를 다시 띄우지 않는다 (refresh 버튼 클릭 시에는 silent=false).
    if (!silent) setLoading(true);
    setError(null);

    /**
     * 3단계 폴백 체인:
     *   1) IP 기반 위치 (ipapi.co)
     *   2) 하드코딩 default (DEFAULT_LAT/LNG, 대구 중구)
     * GPS 실패 시 적어도 default 위치라도 반환해서 지도/추천이 비어 보이지 않게.
     */
    const tryIPFallback = async (reason: string) => {
      if (isStale()) return;
      const ipPos = await fetchIPLocation();
      if (isStale()) return;
      if (ipPos) {
        setPosition(ipPos);
        saveCachedPosition(ipPos);
        setError(`${reason} IP 기반 위치를 사용합니다.`);
      } else {
        // IP API 도 실패 → 하드코딩 default 로 폴백.
        setPosition({
          lat: DEFAULT_LAT,
          lng: DEFAULT_LNG,
          source: "default",
          label: DEFAULT_LOCATION_LABEL,
        });
        setError(
          `${reason} IP 위치 확인도 실패해 기본 위치(${DEFAULT_LOCATION_LABEL})로 표시합니다. 정확한 위치를 보려면 위치 권한을 허용한 뒤 새로고침하세요.`
        );
      }
      setLoading(false);
    };

    // 브라우저 Geolocation 미지원
    if (!("geolocation" in navigator)) {
      tryIPFallback("이 브라우저는 위치 정보를 지원하지 않습니다.");
      return;
    }

    const HIGH_ACCURACY_OPTIONS: PositionOptions = {
      enableHighAccuracy: true,
      timeout: 8000,
      // refresh 호출 시에는 캐시를 우회. 첫 호출은 1분 캐시 허용.
      maximumAge: tickRef.current > 1 ? 0 : 60_000,
    };

    const LOW_ACCURACY_OPTIONS: PositionOptions = {
      enableHighAccuracy: false,
      timeout: 5000,
      maximumAge: tickRef.current > 1 ? 0 : 300_000,
    };

    const onSuccess = (pos: GeolocationPosition) => {
      if (isStale()) return;
      const next: GeoPosition = {
        lat: pos.coords.latitude,
        lng: pos.coords.longitude,
        source: "gps",
        accuracy: pos.coords.accuracy,
      };
      setPosition(next);
      saveCachedPosition(next);
      setLoading(false);
      if (pos.coords.accuracy > 1000) {
        setError(
          `측위 정확도가 낮습니다 (${Math.round(pos.coords.accuracy)}m).`
        );
      }
    };

    const onFinalError = (err: GeolocationPositionError) => {
      if (isStale()) return;
      const reason =
        err.code === 1
          ? "위치 권한이 거부되었습니다."
          : err.code === 2
          ? "위치 정보를 사용할 수 없습니다."
          : "위치 확인 시간 초과.";
      tryIPFallback(reason);
    };

    navigator.geolocation.getCurrentPosition(
      onSuccess,
      (err) => {
        if (isStale()) return;
        if (err.code === 1) {
          tryIPFallback("위치 권한이 거부되었습니다.");
          return;
        }
        navigator.geolocation.getCurrentPosition(
          onSuccess,
          onFinalError,
          LOW_ACCURACY_OPTIONS
        );
      },
      HIGH_ACCURACY_OPTIONS
    );
  }, []);

  // Initial detection on mount. We hydrate from localStorage first so every
  // page starts with the same last-known position; then re-run live detection
  // in the background to refresh GPS/IP. This prevents one page (e.g. Weather)
  // from showing the default fallback while another page (e.g. Discover) has
  // already resolved the user's real location.
  useEffect(() => {
    const cached = loadCachedPosition();
    if (cached) {
      setPosition(cached);
      setLoading(false);
      // 캐시가 있으면 백그라운드 새로고침만 — 화면에 로딩 스피너 노출 안 함.
      runDetection(true);
    } else {
      runDetection(false);
    }
    return () => {
      // Invalidate any pending callbacks if the component unmounts.
      tickRef.current++;
    };
  }, [runDetection]);

  return { position, loading, error, refresh: runDetection };
}
