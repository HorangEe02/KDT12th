/**
 * user_plans/{uid}/items/{planId} CRUD — 사용자 코스 (개인 보관).
 * 스키마: docs/FIREBASE_DB_PLAN.md §3-1
 */
"use client";

import {
  collection,
  doc,
  addDoc,
  getDoc,
  getDocs,
  setDoc,
  deleteDoc,
  query,
  orderBy,
  limit,
  onSnapshot,
  serverTimestamp,
  type Timestamp,
  type Unsubscribe,
} from "firebase/firestore";
import { getClientDb } from "./client";
import type { Filters } from "@/lib/types";

const ROOT = "user_plans";
const ITEMS = "items";

export interface RemoteUserPlan {
  name: string;
  filters: Partial<Filters>;
  gameId?: string | null;
  stadium?: string | null;
  route?: unknown;
  pois?: unknown;
  weather?: unknown;
  aiSummary?: string | null;
  winProb?: number | null;
  public: boolean;
  sharedPlanId?: string | null;
  exports?: { csv?: number; pdf?: number; docx?: number; pptx?: number };
  createdAt?: Timestamp;
  updatedAt?: Timestamp;
}

export interface UserPlanWithId extends RemoteUserPlan {
  id: string;
}

function firebaseAvailable(): boolean {
  return Boolean(process.env.NEXT_PUBLIC_FIREBASE_API_KEY);
}

function itemsRef(uid: string) {
  return collection(getClientDb(), ROOT, uid, ITEMS);
}

/** 새 코스 저장 — 자동 ID 발급 후 ID 반환. */
export async function createUserPlan(
  uid: string,
  plan: Omit<RemoteUserPlan, "createdAt" | "updatedAt">,
): Promise<string | null> {
  if (!firebaseAvailable() || !uid) return null;
  try {
    const ref = await addDoc(itemsRef(uid), {
      ...plan,
      createdAt: serverTimestamp(),
      updatedAt: serverTimestamp(),
    });
    return ref.id;
  } catch (err) {
    console.warn("createUserPlan failed:", err);
    return null;
  }
}

export async function updateUserPlan(
  uid: string,
  planId: string,
  patch: Partial<RemoteUserPlan>,
): Promise<boolean> {
  if (!firebaseAvailable() || !uid) return false;
  try {
    await setDoc(
      doc(itemsRef(uid), planId),
      { ...patch, updatedAt: serverTimestamp() },
      { merge: true },
    );
    return true;
  } catch (err) {
    console.warn("updateUserPlan failed:", err);
    return false;
  }
}

export async function deleteUserPlan(
  uid: string,
  planId: string,
): Promise<boolean> {
  if (!firebaseAvailable() || !uid) return false;
  try {
    await deleteDoc(doc(itemsRef(uid), planId));
    return true;
  } catch (err) {
    console.warn("deleteUserPlan failed:", err);
    return false;
  }
}

export async function getUserPlan(
  uid: string,
  planId: string,
): Promise<UserPlanWithId | null> {
  if (!firebaseAvailable() || !uid) return null;
  try {
    const snap = await getDoc(doc(itemsRef(uid), planId));
    return snap.exists()
      ? ({ id: snap.id, ...(snap.data() as RemoteUserPlan) })
      : null;
  } catch (err) {
    console.warn("getUserPlan failed:", err);
    return null;
  }
}

export async function listUserPlans(
  uid: string,
  pageSize: number = 20,
): Promise<UserPlanWithId[]> {
  if (!firebaseAvailable() || !uid) return [];
  try {
    const q = query(itemsRef(uid), orderBy("updatedAt", "desc"), limit(pageSize));
    const snap = await getDocs(q);
    return snap.docs.map((d) => ({
      id: d.id,
      ...(d.data() as RemoteUserPlan),
    }));
  } catch (err) {
    console.warn("listUserPlans failed:", err);
    return [];
  }
}

/** 실시간 구독 — /badges 페이지에서 사용. */
export function subscribeUserPlans(
  uid: string,
  onChange: (plans: UserPlanWithId[]) => void,
  pageSize: number = 20,
): Unsubscribe {
  if (!firebaseAvailable() || !uid) return () => {};
  try {
    const q = query(itemsRef(uid), orderBy("updatedAt", "desc"), limit(pageSize));
    return onSnapshot(
      q,
      (snap) => {
        onChange(
          snap.docs.map((d) => ({
            id: d.id,
            ...(d.data() as RemoteUserPlan),
          })),
        );
      },
      (err) => {
        console.warn("subscribeUserPlans failed:", err);
      },
    );
  } catch {
    return () => {};
  }
}
