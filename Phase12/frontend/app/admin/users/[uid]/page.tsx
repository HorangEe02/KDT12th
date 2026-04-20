import Link from "next/link";
import { notFound } from "next/navigation";
import { getUserDetail } from "@/lib/firebase/admin-users";
import { UserActions } from "@/components/admin/user-actions";

export const dynamic = "force-dynamic";

interface UserDetailPageProps {
  params: Promise<{ uid: string }>;
}

export default async function UserDetailPage({ params }: UserDetailPageProps) {
  const { uid } = await params;
  const user = await getUserDetail(uid);
  if (!user) notFound();

  const initial = user.displayName.slice(0, 1).toUpperCase();
  const ageDays = user.createdAt
    ? Math.floor(
        (Date.now() - new Date(user.createdAt).getTime()) / (24 * 60 * 60 * 1000),
      )
    : null;

  return (
    <section className="flex flex-col gap-6">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm text-se-on-surface-variant">
        <Link
          href="/admin/users"
          className="inline-flex items-center gap-1 font-display font-bold hover:text-se-primary"
        >
          <span className="material-symbols-outlined text-[18px]">arrow_back</span>
          회원 목록
        </Link>
        <span>/</span>
        <span className="truncate font-bold text-se-on-surface">
          {user.displayName}
        </span>
      </nav>

      {/* Profile header */}
      <header className="flex flex-col gap-4 rounded-[1.5rem] bg-se-surface-container-lowest p-6 shadow-[0_4px_24px_rgba(0,0,0,0.02)] md:flex-row md:items-center md:justify-between md:p-8">
        <div className="flex items-center gap-5">
          {user.photoURL ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={user.photoURL}
              alt={user.displayName}
              className="h-16 w-16 rounded-full object-cover ring-2 ring-se-outline-variant"
              referrerPolicy="no-referrer"
            />
          ) : (
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-se-primary text-white font-display text-2xl font-extrabold">
              {initial}
            </div>
          )}
          <div className="min-w-0">
            <h1 className="font-display text-2xl font-extrabold text-se-on-surface">
              {user.displayName}
            </h1>
            <div className="mt-1 truncate text-sm text-se-on-surface-variant">
              {user.email}
            </div>
            <div className="mt-2 flex flex-wrap gap-2 text-[0.65rem]">
              <Pill
                tone={user.role === "admin" ? "secondary" : "neutral"}
                text={user.role === "admin" ? "🛡 관리자" : "👤 회원"}
              />
              <Pill
                tone={user.status === "active" ? "success" : "danger"}
                text={user.status === "active" ? "● 활성" : "○ 비활성"}
              />
              {user.favoriteTeam ? (
                <Pill tone="primary" text={`⚾ ${user.favoriteTeam}`} />
              ) : null}
            </div>
          </div>
        </div>
        <UserActions
          targetUid={user.uid}
          targetEmail={user.email}
          currentRole={user.role}
          currentStatus={user.status}
        />
      </header>

      {/* Stats grid */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard
          icon="cake"
          label="가입한 지"
          value={ageDays !== null ? `${ageDays}일` : "—"}
          hint={
            user.createdAt
              ? new Date(user.createdAt).toLocaleDateString("ko-KR")
              : ""
          }
        />
        <StatCard
          icon="schedule"
          label="최근 접속"
          value={
            user.lastSignInAt
              ? new Date(user.lastSignInAt).toLocaleDateString("ko-KR")
              : "—"
          }
          hint={
            user.lastSignInAt
              ? new Date(user.lastSignInAt).toLocaleTimeString("ko-KR")
              : ""
          }
        />
        <StatCard
          icon="stadium"
          label="방문 구장"
          value={`${user.stats?.visitedCount ?? 0} / 10`}
          hint="Stadium Tour"
        />
        <StatCard
          icon="confirmation_number"
          label="저장한 코스"
          value={`${user.stats?.planCount ?? 0}건`}
          hint={`AI 챗 ${user.stats?.chatSessionCount ?? 0}회`}
        />
      </div>

      {/* Meta panel */}
      <div className="rounded-[1.5rem] bg-se-surface-container-lowest p-6 shadow-[0_4px_24px_rgba(0,0,0,0.02)] md:p-8">
        <h3 className="mb-4 font-display text-lg font-bold text-se-on-surface">
          식별 정보
        </h3>
        <dl className="grid grid-cols-1 gap-3 text-sm md:grid-cols-2">
          <Field label="UID" value={user.uid} mono />
          <Field label="이메일" value={user.email} />
          <Field label="닉네임" value={user.displayName} />
          <Field label="응원팀" value={user.favoriteTeam ?? "—"} />
          <Field
            label="권한"
            value={user.role === "admin" ? "관리자" : "회원"}
          />
          <Field
            label="상태"
            value={user.status === "active" ? "활성" : "비활성"}
          />
        </dl>
      </div>
    </section>
  );
}

function Pill({
  tone,
  text,
}: {
  tone: "neutral" | "success" | "danger" | "primary" | "secondary";
  text: string;
}) {
  const cls =
    tone === "success"
      ? "bg-emerald-100 text-emerald-900"
      : tone === "danger"
        ? "bg-red-100 text-red-900"
        : tone === "primary"
          ? "bg-se-primary-fixed-dim/40 text-se-primary"
          : tone === "secondary"
            ? "bg-se-secondary-container text-se-on-secondary-container"
            : "bg-se-surface-container text-se-on-surface-variant";
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 font-bold ${cls}`}>
      {text}
    </span>
  );
}

function StatCard({
  icon,
  label,
  value,
  hint,
}: {
  icon: string;
  label: string;
  value: string;
  hint?: string;
}) {
  return (
    <div className="rounded-2xl border-l-4 border-se-secondary-fixed bg-se-surface-container-lowest p-4">
      <div className="mb-2 flex items-center gap-2">
        <span className="material-symbols-outlined text-[18px] text-se-primary">
          {icon}
        </span>
        <h4 className="font-display text-[0.65rem] font-bold uppercase tracking-wider text-se-on-surface-variant">
          {label}
        </h4>
      </div>
      <div className="font-display text-2xl font-extrabold text-se-on-surface">
        {value}
      </div>
      {hint ? (
        <div className="mt-1 text-[0.7rem] text-se-on-surface-variant">
          {hint}
        </div>
      ) : null}
    </div>
  );
}

function Field({
  label,
  value,
  mono,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="rounded-xl bg-se-surface-container-low px-3 py-2">
      <dt className="font-display text-[0.65rem] font-bold uppercase tracking-wider text-se-on-surface-variant">
        {label}
      </dt>
      <dd className={`mt-0.5 truncate ${mono ? "font-mono text-xs" : "text-sm font-semibold"} text-se-on-surface`}>
        {value}
      </dd>
    </div>
  );
}
