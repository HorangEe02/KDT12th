"use client";

import Link from "next/link";
import type { Restaurant } from "@/lib/types";
import { categoryEmoji } from "./categoryEmoji";

/**
 * App Store "오늘의 앱" 스타일의 5줄 row 카드.
 *
 * 한 카드(`appstore-card`) 안에 식당 5곳을 row로 쌓고, 사이는 hairline divider.
 * 각 row: 카테고리 컬러 아이콘 박스(48px) + 이름·메뉴타입·거리 + 받기 캡슐.
 */
interface TodaysTopFiveAppRowsProps {
  items: Array<Restaurant & { score?: number }>;
}

export default function TodaysTopFiveAppRows({ items }: TodaysTopFiveAppRowsProps) {
  if (items.length === 0) {
    return (
      <div className="appstore-card p-6 text-center text-text-tertiary text-sm">
        추천할 식당이 아직 없어요.
      </div>
    );
  }

  return (
    <div className="appstore-card overflow-hidden">
      {items.slice(0, 5).map((r, i) => (
        <Link
          key={r.id}
          href={`/discover?restaurant=${encodeURIComponent(String(r.id))}`}
          className={`flex items-center gap-3 p-4 active:bg-black/5 dark:active:bg-white/5 transition-colors ${
            i > 0 ? "appstore-divider" : ""
          }`}
        >
          {/* 카테고리 컬러 아이콘 박스 */}
          <div
            className="w-12 h-12 rounded-2xl grid place-items-center text-2xl shrink-0
                       bg-gradient-to-br from-primary/20 via-tertiary/15 to-secondary/15"
            aria-hidden
          >
            {categoryEmoji(r.category)}
          </div>

          {/* 텍스트 */}
          <div className="flex-1 min-w-0">
            <p className="text-[15px] font-bold text-text-primary truncate">
              {i + 1}. {r.name}
            </p>
            <p className="text-[12px] text-text-tertiary truncate font-mono">
              {r.menuType ?? r.category} · {r.distance_m ?? r.distance ?? "?"}m
              {r.score != null && ` · ${Math.round(r.score)}점`}
            </p>
          </div>

          {/* 받기 캡슐 */}
          <span className="appstore-pill shrink-0">받기</span>
        </Link>
      ))}
    </div>
  );
}
