import Image from "next/image";
import { getKBOLogoPath, getTeamLogoPath, getTeamPalette } from "@/lib/team-colors";
import { cn } from "@/lib/utils";
import type { Viewport } from "@/lib/types";

interface HeroProps {
  team?: string;
  viewport?: Viewport;
}

/**
 * Stadium Editorial Hero — 팀 컬러 그라디언트 + KBO/팀 로고.
 * 포팅 원본: src/ui/components/hero.py + assets/react/hero.html
 *
 * Server Component — `searchParams.team`으로 부모에서 팀을 주입.
 */
export function Hero({ team = "LG", viewport = "web" }: HeroProps) {
  const palette = getTeamPalette(team);
  const gradient = `linear-gradient(135deg, ${palette.color} 0%, ${palette.subColor} 100%)`;
  const isMobile = viewport === "mobile";

  return (
    <section
      className={cn(
        "relative overflow-hidden rounded-3xl text-white shadow-[0_12px_32px_rgba(0,0,0,0.18)]",
        "mb-5",
        isMobile ? "px-6 py-7" : "px-10 py-8",
      )}
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

      {/* KBO watermark logo (top-left corner, subtle) */}
      <div
        aria-hidden
        className={cn(
          "pointer-events-none absolute opacity-[0.12]",
          isMobile ? "right-4 top-4 h-20 w-20" : "right-10 top-6 h-28 w-28",
        )}
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

      <div
        className={cn(
          "relative z-10 flex items-center justify-between gap-8",
          isMobile && "flex-col items-start gap-4",
        )}
      >
        <div className="flex-1 min-w-0">
          <span
            className={cn(
              "mb-3 inline-block rounded-full px-3.5 py-1.5 text-[0.72rem] font-bold uppercase tracking-[0.16em] backdrop-blur-sm",
            )}
            style={{ background: "rgba(255,255,255,0.22)" }}
          >
            KBO 2026 · AWAY COMPANION
          </span>
          <h1
            className={cn(
              "font-display font-extrabold leading-[1.1] tracking-[-0.03em] drop-shadow-[0_2px_14px_rgba(0,0,0,0.28)]",
              "text-white",
              isMobile ? "text-[1.9rem]" : "text-[2.6rem]",
              "mt-0 mb-2",
            )}
            style={{ color: "#FFFDF5" }}
          >
            <span className="se-ball mr-1.5">⚾</span> 원정 응원 플래너
          </h1>
          <p
            className={cn(
              "font-body text-[1.02rem] opacity-90",
              "m-0",
              isMobile && "text-base",
            )}
          >
            팀 선택 한 번으로 티켓·교통·맛집·숙소·관광을 한 번에
          </p>
        </div>

        <div
          className={cn(
            "flex items-center gap-4",
            isMobile ? "self-stretch justify-between" : "text-right flex-col",
          )}
        >
          <div
            className={cn(
              "relative flex h-20 w-20 shrink-0 items-center justify-center rounded-full bg-white/95 shadow-[0_6px_18px_rgba(0,0,0,0.25)]",
              !isMobile && "order-1",
            )}
          >
            <Image
              src={getTeamLogoPath(team)}
              alt={`${palette.nameKo} 로고`}
              width={56}
              height={56}
              className="object-contain"
              priority
            />
          </div>
          <div className={cn(isMobile ? "text-left" : "text-right")}>
            <div className="font-display text-[1.55rem] font-bold leading-tight tracking-[-0.01em] drop-shadow-[0_2px_12px_rgba(0,0,0,0.3)]">
              {palette.nameKo}
            </div>
            <div className="mt-1 text-[0.82rem] opacity-80">
              선택된 팀 컬러로 테마가 변경됩니다
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
