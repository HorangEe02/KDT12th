/**
 * 클라이언트 인증 헬퍼 — Firebase Web SDK v12 wrapper.
 * 모든 함수는 "use client" 컴포넌트 / 이벤트 핸들러에서 호출.
 *
 * 흐름: signUp/signIn → cred.user.getIdToken() → POST /api/auth/session 으로 쿠키 설정
 */
import {
  getAuth,
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signInWithPopup,
  signInWithCustomToken,
  signOut as fbSignOut,
  GoogleAuthProvider,
  updateProfile as fbUpdateProfile,
  sendPasswordResetEmail,
  type Auth,
  type User as FirebaseUser,
} from "firebase/auth";
import { getClientApp } from "./client";

let _auth: Auth | null = null;
function auth(): Auth {
  if (_auth) return _auth;
  _auth = getAuth(getClientApp());
  return _auth;
}

const SESSION_ENDPOINT = "/api/auth/session";

/** 서버 세션 쿠키 발급 (POST) — 클라이언트 코드에서 직접 호출 */
async function postSessionCookie(
  user: FirebaseUser,
  initialProfile?: Record<string, unknown>,
): Promise<void> {
  const idToken = await user.getIdToken(/* forceRefresh */ true);
  const res = await fetch(SESSION_ENDPOINT, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ idToken, profile: initialProfile }),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`세션 발급 실패 (${res.status}): ${text}`);
  }
}

/** 서버 세션 쿠키 삭제 (DELETE) */
async function deleteSessionCookie(): Promise<void> {
  await fetch(SESSION_ENDPOINT, { method: "DELETE" }).catch(() => {
    /* 네트워크 실패해도 클라이언트 signOut 은 진행 */
  });
}

// ────────────────────────────────────────────────────────────
// Email / Password
// ────────────────────────────────────────────────────────────

export interface SignUpEmailParams {
  email: string;
  password: string;
  displayName: string;
  favoriteTeam?: string | null;
  consent: {
    tos: boolean;
    privacy: boolean;
    marketing: boolean;
  };
}

export async function signUpWithEmail(
  params: SignUpEmailParams,
): Promise<FirebaseUser> {
  const cred = await createUserWithEmailAndPassword(
    auth(),
    params.email,
    params.password,
  );
  await fbUpdateProfile(cred.user, { displayName: params.displayName });
  await postSessionCookie(cred.user, {
    displayName: params.displayName,
    favoriteTeam: params.favoriteTeam ?? null,
    consent: {
      tos: params.consent.tos,
      tosVersion: "v1",
      tosAt: Date.now(),
      privacy: params.consent.privacy,
      privacyAt: Date.now(),
      marketing: params.consent.marketing,
    },
  });
  return cred.user;
}

export async function signInWithEmail(
  email: string,
  password: string,
): Promise<FirebaseUser> {
  const cred = await signInWithEmailAndPassword(auth(), email, password);
  await postSessionCookie(cred.user);
  return cred.user;
}

// ────────────────────────────────────────────────────────────
// Google OIDC
// ────────────────────────────────────────────────────────────

export async function signInWithGoogle(): Promise<FirebaseUser> {
  const provider = new GoogleAuthProvider();
  provider.setCustomParameters({ prompt: "select_account" });
  const cred = await signInWithPopup(auth(), provider);
  await postSessionCookie(cred.user, {
    displayName: cred.user.displayName ?? "사용자",
    photoURL: cred.user.photoURL ?? null,
    consent: {
      tos: true,
      tosVersion: "v1",
      tosAt: Date.now(),
      privacy: true,
      privacyAt: Date.now(),
      marketing: false,
    },
  });
  return cred.user;
}

// ────────────────────────────────────────────────────────────
// Kakao (Firebase Custom Token)
// ────────────────────────────────────────────────────────────

/**
 * /api/auth/kakao/consume 가 반환한 custom token 으로 Firebase 로그인 + 세션 쿠키 발급.
 * 호출 위치: app/login/complete/kakao-complete.tsx
 */
export async function signInWithKakaoCustomToken(
  token: string,
): Promise<FirebaseUser> {
  const cred = await signInWithCustomToken(auth(), token);
  await postSessionCookie(cred.user, {
    displayName: cred.user.displayName ?? "사용자",
    photoURL: cred.user.photoURL ?? null,
    consent: {
      tos: true,
      tosVersion: "v1",
      tosAt: Date.now(),
      privacy: true,
      privacyAt: Date.now(),
      marketing: false,
    },
  });
  return cred.user;
}

// ────────────────────────────────────────────────────────────
// Sign Out / Reset
// ────────────────────────────────────────────────────────────

export async function signOut(): Promise<void> {
  await deleteSessionCookie();
  await fbSignOut(auth());
}

export async function sendPasswordReset(email: string): Promise<void> {
  await sendPasswordResetEmail(auth(), email, {
    url:
      typeof window !== "undefined"
        ? `${window.location.origin}/login`
        : "https://mini12-310f5.web.app/login",
    handleCodeInApp: false,
  });
}

/** 강제 토큰 갱신 — Custom claim 변경 후 즉시 반영 시 사용 */
export async function refreshIdToken(): Promise<string | null> {
  const u = auth().currentUser;
  if (!u) return null;
  return u.getIdToken(true);
}

export { auth as getClientAuth };
