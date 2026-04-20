/**
 * 사용자 / 권한 / 감사 타입 정의.
 * Firestore 스키마 기준: docs/FIREBASE_DB_PLAN.md §3
 */
import type { Timestamp } from "firebase/firestore";

export type UserRole = "user" | "admin";
export type UserStatus = "active" | "disabled";

export interface UserConsent {
  tos: boolean;
  tosVersion: string;
  tosAt: Timestamp | Date | number;
  privacy: boolean;
  privacyAt: Timestamp | Date | number;
  marketing: boolean;
}

export interface UserStats {
  visitedCount: number;
  planCount: number;
  chatSessionCount: number;
  lastPlanAt: Timestamp | Date | null;
}

/** Firestore `users/{uid}` 도큐먼트 스키마 */
export interface UserProfile {
  uid: string;
  email: string;
  displayName: string;
  photoURL: string | null;
  role: UserRole;
  status: UserStatus;
  favoriteTeam: string | null;
  createdAt: Timestamp | Date;
  lastSignInAt: Timestamp | Date;
  lastActiveAt: Timestamp | Date;
  stats: UserStats;
  consent: UserConsent;
}

/** Firebase Auth ID Token 안의 Custom Claims */
export interface UserClaims {
  admin?: true;
  disabled?: true;
  role?: UserRole;
}

/** 클라이언트 Zustand auth store 가 들고 있는 형태 */
export interface AuthState {
  user: AuthUser | null;
  profile: UserProfile | null;
  claims: UserClaims | null;
  loading: boolean;
  error: string | null;
}

export interface AuthUser {
  uid: string;
  email: string | null;
  displayName: string | null;
  photoURL: string | null;
  emailVerified: boolean;
}

/** 회원가입 폼 값 */
export interface SignupValues {
  email: string;
  password: string;
  passwordConfirm: string;
  displayName: string;
  favoriteTeam: string | null;
  consentTos: boolean;
  consentPrivacy: boolean;
  consentMarketing: boolean;
}

/** 로그인 폼 값 */
export interface LoginValues {
  email: string;
  password: string;
}

/** Admin audit log 액션 종류 */
export type AdminAction =
  | "grant_admin"
  | "revoke_admin"
  | "disable_user"
  | "enable_user"
  | "delete_user"
  | "reset_password";

export interface AdminAuditEvent {
  adminUid: string;
  adminEmail: string;
  action: AdminAction;
  targetUid: string;
  targetEmail: string;
  reason: string;
  createdAt: Timestamp | Date;
  ip: string | null;
}
