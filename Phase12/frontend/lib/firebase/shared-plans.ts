/**
 * shared_plans Firestore CRUD (서버 Admin SDK).
 * Firebase Admin 미구성 시 graceful skip.
 */
import "server-only";
import { getAdminDb, isAdminConfigured } from "./admin";
import type { Filters } from "@/lib/types";

const COLLECTION = "shared_plans";

function adminAvailable(): boolean {
  // 서비스 계정 키 파일이 실재하거나 Cloud 환경일 때만 Firestore 시도
  return Boolean(process.env.FIREBASE_PROJECT_ID) && isAdminConfigured();
}

export async function createSharedPlan(
  filters: Partial<Filters>,
  title?: string,
): Promise<string | null> {
  if (!adminAvailable()) return null;
  try {
    const db = getAdminDb();
    const ref = await db.collection(COLLECTION).add({
      filters,
      title: title ?? null,
      createdAt: new Date(),
    });
    return ref.id;
  } catch (err) {
    console.warn("createSharedPlan failed:", err);
    return null;
  }
}

export async function getSharedPlan(
  planId: string,
): Promise<{ filters: Partial<Filters>; title?: string } | null> {
  if (!adminAvailable() || !planId) return null;
  try {
    const db = getAdminDb();
    const snap = await db.collection(COLLECTION).doc(planId).get();
    if (!snap.exists) return null;
    const data = snap.data();
    if (!data) return null;
    return {
      filters: (data.filters ?? {}) as Partial<Filters>,
      title: data.title ?? undefined,
    };
  } catch (err) {
    console.warn("getSharedPlan failed:", err);
    return null;
  }
}
