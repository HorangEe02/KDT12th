/**
 * Error helpers — shared classification for UI error handling.
 *
 * `NLPPendingError` is defined in lib/api.ts (thrown when NLP service returns
 * HTTP 503 during warm-up). We re-export it here so callers have one canonical
 * import site, and we add a type guard and a lightweight fetch-failure detector.
 */
export { NLPPendingError } from "./api";
import { NLPPendingError } from "./api";

export function isWarmingUp(err: unknown): err is NLPPendingError {
  return err instanceof NLPPendingError;
}

/**
 * Detect low-level network errors (server down, CORS, DNS) — these are the
 * cases where mock fallback should kick in and where a "retry" button makes
 * sense. `fetch` throws a TypeError for these.
 */
export function isNetworkError(err: unknown): boolean {
  return err instanceof TypeError && /fetch|network|load failed/i.test(err.message);
}

export function formatError(err: unknown): string {
  if (err instanceof NLPPendingError) return "AI 모듈 준비 중입니다";
  if (err instanceof Error) return err.message;
  return String(err);
}
