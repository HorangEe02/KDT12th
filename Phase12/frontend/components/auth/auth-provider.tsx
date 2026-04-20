"use client";

import { useEffect, type ReactNode } from "react";
import { onAuthStateChanged, type User as FbUser } from "firebase/auth";
import { doc, onSnapshot } from "firebase/firestore";
import { getClientAuth } from "@/lib/firebase/auth";
import { getClientDb } from "@/lib/firebase/client";
import { syncOnSignIn, clearSyncFlag } from "@/lib/firebase/sync-on-signin";
import { useFirestoreSync } from "@/lib/firebase/use-firestore-sync";
import { useFavoriteTeamSync } from "@/lib/hooks/use-favorite-team-sync";
import { useAuthStore, useAuthUser } from "@/lib/store/auth";
import { useBadges } from "@/lib/store/badges";
import type { UserClaims, UserProfile } from "@/lib/types/user";

/**
 * 최상위 AuthProvider — onAuthStateChanged + Firestore profile 구독 + sync-on-signin.
 *
 * 추가로 useFirestoreSync 를 자식으로 둬서 store ↔ Firestore 양방향 자동 동기화.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  const setUser = useAuthStore((s) => s.setUser);
  const setProfile = useAuthStore((s) => s.setProfile);
  const setClaims = useAuthStore((s) => s.setClaims);
  const setLoading = useAuthStore((s) => s.setLoading);
  const reset = useAuthStore((s) => s.reset);

  useEffect(() => {
    let unsubProfile: (() => void) | null = null;

    const unsub = onAuthStateChanged(getClientAuth(), async (fbUser: FbUser | null) => {
      if (unsubProfile) {
        unsubProfile();
        unsubProfile = null;
      }

      if (!fbUser) {
        // 로그아웃 — store + sync flag 정리
        clearSyncFlag();
        useBadges.getState().reset();
        // filters 는 비로그인 사용자도 쓰니까 reset 안 함 (기본값 유지)
        reset();
        return;
      }

      // 로그인 / 토큰 refresh
      setUser({
        uid: fbUser.uid,
        email: fbUser.email,
        displayName: fbUser.displayName,
        photoURL: fbUser.photoURL,
        emailVerified: fbUser.emailVerified,
      });

      // Custom claims
      try {
        const tokenResult = await fbUser.getIdTokenResult();
        setClaims(tokenResult.claims as unknown as UserClaims);
      } catch {
        setClaims(null);
      }

      // 1회 머지 (anon → 본인)
      try {
        await syncOnSignIn(fbUser.uid);
      } catch (err) {
        console.warn("syncOnSignIn failed:", err);
      }

      // users/{uid} 실시간 구독
      try {
        const ref = doc(getClientDb(), "users", fbUser.uid);
        unsubProfile = onSnapshot(
          ref,
          (snap) => {
            setProfile(snap.exists() ? (snap.data() as UserProfile) : null);
            setLoading(false);
          },
          () => {
            setProfile(null);
            setLoading(false);
          },
        );
      } catch {
        setProfile(null);
        setLoading(false);
      }
    });

    return () => {
      if (unsubProfile) unsubProfile();
      unsub();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <>
      <FirestoreSyncBridge />
      {children}
    </>
  );
}

/**
 * Auth user 가 있을 때만 store ↔ Firestore 동기화 hook 활성.
 * 별도 컴포넌트로 분리 — useFirestoreSync 가 zustand subscribe 를 사용해
 * useEffect 의 dep 폭증을 방지.
 */
function FirestoreSyncBridge() {
  const user = useAuthUser();
  useFirestoreSync({ uid: user?.uid ?? null });
  // 로그인 직후 1회: users/{uid}.favoriteTeam → filters.team hydrate
  // (URL ?team= 있으면 건너뜀. 자세한 규칙은 훅 JSDoc 참조)
  useFavoriteTeamSync();
  return null;
}
