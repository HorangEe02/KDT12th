/**
 * KBO 10개 구단 팀 컬러 팔레트.
 * 포팅 원본: src/ui/components/hero.py TEAM_COLORS
 * 런타임 확장본: frontend/public/data/team-colors.json
 */

export interface TeamPalette {
  color: string;
  subColor: string;
  nameKo: string;
}

export const TEAM_COLORS: Record<string, TeamPalette> = {
  LG: { color: "#C30452", subColor: "#FFCC00", nameKo: "LG 트윈스" },
  KT: { color: "#000000", subColor: "#E5002D", nameKo: "KT 위즈" },
  SSG: { color: "#CE0E2D", subColor: "#FFB81C", nameKo: "SSG 랜더스" },
  두산: { color: "#131230", subColor: "#ED1C24", nameKo: "두산 베어스" },
  KIA: { color: "#EA002C", subColor: "#06141F", nameKo: "KIA 타이거즈" },
  NC: { color: "#315288", subColor: "#A39161", nameKo: "NC 다이노스" },
  삼성: { color: "#074CA1", subColor: "#C0C0C0", nameKo: "삼성 라이온즈" },
  롯데: { color: "#041E42", subColor: "#ED1C24", nameKo: "롯데 자이언츠" },
  한화: { color: "#FF6600", subColor: "#000000", nameKo: "한화 이글스" },
  키움: { color: "#570514", subColor: "#B07F4A", nameKo: "키움 히어로즈" },
};

/** 사이드바·탭에서 순회할 때 사용하는 정식 순서 */
export const TEAMS: readonly string[] = [
  "LG",
  "KT",
  "SSG",
  "두산",
  "KIA",
  "NC",
  "삼성",
  "롯데",
  "한화",
  "키움",
] as const;

/** 팀 코드 → 로고 파일명 매핑 (public/logos/{file}.svg) */
const LOGO_FILE: Record<string, string> = {
  LG: "LG",
  KT: "KT",
  SSG: "SSG",
  두산: "DOOSAN",
  KIA: "KIA",
  NC: "NC",
  삼성: "SAMSUNG",
  롯데: "LOTTE",
  한화: "HANWHA",
  키움: "KIWOOM",
};

export function getTeamLogoPath(team: string): string {
  const file = LOGO_FILE[team] ?? "KBO_1";
  return `/logos/${file}.svg`;
}

export function getKBOLogoPath(variant: 1 | 2 = 1): string {
  return `/logos/KBO_${variant}.svg`;
}

export function getTeamPalette(team: string): TeamPalette {
  return TEAM_COLORS[team] ?? TEAM_COLORS.LG;
}
