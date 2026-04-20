/**
 * 외부 길안내 앱 deeplink 헬퍼.
 * 5개 앱 지원: 카카오맵 / 네이버지도 / Google Maps / Apple Maps / Tmap.
 *
 * 동작:
 *   - kakao/naver/tmap: app-scheme deeplink → 앱 미설치 시 1.5초 후 Google Maps 웹 fallback
 *   - google/apple: 웹 URL → 새 탭
 */

export type NavApp = "kakao" | "naver" | "google" | "apple" | "tmap";
export type TravelMode = "transit" | "car" | "walk";

export interface NavDeepLinkParams {
  origin: [number, number];           // [lat, lng]
  destination: [number, number];
  destinationName?: string;
  waypoints?: Array<{ lat: number; lng: number; name?: string }>;
  mode?: TravelMode;
}

export const NAV_APP_META: Record<
  NavApp,
  { label: string; emoji: string; brandColor: string; available: "all" | "ios" | "mobile" }
> = {
  kakao: { label: "카카오맵", emoji: "🟡", brandColor: "#FEE500", available: "mobile" },
  naver: { label: "네이버지도", emoji: "🟢", brandColor: "#03C75A", available: "mobile" },
  google: { label: "Google Maps", emoji: "🌐", brandColor: "#4285F4", available: "all" },
  apple: { label: "Apple Maps", emoji: "🍎", brandColor: "#000000", available: "ios" },
  tmap: { label: "T맵", emoji: "🚗", brandColor: "#EE2737", available: "mobile" },
};

const FALLBACK_TIMEOUT_MS = 1500;

/** OS 감지 (lazy) */
export function detectOS(): "ios" | "android" | "desktop" {
  if (typeof navigator === "undefined") return "desktop";
  const ua = navigator.userAgent.toLowerCase();
  if (/iphone|ipad|ipod/.test(ua)) return "ios";
  if (/android/.test(ua)) return "android";
  return "desktop";
}

/** 사용자 OS 에서 앱이 동작 가능한지 */
export function isAppAvailable(app: NavApp): boolean {
  const os = detectOS();
  const meta = NAV_APP_META[app];
  if (meta.available === "all") return true;
  if (meta.available === "mobile") return os !== "desktop";
  if (meta.available === "ios") return os === "ios" || os === "desktop"; // Apple Maps 웹은 데스크톱(Safari) 도 동작
  return false;
}

/** URL builder */
function buildUrl(app: NavApp, p: NavDeepLinkParams): string {
  const [olat, olng] = p.origin;
  const [dlat, dlng] = p.destination;
  const mode = p.mode ?? "transit";
  switch (app) {
    case "kakao": {
      const by = mode === "car" ? "CAR" : mode === "walk" ? "FOOT" : "PUBLICTRANSIT";
      return `kakaomap://route?sp=${olat},${olng}&ep=${dlat},${dlng}&by=${by}`;
    }
    case "naver":
      return `nmap://route/public?slat=${olat}&slng=${olng}&dlat=${dlat}&dlng=${dlng}&dname=${encodeURIComponent(p.destinationName ?? "도착지")}&appname=stadium-editorial`;
    case "google": {
      const wp =
        p.waypoints && p.waypoints.length > 0
          ? `&waypoints=${p.waypoints.map((w) => `${w.lat},${w.lng}`).join("|")}`
          : "";
      const travelmode = mode === "walk" ? "walking" : mode === "car" ? "driving" : "transit";
      return `https://www.google.com/maps/dir/?api=1&origin=${olat},${olng}&destination=${dlat},${dlng}&travelmode=${travelmode}${wp}`;
    }
    case "apple": {
      const dirflg = mode === "walk" ? "w" : mode === "car" ? "d" : "r"; // r=transit
      return `https://maps.apple.com/?saddr=${olat},${olng}&daddr=${dlat},${dlng}&dirflg=${dirflg}`;
    }
    case "tmap":
      return `tmap://route?startx=${olng}&starty=${olat}&endx=${dlng}&endy=${dlat}`;
  }
}

/** 길안내 실행 — app 호출, 미설치 시 fallback */
export function launchNavigation(app: NavApp, p: NavDeepLinkParams): void {
  const url = buildUrl(app, p);

  // 웹 URL 인 앱 (google/apple) — 새 탭
  if (app === "google" || app === "apple") {
    window.open(url, "_blank", "noopener,noreferrer");
    return;
  }

  // 앱 deeplink — 미설치 시 google fallback
  const fallback = buildUrl("google", p);
  const start = Date.now();
  const visibilityHandler = () => {
    if (document.hidden) {
      // 앱 전환 됨 → fallback 취소
      window.removeEventListener("visibilitychange", visibilityHandler);
    }
  };
  document.addEventListener("visibilitychange", visibilityHandler);
  window.location.href = url;

  setTimeout(() => {
    document.removeEventListener("visibilitychange", visibilityHandler);
    if (!document.hidden && Date.now() - start < FALLBACK_TIMEOUT_MS + 500) {
      // 페이지 여전히 활성 → 앱 전환 실패 → fallback
      window.open(fallback, "_blank", "noopener,noreferrer");
    }
  }, FALLBACK_TIMEOUT_MS);
}

/** localStorage 에 선호 앱 저장/조회 */
const PREF_KEY = "nav-app-preference";
export function getPreferredNavApp(): NavApp | null {
  if (typeof localStorage === "undefined") return null;
  const v = localStorage.getItem(PREF_KEY);
  if (v && (v === "kakao" || v === "naver" || v === "google" || v === "apple" || v === "tmap")) {
    return v;
  }
  return null;
}
export function setPreferredNavApp(app: NavApp): void {
  if (typeof localStorage === "undefined") return;
  localStorage.setItem(PREF_KEY, app);
}
