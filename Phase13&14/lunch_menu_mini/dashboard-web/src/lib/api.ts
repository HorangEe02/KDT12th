/**
 * Mini API Client
 *
 * Two backends:
 *   - lunch-optimizer (FastAPI) on :8000/api
 *   - NLP service     (FastAPI) on :8001
 *
 * Both wrapped by thin helpers with graceful error shapes.
 */

export const LUNCH_API =
  process.env.NEXT_PUBLIC_LUNCH_API || "http://localhost:8000/api";

export const NLP_API =
  process.env.NEXT_PUBLIC_NLP_API || "http://localhost:8001";

export const DEFAULT_USER_ID = Number(
  process.env.NEXT_PUBLIC_DEFAULT_USER_ID || "1"
);

// 위치 정보가 전혀 확보되지 않을 때(GPS 거부 + IP 폴백 실패)의 최후 fallback.
// 기본값: 대구 중구 (Phase 13&14 .env 의 OFFICE_LAT/OFFICE_LNG 와 일치).
export const DEFAULT_LAT = Number(
  process.env.NEXT_PUBLIC_DEFAULT_LAT || "35.8714"
);
export const DEFAULT_LNG = Number(
  process.env.NEXT_PUBLIC_DEFAULT_LNG || "128.6014"
);
export const DEFAULT_LOCATION_LABEL =
  process.env.NEXT_PUBLIC_DEFAULT_LOCATION_LABEL || "대구 중구";

// =============================================================================
// Auth header helper — JWT 가 localStorage 에 있으면 모든 호출에 자동 부착
// =============================================================================
function authHeaders(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const token = localStorage.getItem("p11_auth_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/** 401 응답 시 토큰 만료로 간주 → 로그아웃 + 이벤트 발행. */
function handleUnauthorized(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem("p11_auth_token");
  localStorage.removeItem("p11_current_user");
  window.dispatchEvent(new CustomEvent("p11_auth_updated"));
}

// =============================================================================
// lunch-optimizer
// =============================================================================
export async function apiFetchLunch<T>(
  path: string,
  init?: RequestInit
): Promise<T> {
  const url = `${LUNCH_API}${path}`;
  const res = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...init?.headers,
    },
    ...init,
  });
  if (res.status === 401) {
    handleUnauthorized();
  }
  if (!res.ok) {
    const detail = await res.text().catch(() => "Unknown error");
    throw new Error(`Lunch API ${res.status}: ${detail}`);
  }
  return res.json();
}

export async function apiUploadLunch<T>(
  path: string,
  formData: FormData,
  params?: Record<string, string>
): Promise<T> {
  const query = params ? "?" + new URLSearchParams(params).toString() : "";
  const url = `${LUNCH_API}${path}${query}`;
  const res = await fetch(url, { method: "POST", body: formData });
  if (!res.ok) {
    const detail = await res.text().catch(() => "Unknown error");
    throw new Error(`Upload ${res.status}: ${detail}`);
  }
  return res.json();
}

// =============================================================================
// NLP service — includes "pending" sentinel for 503 (module warming up)
// =============================================================================
export class NLPPendingError extends Error {
  retryAfter: number;
  constructor(message = "NLP module is warming up", retryAfter = 5) {
    super(message);
    this.name = "NLPPendingError";
    this.retryAfter = retryAfter;
  }
}

export async function apiFetchNLP<T>(
  path: string,
  init?: RequestInit
): Promise<T> {
  const url = `${NLP_API}${path}`;
  const res = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...init?.headers,
    },
    ...init,
  });
  if (res.status === 503) {
    const hdr = res.headers.get("Retry-After");
    const secs = hdr ? Number(hdr) : NaN;
    throw new NLPPendingError(
      "NLP module is warming up",
      Number.isFinite(secs) && secs > 0 ? secs : 5,
    );
  }
  if (!res.ok) {
    const detail = await res.text().catch(() => "Unknown error");
    throw new Error(`NLP API ${res.status}: ${detail}`);
  }
  return res.json();
}

// =============================================================================
// SSE streaming — for /nlp/chatbot/chat/stream (M7)
// =============================================================================
/**
 * Backend frames have shape `{ type: "token"|"meta"|"final"|"error", ... }`.
 * Callers can pass `onMessage` to handle every frame type, or the convenience
 * hooks `onToken/onFinal` to handle specific types only.
 */
export interface StreamFrame {
  type: "token" | "meta" | "final" | "error" | string;
  [key: string]: unknown;
}

export interface SSECallbacks {
  onMessage?: (frame: StreamFrame) => void;
  onToken?: (token: string) => void;
  onMeta?: (meta: Record<string, unknown>) => void;
  onFinal?: (meta: Record<string, unknown>) => void;
  onDone: () => void;
  onError: (err: string) => void;
}

export async function apiStreamSSENLP(
  path: string,
  body: unknown,
  cbs: SSECallbacks,
  signal?: AbortSignal,
): Promise<void> {
  const url = `${NLP_API}${path}`;
  let res: Response;
  try {
    res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal,
    });
  } catch (e) {
    if ((e as Error).name === "AbortError") {
      cbs.onDone();
      return;
    }
    cbs.onError(String((e as Error).message || e));
    return;
  }

  if (!res.ok) {
    cbs.onError(`HTTP ${res.status}`);
    return;
  }

  const reader = res.body?.getReader();
  if (!reader) {
    cbs.onError("No response body");
    return;
  }

  const decoder = new TextDecoder();
  let buffer = "";
  let done = false;

  const flushLine = (line: string) => {
    if (!line.startsWith("data: ")) return;
    const raw = line.slice(6).trim();
    if (raw === "[DONE]") {
      done = true;
      cbs.onDone();
      return;
    }
    let frame: StreamFrame;
    try {
      frame = JSON.parse(raw);
    } catch {
      return;
    }
    // Route by type + call generic onMessage if provided
    cbs.onMessage?.(frame);
    switch (frame.type) {
      case "token":
        if (typeof frame.token === "string") cbs.onToken?.(frame.token);
        break;
      case "meta":
        cbs.onMeta?.(frame as Record<string, unknown>);
        break;
      case "final":
        cbs.onFinal?.(frame as Record<string, unknown>);
        break;
      case "error":
        cbs.onError(
          typeof frame.message === "string" ? frame.message : "stream error"
        );
        break;
    }
  };

  try {
    while (!done) {
      const { done: rdDone, value } = await reader.read();
      if (rdDone) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";
      for (const line of lines) flushLine(line);
    }
    if (!done && buffer.trim()) flushLine(buffer.trim());
    if (!done) cbs.onDone();
  } catch (e) {
    if ((e as Error).name === "AbortError") {
      cbs.onDone();
      return;
    }
    cbs.onError(String((e as Error).message || e));
  }
}
