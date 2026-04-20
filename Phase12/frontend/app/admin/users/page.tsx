import { listUsers } from "@/lib/firebase/admin-users";
import { UserTable } from "@/components/admin/user-table";
import { UserFilters } from "@/components/admin/user-filters";

export const dynamic = "force-dynamic";

interface UsersPageProps {
  searchParams: Promise<{
    q?: string;
    role?: string;
    status?: string;
    cursor?: string;
  }>;
}

export default async function AdminUsersPage({ searchParams }: UsersPageProps) {
  const sp = await searchParams;
  const role = sp.role === "admin" ? "admin" : sp.role === "user" ? "user" : undefined;
  const status =
    sp.status === "disabled" ? "disabled" : sp.status === "active" ? "active" : undefined;

  const page = await listUsers({
    pageSize: 25,
    cursor: sp.cursor ?? null,
    role,
    status,
    search: sp.q,
  });

  return (
    <section className="flex flex-col gap-6">
      <header className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="font-display text-3xl font-extrabold tracking-tight text-se-on-surface">
            회원 관리
          </h1>
          <p className="mt-1 font-medium text-se-on-surface-variant">
            전체{" "}
            <strong className="text-se-primary">
              {page.total.toLocaleString("ko-KR")}명
            </strong>
            의 회원이 가입했습니다.
          </p>
        </div>
      </header>

      <UserFilters
        currentRole={role}
        currentStatus={status}
        currentSearch={sp.q ?? ""}
      />

      <UserTable
        items={page.items}
        nextCursor={page.nextCursor}
        currentSearch={sp.q ?? ""}
        currentRole={role}
        currentStatus={status}
      />
    </section>
  );
}
