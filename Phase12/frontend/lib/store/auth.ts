/**
 * Zustand auth store — onAuthStateChanged 결과 보관 + 컴포넌트 구독.
 * AuthProvider (top-level) 가 listener 등록 후 setState 호출.
 */
import { create } from "zustand";
import type { AuthState, AuthUser, UserClaims, UserProfile } from "@/lib/types/user";

interface AuthStore extends AuthState {
  setUser: (u: AuthUser | null) => void;
  setProfile: (p: UserProfile | null) => void;
  setClaims: (c: UserClaims | null) => void;
  setLoading: (v: boolean) => void;
  setError: (msg: string | null) => void;
  reset: () => void;
}

const initialState: AuthState = {
  user: null,
  profile: null,
  claims: null,
  loading: true,
  error: null,
};

export const useAuthStore = create<AuthStore>((set) => ({
  ...initialState,
  setUser: (user) => set({ user }),
  setProfile: (profile) => set({ profile }),
  setClaims: (claims) => set({ claims }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  reset: () => set({ ...initialState, loading: false }),
}));

/** 컴포넌트에서 손쉽게 읽기 위한 셀렉터 헬퍼 */
export const useAuthUser = () => useAuthStore((s) => s.user);
export const useAuthProfile = () => useAuthStore((s) => s.profile);
export const useAuthClaims = () => useAuthStore((s) => s.claims);
export const useIsAdmin = () =>
  useAuthStore((s) => s.claims?.admin === true || s.profile?.role === "admin");
export const useIsAuthLoading = () => useAuthStore((s) => s.loading);
