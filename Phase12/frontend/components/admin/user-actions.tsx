"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { useAuthUser } from "@/lib/store/auth";

interface UserActionsProps {
  targetUid: string;
  targetEmail: string;
  currentRole: "user" | "admin";
  currentStatus: "active" | "disabled";
}

export function UserActions({
  targetUid,
  targetEmail,
  currentRole,
  currentStatus,
}: UserActionsProps) {
  const router = useRouter();
  const me = useAuthUser();
  const isSelf = me?.uid === targetUid;
  const [busy, setBusy] = useState<null | "role" | "status" | "delete">(null);

  async function withReason(promptText: string): Promise<string | null> {
    const reason = window.prompt(`${promptText}\n\n사유를 입력해 주세요 (감사 로그에 기록됩니다):`);
    if (reason === null) return null;
    if (reason.trim().length < 2) {
      toast.error("사유는 2자 이상 입력해 주세요.");
      return null;
    }
    return reason.trim();
  }

  async function onToggleRole() {
    if (isSelf && currentRole === "admin") {
      toast.error("본인의 관리자 권한은 회수할 수 없습니다.");
      return;
    }
    const newRole = currentRole === "admin" ? "user" : "admin";
    const reason = await withReason(
      `${targetEmail} 의 권한을 ${newRole === "admin" ? "관리자로" : "일반 회원으로"} 변경합니다.`,
    );
    if (reason === null) return;
    setBusy("role");
    try {
      const res = await fetch(`/api/admin/users/${targetUid}/role`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ role: newRole, reason }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? "변경 실패");
      toast.success("권한 변경 완료 — 대상자는 다음 로그인 시 반영됩니다.");
      router.refresh();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "오류");
    } finally {
      setBusy(null);
    }
  }

  async function onToggleStatus() {
    if (isSelf) {
      toast.error("본인 계정 상태는 변경할 수 없습니다.");
      return;
    }
    const newStatus = currentStatus === "active" ? "disabled" : "active";
    const reason = await withReason(
      `${targetEmail} 계정을 ${newStatus === "disabled" ? "비활성화" : "활성화"}합니다.`,
    );
    if (reason === null) return;
    setBusy("status");
    try {
      const res = await fetch(`/api/admin/users/${targetUid}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus, reason }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? "변경 실패");
      toast.success(
        newStatus === "disabled" ? "계정 비활성화됨" : "계정 활성화됨",
      );
      router.refresh();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "오류");
    } finally {
      setBusy(null);
    }
  }

  async function onDelete() {
    if (isSelf) {
      toast.error("본인 계정은 삭제할 수 없습니다.");
      return;
    }
    const confirmText = window.prompt(
      `⚠ ${targetEmail} 계정을 영구 삭제합니다.\n\n계정 데이터(prefs, visits, plans)도 함께 삭제되며 복구 불가합니다.\n\n계속하려면 이메일을 정확히 입력하세요:`,
    );
    if (confirmText === null) return;
    if (confirmText !== targetEmail) {
      toast.error("이메일이 일치하지 않습니다. 취소되었습니다.");
      return;
    }
    const reason = await withReason("삭제 사유");
    if (reason === null) return;
    setBusy("delete");
    try {
      const res = await fetch(`/api/admin/users/${targetUid}`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? "삭제 실패");
      toast.success("계정 삭제 완료");
      router.replace("/admin/users");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "오류");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="flex flex-wrap gap-2">
      <ActionButton
        icon={currentRole === "admin" ? "remove_moderator" : "shield_person"}
        label={currentRole === "admin" ? "관리자 회수" : "관리자 부여"}
        onClick={onToggleRole}
        disabled={busy !== null || (isSelf && currentRole === "admin")}
        loading={busy === "role"}
        variant={currentRole === "admin" ? "warning" : "primary"}
      />
      <ActionButton
        icon={currentStatus === "active" ? "block" : "check_circle"}
        label={currentStatus === "active" ? "계정 비활성화" : "계정 활성화"}
        onClick={onToggleStatus}
        disabled={busy !== null || isSelf}
        loading={busy === "status"}
        variant={currentStatus === "active" ? "warning" : "secondary"}
      />
      <ActionButton
        icon="delete_forever"
        label="계정 삭제"
        onClick={onDelete}
        disabled={busy !== null || isSelf}
        loading={busy === "delete"}
        variant="danger"
      />
    </div>
  );
}

function ActionButton({
  icon,
  label,
  onClick,
  disabled,
  loading,
  variant,
}: {
  icon: string;
  label: string;
  onClick: () => void;
  disabled?: boolean;
  loading?: boolean;
  variant: "primary" | "secondary" | "warning" | "danger";
}) {
  const tone =
    variant === "primary"
      ? "border-se-primary bg-se-primary text-white hover:opacity-90"
      : variant === "secondary"
        ? "border-se-secondary bg-se-secondary text-white hover:opacity-90"
        : variant === "warning"
          ? "border-amber-400 bg-amber-50 text-amber-900 hover:bg-amber-100"
          : "border-red-300 bg-red-50 text-red-900 hover:bg-red-100";
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-xl border px-3 py-2 font-display text-xs font-bold transition-colors disabled:cursor-not-allowed disabled:opacity-50",
        tone,
      )}
    >
      <span className="material-symbols-outlined text-[16px]">
        {loading ? "progress_activity" : icon}
      </span>
      {label}
    </button>
  );
}
