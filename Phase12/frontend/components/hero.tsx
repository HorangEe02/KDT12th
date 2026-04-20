import Image from "next/image";
import { getKBOLogoPath, getTeamLogoPath, getTeamPalette } from "@/lib/team-colors";
import type { Viewport } from "@/lib/types";

interface HeroProps {
  team?: string;
  /**
   * @deprecated viewport 분기는 더 이상 사용하지 않습니다.
   * 현재는 Tailwind responsive (sm:/md:/lg:) 로 자동 분기.
   * 호환성을 위해 prop 자체는 받지만 무시.
   */
  viewport?: Viewport;
}

/**
 * Stadium Editorial Hero — 팀 컬러 그라디언트 + KBO/팀 로고.
 *
 * v2 (2026-04-19): viewport prop 폐기 + Tailwind 자동 반응형
 *   - 모바일 (< sm): vertical stack, 작은 폰트, KBO watermark 숨김
 *   - sm (≥ 640px): 폰트 + KBO watermark 등장
 *   - md (≥ 768px): horizontal split (텍스트 좌 + 팀 로고 우)
 *   - lg (≥ 1024px): 데스크톱 헤딩 크기
 */
export function Hero({ team = "LG" }: HeroProps) {
  const palette = getTeamPalette(team);
  const gradient = `linear-gradient(135deg, ${palette.color} 0%, ${palette.subColor} 100%)`;

  return (
    <section
      className="relative mb-5 overflow-hidden rounded-3xl px-5 py-6 text-white shadow-[0_12px_32px_rgba(0,0,0,0.18)] sm:px-8 sm:py-7 md:px-10 md:py-8"
      style={{ background: gradient }}
      aria-label={`${palette.nameKo} 원정 응원 배너`}
    >
      {/* Radial highlight */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(circle at 85% 30%, rgba(255,255,255,0.22), transparent 55%)",
        }}
      />

      {/* KBO watermark — sm 이상에서만 표시 (모바일에선 텍스트 영역 확보 우선) */}
      <div
        aria-hidden
        className="pointer-events-none absolute right-4 top-4 hidden h-20 w-20 opacity-[0.12] sm:block md:right-10 md:top-6 md:h-28 md:w-28"
      >
        <Image
          src={getKBOLogoPath(1)}
          alt=""
          fill
          sizes="120px"
          className="object-contain"
          priority={false}
        />
      </div>

      {/* Layout: vertical on mobile, horizontal on md+ */}
      <div className="relative z-10 flex flex-col items-start gap-4 md:flex-row md:items-center md:justify-between md:gap-8">
        <div className="min-w-0 flex-1">
          <span
            className="mb-3 inline-block rounded-full px-3 py-1 text-[0.62rem] font-bold uppercase tracking-[0.14em] backdrop-blur-sm sm:px-3.5 sm:py-1.5 sm:text-[0.72rem] sm:tracking-[0.16em]"
            style={{ background: "rgba(255,255,255,0.22)" }}
          >
            KBO 2026 · AWAY COMPANION
          </span>
          <h1
            className="mb-2 mt-0 font-display text-2xl font-extrabold leading-[1.15] tracking-[-0.03em] !text-white drop-shadow-[0_2px_14px_rgba(0,0,0,0.28)] sm:text-3xl md:text-[2rem] lg:text-[2.6rem]"
            style={{ color: "#FFFDF5" }}
          >
            <span className="se-ball mr-1.5">⚾</span> 원정 응원 플래너
          </h1>
          <p className="m-0 font-body text-sm leading-relaxed opacity-90 sm:text-base md:text-[1.02rem]">
            팀 선택 한 번으로 티켓·교통·맛집·숙소·관광을 한 번에
          </p>
        </div>

        {/* Team logo + name — mobile: row, md+: column right-aligned */}
        <div className="flex w-full items-center gap-3 md:w-auto md:flex-col md:items-end md:gap-4 md:text-right">
          <div className="relative flex h-16 w-16 shrink-0 items-center justify-center rounded-full bg-white/95 shadow-[0_6px_18px_rgba(0,0,0,0.25)] sm:h-20 sm:w-20 md:order-1">
            <Image
              src={getTeamLogoPath(team)}
              alt={`${palette.nameKo} 로고`}
              width={56}
              height={56}
              className="object-contain"
              priority
            />
          </div>
          <div className="min-w-0">
            <div className="font-display text-lg font-bold leading-tight tracking-[-0.01em] !text-white drop-shadow-[0_2px_12px_rgba(0,0,0,0.3)] sm:text-xl md:text-[1.55rem]">
              {palette.nameKo}
            </div>
            <div className="mt-1 hidden text-xs opacity-80 sm:block sm:text-[0.82rem]">
              선택된 팀 컬러로 테마가 변경됩니다
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
