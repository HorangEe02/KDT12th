"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Search, RotateCcw, ShieldOff, ShieldCheck, Edit3, Trash2 } from "lucide-react";
import { apiFetchLunch } from "@/lib/api";
import EditUserModal, { type AdminUser } from "@/components/admin/EditUserModal";

interface UserListResponse {
  total: number;
  offset: number;
  limit: number;
  items: AdminUser[];
}

interface AdminStats {
  total_users: number;
  active_users: number;
  active_admins: number;
}

const PAGE_SIZE = 20;

export default function AdminPage() {
  const qc = useQueryClient();
  const [offset, setOffset] = useState(0);
  const [q, setQ] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [roleFilter, setRoleFilter] = useState<"" | "admin" | "user">("");
  const [activeFilter, setActiveFilter] = useState<"" | "true" | "false">("");
  const [editing, setEditing] = useState<AdminUser | null>(null);

  const stats = useQuery<AdminStats>({
    queryKey: ["admin", "stats"],
    queryFn: () => apiFetchLunch<AdminStats>("/admin/stats"),
    staleTime: 30_000,
  });

  const users = useQuery<UserListResponse>({
    queryKey: ["admin", "users", { offset, q, roleFilter, activeFilter }],
    queryFn: () => {
      const params = new URLSearchParams({
        offset: String(offset),
        limit: String(PAGE_SIZE),
      });
      if (q) params.set("q", q);
      if (roleFilter) params.set("role", roleFilter);
      if (activeFilter) params.set("is_active", activeFilter);
      return apiFetchLunch<UserListResponse>(`/admin/users?${params}`);
    },
  });

  const deactivate = useMutation({
    mutationFn: (id: string) =>
      apiFetchLunch<AdminUser>(`/admin/users/${encodeURIComponent(id)}`, {
        method: "DELETE",
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin"] });
    },
  });

  const restore = useMutation({
    mutationFn: (id: string) =>
      apiFetchLunch<AdminUser>(
        `/admin/users/${encodeURIComponent(id)}/restore`,
        { method: "POST" },
      ),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin"] });
    },
  });

  const hardDelete = useMutation({
    mutationFn: (id: string) =>
      apiFetchLunch<{ ok: boolean; cascaded: Record<string, number> }>(
        `/admin/users/${encodeURIComponent(id)}/permanent`,
        { method: "DELETE" },
      ),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin"] });
    },
    onError: (e: Error) => {
      alert(`영구 삭제 실패: ${e.message}`);
    },
  });

  const confirmHardDelete = (user: AdminUser) => {
    const first = window.confirm(
      `⚠️ 정말로 "${user.name}" (${user.email ?? user.id}) 계정을 영구 삭제하시겠습니까?\n\n` +
      `• 사용자 정보, 투표 기록, 식사 이력, 버디 게시글 등 모든 관련 데이터가 함께 삭제됩니다.\n` +
      `• 이 작업은 되돌릴 수 없습니다.\n\n` +
      `복구가 필요할 수도 있다면 [비활성화]를 사용하세요.`
    );
    if (!first) return;
    const typed = window.prompt(
      `최종 확인: 삭제하려면 사용자 이메일 또는 ID 를 정확히 입력하세요.\n\n` +
      `대상: ${user.email ?? user.id}`
    );
    if (typed === null) return;
    if (typed.trim() !== (user.email ?? user.id).trim()) {
      alert("입력이 일치하지 않아 취소되었습니다.");
      return;
    }
    hardDelete.mutate(user.id);
  };

  const submitSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setQ(searchInput.trim());
    setOffset(0);
  };

  const total = users.data?.total ?? 0;
  const items = users.data?.items ?? [];

  return (
    <>
      <div className="flex items-end justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-heading font-bold text-text-primary tracking-tight">
            관리자 콘솔
          </h1>
          <p className="text-xs text-text-tertiary mt-1" style={{ fontFamily: "var(--font-ko)" }}>
            가입자 조회 · 권한 변경 · 비활성/복원
          </p>
        </div>
        {stats.data && (
          <div className="flex gap-2 text-xs font-mono">
            <span className="px-2 py-1 bg-surface-2 rounded-sm border border-outline/15">
              total <b className="text-text-primary">{stats.data.total_users}</b>
            </span>
            <span className="px-2 py-1 bg-surface-2 rounded-sm border border-outline/15">
              active <b className="text-text-primary">{stats.data.active_users}</b>
            </span>
            <span className="px-2 py-1 bg-surface-2 rounded-sm border border-outline/15">
              admins <b className="text-primary">{stats.data.active_admins}</b>
            </span>
          </div>
        )}
      </div>

      <div className="bg-surface-1 border border-outline/15 rounded-sm p-4 space-y-3">
        <form onSubmit={submitSearch} className="flex gap-2 flex-wrap">
          <div className="flex-1 min-w-[200px] relative">
            <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-text-tertiary" />
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="이름 / 이메일 검색"
              className="w-full pl-8 pr-3 py-2 bg-surface-2 border border-outline/20 rounded-sm text-sm outline-none focus:border-primary/40"
            />
          </div>
          <select
            value={roleFilter}
            onChange={(e) => {
              setRoleFilter(e.target.value as "" | "admin" | "user");
              setOffset(0);
            }}
            className="px-3 py-2 bg-surface-2 border border-outline/20 rounded-sm text-sm font-mono"
          >
            <option value="">all roles</option>
            <option value="admin">admin</option>
            <option value="user">user</option>
          </select>
          <select
            value={activeFilter}
            onChange={(e) => {
              setActiveFilter(e.target.value as "" | "true" | "false");
              setOffset(0);
            }}
            className="px-3 py-2 bg-surface-2 border border-outline/20 rounded-sm text-sm font-mono"
          >
            <option value="">all status</option>
            <option value="true">active</option>
            <option value="false">inactive</option>
          </select>
          <button
            type="submit"
            className="px-4 py-2 bg-primary text-background text-xs font-bold uppercase tracking-wider rounded-sm hover:bg-primary-dark"
          >
            검색
          </button>
        </form>
      </div>

      <div className="bg-surface-1 border border-outline/15 rounded-sm overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-surface-2 text-text-secondary text-[10px] font-bold uppercase tracking-wider">
            <tr>
              <th className="text-left px-3 py-2.5 w-12"></th>
              <th className="text-left px-3 py-2.5">이름</th>
              <th className="text-left px-3 py-2.5">이메일</th>
              <th className="text-left px-3 py-2.5 w-20">역할</th>
              <th className="text-left px-3 py-2.5 w-20">상태</th>
              <th className="text-left px-3 py-2.5 w-32">가입일</th>
              <th className="text-left px-3 py-2.5 w-32">최근 로그인</th>
              <th className="text-right px-3 py-2.5 w-48">동작</th>
            </tr>
          </thead>
          <tbody>
            {users.isLoading && (
              <tr>
                <td colSpan={8} className="text-center py-6 text-text-tertiary text-xs">
                  불러오는 중...
                </td>
              </tr>
            )}
            {users.isError && (
              <tr>
                <td colSpan={8} className="text-center py-6 text-error text-xs">
                  사용자 목록 조회 실패
                </td>
              </tr>
            )}
            {!users.isLoading && items.length === 0 && (
              <tr>
                <td colSpan={8} className="text-center py-6 text-text-tertiary text-xs">
                  결과 없음
                </td>
              </tr>
            )}
            {items.map((u) => (
              <tr key={u.id} className="border-t border-outline/10 hover:bg-surface-2/40">
                <td className="px-3 py-2.5 text-xl">{u.avatar_emoji}</td>
                <td className="px-3 py-2.5">
                  <div className="text-text-primary">{u.name}</div>
                  <div className="text-[10px] text-text-tertiary font-mono">{u.id}</div>
                </td>
                <td className="px-3 py-2.5 font-mono text-xs">{u.email ?? "—"}</td>
                <td className="px-3 py-2.5">
                  <span
                    className={`px-1.5 py-0.5 rounded-sm text-[10px] font-bold uppercase ${
                      u.role === "admin"
                        ? "bg-primary/20 text-primary"
                        : "bg-surface-2 text-text-secondary"
                    }`}
                  >
                    {u.role}
                  </span>
                </td>
                <td className="px-3 py-2.5">
                  <span
                    className={`px-1.5 py-0.5 rounded-sm text-[10px] font-bold uppercase ${
                      u.is_active ? "bg-success/20 text-success" : "bg-error/20 text-error"
                    }`}
                  >
                    {u.is_active ? "active" : "inactive"}
                  </span>
                </td>
                <td className="px-3 py-2.5 text-[11px] font-mono text-text-tertiary">
                  {u.created_at?.slice(0, 10) ?? "—"}
                </td>
                <td className="px-3 py-2.5 text-[11px] font-mono text-text-tertiary">
                  {u.last_login_at?.slice(0, 10) ?? "—"}
                </td>
                <td className="px-3 py-2.5 text-right space-x-1">
                  <button
                    onClick={() => setEditing(u)}
                    title="편집"
                    className="p-1.5 bg-surface-2 rounded-sm text-text-secondary hover:text-primary hover:bg-primary/10"
                  >
                    <Edit3 size={14} />
                  </button>
                  {u.is_active ? (
                    <button
                      onClick={() => {
                        if (confirm(`"${u.name}" 계정을 비활성화할까요?\n(데이터는 보존, 복원 가능)`)) {
                          deactivate.mutate(u.id);
                        }
                      }}
                      title="비활성 (soft delete)"
                      className="p-1.5 bg-surface-2 rounded-sm text-text-secondary hover:text-error hover:bg-error/10"
                    >
                      <ShieldOff size={14} />
                    </button>
                  ) : (
                    <button
                      onClick={() => restore.mutate(u.id)}
                      title="복원"
                      className="p-1.5 bg-surface-2 rounded-sm text-text-secondary hover:text-success hover:bg-success/10"
                    >
                      <ShieldCheck size={14} />
                    </button>
                  )}
                  <button
                    onClick={() => confirmHardDelete(u)}
                    title="영구 삭제 (복구 불가)"
                    disabled={hardDelete.isPending}
                    className="p-1.5 bg-surface-2 rounded-sm text-text-tertiary hover:text-error hover:bg-error/20 disabled:opacity-40"
                  >
                    <Trash2 size={14} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between text-xs">
        <div className="text-text-tertiary font-mono">
          {total > 0 ? `${offset + 1}–${Math.min(offset + PAGE_SIZE, total)} / ${total}` : "0"}
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
            disabled={offset === 0}
            className="px-3 py-1.5 bg-surface-2 border border-outline/20 rounded-sm text-xs disabled:opacity-40"
          >
            ← 이전
          </button>
          <button
            onClick={() => setOffset(offset + PAGE_SIZE)}
            disabled={offset + PAGE_SIZE >= total}
            className="px-3 py-1.5 bg-surface-2 border border-outline/20 rounded-sm text-xs disabled:opacity-40"
          >
            다음 →
          </button>
          <button
            onClick={() => users.refetch()}
            className="p-1.5 bg-surface-2 border border-outline/20 rounded-sm text-text-tertiary hover:text-primary"
            title="새로고침"
          >
            <RotateCcw size={14} />
          </button>
        </div>
      </div>

      {editing && (
        <EditUserModal
          user={editing}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null);
            qc.invalidateQueries({ queryKey: ["admin"] });
          }}
        />
      )}
    </>
  );
}
