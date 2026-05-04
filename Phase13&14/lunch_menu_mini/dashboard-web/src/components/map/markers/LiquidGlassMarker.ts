/**
 * LiquidGlassMarker — Apple Liquid Glass(macOS Tahoe / iOS 26+) 톤의
 * 지도 마커 HTML 빌더.
 *
 * KakaoMap(`CustomOverlay.content`) 와 LeafletMap(`L.divIcon.html`) 모두에서
 * 동일한 빌더를 재사용한다 → 단일 진실 공급원.
 *
 *   - 반투명 + backdrop-filter blur + saturate
 *   - 1px 내부 하이라이트(top inset) + 1px 외곽 라인
 *   - 이중 그림자 (소프트 + 미세 컬러글로우)
 *   - 미니멀 인라인 SVG 픽토그램 (포크/스푼, 컴퍼스 도트)
 */

export type GlassMarkerKind = "user" | "restaurant" | "restaurantSelected";

interface BuildOpts {
  kind: GlassMarkerKind;
  rid?: string | number;
}

interface MarkerSize {
  w: number;
  h: number;
  /** Leaflet iconAnchor(top-left 기준의 픽셀). KakaoMap 은 yAnchor/xAnchor 비율로 따로 처리. */
  anchor: [number, number];
}

const SIZES: Record<GlassMarkerKind, MarkerSize> = {
  user: { w: 32, h: 32, anchor: [16, 16] },
  restaurant: { w: 28, h: 28, anchor: [14, 28] },
  restaurantSelected: { w: 34, h: 34, anchor: [17, 34] },
};

export function buildGlassMarkerSize(kind: GlassMarkerKind): MarkerSize {
  return SIZES[kind];
}

// ── 인라인 SVG 픽토그램 (14×14, currentColor stroke) ─────────────
const SVG_FORK_SPOON = `
<svg viewBox="0 0 16 16" width="14" height="14" fill="none"
     stroke="currentColor" stroke-width="1.4"
     stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
  <path d="M5 2v5a1.5 1.5 0 0 0 1.5 1.5v0V14"/>
  <path d="M3.6 2v3.4"/>
  <path d="M6.4 2v3.4"/>
  <path d="M11 2c-1.2 0-2 1.4-2 3.2 0 1.4.7 2.5 1.6 2.8L10.5 14"/>
</svg>`.trim();

const SVG_USER_DOT = `
<svg viewBox="0 0 16 16" width="14" height="14" fill="none" aria-hidden="true">
  <circle cx="8" cy="8" r="5.6" stroke="currentColor"
          stroke-width="1.4" stroke-opacity="0.85" fill="none"/>
  <circle cx="8" cy="8" r="2.2" fill="currentColor"/>
</svg>`.trim();

// ── 메인 빌더 ─────────────────────────────────────────────
export function buildGlassMarkerHTML(opts: BuildOpts): string {
  const { kind, rid } = opts;
  const size = SIZES[kind];

  const ridAttr = rid != null ? ` data-rid="${escapeAttr(String(rid))}"` : "";
  const cls = `lgm lgm--${kind}`;
  // restaurant 마커는 위치 기준점이 바닥(yAnchor:1)이므로 살짝 들어 올림
  const lift = kind === "restaurant" || kind === "restaurantSelected" ? "translateY(0)" : "translate(-50%,-50%)";

  // user 마커는 정중앙 정렬 위해 absolute-style transform 적용
  const positioning =
    kind === "user"
      ? "position:relative;transform:translate(-50%,-50%);"
      : "position:relative;";

  const inner = kind === "user" ? SVG_USER_DOT : SVG_FORK_SPOON;

  return (
    `<div${ridAttr} class="${cls}" style="` +
    `${positioning}` +
    `width:${size.w}px;height:${size.h}px;` +
    `display:inline-flex;align-items:center;justify-content:center;` +
    `cursor:${kind === "user" ? "default" : "pointer"};` +
    `pointer-events:${kind === "user" ? "none" : "auto"};` +
    `transform:${lift};` +
    `">${inner}</div>`
  );
}

