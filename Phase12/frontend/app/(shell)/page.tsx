import Link from "next/link";
import { Hero } from "@/components/hero";
import { TeamSelector } from "@/components/team-selector";
import type { Viewport } from "@/lib/types";
import { resolveTeam } from "@/lib/data/resolve-team";

interface PageProps {
  searchParams: Promise<{ team?: string; device?: string }>;
}

const NEXT_TABS = [
  {
    href: "/matches",
    icon: "sports_baseball",
    title: "원정 경기 + 승률",
    desc: "기간 내 원정 경기 리스트와 팀별 원정 승률 예측",
  },
  {
    href: "/map",
    icon: "map",
    title: "구장 · 길찾기",
    desc: "구장 주변 맛집·숙소·관광 4레이어 지도 + 카카오 경로",
  },
  {
    href: "/places",
    icon: "restaurant",
    title: "맛집 · 숙소 · 관광",
    desc: "TourAPI 기반 POI 카드와 거리-평점 분포",
  },
  {
    href: "/ai",
    icon: "smart_toy",
    title: "AI 챗봇",
    desc: "Gemini 기반 원정 코스 추천 챗봇 (도구 호출 + Multi-Agent)",
  },
  {
    href: "/badges",
    icon: "workspace_premium",
    title: "내 뱃지",
    desc: "방문 구장 Stadium Tour + Firestore 동기화",
  },
];

export default async function Home({ searchParams }: PageProps) {
  const params = await searchParams;
  const team = await resolveTeam(params.team);
  const viewport: Viewport = params.device === "mobile" ? "mobile" : "web";
  const qs = new URLSearchParams(
    Object.entries(params).filter(([, v]) => typeof v === "string") as [
      string,
      string,
    ][],
  ).toString();

  return (
    <div className={viewport === "mobile" ? "mx-auto max-w-[480px]" : ""}>
      {/* Hero + TeamSelector: viewport prop 폐기 — 자동 반응형 (Tailwind sm:/md:/lg:) */}
      <Hero team={team} />
      <TeamSelector selected={team} />

      <section className="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {NEXT_TABS.map((t) => (
          <Link
            key={t.href}
            href={qs ? `${t.href}?${qs}` : t.href}
            className="group rounded-2xl border border-se-outline-variant bg-se-surface-container-lowest p-5 no-underline transition-all hover:-translate-y-0.5 hover:border-se-primary hover:shadow-[0_10px_22px_rgba(0,25,60,0.1)]"
          >
            <span className="material-symbols-outlined text-3xl text-se-primary">
              {t.icon}
            </span>
            <h3 className="mt-2 font-display text-base font-extrabold text-se-primary">
              {t.title}
            </h3>
            <p className="mt-1 text-sm leading-relaxed text-se-on-surface-variant">
              {t.desc}
            </p>
          </Link>
        ))}
      </section>
    </div>
  );
}
