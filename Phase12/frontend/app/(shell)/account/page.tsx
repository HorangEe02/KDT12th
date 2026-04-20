import Link from "next/link";
import { redirect } from "next/navigation";
import { getOptionalUser } from "@/lib/firebase/server-session";
import { isAdminConfigured } from "@/lib/firebase/admin";
import { ProfileEditForm } from "@/components/account/profile-edit-form";
import { LogoutButton } from "@/components/account/logout-button";

export const dynamic = "force-dynamic";

export const metadata = {
  title: "내 계정 · 원정 응원 플래너",
  robots: { index: false, follow: false },
};

/**
 * /account — 닉네임 + 응원팀 편집 페이지.
 *
 * - 미인증 → /login?next=/account 로 리다이렉트
 * - Firebase Admin 미구성(로컬 no-secrets 모드) → 안내 페이지
 * - 실제 폼은 `ProfileEditForm` 클라이언트 컴포넌트가 담당
 */
export default async function AccountPage() {
  if (!isAdminConfigured()) {
    return (
      <section className="mx-auto max-w-2xl space-y-4 py-6">
        <h1 className="font-display text-2xl font-extrabold text-se-primary">
          👤 내 계정
        </h1>
        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-900">
          <p className="font-display text-base font-bold">
            Firebase 서비스 미연결
          </p>
          <p className="mt-1.5">
            현재 환경에서는 계정 기능을 사용할 수 없습니다. 응원팀 설정은
            사이드바의 팀 필터를 통해 임시로 저장되며, 브라우저 로컬 저장소에만
            보존됩니다.
          </p>
        </div>
      </section>
    );
  }

  const user = await getOptionalUser({ checkRevoked: true });
  if (!user) redirect("/login?next=/account");

  return (
    <section className="mx-auto max-w-2xl space-y-5 py-4 md:py-6">
      <header className="flex items-center justify-between gap-3">
        <div className="min-w-0">
          <h1 className="font-display text-2xl font-extrabold text-se-primary md:text-[1.75rem]">
            👤 내 계정
          </h1>
          <p className="mt-0.5 text-sm text-se-on-surface-variant">
            닉네임과 응원팀을 변경합니다. 변경 즉시 사이드바와 대시보드에
            반영됩니다.
          </p>
        </div>
        <Link
          href="/"
          className="hidden h-10 items-center rounded-full border border-se-outline-variant bg-white px-4 font-display text-xs font-bold text-se-primary hover:border-se-primary md:inline-flex"
        >
          ← 홈으로
        </Link>
      </header>

      <ProfileEditForm />

      {/* 위험 영역 — 로그아웃 (확인 다이얼로그 포함) */}
      <section
        aria-label="계정 관리"
        className="mt-4 border-t border-se-outline-variant pt-5"
      >
        <h2 className="mb-3 font-display text-sm font-extrabold uppercase tracking-[0.12em] text-se-on-surface-variant">
          계정 관리
        </h2>
        <LogoutButton />
      </section>
    </section>
  );
}
