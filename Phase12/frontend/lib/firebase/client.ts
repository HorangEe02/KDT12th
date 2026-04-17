/**
 * Firebase Web SDK v12 (클라이언트 전용).
 * 포팅 원본: src/db/firestore_client.py (storage_client.py는 서버로 분리)
 *
 * 환경변수 (Next.js public 접두사 필수):
 *   NEXT_PUBLIC_FIREBASE_API_KEY
 *   NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN
 *   NEXT_PUBLIC_FIREBASE_PROJECT_ID
 *   NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET
 *   NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID
 *   NEXT_PUBLIC_FIREBASE_APP_ID
 */
import { initializeApp, getApps, type FirebaseApp } from "firebase/app";
import { getFirestore, type Firestore } from "firebase/firestore";
import { getStorage, type FirebaseStorage } from "firebase/storage";

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId:
    process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID ?? "mini12-310f5",
  storageBucket:
    process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET ??
    "mini12-310f5.appspot.com",
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
};

let _app: FirebaseApp | null = null;
let _db: Firestore | null = null;
let _storage: FirebaseStorage | null = null;

export function getClientApp(): FirebaseApp {
  if (_app) return _app;
  _app = getApps()[0] ?? initializeApp(firebaseConfig);
  return _app;
}

export function getClientDb(): Firestore {
  if (!_db) _db = getFirestore(getClientApp());
  return _db;
}

export function getClientStorage(): FirebaseStorage {
  if (!_storage) _storage = getStorage(getClientApp());
  return _storage;
}

/** Firestore 컬렉션 이름 (Phase 5a와 동일) */
export const COLLECTIONS = {
  VISITED_STADIUMS: "visited_stadiums",
  SHARED_PLANS: "shared_plans",
  CHAT_SESSIONS: "chat_sessions",
} as const;
