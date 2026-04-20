/**
 * Admin server-side user management — Firebase Admin SDK 기반.
 * 호출처: app/api/admin/users/* 라우트, app/admin/* RSC.
 * 모든 함수는 호출 전에 requireAdmin() 으로 보호 필요.
 */
import "server-only";
import { getAdminAuth, getAdminFirestore, isAdminConfigured } from "./admin";
import { logAuditEvent } from "./server-session";
import type { Timestamp } from "firebase-admin/firestore";
import type { AdminAction } from "@/lib/types/user";

const USERS = "users";

export interface UserListItem {
  uid: string;
  email: string;
  displayName: string;
  photoURL: string | null;
  role: "user" | "admin";
  status: "active" | "disabled";
  favoriteTeam: string | null;
  createdAt: string | null;
  lastSignInAt: string | null;
  stats?: {
    visitedCount?: number;
    planCount?: number;
    chatSessionCount?: number;
  };
}

export interface UserListPage {
  items: UserListItem[];
  nextCursor: string | null;
  total: number;
}

function tsToIso(v: Timestamp | Date | null | undefined): string | null {
  if (!v) return null;
  if (v instanceof Date) return v.toISOString();
  if (typeof v === "object" && "toDate" in v && typeof v.toDate === "function") {
    try {
      return v.toDate().toISOString();
    } catch {
      return null;
    }
  }
  return null;
}

/**
 * Firestore users 컬렉션 페이지네이션 조회.
 * filter: role/status/favoriteTeam, search: email prefix.
 * cursor: 마지막 도큐먼트 createdAt ISO (epoch ms 형식)
 */
export async function listUsers(opts: {
  pageSize?: number;
  cursor?: string | null;
  role?: "user" | "admin";
  status?: "active" | "disabled";
  search?: string;
}): Promise<UserListPage> {
  if (!isAdminConfigured()) {
    return { items: [], nextCursor: null, total: 0 };
  }
  const db = getAdminFirestore();
  const pageSize = Math.min(Math.max(opts.pageSize ?? 25, 1), 100);

  let q = db.collection(USERS).orderBy("createdAt", "desc");
  if (opts.role) q = q.where("role", "==", opts.role);
  if (opts.status) q = q.where("status", "==", opts.status);

  if (opts.cursor) {
    const cursorMs = Number.parseInt(opts.cursor, 10);
    if (Number.isFinite(cursorMs)) {
      q = q.startAfter(new Date(cursorMs));
    }
  }

  const snap = await q.limit(pageSize + 1).get();
  let docs = snap.docs;

  // 검색 필터 (post-filter — Firestore prefix 한계)
  if (opts.search) {
    const needle = opts.search.toLowerCase();
    docs = docs.filter((d) => {
      const data = d.data();
      const email = String(data.email ?? "").toLowerCase();
      const name = String(data.displayName ?? "").toLowerCase();
      return email.includes(needle) || name.includes(needle);
    });
  }

  const hasMore = docs.length > pageSize;
  const sliced = hasMore ? docs.slice(0, pageSize) : docs;
  const items: UserListItem[] = sliced.map((d) => {
    const data = d.data();
    return {
      uid: d.id,
      email: data.email ?? "",
      displayName: data.displayName ?? "사용자",
      photoURL: data.photoURL ?? null,
      role: data.role === "admin" ? "admin" : "user",
      status: data.status === "disabled" ? "disabled" : "active",
      favoriteTeam: data.favoriteTeam ?? null,
      createdAt: tsToIso(data.createdAt),
      lastSignInAt: tsToIso(data.lastSignInAt),
      stats: {
        visitedCount: data.stats?.visitedCount ?? 0,
        planCount: data.stats?.planCount ?? 0,
        chatSessionCount: data.stats?.chatSessionCount ?? 0,
      },
    };
  });

  let nextCursor: string | null = null;
  if (hasMore) {
    const last = sliced[sliced.length - 1].data();
    const lastCreated = last.createdAt;
    if (lastCreated && typeof lastCreated === "object" && "toMillis" in lastCreated) {
      nextCursor = String((lastCreated as Timestamp).toMillis());
    }
  }

  // count() 는 read 1만 사용 (Firestore optimization)
  let total = items.length;
  try {
    const cnt = await db.collection(USERS).count().get();
    total = cnt.data().count;
  } catch {
    /* fallback: items.length */
  }

  return { items, nextCursor, total };
}

