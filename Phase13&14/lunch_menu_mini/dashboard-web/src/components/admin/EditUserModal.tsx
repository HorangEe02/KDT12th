"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { X, Save, Loader2 } from "lucide-react";
import { apiFetchLunch } from "@/lib/api";

export interface AdminUser {
  id: string;
  name: string;
  email: string | null;
  role: "admin" | "user";
  team_id: string;
  avatar_emoji: string;
  is_active: boolean;
  created_at: string | null;
  updated_at: string | null;
  last_login_at: string | null;
  dislike_categories?: string | null;
  allergy_info?: string | null;
}

interface EditUserModalProps {
  user: AdminUser;
  onClose: () => void;
  onSaved: () => void;
}

export default function EditUserModal({ user, onClose, onSaved }: EditUserModalProps) {
  const [name, setName] = useState(user.name);
  const [email, setEmail] = useState(user.email ?? "");
  const [role, setRole] = useState<"admin" | "user">(user.role);
  const [team, setTeam] = useState(user.team_id);
  const [avatar, setAvatar] = useState(user.avatar_emoji);
  const [newPassword, setNewPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  const save = useMutation({
    mutationFn: async () => {
      const body: Record<string, unknown> = {};
      if (name !== user.name) body.name = name;
      if (email !== (user.email ?? "")) body.email = email || null;
      if (role !== user.role) body.role = role;
      if (team !== user.team_id) body.team_id = team;
      if (avatar !== user.avatar_emoji) body.avatar_emoji = avatar;
      if (newPassword) {
        if (newPassword.length < 8)
          throw new Error("비밀번호는 8자 이상이어야 합니다.");
        body.new_password = newPassword;
      }
      if (Object.keys(body).length === 0) {
        throw new Error("변경 사항 없음");
      }
      return apiFetchLunch<AdminUser>(`/admin/users/${encodeURIComponent(user.id)}`, {
        method: "PATCH",
        body: JSON.stringify(body),
      });
    },
    onSuccess: () => {
      onSaved();
    },
    onError: (e: Error) => setError(e.message),
  });

  const labelClass =
    "block text-[10px] font-bold uppercase tracking-wider text-text-secondary mb-1";
  const inputClass =
    "w-full bg-surface-2 border border-outline/20 px-2.5 py-2 text-sm text-text-primary rounded-sm outline-none focus:border-primary/40";

  return (
    <div
      className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-surface-1 border border-outline/15 rounded-sm p-6 w-full max-w-md max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-heading font-bold text-text-primary">
            사용자 편집
          </h2>
          <button onClick={onClose} className="text-text-tertiary hover:text-text-primary">
            <X size={20} />
          </button>
        </div>

        <div className="text-[11px] font-mono text-text-tertiary mb-4">
          id: {user.id}
        </div>

        <div className="space-y-3">
          <div>
            <label className={labelClass}>이름</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className={inputClass}
              style={{ fontFamily: "var(--font-ko)" }}
            />
          </div>

          <div>
            <label className={labelClass}>이메일</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="없음 (게스트)"
              className={`${inputClass} font-mono`}
            />
          </div>

          <div>
            <label className={labelClass}>역할</label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value as "admin" | "user")}
              className={`${inputClass} font-mono`}
            >
              <option value="user">user</option>
              <option value="admin">admin</option>
            </select>
            {user.role === "admin" && role !== "admin" && (
              <p className="text-[10px] text-warning mt-1">
                ⚠ 마지막 admin 강등은 백엔드가 차단합니다.
              </p>
            )}
          </div>

          <div>
            <label className={labelClass}>팀</label>
            <input
              type="text"
              value={team}
              onChange={(e) => setTeam(e.target.value)}
              className={`${inputClass} font-mono`}
            />
          </div>

          <div>
            <label className={labelClass}>아바타</label>
            <input
              type="text"
              value={avatar}
              onChange={(e) => setAvatar(e.target.value)}
              className={`${inputClass} text-center text-xl`}
              maxLength={10}
            />
          </div>

          <div className="pt-3 border-t border-outline/10">
            <label className={labelClass}>비밀번호 재설정 (선택)</label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="비워두면 변경 안 함 (8자+)"
              className={`${inputClass} font-mono`}
            />
            <p className="text-[10px] text-text-tertiary mt-1">
              관리자 권한으로 임시 비밀번호 설정. 사용자에게 안전하게 전달 필요.
            </p>
          </div>

          {error && <div className="text-xs text-error font-mono">{error}</div>}
        </div>

        <div className="flex gap-2 mt-5 pt-3 border-t border-outline/10">
          <button
            onClick={onClose}
            className="flex-1 py-2.5 bg-surface-2 border border-outline/20 text-text-secondary text-xs font-bold uppercase tracking-wider rounded-sm hover:text-text-primary"
          >
            취소
          </button>
          <button
            onClick={() => save.mutate()}
            disabled={save.isPending}
            className="flex-1 py-2.5 bg-primary text-background text-xs font-bold uppercase tracking-wider rounded-sm hover:bg-primary-dark disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {save.isPending ? (
              <>
                <Loader2 size={14} className="animate-spin" />
                저장 중...
              </>
            ) : (
              <>
                <Save size={14} />
                저장
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
