import { loadStadiums } from "@/lib/data/loaders";
import { StadiumTour } from "@/components/badges/stadium-tour";
import { SharePlanButton } from "@/components/badges/share-plan-button";
import { BadgesMobileView } from "@/components/badges/badges-mobile-view";
import { AchievementGrid } from "@/components/badges/achievement-grid";

export default async function BadgesPage() {
  const stadiums = await loadStadiums();
  return (
    <>
      {/* === Mobile === */}
      <BadgesMobileView stadiums={stadiums} />

      {/* === Desktop === */}
      <section className="hidden space-y-6 md:block">
        <header>
          <h1 className="font-display text-2xl font-extrabold text-se-primary">
            🏆 My Badges
          </h1>
          <p className="text-sm text-se-on-surface-variant">
            10 구장을 모두 방문해 Stadium Tour 를 완성하세요. 클릭으로 방문 체크 토글.
          </p>
        </header>

        <StadiumTour stadiums={stadiums} />

        <AchievementGrid />

        <section className="rounded-3xl border border-se-outline-variant bg-se-surface-container-lowest p-5">
          <h3 className="mb-3 font-display text-sm font-extrabold uppercase tracking-[0.12em] text-se-on-surface-variant">
            🔗 원정 계획 공유
          </h3>
          <p className="mb-3 text-xs text-se-on-surface-variant">
            현재 사이드바 필터 (팀 · 기간 · 예산 · 인원 · 이동수단) 를 URL 로
            직렬화합니다. 링크 수신자는 동일한 필터 상태로 앱이 열립니다.
          </p>
          <SharePlanButton pathname="/" />
        </section>
      </section>
    </>
  );
}
