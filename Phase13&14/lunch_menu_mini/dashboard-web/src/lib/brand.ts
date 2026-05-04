/**
 * 브랜드 상수 — 웹 전반에서 사용하는 서비스 이름/태그라인/버전.
 *
 * 여기 한 곳만 수정하면 Sidebar/TopNav/SettingsPanel/메타 전부 반영됩니다.
 */
export const BRAND = {
  name: "오늘 뭐 먹지",
  tagline: "직장인 점심 결정 도우미",
  version: "0.5",
  /** 로고 이모지 (이미지 로드 실패 시 폴백) */
  logoEmoji: "🍱",
  /** 메인 로고 이미지 (UI 표시용 — rembg isnet으로 배경 투명화한 버전, 다크/라이트 모드 양쪽 자연스러움). PWA 홈 아이콘은 흰 카드 버전(mini1314-180/192/512/1024 + apple-touch-icon*) 그대로 유지. */
  logoSrc: "/logo/mini1314-transparent.png",
  logoAlt: "오늘 뭐 먹지 로고",
  /** 메타 description (SEO/OG) */
  description:
    "날씨 · 영양 · 팀 선호를 반영한 직장인 점심 추천 — 오늘 뭐 먹지",
} as const;
