/**
 * CSS 변수 값을 JS에서 읽어오는 유틸리티
 * Recharts SVG 속성은 var() 문법을 지원하지 않으므로
 * getComputedStyle로 런타임 값을 추출하여 사용
 */
import { useMemo } from "react";
import { useSettings } from "../context/SettingsContext";

let cache = {};
let lastTheme = null;

export function getCssVar(name) {
  const currentTheme = document.documentElement.getAttribute("data-theme") || "dark";

  // 테마 변경 시 캐시 무효화
  if (currentTheme !== lastTheme) {
    cache = {};
    lastTheme = currentTheme;
  }

  if (cache[name]) return cache[name];

  const value = getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim();

  cache[name] = value;
  return value;
}

/**
 * 차트용 색상 훅 — 테마 전환 시 자동 리렌더
 * settings.darkMode를 의존성으로 사용하여 테마 변경 감지
 */
export function useChartColors() {
  const { settings } = useSettings();

  // settings.darkMode가 변경되면 useMemo가 재실행 → 새 CSS 변수값 추출
  return useMemo(() => ({
    cyan: getCssVar("--cyan"),
    orange: getCssVar("--orange"),
    red: getCssVar("--red"),
    yellow: getCssVar("--yellow"),
    green: getCssVar("--green"),
    grid: getCssVar("--chart-grid") || getCssVar("--border"),
    tick: getCssVar("--chart-tick") || getCssVar("--text-muted"),
    label: getCssVar("--chart-label") || getCssVar("--text-dim"),
    textDim: getCssVar("--text-dim"),
    textMuted: getCssVar("--text-muted"),
    border: getCssVar("--border"),
  }), [settings.darkMode]);
}
