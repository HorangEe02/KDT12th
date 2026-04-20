import Link from "next/link";
import type { Game } from "@/lib/types";

/**
 * 모바일 전용 — 다음 원정 경기 Bento card (한 건).
 * mockup: uiux/mobile_uiux/matches_predictions_mobile/code.html § Away Matrix
 */
interface AwayMatrixCardProps {
  game: Game;
  highlight?: boolean;
  baseQuery?: Record<string, string>;
}

const TRANSPORT_BY_REGION: Record<string, { icon: string; label: string }> = {
  서울: { icon: "directions_subway", label: "지하철" },
  수원: { icon: "train", label: "전철" },
  인천: { icon: "directions_subway", label: "공항철도" },
  대전: { icon: "train", label: "KTX" },
  대구: { icon: "train", label: "KTX" },
  광주: { icon: "train", label: "KTX" },
  부산: { icon: "train", label: "KTX" },
  창원: { icon: "directions_bus", label: "고속버스" },
  default: { icon: "directions_car", label: "자차" },
};

function pickTransport(stadium: string) {
  const city = Object.keys(TRANSPORT_BY_REGION).find((k) =>
    stadium.includes(k),
  );
  return TRANSPORT_BY_REGION[city ?? "default"];
}

function relativeDate(dateStr: string): string {
  const today = new Date().toISOString().slice(0, 10);
  const tomorrow = new Date(Date.now() + 24 * 60 * 60 * 1000)
    .toISOString()
    .slice(0, 10);
  if (dateStr === today) return "오늘";
  if (dateStr === tomorrow) return "내일";
  // M/D 형식
  return dateStr.slice(5).replace("-", "/");
}

export function AwayMatrixCard({
  game,
  highlight,
  baseQuery,
}: AwayMatrixCardProps) {
  const transport = pickTransport(game.stadium);
  const dateLabel = relativeDate(game.date);
  const qs = new URLSearchParams({
    ...(baseQuery ?? {}),
    game: game.game_id,
  }).toString();

  return (
    <Link
      href={`/matches?${qs}`}
      className="relative flex items-start gap-3 overflow-hidden rounded-2xl border border-se-outline-variant/40 bg-se-surface-container-lowest p-4 no-underline shadow-[0_4px_24px_rgba(25,28,29,0.04)] transition-all active:scale-[0.98]"
    >
      <div
        className={`absolute left-0 top-0 bottom-0 w-1 ${
          highlight ? "bg-se-secondary-fixed" : "bg-se-outline-variant/30"
        }`}
      />
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-se-surface-container">
        <span
          className="material-symbols-outlined text-[20px] text-se-primary"
          style={{ fontVariationSettings: "'FILL' 1" }}
        >
          {transport.icon}
        </span>
      </div>
      <div className="min-w-0 flex-1">
        <div className="mb-1 flex items-start justify-between gap-2">
          <h3 className="truncate font-display text-sm font-bold text-se-on-surface">
            vs {game.home_team}
          </h3>
          <span className="shrink-0 rounded-md bg-se-surface-container-low px-2 py-0.5 font-display text-[0.65rem] font-bold text-se-on-surface-variant">
            {dateLabel}
          </span>
        </div>
        <p className="truncate font-body text-xs text-se-on-surface-variant">
          {game.stadium}
        </p>
        <div className="mt-2 flex flex-wrap gap-1.5">
          <Chip icon={transport.icon} label={transport.label} />
          {game.day_of_week ? (
            <Chip icon="event" label={game.day_of_week} />
          ) : null}
          {game.start_time ? (
            <Chip icon="schedule" label={game.start_time} />
          ) : null}
        </div>
      </div>
    </Link>
  );
}

function Chip({ icon, label }: { icon: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-se-surface-container-high px-2 py-0.5 font-display text-[0.65rem] font-medium uppercase tracking-wider text-se-on-surface">
      <span className="material-symbols-outlined text-[12px]">{icon}</span>
      {label}
    </span>
  );
}
