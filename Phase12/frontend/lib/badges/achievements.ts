/**
 * 도전 과제 — 공통 정의.
 * 모바일 (AchievementScroll) / 데스크톱 (AchievementGrid) 에서 공유.
 */

export interface Achievement {
  id: string;
  label: string;
  /** Material Symbols Outlined 아이콘명 */
  icon: string;
  /** visited.length 기준 해제 임계값 */
  threshold: number;
  gradient: string;
  description: string;
}

export const ACHIEVEMENTS: Achievement[] = [
  {
    id: "first",
    label: "첫 원정",
    icon: "military_tech",
    threshold: 1,
    gradient: "from-se-primary to-se-primary-container",
    description: "원정 여정의 첫 발걸음",
  },
  {
    id: "trio",
    label: "3구장 정복",
    icon: "local_fire_department",
    threshold: 3,
    gradient: "from-orange-500 to-red-600",
    description: "뜨거운 원정러의 증거",
  },
  {
    id: "five",
    label: "5구장 정복",
    icon: "stars",
    threshold: 5,
    gradient: "from-amber-500 to-yellow-600",
    description: "KBO 절반을 섭렵",
  },
  {
    id: "warrior",
    label: "원정 전사",
    icon: "shield",
    threshold: 7,
    gradient: "from-emerald-500 to-teal-600",
    description: "진정한 팬의 여정",
  },
  {
    id: "legend",
    label: "전설",
    icon: "workspace_premium",
    threshold: 10,
    gradient: "from-purple-500 to-pink-600",
    description: "10 구장 모두 방문 — KBO 완주",
  },
];

export function getAchievementProgress(visitedCount: number) {
  return ACHIEVEMENTS.map((a) => ({
    ...a,
    unlocked: visitedCount >= a.threshold,
    progress: Math.min(1, visitedCount / a.threshold),
  }));
}