function escapeAttr(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

// ── 글로벌 스타일 1회 주입 ────────────────────────────────────
const STYLE_ID = "lg-marker-styles";

export function ensureGlassMarkerStylesInjected(): void {
  if (typeof document === "undefined") return;
  if (document.getElementById(STYLE_ID)) return;

  const style = document.createElement("style");
  style.id = STYLE_ID;
  style.textContent = LG_CSS;
  document.head.appendChild(style);
}

const LG_CSS = `
.lgm {
  border-radius: 9999px;
  background: rgba(255,255,255,0.55);
  -webkit-backdrop-filter: blur(12px) saturate(180%);
  backdrop-filter: blur(12px) saturate(180%);
  border: 1px solid rgba(255,255,255,0.6);
  box-shadow:
    0 1px 2px rgba(0,0,0,0.18),
    0 4px 12px rgba(0,0,0,0.10),
    inset 0 1px 0 rgba(255,255,255,0.7);
  color: #2a2a2a;
  transition: transform 160ms ease, box-shadow 160ms ease, background 160ms ease;
  will-change: transform;
}

/* 기본 음식점 */
.lgm--restaurant { color: #2a2a2a; }
.lgm--restaurant:hover {
  transform: scale(1.08);
  background: rgba(255,255,255,0.7);
}

/* 선택된 음식점 — 주황 틴트 */
.lgm--restaurantSelected {
  background: rgba(232,89,60,0.18);
  border-color: rgba(232,89,60,0.55);
  color: #b8351f;
  box-shadow:
    0 1px 2px rgba(232,89,60,0.30),
    0 6px 18px rgba(232,89,60,0.28),
    inset 0 1px 0 rgba(255,255,255,0.55);
}

/* 사용자 위치 — 청록 틴트 + 펄스 */
.lgm--user {
  background: rgba(10,132,255,0.20);
  border-color: rgba(10,132,255,0.55);
  color: #0a3a8a;
  box-shadow:
    0 1px 2px rgba(10,132,255,0.30),
    0 6px 18px rgba(10,132,255,0.20),
    inset 0 1px 0 rgba(255,255,255,0.55);
  animation: lgm-pulse 2.4s ease-in-out infinite;
}

@keyframes lgm-pulse {
  0%, 100% { box-shadow:
      0 1px 2px rgba(10,132,255,0.30),
      0 6px 18px rgba(10,132,255,0.20),
      inset 0 1px 0 rgba(255,255,255,0.55),
      0 0 0 0 rgba(10,132,255,0.45); }
  60% { box-shadow:
      0 1px 2px rgba(10,132,255,0.30),
      0 6px 18px rgba(10,132,255,0.20),
      inset 0 1px 0 rgba(255,255,255,0.55),
      0 0 0 12px rgba(10,132,255,0); }
}

/* backdrop-filter 미지원 폴백 */
@supports not ((backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px))) {
  .lgm { background: rgba(255,255,255,0.92); }
  .lgm--restaurantSelected { background: rgba(232,89,60,0.85); color: #fff; }
  .lgm--user { background: rgba(10,132,255,0.85); color: #fff; }
}

/* 다크 모드 — 시스템 prefers-color-scheme 기반 */
@media (prefers-color-scheme: dark) {
  .lgm {
    background: rgba(28,28,30,0.55);
    border-color: rgba(255,255,255,0.18);
    color: #f2f2f2;
    box-shadow:
      0 1px 2px rgba(0,0,0,0.6),
      0 6px 18px rgba(0,0,0,0.45),
      inset 0 1px 0 rgba(255,255,255,0.10);
  }
  .lgm--restaurantSelected {
    background: rgba(232,89,60,0.32);
    color: #ffd5cc;
    border-color: rgba(232,89,60,0.65);
  }
  .lgm--user {
    background: rgba(10,132,255,0.32);
    color: #d6e8ff;
    border-color: rgba(10,132,255,0.65);
  }
}

/* Leaflet DivIcon 컨테이너 자체의 기본 배경 제거 */
.lg-marker {
  background: transparent !important;
  border: 0 !important;
}
`.trim();
