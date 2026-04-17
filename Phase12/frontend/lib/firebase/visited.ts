/**
 * visited_stadiums Firestore CRUD (브라우저 클라이언트).
 * Firebase env 미구성 시 자동 skip — 호출부는 try/catch 불필요.
 */
"use client";

import { doc, getDoc, setDoc, serverTimestamp } from "firebase/firestore";
import { COLLECTIONS, getClientDb } from "./client";

function firebaseAvailable(): boolean {
  return Boolean(process.env.NEXT_PUBLIC_FIREBASE_API_KEY);
}

export async function loadVisited(uid: string): Promise<string[] | null> {
  if (!firebaseAvailable() || !uid) return null;
  try {
    const db = getClientDb();
    const snap = await getDoc(doc(db, COLLECTIONS.VISITED_STADIUMS, uid));
    if (!snap.exists()) return [];
    const data = snap.data() as { stadiums?: unknown };
    if (Array.isArray(data.stadiums)) {
      return data.stadiums.filter((s): s is string => typeof s === "string");
    }
    return [];
  } catch (err) {
    console.warn("loadVisited failed:", err);
    return null;
  }
}

export async function saveVisited(
  uid: string,
  stadiums: string[],
): Promise<boolean> {
  if (!firebaseAvailable() || !uid) return false;
  try {
    const db = getClientDb();
    await setDoc(
      doc(db, COLLECTIONS.VISITED_STADIUMS, uid),
      {
        stadiums: [...new Set(stadiums)],
        updatedAt: serverTimestamp(),
      },
      { merge: true },
    );
    return true;
  } catch (err) {
    console.warn("saveVisited failed:", err);
    return false;
  }
}
