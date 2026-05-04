"use client";

import Link from "next/link";
import type { Restaurant } from "@/lib/types";
import { categoryEmoji } from "./categoryEmoji";

/**
 * Apple App Store "App of the Day" 스타일 풀블리드 hero 카드.
 *
 * 식당 사진이 없으므로 카테고리 컬러 그래디언트 + 큰 이모지로 비주얼 채움.
 * 향후 Kakao 사진 URL 받으면 `<img>` 추가.
 */
interface HeroPickCardProps {
  restaurant: Restaurant & { score?: number };
  eyebrow?: string;
}

const GRADIENTS: Record<string, string> = {
  한식: "from-rose-500/40 via-orange-500/30 to-amber-400/30",
  일식: "from-sky-500/40 via-cyan-400/30 to-teal-400/30",
  중식: "from-red-500/40 via-rose-500/30 to-orange-400/30",
  양식: "from-amber-400/40 via-yellow-400/30 to-lime-400/30",
  치킨: "from-amber-500/40 via-orange-500/30 to-red-400/30",
  카페: "from-stone-400/40 via-amber-300/30 to-rose-300/30",
  베이커리: "from-amber-300/40 via-orange-300/30 to-rose-300/30",
  분식: "from-fuchsia-500/40 via-rose-400/30 to-orange-300/30",
  술집: "from-violet-500/40 via-fuchsia-500/30 to-rose-400/30",
  뷔페: "from-emerald-500/40 via-teal-400/30 to-sky-400/30",
  고깃집: "from-orange-700/40 via-red-600/30 to-rose-500/30",
};

export default function HeroPickCard({
  restaurant,
  eyebrow = "오늘의 픽",
}: HeroPickCardProps) {
  const grad = GRADIENTS[restaurant.category] ?? GRADIENTS["한식"];
  const emoji = categoryEmoji(restaurant.category);

  return (
    <Link
      href={`/discover?restaurant=${encodeURIComponent(String(restaurant.id))}`}
      className="appstore-hero block active:scale-[0.98] transition-transform"
    >
      {/* 컬러 그래디언트 배경 */}
      <div className={`absolute inset-0 bg-gradient-to-br ${grad}`} />

      {/* 큰 이모지 (식당 사진 대체) */}
      <div className="absolute inset-0 grid place-items-center">
        <span
          className="text-[140px] leading-none opacity-25 select-none"
          aria-hidden
        >
          {emoji}
        </span>
      </div>

      {/* 하단 텍스트 스크림 */}
      <div className="absolute inset-0 appstore-scrim" />

      {/* 텍스트 영역 */}
      <div className="absolute bottom-0 left-0 right-0 p-6 text-white">
        <p className="text-[11px] uppercase tracking-widest font-bold opacity-85">
          {eyebrow} · {restaurant.category}
        </p>
        <h3 className="text-2xl sm:text-3xl font-extrabold leading-tight mt-1.5 line-clamp-2">
          {restaurant.name}
        </h3>
        <p className="text-sm opacity-90 mt-2 font-mono">
          {restaurant.distance_m ?? restaurant.distance ?? "?"}m
          {restaurant.score != null && ` · 점수 ${Math.round(restaurant.score)}`}
        </p>
      </div>
    </Link>
  );
}
