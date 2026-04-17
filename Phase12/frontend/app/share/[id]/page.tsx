/**
 * /share/[id] — Firestore 단축 링크 → 원본 필터로 복원 후 홈 리다이렉트.
 */
import { redirect } from "next/navigation";
import { getSharedPlan } from "@/lib/firebase/shared-plans";
import { serializeFilters } from "@/lib/share/serialize";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function SharePage({ params }: PageProps) {
  const { id } = await params;
  const plan = await getSharedPlan(id);

  if (!plan) {
    return (
      <main className="mx-auto flex max-w-md flex-col items-center gap-4 px-6 py-20 text-center">
        <span className="material-symbols-outlined text-5xl text-se-outline">
          link_off
        </span>
        <h1 className="font-display text-xl font-extrabold text-se-primary">
          공유 링크를 찾을 수 없습니다
        </h1>
        <p className="text-sm text-se-on-surface-variant">
          링크가 만료되었거나 Firestore 가 구성되지 않은 환경입니다. 홈으로
          이동해 새 계획을 만들어 주세요.
        </p>
        <a
          href="/"
          className="rounded-full bg-se-primary px-5 py-2 text-sm font-bold text-white no-underline"
        >
          홈으로
        </a>
      </main>
    );
  }

  // 원본 filters → URLSearchParams
  const f = plan.filters as {
    team?: string;
    dateRange?: [string, string];
    budget?: number;
    party?: string;
    transport?: string;
  };
  const params2 = serializeFilters({
    team: f.team,
    start: f.dateRange?.[0],
    end: f.dateRange?.[1],
    budget: typeof f.budget === "number" ? f.budget : undefined,
    party: f.party as "solo" | "couple" | "family" | "friends" | undefined,
    transport: f.transport as "train" | "car" | "bus" | undefined,
  });
  redirect(`/?${params2.toString()}`);
}
