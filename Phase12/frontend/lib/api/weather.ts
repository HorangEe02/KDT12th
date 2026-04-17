/**
 * 기상청 단기예보 — WGS84 좌표 → 기상청 격자 변환 + /getVilageFcst 호출.
 * 포팅 원본: src/api/weather_api.py
 *
 * 키 미설정/실패 시 Mock 반환 → AI 도구 호출이 절대 실패하지 않도록.
 */
import "server-only";

const BASE_URL =
  "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst";
const BASE_TIMES = [
  "0200",
  "0500",
  "0800",
  "1100",
  "1400",
  "1700",
  "2000",
  "2300",
];

export interface Forecast {
  date: string;
  sky: string | null;
  precipitation_prob: number | null;
  temp_min: number | null;
  temp_max: number | null;
  rain_expected: boolean | null;
  source: "kma" | "mock" | "error";
}

const SKY_MAP: Record<string, string> = {
  "1": "맑음",
  "3": "구름많음",
  "4": "흐림",
};

/** WGS84 (lat/lng) → 기상청 Lambert Conformal Conic 격자 (nx, ny). */
export function dfsXYConv(lat: number, lon: number): [number, number] {
  const RE = 6371.00877;
  const GRID = 5.0;
  const SLAT1 = 30.0;
  const SLAT2 = 60.0;
  const OLON = 126.0;
  const OLAT = 38.0;
  const XO = 43;
  const YO = 136;

  const DEGRAD = Math.PI / 180.0;
  const re = RE / GRID;
  const slat1 = SLAT1 * DEGRAD;
  const slat2 = SLAT2 * DEGRAD;
  const olon = OLON * DEGRAD;
  const olat = OLAT * DEGRAD;

  let sn =
    Math.tan(Math.PI * 0.25 + slat2 * 0.5) /
    Math.tan(Math.PI * 0.25 + slat1 * 0.5);
  sn = Math.log(Math.cos(slat1) / Math.cos(slat2)) / Math.log(sn);
  let sf = Math.tan(Math.PI * 0.25 + slat1 * 0.5);
  sf = (Math.pow(sf, sn) * Math.cos(slat1)) / sn;
  let ro = Math.tan(Math.PI * 0.25 + olat * 0.5);
  ro = (re * sf) / Math.pow(ro, sn);

  let ra = Math.tan(Math.PI * 0.25 + lat * DEGRAD * 0.5);
  ra = (re * sf) / Math.pow(ra, sn);
  let theta = lon * DEGRAD - olon;
  if (theta > Math.PI) theta -= 2.0 * Math.PI;
  if (theta < -Math.PI) theta += 2.0 * Math.PI;
  theta *= sn;

  const x = Math.floor(ra * Math.sin(theta) + XO + 0.5);
  const y = Math.floor(ro - ra * Math.cos(theta) + YO + 0.5);
  return [x, y];
}

function latestBase(now: Date): [string, string] {
  const threshold = new Date(now.getTime() - 10 * 60 * 1000);
  const hhmm = `${String(threshold.getHours()).padStart(2, "0")}${String(
    threshold.getMinutes(),
  ).padStart(2, "0")}`;
  for (const bt of BASE_TIMES.slice().reverse()) {
    if (hhmm >= bt) {
      const y = threshold.getFullYear();
      const m = String(threshold.getMonth() + 1).padStart(2, "0");
      const d = String(threshold.getDate()).padStart(2, "0");
      return [`${y}${m}${d}`, bt];
    }
  }
  const yesterday = new Date(threshold.getTime() - 24 * 60 * 60 * 1000);
  const y = yesterday.getFullYear();
  const m = String(yesterday.getMonth() + 1).padStart(2, "0");
  const d = String(yesterday.getDate()).padStart(2, "0");
  return [`${y}${m}${d}`, "2300"];
}

function mockForecast(targetDate: string): Forecast {
  return {
    date: targetDate,
    sky: "맑음",
    precipitation_prob: 0,
    temp_min: 15,
    temp_max: 23,
    rain_expected: false,
    source: "mock",
  };
}

interface KMAItem {
  category: string;
  fcstDate: string;
  fcstTime: string;
  fcstValue: string;
}

export async function getForecast(
  lat: number,
  lng: number,
  targetDate: string,
): Promise<Forecast> {
  const apiKey = process.env.WEATHER_API_KEY_ENCODED ?? process.env.WEATHER_API_KEY;
  if (!apiKey) return mockForecast(targetDate);

  const [nx, ny] = dfsXYConv(lat, lng);
  const [baseDate, baseTime] = latestBase(new Date());
  const targetYmd = targetDate.replace(/-/g, "");

  const params = new URLSearchParams({
    serviceKey: apiKey,
    numOfRows: "1000",
    pageNo: "1",
    dataType: "JSON",
    base_date: baseDate,
    base_time: baseTime,
    nx: String(nx),
    ny: String(ny),
  });

  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), 5000);
  try {
    const resp = await fetch(`${BASE_URL}?${params.toString()}`, {
      signal: ctl.signal,
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();
    const items: KMAItem[] =
      data?.response?.body?.items?.item ?? [];
    if (items.length === 0) {
      return { ...mockForecast(targetDate), source: "mock" };
    }

    const todays = items.filter((it) => it.fcstDate === targetYmd);
    if (todays.length === 0) {
      return { ...mockForecast(targetDate), source: "mock" };
    }

    const popValues = todays
      .filter((it) => it.category === "POP")
      .map((it) => Number(it.fcstValue))
      .filter((n) => Number.isFinite(n));
    const tmpValues = todays
      .filter((it) => it.category === "TMP")
      .map((it) => Number(it.fcstValue))
      .filter((n) => Number.isFinite(n));
    const skyValue = todays.find((it) => it.category === "SKY")?.fcstValue;
    const ptyValues = todays
      .filter((it) => it.category === "PTY")
      .map((it) => it.fcstValue);

    const maxPOP = popValues.length ? Math.max(...popValues) : 0;
    const rainExpected =
      maxPOP >= 60 || ptyValues.some((v) => v !== "0");

    return {
      date: targetDate,
      sky: skyValue ? SKY_MAP[skyValue] ?? "흐림" : null,
      precipitation_prob: maxPOP,
      temp_min: tmpValues.length ? Math.min(...tmpValues) : null,
      temp_max: tmpValues.length ? Math.max(...tmpValues) : null,
      rain_expected: rainExpected,
      source: "kma",
    };
  } catch {
    return { ...mockForecast(targetDate), source: "error" };
  } finally {
    clearTimeout(timer);
  }
}
