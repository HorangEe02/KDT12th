import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Tailwind 클래스 병합 헬퍼.
 * 조건부 클래스와 충돌 해결(tailwind-merge)을 동시에 처리.
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/** 팀 코드 정규화 (한/영 혼용 대응). */
export function normalizeTeam(input: string | null | undefined): string {
  if (!input) return "LG";
  return input.trim();
}

/** 숫자 → 한국어 콤마 포맷 */
export function formatKRW(value: number): string {
  return new Intl.NumberFormat("ko-KR").format(value);
}

/** 승률(0~1) → "54.3%" */
export function formatWinRate(rate: number): string {
  return `${(rate * 100).toFixed(1)}%`;
}
