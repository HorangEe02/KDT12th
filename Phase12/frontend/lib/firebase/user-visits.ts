/**
 * user_visits/{uid} CRUD — 방문 구장 (Stadium Tour).
 * 컬렉션: user_visits  (기존 visited_stadiums 와 분리 — 신규 인증 사용자 전용)
 * 스키마: docs/FIREBASE_DB_PLAN.md §3-1
 *
 * 데이터:
 *   visited: string[]                 — short_name 배열
 *   perStadium: { [short]: { firstAt, lastAt, count } }  — 방문 횟수
 *   updatedAt: Timestamp
 */
"use client";

import {
  doc,
  getDoc,
  setDoc,
  updateDoc,
  serverTimestamp,
  onSnapshot,
  type Timestamp,
  type Unsubscribe,
} from "firebase/firestore";
import { getClientDb } from "./client";

const COLLECTION = "user_visits";

export interface PerStadiumEntry {
  firstAt: Timestamp;
  lastAt: Timestamp;
  count: number;
}

export interface RemoteUserVisits {
  visited: string[];
  perStadium?: Record<string, PerStadiumEntry>;
  updatedAt?: Timestamp;
}

function firebaseAvailable(): boolean {
  return Boolean(process.env.NEXT_PUBLIC_FIREBASE_API_KEY);
}

export async function loadUserVisits(
  uid: string,
): Promise<RemoteUserVisits | null> {
  if (!firebaseAvailable() || !uid) return null;
  try {
    const snap = await getDoc(doc(getClientDb(), COLLECTION, uid));
    if (!snap.exists()) return { visited: [] };
    const data = snap.data() as RemoteUserVisits;
    return {
      visited: Array.isArray(data.visited) ? data.visited : [],
      perStadium: data.perStadium ?? {},
      updatedAt: data.updatedAt,
    };
  } catch (err) {
    console.warn("loadUserVisits failed:", err);
    return null;
  }
}

export async function saveUserVisits(
  uid: string,
  visited: string[],
): Promise<boolean> {
  if (!firebaseAvailable() || !uid) return false;
  try {
    await setDoc(
      doc(getClientDb(), COLLECTION, uid),
      {
        visited: [...new Set(visited)],
        updatedAt: serverTimestamp(),
      },
      { merge: true },
    );
    return true;
  } catch (err) {
    console.warn("saveUserVisits failed:", err);
    return false;
  }
}

/**
 * 방문 카운터 증가 — 토글 시 호출 (선택).
 * 첫 방문 시 firstAt + lastAt + count=1, 이후 lastAt + count++.
 */
export async function incrementVisit(
  uid: string,
  short: string,
): Promise<void> {
  if (!firebaseAvailable() || !uid || !short) return;
  try {
    const ref = doc(getClientDb(), COLLECTION, uid);
    const snap = await getDoc(ref);
    const now = serverTimestamp();
    if (!snap.exists()) {
      await setDoc(ref, {
        visited: [short],
        perStadium: { [short]: { firstAt: now, lastAt: now, count: 1 } },
        updatedAt: now,
      });
      return;
    }
    const data = snap.data() as RemoteUserVisits;
    const entry = data.perStadium?.[short];
    const next = entry
      ? { ...entry, lastAt: now, count: entry.count + 1 }
      : { firstAt: now, lastAt: now, count: 1 };
    const visited = [...new Set([...(data.visited ?? []), short])];
    await updateDoc(ref, {
      visited,
      [`perStadium.${short}`]: next,
      updatedAt: now,
    });
  } catch (err) {
    console.warn("incrementVisit failed:", err);
  }
}

/** 실시간 구독 — 다른 디바이스에서 변경 시 즉시 반영. */
export function subscribeUserVisits(
  uid: string,
  onChange: (data: RemoteUserVisits | null) => void,
): Unsubscribe {
  if (!firebaseAvailable() || !uid) return () => {};
  try {
    return onSnapshot(
      doc(getClientDb(), COLLECTION, uid),
      (snap) => {
        if (!snap.exists()) return onChange({ visited: [] });
        onChange(snap.data() as RemoteUserVisits);
      },
      (err) => {
        console.warn("subscribeUserVisits failed:", err);
        onChange(null);
      },
    );
  } catch {
    return () => {};
  }
}
