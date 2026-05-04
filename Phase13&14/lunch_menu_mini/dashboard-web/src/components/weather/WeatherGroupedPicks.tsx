"use client";

import type { MoodRecommendationGroup } from "@/lib/types";

interface Props {
  groups: MoodRecommendationGroup[];
}

export default function WeatherGroupedPicks({ groups }: Props) {
  if (groups.length === 0) return null;

  return (
    <div className="space-y-4 mb-5">
      {groups.map((group) => (
        <div key={group.group_label} className="bento-card">
          <h3
            className="text-base font-bold text-text-primary mb-3 flex items-center gap-2"
            style={{ fontFamily: "var(--font-ko)" }}
          >
            <span className="text-xl">{group.group_emoji}</span>
            {group.group_label}
          </h3>

          <div className="space-y-2">
            {group.items.map((item, idx) => {
              const highlight = idx === 0;
              return (
                <div
                  key={item.restaurant_id}
                  className={`flex items-center gap-3 p-3 rounded-sm border ${
                    highlight
                      ? "bg-success/10 border-success/40"
                      : "bg-surface-2 border-outline/15"
                  }`}
                >
                  <div
                    className={`w-7 h-7 flex items-center justify-center font-heading font-bold text-sm rounded-sm ${
                      highlight ? "text-success" : "text-text-tertiary"
                    }`}
                  >
                    {idx + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-bold text-text-primary truncate">
                      {item.restaurant_name}
                    </div>
                    <div className="text-[11px] text-text-tertiary font-mono">
                      {item.menu_type || item.category || "기타"} ·{" "}
                      {item.distance_m}m
                    </div>
                    <div
                      className="text-[10px] text-primary/80 mt-0.5"
                      style={{ fontFamily: "var(--font-ko)" }}
                    >
                      {item.reason}
                    </div>
                  </div>
                  <div className="text-lg font-heading font-bold text-success leading-none">
                    {item.mood_score}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
