/**
 * 외부 길안내 앱 deeplink 헬퍼.
 * 5개 앱 지원: 카카오맵 / 네이버지도 / Google Maps / Apple Maps / Tmap.
 *
 * 동작:
 *   - 모바일: app-scheme deeplink → 앱 미설치 시 1.5초 후 Google Maps 웹 fallback
 *   - 데스크톱:
 *       google/apple → 공식 웹 URL 새 탭
 *       kakao/naver  → 공식/관찰 기반 웹 URL 새 탭 (경유지 제한적)
 *       tmap         → 앱 전용 (데스크톱 비활성)
 */

export type NavApp = "kakao" | "naver" | "google" | "apple" | "tmap";
export type TravelMode = "transit" | "car" | "walk";

export interface NavDeepLinkParams {
  origin: [number, number]; // [lat, lng]
  destination: [number, number];
  destinationName?: string;
  waypoints?: Array<{ lat: number; lng: number; name?: string }>;
  mode?: TravelMode;
}

export const NAV_APP_META: Record<
  NavApp,
  {
    label: string;
    emoji: string;
    brandColor: string;
    /** "all": 모바일+데스크톱 / "mobile": 모바일만 / "ios": iOS + Safari 데스크톱 */
    available: "all" | "ios" | "mobile";
  }
> = {
  kakao: { label: "카카오맵", emoji: "🟡", brandColor: "#FEE500", available: "all" },
  naver: { label: "네이버지도", emoji: "🟢", brandColor: "#03C75A", available: "all" },
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
  if (meta.available === "ios") return os === "ios" || os === "desktop"; // Apple Maps 웹은 Safari 데스크톱 OK
  return false;
}

/** 현재 OS + 앱 조합에서 경유지(waypoints) 전달 가능한지 */
export function getWaypointSupport(
  app: NavApp,
): "full" | "mobile-only" | "none" {
  if (app === "google") return "full"; // Google Maps 웹+앱 둘 다 waypoints 지원
  return "none"; // 나머지는 모두 경유지 미지원 (kakao/naver/apple/tmap)
}

/** URL builder — OS 에 따라 app deeplink 또는 web URL 선택 */
function buildUrl(app: NavApp, p: NavDeepLinkParams): string {
  const [olat, olng] = p.origin;
  const [dlat, dlng] = p.destination;
  const mode = p.mode ?? "transit";
  const os = detectOS();
  const eName = p.destinationName ?? "도착지";
  const sName = "출발";

  switch (app) {
    case "kakao": {
      if (os === "desktop") {
        // 공식 Kakao Maps link API (https://apis.map.kakao.com/web/documentation/#url-link-api)
        return `https://map.kakao.com/link/from/${encodeURIComponent(sName)},${olat},${olng}/to/${encodeURIComponent(eName)},${dlat},${dlng}`;
      }
      const by = mode === "car" ? "CAR" : mode === "walk" ? "FOOT" : "PUBLICTRANSIT";
      return `kakaomap://route?sp=${olat},${olng}&ep=${dlat},${dlng}&by=${by}`;
    }
    case "naver": {
      if (os === "desktop") {
        // Naver v5 directions 웹 URL (관찰 기반, 공식 문서 없음)
        // 포맷: /v5/directions/<slng>,<slat>,<sname>,,/<elng>,<elat>,<ename>,,/-/<mode>
        const naverMode =
          mode === "walk" ? "walk" : mode === "transit" ? "publictransport" : "car";
        return `https://map.naver.com/v5/directions/${olng},${olat},${encodeURIComponent(sName)},,/${dlng},${dlat},${encodeURIComponent(eName)},,/-/${naverMode}`;
      }
      return `nmap://route/public?slat=${olat}&slng=${olng}&dlat=${dlat}&dlng=${dlng}&dname=${encodeURIComponent(eName)}&appname=stadium-editorial`;
    }
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
  const os = detectOS();

  // 웹 URL (새 탭) 로 여는 경우:
  //   - 항상 웹 URL 인 google/apple
  //   - 데스크톱에서 웹 지원되는 kakao/naver
  const isWebOpen =
    app === "google" ||
    app === "apple" ||
    (os === "desktop" && (app === "kakao" || app === "naver"));

  if (isWebOpen) {
    window.open(url, "_blank", "noopener,noreferrer");
    return;
  }

  // 모바일 앱 deeplink — 미설치 시 google fallback
  const fallback = buildUrl("google", p);
  const start = Date.now();
  const visibilityHandler = () => {
    if (document.hidden) {
      window.removeEventListener("visibilitychange", visibilityHandler);
    }
  };
  document.addEventListener("visibilitychange", visibilityHandler);
  window.location.href = url;

  setTimeout(() => {
    document.removeEventListener("visibilitychange", visibilityHandler);
    if (!document.hidden && Date.now() - start < FALLBACK_TIMEOUT_MS + 500) {
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