export async function getUserDetail(uid: string): Promise<UserListItem | null> {
  if (!isAdminConfigured()) return null;
  const db = getAdminFirestore();
  const snap = await db.collection(USERS).doc(uid).get();
  if (!snap.exists) return null;
  const data = snap.data() ?? {};
  return {
    uid,
    email: data.email ?? "",
    displayName: data.displayName ?? "사용자",
    photoURL: data.photoURL ?? null,
    role: data.role === "admin" ? "admin" : "user",
    status: data.status === "disabled" ? "disabled" : "active",
    favoriteTeam: data.favoriteTeam ?? null,
    createdAt: tsToIso(data.createdAt),
    lastSignInAt: tsToIso(data.lastSignInAt),
    stats: {
      visitedCount: data.stats?.visitedCount ?? 0,
      planCount: data.stats?.planCount ?? 0,
      chatSessionCount: data.stats?.chatSessionCount ?? 0,
    },
  };
}

/** role 변경 — Custom Claim + Firestore 업데이트 + Audit */
export async function patchUserRole(args: {
  targetUid: string;
  newRole: "user" | "admin";
  adminUid: string;
  adminEmail: string;
  reason: string;
}): Promise<{ ok: true } | { ok: false; error: string }> {
  if (!isAdminConfigured()) return { ok: false, error: "Admin SDK 미구성" };
  try {
    const auth = getAdminAuth();
    const db = getAdminFirestore();
    const targetUser = await auth.getUser(args.targetUid);

    const newClaims =
      args.newRole === "admin"
        ? { ...(targetUser.customClaims ?? {}), admin: true, role: "admin" }
        : { ...(targetUser.customClaims ?? {}), admin: false, role: "user" };
    await auth.setCustomUserClaims(args.targetUid, newClaims);
    await auth.revokeRefreshTokens(args.targetUid);

    await db.collection(USERS).doc(args.targetUid).update({
      role: args.newRole,
      lastActiveAt: new Date(),
    });

    await logAuditEvent({
      adminUid: args.adminUid,
      adminEmail: args.adminEmail,
      action: (args.newRole === "admin" ? "grant_admin" : "revoke_admin") satisfies AdminAction,
      targetUid: args.targetUid,
      targetEmail: targetUser.email ?? "",
      reason: args.reason,
    });

    return { ok: true };
  } catch (err) {
    const msg = err instanceof Error ? err.message : "patchUserRole failed";
    return { ok: false, error: msg };
  }
}

/** active/disabled 토글 — Firebase Auth disabled flag + Firestore + claims */
export async function patchUserStatus(args: {
  targetUid: string;
  newStatus: "active" | "disabled";
  adminUid: string;
  adminEmail: string;
  reason: string;
}): Promise<{ ok: true } | { ok: false; error: string }> {
  if (!isAdminConfigured()) return { ok: false, error: "Admin SDK 미구성" };
  try {
    const auth = getAdminAuth();
    const db = getAdminFirestore();
    const targetUser = await auth.getUser(args.targetUid);

    const disabled = args.newStatus === "disabled";
    await auth.updateUser(args.targetUid, { disabled });
    const claims = { ...(targetUser.customClaims ?? {}), disabled };
    await auth.setCustomUserClaims(args.targetUid, claims);
    if (disabled) await auth.revokeRefreshTokens(args.targetUid);

    await db.collection(USERS).doc(args.targetUid).update({
      status: args.newStatus,
    });

    await logAuditEvent({
      adminUid: args.adminUid,
      adminEmail: args.adminEmail,
      action: (disabled ? "disable_user" : "enable_user") satisfies AdminAction,
      targetUid: args.targetUid,
      targetEmail: targetUser.email ?? "",
      reason: args.reason,
    });

    return { ok: true };
  } catch (err) {
    const msg = err instanceof Error ? err.message : "patchUserStatus failed";
    return { ok: false, error: msg };
  }
}

export async function deleteUserAccount(args: {
  targetUid: string;
  adminUid: string;
  adminEmail: string;
  reason: string;
}): Promise<{ ok: true } | { ok: false; error: string }> {
  if (!isAdminConfigured()) return { ok: false, error: "Admin SDK 미구성" };
  try {
    const auth = getAdminAuth();
    const db = getAdminFirestore();
    const targetUser = await auth.getUser(args.targetUid);
    await auth.deleteUser(args.targetUid);

    // Cascade — 본인 데이터 삭제 (best effort)
    const refs = [
      db.collection(USERS).doc(args.targetUid),
      db.collection("user_visits").doc(args.targetUid),
      db.collection("user_prefs").doc(args.targetUid),
    ];
    await Promise.all(refs.map((r) => r.delete().catch(() => null)));

    await logAuditEvent({
      adminUid: args.adminUid,
      adminEmail: args.adminEmail,
      action: "delete_user" satisfies AdminAction,
      targetUid: args.targetUid,
      targetEmail: targetUser.email ?? "",
      reason: args.reason,
    });
    return { ok: true };
  } catch (err) {
    const msg = err instanceof Error ? err.message : "deleteUserAccount failed";
    return { ok: false, error: msg };
  }
}
