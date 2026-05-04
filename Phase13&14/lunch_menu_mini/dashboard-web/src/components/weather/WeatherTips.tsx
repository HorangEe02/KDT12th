"use client";

import type { WeatherNow } from "@/lib/types";

function getTips(w: WeatherNow): string[] {
  const tips: string[] = [];
  if (w.temp < 10) tips.push("쌀쌀한 날씨에는 따뜻한 국물류를 추천합니다");
  if (w.temp > 28) tips.push("더운 날씨에는 시원한 면류나 초밥이 좋겠어요");
  if (w.dust === "나쁨") tips.push("미세먼지가 나쁘니 실내 식당을 이용하세요");
  if (w.rain > 50) tips.push("비 올 확률이 높아 가까운 곳을 추천합니다");
  return tips.length > 0 ? tips : ["오늘은 어떤 메뉴든 좋은 날씨입니다!"];
}

export default function WeatherTips({ weather }: { weather: WeatherNow }) {
  const tips = getTips(weather);
  return (
    <div className="space-y-2 mb-5">
      {tips.map((t, i) => (
        <div
          key={i}
          className="bg-primary/5 border-l-[3px] border-primary text-text-primary rounded-sm px-4 py-2.5 text-sm"
          style={{ fontFamily: "var(--font-ko)" }}
        >
          {t}
        </div>
      ))}
    </div>
  );
}
