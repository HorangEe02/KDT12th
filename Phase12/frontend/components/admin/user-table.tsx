"use client";

import Link from "next/link";
import { useSearchParams, usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import type { UserListItem } from "@/lib/firebase/admin-users";

interface UserTableProps {
  items: UserListItem[];
  nextCursor: string | null;
  currentSearch: string;
  currentRole?: "user" | "admin";
  currentStatus?: "active" | "disabled";
}

export function UserTable({
  items,
  nextCursor,
  currentSearch,
  currentRole,
  currentStatus,
}: UserTableProps) {
  const pathname = usePathname();
  const searchParams = useSearchParams();

  function buildHref(extra: Record<string, string | null>): string {
    const p = new URLSearchParams(searchParams.toString());
    for (const [k, v] of Object.entries(extra)) {
      if (v === null) p.delete(k);
      else p.set(k, v);
    }
    return `${pathname}?${p.toString()}`;
  }

  if (items.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-se-outline-variant bg-white p-8 text-center text-sm text-se-on-surface-variant">
        조건에 맞는 회원이 없습니다.
        {currentSearch || currentRole || currentStatus ? (
          <Link
            href={pathname}
            className="ml-2 font-display font-bold text-se-primary hover:underline"
          >
            필터 초기화
          </Link>
        ) : null}
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-se-outline-variant bg-white shadow-[0_4px_24px_rgba(0,0,0,0.02)]">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-se-surface-container-low text-left">
            <tr className="text-xs font-display font-bold uppercase tracking-wider text-se-on-surface-variant">
              <th className="px-4 py-3">회원</th>
              <th className="px-4 py-3 hidden md:table-cell">응원팀</th>
              <th className="px-4 py-3 hidden lg:table-cell">가입일</th>
              <th className="px-4 py-3 hidden lg:table-cell">최근 접속</th>
              <th className="px-4 py-3">권한</th>
              <th className="px-4 py-3">상태</th>
              <th className="px-4 py-3 text-right">활동</th>
            </tr>
          </thead>
          <tbody>
            {items.map((u) => (
              <tr
                key={u.uid}
                className="border-t border-se-outline-variant/60 transition-colors hover:bg-se-surface-container-low"
              >
                <td className="px-4 py-3">
                  <Link href={`/admin/users/${u.uid}`} className="flex items-center gap-3">
                    {u.photoURL ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={u.photoURL}
                        alt=""
                        className="h-8 w-8 rounded-full object-cover"
                        referrerPolicy="no-referrer"
                      />
                    ) : (
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-se-primary text-white font-display text-xs font-bold">
                        {u.displayName.slice(0, 1).toUpperCase()}
                      </div>
                    )}
                    <div className="min-w-0">
                      <div className="truncate font-bold text-se-on-surface">
                        {u.displayName}
                      </div>
                      <div className="truncate text-xs text-se-on-surface-variant">
                        {u.email}
                      </div>
                    </div>
                  </Link>
                </td>
                <td className="px-4 py-3 hidden md:table-cell text-se-on-surface-variant">
                  {u.favoriteTeam ?? "—"}
                </td>
                <td className="px-4 py-3 hidden lg:table-cell text-xs text-se-on-surface-variant">
                  {u.createdAt
                    ? new Date(u.createdAt).toLocaleDateString("ko-KR")
                    : "—"}
                </td>
                <td className="px-4 py-3 hidden lg:table-cell text-xs text-se-on-surface-variant">
                  {u.lastSignInAt
                    ? new Date(u.lastSignInAt).toLocaleDateString("ko-KR")
                    : "—"}
                </td>
                <td className="px-4 py-3">
                  <RoleBadge role={u.role} />
                </td>
                <td className="px-4 py-3">
                  <StatusBadge status={u.status} />
                </td>
                <td className="px-4 py-3 text-right">
                  <Link
                    href={`/admin/users/${u.uid}`}
                    className="inline-flex items-center gap-1 rounded-lg border border-se-outline-variant bg-white px-2.5 py-1 text-xs font-bold text-se-on-surface hover:border-se-primary"
                  >
                    상세
                    <span className="material-symbols-outlined text-[14px]">
                      chevron_right
                    </span>
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination — cursor 기반 */}
      <div className="flex items-center justify-between border-t border-se-outline-variant bg-se-surface-container-low px-4 py-3 text-xs text-se-on-surface-variant">
        <span>{items.length}건 표시</span>
        <div className="flex gap-2">
          {searchParams.get("cursor") ? (
            <Link
              href={buildHref({ cursor: null })}
              className="rounded-lg border border-se-outline-variant bg-white px-3 py-1.5 font-bold text-se-on-surface hover:border-se-primary"
            >
              ← 처음
            </Link>
          ) : null}
          {nextCursor ? (
            <Link
              href={buildHref({ cursor: nextCursor })}
              className="rounded-lg border border-se-primary bg-se-primary px-3 py-1.5 font-bold text-white hover:opacity-90"
            >
              다음 →
            </Link>
          ) : null}
        </div>
      </div>
    </div>
  );
}

function RoleBadge({ role }: { role: "user" | "admin" }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[0.65rem] font-bold",
        role === "admin"
          ? "bg-se-secondary-container text-se-on-secondary-container"
          : "bg-se-surface-container text-se-on-surface-variant",
      )}
    >
      {role === "admin" ? "🛡 관리자" : "👤 회원"}
    </span>
  );
}

function StatusBadge({ status }: { status: "active" | "disabled" }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[0.65rem] font-bold",
        status === "active"
          ? "bg-emerald-100 text-emerald-900"
          : "bg-red-100 text-red-900",
      )}
    >
      {status === "active" ? "● 활성" : "○ 비활성"}
    </span>
  );
}
