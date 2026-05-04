"use client";

import type { WeatherNow } from "@/lib/types";

function getBgEmoji(w: WeatherNow): string {
  if (w.rainTypeStr && w.rainTypeStr !== "없음") return "🌧️";
  if (w.rain > 50) return "🌧️";
  if (w.sky === "흐림") return "☁️";
  if (w.temp > 28) return "☀️";
  if (w.temp < 5) return "❄️";
  return "⛅";
}

export default function CurrentWeatherCard({ weather }: { weather: WeatherNow }) {
  const meta: [string, string][] = [
    ["기온", `${weather.temp}°C`],
    ["습도", `${weather.humidity}%`],
    ["미세먼지", weather.dust],
    ["하늘", weather.sky],
    ["강수확률", `${weather.rain}%`],
  ];

  // 강수 형태가 있으면 추가 표시
  if (weather.rainTypeStr && weather.rainTypeStr !== "없음") {
    meta.push(["강수", weather.rainTypeStr]);
  }
  if (weather.windSpeed !== undefined && weather.windSpeed > 0) {
    meta.push(["바람", `${weather.windSpeed.toFixed(1)}m/s`]);
  }

  return (
    <div className="bento-card mb-5 flex items-center gap-6 flex-wrap">
      <div className="text-6xl" aria-hidden>
        {getBgEmoji(weather)}
      </div>
      <div className="flex-1 min-w-[240px]">
        <div className="text-xs text-text-tertiary uppercase tracking-[0.1em] font-bold mb-3">
          Today&apos;s Weather{" "}
          <span
            className="text-[10px] font-normal normal-case tracking-normal text-text-tertiary opacity-70"
            style={{ fontFamily: "var(--font-ko)" }}
          >
            오늘의 날씨
          </span>
        </div>
        <div className="flex gap-6 flex-wrap">
          {meta.map(([k, v]) => (
            <div key={k}>
              <div
                className="text-[10px] text-text-tertiary"
                style={{ fontFamily: "var(--font-ko)" }}
              >
                {k}
              </div>
              <div className="text-base font-bold text-text-primary font-mono">
                {v}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
