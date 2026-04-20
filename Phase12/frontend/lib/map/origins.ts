/**
 * 출발지 프리셋 — server/client 양쪽에서 임포트 가능해야 하므로 "use client" 없이 순수 모듈.
 * 포팅 원본: src/ui/tabs/tab2_map.py _ORIGIN_PRESETS
 *
 * 확장 (2026-04-18 · NEXT_SESSION_PLAN Feature 5):
 * - 4 → 17 정거장 + 지역별 그룹
 * - 모바일/공항 추가 가능 (geolocation 은 client 측에서 ?origin=custom&lat=..&lng=.. 로 처리)
 */

export const ORIGIN_PRESETS: Record<string, [number, number]> = {
  // ── 수도권 (Capital area) ──
  seoul: [37.5547, 126.9707],         // 서울역
  yongsan: [37.5299, 126.9648],       // 용산역
  cheongnyangni: [37.5803, 127.0467], // 청량리역
  gangnam: [37.4979, 127.0276],       // 강남역
  suwon: [37.2657, 127.0009],         // 수원역

  // ── 중부 (Central) ──
  cheonan_asan: [36.7943, 127.1047],  // 천안아산역
  osong: [36.6201, 127.3266],         // 오송역
  daejeon: [36.3322, 127.4342],       // 대전역

  // ── 영남 (Yeongnam) ──
  dongdaegu: [35.8797, 128.6286],     // 동대구역
  pohang: [36.0172, 129.3415],        // 포항역
  busan: [35.1156, 129.0413],         // 부산역
  ulsan: [35.5519, 129.1379],         // 울산역
  jinyeong: [35.3739, 128.7407],      // 진영역 (창원 NC 가까움)

  // ── 호남 (Honam) ──
  gwangju_songjeong: [35.1349, 126.7853], // 광주송정역
  yeosu_expo: [34.7474, 127.7474],    // 여수엑스포역
  mokpo: [34.7919, 126.3873],         // 목포역

  // ── 공항 (Airports) ──
  incheon_airport: [37.4602, 126.4407], // 인천국제공항
  gimpo_airport: [37.5587, 126.7905],   // 김포공항
};

export const ORIGIN_LABEL: Record<string, string> = {
  seoul: "서울역",
  yongsan: "용산역",
  cheongnyangni: "청량리역",
  gangnam: "강남역",
  suwon: "수원역",
  cheonan_asan: "천안아산역",
  osong: "오송역",
  daejeon: "대전역",
  dongdaegu: "동대구역",
  pohang: "포항역",
  busan: "부산역",
  ulsan: "울산역",
  jinyeong: "진영역",
  gwangju_songjeong: "광주송정역",
  yeosu_expo: "여수엑스포역",
  mokpo: "목포역",
  incheon_airport: "인천공항",
  gimpo_airport: "김포공항",
};

/** 지역별 그룹 — accordion UI 에서 사용 */
export interface OriginGroup {
  id: string;
  label: string;
  emoji: string;
  keys: string[];
}

export const ORIGIN_GROUPS: OriginGroup[] = [
  {
    id: "capital",
    label: "수도권",
    emoji: "🚄",
    keys: ["seoul", "yongsan", "cheongnyangni", "gangnam", "suwon"],
  },
  {
    id: "central",
    label: "중부",
    emoji: "🚅",
    keys: ["cheonan_asan", "osong", "daejeon"],
  },
  {
    id: "yeongnam",
    label: "영남",
    emoji: "🚆",
    keys: ["dongdaegu", "pohang", "busan", "ulsan", "jinyeong"],
  },
  {
    id: "honam",
    label: "호남",
    emoji: "🚝",
    keys: ["gwangju_songjeong", "yeosu_expo", "mokpo"],
  },
  {
    id: "airport",
    label: "공항",
    emoji: "🛫",
    keys: ["incheon_airport", "gimpo_airport"],
  },
];

/**
 * Custom origin (geolocation) 키 — URL 에 lat/lng 파라미터로 함께 전달.
 * page.tsx 서버 컴포넌트는 이 키를 보면 ORIGIN_PRESETS 대신 lat/lng 쿼리를 사용.
 */
export const CUSTOM_ORIGIN_KEY = "custom";

/** Haversine — 가장 가까운 프리셋 추천 (geolocation 보조 용) */
export function findNearestPreset(
  lat: number,
  lng: number,
): { key: string; label: string; distanceKm: number } {
  let best: { key: string; distance: number } = {
    key: "seoul",
    distance: Infinity,
  };
  for (const [key, [plat, plng]] of Object.entries(ORIGIN_PRESETS)) {
    const d = haversineKm(lat, lng, plat, plng);
    if (d < best.distance) best = { key, distance: d };
  }
  return {
    key: best.key,
    label: ORIGIN_LABEL[best.key],
    distanceKm: Math.round(best.distance * 10) / 10,
  };
}

function haversineKm(
  lat1: number,
  lng1: number,
  lat2: number,
  lng2: number,
): number {
  const R = 6371;
  const toRad = (d: number) => (d * Math.PI) / 180;
  const dLat = toRad(lat2 - lat1);
  const dLng = toRad(lng2 - lng1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLng / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(a));
}
