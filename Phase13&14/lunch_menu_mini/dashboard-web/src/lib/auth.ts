/**
 * Phase 13&14 — JWT 기반 자체 인증 + RBAC.
 *
 * 백엔드(/api/auth/*) 가 발급한 JWT 를 localStorage 에 저장하고
 * 모든 API 호출에 Authorization: Bearer 헤더로 부착한다 (api.ts 와 협력).
 *
 * 게스트 호환:
 *   기존 id-only "loginGuest" 흐름은 그대로 유지 — 일부 페이지가
 *   비로그인 상태에서도 사용 가능하도록 (인증 미적용 엔드포인트만 호출).
 */
import type { UserAccount } from "./types";
import { apiFetchLunch } from "./api";
import { loadPreferences, savePreferences } from "./preferences";

const TOKEN_KEY = "p11_auth_token";
const USER_KEY = "p11_current_user";

export type Role = "admin" | "user";

export interface CurrentUser {
  id: string;
  name: string;
  team_id: string;
  avatar_emoji: string;
  email?: string | null;
  role?: Role;
}

interface JwtPayload {
  sub: string;
  email?: string | null;
  role?: Role;
  exp?: number;
  iat?: number;
}

interface TokenResponse {
  access_token: string;
  token_type: string;
  user: UserAccount & { email?: string | null; role?: Role };
}

// -----------------------------------------------------------------------------
// Token / User 저장소
// -----------------------------------------------------------------------------
export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null): void {
  if (typeof window === "undefined") return;
  if (token === null) localStorage.removeItem(TOKEN_KEY);
  else localStorage.setItem(TOKEN_KEY, token);
}

export function loadCurrentUser(): CurrentUser | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as CurrentUser) : null;
  } catch {
    return null;
  }
}

export function saveCurrentUser(user: CurrentUser | null): void {
  if (typeof window === "undefined") return;
  if (user === null) localStorage.removeItem(USER_KEY);
  else localStorage.setItem(USER_KEY, JSON.stringify(user));
  window.dispatchEvent(new CustomEvent("p11_auth_updated"));
}

// -----------------------------------------------------------------------------
// JWT 디코드 (서명 검증은 백엔드 담당, 클라는 페이로드만 읽음)
// -----------------------------------------------------------------------------
export function decodeToken(token: string | null = getToken()): JwtPayload | null {
  if (!token) return null;
  const parts = token.split(".");
  if (parts.length !== 3) return null;
  try {
    const payload = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const padded = payload + "=".repeat((4 - (payload.length % 4)) % 4);
    return JSON.parse(atob(padded)) as JwtPayload;
  } catch {
    return null;
  }
}

export function isTokenValid(token: string | null = getToken()): boolean {
  const payload = decodeToken(token);
  if (!payload || !payload.exp) return false;
  return payload.exp * 1000 > Date.now();
}

export function getRole(): Role | null {
  const payload = decodeToken();
  return (payload?.role as Role) ?? null;
}

export function hasRole(role: Role): boolean {
  return getRole() === role;
}

// -----------------------------------------------------------------------------
// 인증 흐름 — register / login (email+password) / loginGuest / logout
// -----------------------------------------------------------------------------
function persistAuthResponse(res: TokenResponse): CurrentUser {
  setToken(res.access_token);
  const user: CurrentUser = {
    id: res.user.id,
    name: res.user.name,
    team_id: res.user.team_id,
    avatar_emoji: res.user.avatar_emoji,
    email: res.user.email ?? null,
    role: (res.user.role as Role) ?? "user",
  };
  saveCurrentUser(user);
  return user;
}

export async function register(input: {
  email: string;
  password: string;
  name: string;
  team_id?: string;
  avatar_emoji?: string;
}): Promise<CurrentUser> {
  const res = await apiFetchLunch<TokenResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify({
      email: input.email,
      password: input.password,
      name: input.name,
      team_id: input.team_id ?? "team1",
      avatar_emoji: input.avatar_emoji ?? "🧑‍💻",
    }),
  });
  return persistAuthResponse(res);
}

export async function login(
  emailOrInput: string | { email: string; password: string },
  passwordArg?: string,
): Promise<CurrentUser> {
  const email = typeof emailOrInput === "string" ? emailOrInput : emailOrInput.email;
  const password =
    typeof emailOrInput === "string" ? passwordArg ?? "" : emailOrInput.password;
  const res = await apiFetchLunch<TokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  return persistAuthResponse(res);
}

/**
 * 게스트 로그인 — 기존 id-only 흐름 호환.
 * 토큰 없이 localStorage 에만 사용자 식별자 저장.
 * 백엔드의 인증 필수 엔드포인트는 호출 불가.
 */
export async function loginGuest(
  id: string,
  name: string,
  team_id = "team1",
  avatar_emoji = "🧑‍💻",
): Promise<CurrentUser> {
  try {
    const res = await apiFetchLunch<UserAccount>("/users", {
      method: "POST",
      body: JSON.stringify({ id, name, team_id, avatar_emoji }),
    });
    const user: CurrentUser = {
      id: res.id,
      name: res.name,
      team_id: res.team_id,
      avatar_emoji: res.avatar_emoji,
      role: "user",
    };
    saveCurrentUser(user);
    return user;
  } catch {
    const user: CurrentUser = { id, name, team_id, avatar_emoji, role: "user" };
    saveCurrentUser(user);
    return user;
  }
}

export function logout(): void {
  setToken(null);
  saveCurrentUser(null);
}

// -----------------------------------------------------------------------------
// 백엔드 동기화 (기존 호환 — 토큰 있으면 자동 부착)
// -----------------------------------------------------------------------------
export async function syncPreferencesToBackend(user: CurrentUser): Promise<boolean> {
  const prefs = loadPreferences();
  try {
    await apiFetchLunch(`/users/${encodeURIComponent(user.id)}/preferences`, {
      method: "PATCH",
      body: JSON.stringify({
        dislike_categories: prefs.dislikedCategories.join(",") || null,
        allergy_info: prefs.allergies.join(",") || null,
        avatar_emoji: user.avatar_emoji,
        name: user.name,
      }),
    });
    return true;
  } catch {
    return false;
  }
}

export async function pullPreferencesFromBackend(user: CurrentUser): Promise<void> {
  try {
    const res = await apiFetchLunch<UserAccount>(
      `/users/${encodeURIComponent(user.id)}`,
    );
    const prefs = loadPreferences();
    if (res.dislike_categories) {
      prefs.dislikedCategories = res.dislike_categories
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);
    }
    if (res.allergy_info) {
      prefs.allergies = res.allergy_info
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);
    }
    savePreferences(prefs);
  } catch {
    /* best-effort only */
  }
}
