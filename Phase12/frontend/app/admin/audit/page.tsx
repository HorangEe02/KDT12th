import { getAdminFirestore, isAdminConfigured } from "@/lib/firebase/admin";
import { cn } from "@/lib/utils";

export const dynamic = "force-dynamic";

interface AuditEntry {
  id: string;
  adminEmail: string;
  action: string;
  targetEmail: string;
  reason: string;
  createdAt: string | null;
}

const ACTION_META: Record<string, { label: string; tone: string }> = {
  grant_admin: { label: "관리자 부여", tone: "bg-se-secondary-container text-se-on-secondary-container" },
  revoke_admin: { label: "관리자 회수", tone: "bg-amber-100 text-amber-900" },
  disable_user: { label: "계정 비활성화", tone: "bg-red-100 text-red-900" },
  enable_user: { label: "계정 활성화", tone: "bg-emerald-100 text-emerald-900" },
  delete_user: { label: "계정 삭제", tone: "bg-red-200 text-red-900" },
  reset_password: {
    label: "비밀번호 재설정 발송",
    tone: "bg-blue-100 text-blue-900",
  },
};

async function fetchAudit(limit: number = 50): Promise<AuditEntry[]> {
  if (!isAdminConfigured()) return [];
  const db = getAdminFirestore();
  const snap = await db
    .collection("admin_audit")
    .orderBy("createdAt", "desc")
    .limit(limit)
    .get()
    .catch(() => null);
  if (!snap) return [];
  return snap.docs.map((d) => {
    const data = d.data();
    let createdAt: string | null = null;
    if (data.createdAt && typeof data.createdAt.toDate === "function") {
      try {
        createdAt = data.createdAt.toDate().toISOString();
      } catch {
        /* ignore */
      }
    }
    return {
      id: d.id,
      adminEmail: data.adminEmail ?? "system",
      action: data.action ?? "unknown",
      targetEmail: data.targetEmail ?? "—",
      reason: data.reason ?? "",
      createdAt,
    };
  });
}

export default async function AuditPage() {
  const entries = await fetchAudit(50);

  return (
    <section className="flex flex-col gap-6">
      <header>
        <h1 className="font-display text-3xl font-extrabold tracking-tight text-se-on-surface">
          감사 로그
        </h1>
        <p className="mt-1 font-medium text-se-on-surface-variant">
          관리자 액션 (권한 변경 · 계정 비활성/삭제 등) 기록 — 최근 50건
        </p>
      </header>

      {entries.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-se-outline-variant bg-white p-8 text-center text-sm text-se-on-surface-variant">
          기록된 감사 이벤트가 없습니다.
        </div>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-se-outline-variant bg-white shadow-[0_4px_24px_rgba(0,0,0,0.02)]">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-se-surface-container-low text-left">
                <tr className="text-xs font-display font-bold uppercase tracking-wider text-se-on-surface-variant">
                  <th className="px-4 py-3">시간</th>
                  <th className="px-4 py-3">관리자</th>
                  <th className="px-4 py-3">액션</th>
                  <th className="px-4 py-3">대상</th>
                  <th className="px-4 py-3">사유</th>
                </tr>
              </thead>
              <tbody>
                {entries.map((e) => {
                  const m = ACTION_META[e.action] ?? {
                    label: e.action,
                    tone: "bg-se-surface-container text-se-on-surface-variant",
                  };
                  return (
                    <tr
                      key={e.id}
                      className="border-t border-se-outline-variant/60 align-top"
                    >
                      <td className="px-4 py-3 text-xs text-se-on-surface-variant">
                        {e.createdAt
                          ? new Date(e.createdAt).toLocaleString("ko-KR")
                          : "—"}
                      </td>
                      <td className="px-4 py-3 text-xs text-se-on-surface">
                        {e.adminEmail}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={cn(
                            "inline-block rounded-full px-2 py-0.5 text-[0.65rem] font-bold",
                            m.tone,
                          )}
                        >
                          {m.label}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-xs text-se-on-surface">
                        {e.targetEmail}
                      </td>
                      <td className="px-4 py-3 text-xs text-se-on-surface-variant">
                        {e.reason}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </section>
  );
}
