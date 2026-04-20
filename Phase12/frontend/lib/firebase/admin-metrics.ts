/**
 * Admin 대시보드 KPI + Live Feed — Firestore 즉석 집계.
 * Cloud Function 미도입 단계의 MVP 구현. 100~1000명 트래픽까지 무난.
 */
import "server-only";
import { getAdminAuth, getAdminFirestore, isAdminConfigured } from "./admin";

export interface AdminMetrics {
  totalUsers: number;
  newUsers7d: number;
  totalAdmins: number;
  disabledUsers: number;
  totalPlans: number;
  totalChatSessions: number;
  byTeam: Array<{ team: string; count: number }>;
  engagement: Array<{ date: string; activeUsers: number }>;
  generatedAt: string;
}

export interface FeedItem {
  type: "signup" | "plan_created" | "chat_session" | "shared_plan";
  title: string;
  subtitle: string;
  uid: string | null;
  createdAt: string;
}

export async function fetchAdminMetrics(): Promise<AdminMetrics | null> {
  if (!isAdminConfigured()) return null;
  const db = getAdminFirestore();
  const now = new Date();
  const since7d = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);

  // 병렬 fetch
  const [usersSnap, adminsSnap, disabledSnap, plansSnap, chatsSnap, since7dSnap] =
    await Promise.all([
      db.collection("users").count().get().catch(() => null),
      db
        .collection("users")
        .where("role", "==", "admin")
        .count()
        .get()
        .catch(() => null),
      db
        .collection("users")
        .where("status", "==", "disabled")
        .count()
        .get()
        .catch(() => null),
      db.collectionGroup("items").count().get().catch(() => null),
      db.collectionGroup("sessions").count().get().catch(() => null),
      db
        .collection("users")
        .where("createdAt", ">=", since7d)
        .count()
        .get()
        .catch(() => null),
    ]);

  // byTeam — Firestore aggregations 한계로 상위 favoriteTeam 만 read
  let byTeam: Array<{ team: string; count: number }> = [];
  try {
    const recent = await db
      .collection("users")
      .where("favoriteTeam", "!=", null)
      .limit(500)
      .get();
    const tally = new Map<string, number>();
    recent.docs.forEach((d) => {
      const t = d.data().favoriteTeam as string;
      tally.set(t, (tally.get(t) ?? 0) + 1);
    });
    byTeam = [...tally.entries()]
      .map(([team, count]) => ({ team, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);
  } catch {
    byTeam = [];
  }

  // engagement (지난 14일) — users.lastSignInAt 기준
  let engagement: Array<{ date: string; activeUsers: number }> = [];
  try {
    const since14d = new Date(now.getTime() - 14 * 24 * 60 * 60 * 1000);
    const recent = await db
      .collection("users")
      .where("lastSignInAt", ">=", since14d)
      .limit(2000)
      .get();
    const buckets = new Map<string, Set<string>>();
    for (let i = 13; i >= 0; i--) {
      const d = new Date(now.getTime() - i * 24 * 60 * 60 * 1000);
      buckets.set(d.toISOString().slice(0, 10), new Set());
    }
    recent.docs.forEach((doc) => {
      const ls = doc.data().lastSignInAt;
      if (ls && typeof ls.toDate === "function") {
        const dateStr = ls.toDate().toISOString().slice(0, 10);
        const bucket = buckets.get(dateStr);
        if (bucket) bucket.add(doc.id);
      }
    });
    engagement = [...buckets.entries()].map(([date, set]) => ({
      date,
      activeUsers: set.size,
    }));
  } catch {
    engagement = [];
  }

  return {
    totalUsers: usersSnap?.data().count ?? 0,
    newUsers7d: since7dSnap?.data().count ?? 0,
    totalAdmins: adminsSnap?.data().count ?? 0,
    disabledUsers: disabledSnap?.data().count ?? 0,
    totalPlans: plansSnap?.data().count ?? 0,
    totalChatSessions: chatsSnap?.data().count ?? 0,
    byTeam,
    engagement,
    generatedAt: now.toISOString(),
  };
}

/** 최근 활동 N개 (4 컬렉션 병렬 → 시간순 정렬) */
export async function fetchLiveFeed(limit: number = 12): Promise<FeedItem[]> {
  if (!isAdminConfigured()) return [];
  const db = getAdminFirestore();
  const auth = getAdminAuth();

  const [signups, plans, chats, shares] = await Promise.all([
    db
      .collection("users")
      .orderBy("createdAt", "desc")
      .limit(limit)
      .get()
      .catch(() => null),
    db
      .collectionGroup("items")
      .orderBy("createdAt", "desc")
      .limit(limit)
      .get()
      .catch(() => null),
    db
      .collectionGroup("sessions")
      .orderBy("createdAt", "desc")
      .limit(limit)
      .get()
      .catch(() => null),
    db
      .collection("shared_plans")
      .orderBy("createdAt", "desc")
      .limit(limit)
      .get()
      .catch(() => null),
  ]);

  const items: FeedItem[] = [];

  signups?.docs.forEach((d) => {
    const data = d.data();
    items.push({
      type: "signup",
      title: `${data.displayName ?? "신규 회원"} 가입`,
      subtitle: data.email ?? "",
      uid: d.id,
      createdAt: tsToIso(data.createdAt),
    });
  });

  // plans 의 owner uid 는 path 에서 추출 (user_plans/{uid}/items/{planId})
  await Promise.all(
    (plans?.docs ?? []).map(async (d) => {
      const data = d.data();
      const ownerUid = d.ref.parent.parent?.id ?? null;
      let displayName = "회원";
      if (ownerUid) {
        try {
          const u = await auth.getUser(ownerUid);
          displayName = u.displayName ?? u.email?.split("@")[0] ?? "회원";
        } catch {
          /* ignore */
        }
      }
      items.push({
        type: "plan_created",
        title: `${displayName} — 코스 생성`,
        subtitle: (data.name as string) ?? `경기 ${data.gameId ?? ""}`,
        uid: ownerUid,
        createdAt: tsToIso(data.createdAt),
      });
    }),
  );

  chats?.docs.forEach((d) => {
    const data = d.data();
    const ownerUid =
      d.ref.parent.parent?.parent?.parent?.parent?.parent?.id ?? null;
    items.push({
      type: "chat_session",
      title: "AI 챗 세션 시작",
      subtitle: (data.title as string) ?? "",
      uid: ownerUid,
      createdAt: tsToIso(data.createdAt),
    });
  });

  shares?.docs.forEach((d) => {
    const data = d.data();
    items.push({
      type: "shared_plan",
      title: `${data.ownerDisplayName ?? "익명"} — 코스 공유`,
      subtitle: data.title ?? "공유 링크 발행",
      uid: data.ownerUid ?? null,
      createdAt: tsToIso(data.createdAt),
    });
  });

  return items
    .filter((i) => i.createdAt)
    .sort((a, b) => (a.createdAt < b.createdAt ? 1 : -1))
    .slice(0, limit);
}

function tsToIso(ts: unknown): string {
  if (!ts) return new Date(0).toISOString();
  if (typeof ts === "object" && ts !== null && "toDate" in ts) {
    try {
      return (ts as { toDate(): Date }).toDate().toISOString();
    } catch {
      /* ignore */
    }
  }
  return new Date(0).toISOString();
}
