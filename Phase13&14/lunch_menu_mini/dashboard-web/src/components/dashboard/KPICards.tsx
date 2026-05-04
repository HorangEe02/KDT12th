"use client";

interface KPIItem {
  label: string;
  ko: string;
  value: string;
  sub?: string;
  color: string;
  pct: number;
  badges?: string[];
}

export default function KPICards({
  totalRestaurants,
  trackedMeals,
  avgSentiment,
  chatLatencyMs,
}: {
  totalRestaurants: number;
  trackedMeals: number;
  avgSentiment: number | null;
  chatLatencyMs: number | null;
}) {
  const items: KPIItem[] = [
    {
      label: "Registered Restaurants",
      ko: "등록된 음식점",
      value: totalRestaurants.toLocaleString(),
      sub: "within 500m",
      color: "var(--color-primary)",
      pct: Math.min(100, totalRestaurants * 6),
    },
    {
      label: "This Week Meals",
      ko: "이번 주 기록",
      value: `${trackedMeals}/5`,
      sub: "logged days",
      color: "var(--color-secondary)",
      pct: (trackedMeals / 5) * 100,
    },
    {
      label: "Avg Sentiment",
      ko: "평균 감성 점수",
      value:
        avgSentiment == null
          ? "—"
          : (avgSentiment >= 0 ? "+" : "") + avgSentiment.toFixed(2),
      color: "var(--color-tertiary)",
      pct: avgSentiment == null ? 0 : Math.round(((avgSentiment + 1) / 2) * 100),
      badges: ["A1", "KcELECTRA"],
    },
    {
      label: "Chat Latency",
      ko: "챗봇 평균 지연",
      value: chatLatencyMs == null ? "—" : `${Math.round(chatLatencyMs)}ms`,
      sub: "avg · rolling",
      color: "var(--color-success)",
      pct: chatLatencyMs == null
        ? 0
        : Math.max(0, 100 - Math.min(100, chatLatencyMs / 30)),
    },
  ];

  return (
    // 모바일: 2열 (작은 카드 4개), md 이상: 4열
    <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5 md:gap-4">
      {items.map((item) => (
        <div
          key={item.label}
          className="bento-card border-l-[3px] p-3 md:p-5"
          style={{ borderLeftColor: item.color }}
        >
          <p className="text-[10px] md:text-xs text-text-secondary uppercase tracking-[0.08em] md:tracking-[0.1em] font-bold font-heading mb-0.5 line-clamp-1">
            {item.label}
          </p>
          <p
            className="text-[10px] md:text-[11px] text-text-tertiary mb-1.5 md:mb-2 line-clamp-1"
            style={{ fontFamily: "var(--font-ko)" }}
          >
            {item.ko}
          </p>
          <div className="flex items-baseline gap-1 md:gap-2 flex-wrap">
            <span className="text-xl md:text-[2rem] font-heading font-bold text-text-primary tracking-tight leading-none">
              {item.value}
            </span>
            {item.sub && !item.badges && (
              <span
                className="text-[10px] md:text-xs font-semibold"
                style={{ color: item.color }}
              >
                {item.sub}
              </span>
            )}
          </div>
          {item.badges && (
            <div className="flex gap-1 md:gap-1.5 mt-2 md:mt-3 flex-wrap">
              {item.badges.map((b) => (
                <span
                  key={b}
                  className="text-[8px] md:text-[9px] font-mono font-semibold px-1.5 md:px-2 py-0.5 border rounded-sm"
                  style={{
                    color: item.color,
                    borderColor: `color-mix(in srgb, ${item.color} 30%, transparent)`,
                  }}
                >
                  {b}
                </span>
              ))}
            </div>
          )}
          <div className="mt-3 md:mt-4 h-1 bg-surface-3 overflow-hidden">
            <div
              className="h-full transition-all duration-700"
              style={{ width: `${item.pct}%`, background: item.color }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
