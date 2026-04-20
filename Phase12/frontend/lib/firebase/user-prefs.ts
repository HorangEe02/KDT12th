/**
 * user_prefs/{uid} CRUD — 사이드바 필터 영속화.
 * 컬렉션: user_prefs
 * 스키마: docs/FIREBASE_DB_PLAN.md §3-1
 *
 * 호출부:
 *   - sync-on-signin.ts — 로그인 직후 머지
 *   - useFiltersFirestoreSync (auth-provider) — 변경 시 debounced write
 */
"use client";

import {
  doc,
  getDoc,
  setDoc,
  serverTimestamp,
  type Timestamp,
} from "firebase/firestore";
import { getClientDb } from "./client";
import type { PartyType, TransportType } from "@/lib/types";

const COLLECTION = "user_prefs";

export interface RemoteUserPrefs {
  team?: string;
  startDate?: string;
  endDate?: string;
  budgetMax?: number;
  partySize?: PartyType;
  transport?: TransportType;
  demoMode?: boolean;
  updatedAt?: Timestamp;
}

function firebaseAvailable(): boolean {
  return Boolean(process.env.NEXT_PUBLIC_FIREBASE_API_KEY);
}

export async function loadUserPrefs(
  uid: string,
): Promise<RemoteUserPrefs | null> {
  if (!firebaseAvailable() || !uid) return null;
  try {
    const snap = await getDoc(doc(getClientDb(), COLLECTION, uid));
    return snap.exists() ? (snap.data() as RemoteUserPrefs) : null;
  } catch (err) {
    console.warn("loadUserPrefs failed:", err);
    return null;
  }
}

export async function saveUserPrefs(
  uid: string,
  prefs: Omit<RemoteUserPrefs, "updatedAt">,
): Promise<boolean> {
  if (!firebaseAvailable() || !uid) return false;
  try {
    await setDoc(
      doc(getClientDb(), COLLECTION, uid),
      { ...prefs, updatedAt: serverTimestamp() },
      { merge: true },
    );
    return true;
  } catch (err) {
    console.warn("saveUserPrefs failed:", err);
    return false;
  }
}
