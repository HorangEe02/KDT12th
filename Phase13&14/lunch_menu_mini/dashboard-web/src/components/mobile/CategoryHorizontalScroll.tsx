"use client";

import Link from "next/link";
import { categoryEmoji } from "./categoryEmoji";

/**
 * 가로 스크롤 카테고리 카드 — App Store "장르" 가로 스와이프와 유사.
 * 각 카드: 3:4 세로 비율, 큰 이모지, 카테고리명, 식당 수.
 */
interface CategoryItem {
  name: string;
  count: number;
  color?: string;
}

interface CategoryHorizontalScrollProps {
  categories: CategoryItem[];
  /** 표시 개수 제한 (기본 12) */
  limit?: number;
}

const TINTS: Record<string, string> = {
  한식: "from-rose-500/20 to-orange-400/15",
  일식: "from-sky-500/20 to-cyan-400/15",
  중식: "from-red-500/20 to-rose-400/15",
  양식: "from-amber-400/20 to-yellow-400/15",
  치킨: "from-amber-500/20 to-orange-500/15",
  카페: "from-stone-400/20 to-amber-300/15",
  베이커리: "from-orange-300/20 to-rose-300/15",
  분식: "from-fuchsia-500/20 to-rose-400/15",
  술집: "from-violet-500/20 to-fuchsia-400/15",
  뷔페: "from-emerald-500/20 to-teal-400/15",
  고깃집: "from-orange-700/20 to-red-500/15",
};

export default function CategoryHorizontalScroll({
  categories,
  limit = 12,
}: CategoryHorizontalScrollProps) {
  const items = categories.slice(0, limit);

  if (items.length === 0) {
    return null;
  }

  return (
    <div className="appstore-hscroll -mx-4 px-4">
      {items.map((c) => {
        const tint = TINTS[c.name] ?? "from-primary/15 to-secondary/15";
        return (
          <Link
            key={c.name}
            href={`/discover?cat=${encodeURIComponent(c.name)}`}
            className={`appstore-card grid place-items-center min-w-[140px] aspect-[3/4]
                        bg-gradient-to-br ${tint}
                        active:scale-95 transition-transform p-4`}
          >
            <span className="text-5xl select-none" aria-hidden>
              {categoryEmoji(c.name)}
            </span>
            <p className="font-bold text-[15px] mt-3 text-text-primary">
              {c.name}
            </p>
            <p className="text-[11px] text-text-tertiary font-mono">
              {c.count.toLocaleString()}곳
            </p>
          </Link>
        );
      })}
    </div>
  );
}
