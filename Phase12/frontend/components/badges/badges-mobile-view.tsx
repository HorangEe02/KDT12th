import { StadiumTourBento } from "./stadium-tour-bento";
import { AchievementScroll } from "./achievement-scroll";
import { AwayTimeline } from "./away-timeline";
import { MobileSettingsButton } from "@/components/nav/mobile-settings-button";
import type { Stadium } from "@/lib/types";

/**
 * 모바일 전용 — /badges 페이지 view.
 * mockup: uiux/mobile_uiux/my_badges_records_mobile/code.html
 */
interface BadgesMobileViewProps {
  stadiums: Stadium[];
}

export function BadgesMobileView({ stadiums }: BadgesMobileViewProps) {
  return (
    <div className="space-y-12 md:hidden">
      {/* Hero Title */}
      <section className="flex items-start justify-between gap-3 px-2">
        <div className="min-w-0 flex-1">
          <h1 className="font-display text-3xl font-extrabold tracking-tight text-se-primary">
            기록
          </h1>
          <p className="mt-1 font-body text-sm text-se-on-surface-variant">
            나의 KBO 원정 여정 & 도전 과제
          </p>
        </div>
        <MobileSettingsButton ariaLabel="원정 설정 열기" />
      </section>

      {/* Stadium Tour Bento */}
      <StadiumTourBento stadiums={stadiums} />

      {/* Achievement Badges Horizontal Scroll */}
      <AchievementScroll />

      {/* Away Timeline */}
      <AwayTimeline stadiums={stadiums} />
    </div>
  );
}
