import { cn } from "@/lib/utils";
import type { FeedItem } from "@/lib/firebase/admin-metrics";

const TYPE_META: Record<
  FeedItem["type"],
  { icon: string; tone: string }
> = {
  signup: { icon: "person_add", tone: "bg-se-primary-fixed-dim/50 text-se-primary" },
  plan_created: {
    icon: "confirmation_number",
    tone: "bg-se-secondary-fixed/40 text-se-secondary",
  },
  chat_session: { icon: "smart_toy", tone: "bg-se-tertiary-fixed/40 text-se-tertiary" },
  shared_plan: { icon: "share", tone: "bg-blue-100 text-blue-900" },
};

interface LiveFeedProps {
  items: FeedItem[];
}

function relativeTime(iso: string): string {
  const t = new Date(iso).getTime();
  if (!Number.isFinite(t) || t === 0) return "방금";
  const diff = Date.now() - t;
  const min = Math.floor(diff / 60_000);
  if (min < 1) return "방금";
  if (min < 60) return `${min}분 전`;
  const h = Math.floor(min / 60);
  if (h < 24) return `${h}시간 전`;
  const d = Math.floor(h / 24);
  if (d < 7) return `${d}일 전`;
  return new Date(t).toLocaleDateString("ko-KR");
}

export function LiveFeed({ items }: LiveFeedProps) {
  if (items.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-se-outline-variant bg-se-surface-container-low p-6 text-center text-sm text-se-on-surface-variant">
        최근 활동이 없습니다.
      </div>
    );
  }
  return (
    <div className="flex flex-col gap-3">
      {items.map((item, idx) => {
        const m = TYPE_META[item.type];
        return (
          <div
            key={`${item.uid ?? "-"}-${idx}-${item.createdAt}`}
            className="flex items-center gap-4 rounded-xl bg-se-surface-container-low p-3 transition-colors hover:bg-se-surface-container"
          >
            <div
              className={cn(
                "flex h-10 w-10 shrink-0 items-center justify-center rounded-full",
                m.tone,
              )}
            >
              <span className="material-symbols-outlined text-[20px]">
                {m.icon}
              </span>
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-bold text-se-on-surface">
                {item.title}
              </p>
              <p className="truncate text-xs text-se-on-surface-variant">
                {item.subtitle}
                {item.subtitle ? " · " : ""}
                {relativeTime(item.createdAt)}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
