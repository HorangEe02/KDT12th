"use client";

import { useEffect, useMemo, useState } from "react";
import dynamic from "next/dynamic";
import AICommentCard from "@/components/nutrition/AICommentCard";
import MealEntryPanel from "@/components/nutrition/MealEntryPanel";
import MealHistoryList from "@/components/nutrition/MealHistoryList";
import MealTargetsCard from "@/components/nutrition/MealTargetsCard";
import StatCard from "@/components/nutrition/StatCard";
import { type MacroSlice } from "@/components/nutrition/MacroDonut";
import { SkeletonChart } from "@/components/common/Skeleton";
import ErrorBanner from "@/components/common/ErrorBanner";
import { useWeeklyNutrition } from "@/lib/queries";

// Recharts is heavy (~90kB gzip). Load chart components only when Nutrition
// route is visited so Dashboard/Discover stay small.
const CalorieTrend = dynamic(
  () => import("@/components/nutrition/CalorieTrend"),
  { ssr: false, loading: () => <SkeletonChart height={240} /> },
);
const MacroDonut = dynamic(
  () => import("@/components/nutrition/MacroDonut"),
  { ssr: false, loading: () => <SkeletonChart height={200} /> },
);
const DailyBreakdown = dynamic(
  () => import("@/components/nutrition/DailyBreakdown"),
  { ssr: false, loading: () => <SkeletonChart height={220} /> },
);
import { useAuth } from "@/lib/useAuth";

export default function NutritionPage() {
  const user = useAuth();
  const [userId, setUserId] = useState<string>("user1");
  useEffect(() => {
    if (user?.id) {
      setUserId(user.id);
      return;
    }
    const saved = localStorage.getItem("p11_user_id");
    if (saved) setUserId(saved);
  }, [user]);

  const {
    data: weekly = [],
    isPending: weeklyLoading,
    isError: weeklyError,
    refetch: refetchWeekly,
  } = useWeeklyNutrition(userId);

  const stats = useMemo(() => {
    const eaten = weekly.filter((d) => d.calories > 0);
    const avg = (k: "calories" | "protein" | "carbs" | "fat") =>
      eaten.length
        ? Math.round(eaten.reduce((s, d) => s + d[k], 0) / eaten.length)
        : 0;
    const avgCal = avg("calories");
    const avgProtein = avg("protein");
    const avgCarbs = avg("carbs");
    const avgFat = avg("fat");
    const totalMacro = avgProtein + avgCarbs + avgFat;

    const macros: MacroSlice[] = [
      {
        name: "탄수화물",
        value: avgCarbs,
        color: "#3B8BD4",
        target: 60,
        percent: totalMacro ? Math.round((avgCarbs / totalMacro) * 100) : 0,
      },
      {
        name: "단백질",
        value: avgProtein,
        color: "var(--color-secondary)",
        target: 25,
        percent: totalMacro ? Math.round((avgProtein / totalMacro) * 100) : 0,
      },
      {
        name: "지방",
        value: avgFat,
        color: "var(--color-tertiary)",
        target: 20,
        percent: totalMacro ? Math.round((avgFat / totalMacro) * 100) : 0,
      },
    ];

    const pRatio = totalMacro ? (avgProtein / totalMacro) * 100 : 0;
    const balance =
      pRatio < 20
        ? { text: "단백질 부족", color: "var(--color-error)", emoji: "⚠️" }
        : pRatio > 35
        ? { text: "단백질 과다", color: "var(--color-tertiary)", emoji: "📊" }
        : { text: "균형 양호", color: "var(--color-success)", emoji: "✅" };

    return {
      avgCal,
      avgProtein,
      eatenCount: eaten.length,
      macros,
      balance,
    };
  }, [weekly]);

  return (
    <div>
      {/* Mobile header — App Store Today 스타일 */}
      <header className="md:hidden mb-5">
        <p className="appstore-eyebrow">NUTRITION</p>
        <h1 className="appstore-title mt-1">영양 리포트</h1>
        <p className="text-[12px] text-text-tertiary mt-1.5"
           style={{ fontFamily: "var(--font-ko)" }}>
          주간 탄·단·지 균형 + 식사별 목표
          <span className="font-mono ml-2 opacity-70">#{userId}</span>
        </p>
      </header>

      {/* Desktop header */}
      <div className="hidden md:flex items-start justify-between mb-6 gap-3">
        <div className="min-w-0">
          <h1 className="text-xl md:text-2xl font-heading font-bold text-text-primary uppercase tracking-tight">
            Nutrition
          </h1>
          <p className="text-[10px] md:text-xs text-text-tertiary uppercase tracking-[0.1em] mt-0.5">
            Weekly Balance &amp; AI Commentary
          </p>
          <p
            className="text-[11px] text-text-tertiary mt-0.5"
            style={{ fontFamily: "var(--font-ko)" }}
          >
            주간 탄·단·지 비율 추적 + NLP D5 NLG 리포트
          </p>
        </div>
        <div className="text-right flex-shrink-0 min-w-0 max-w-[40%]">
          <p className="text-[10px] text-text-tertiary uppercase tracking-[0.08em]">
            User ID
          </p>
          <p
            className="text-xs md:text-lg font-heading font-bold text-text-primary tracking-tight font-mono truncate"
            title={userId}
          >
            #{userId}
          </p>
        </div>
      </div>

      <MealEntryPanel userId={userId} />
      <MealHistoryList userId={userId} />

      {/* 식사별 영양 목표 (헤비 옵션 / 다중 식사 시간) */}
      <div className="mt-4">
        <MealTargetsCard userId={userId} />
      </div>

      {/* NLP NLG */}
      <AICommentCard userId={userId} />

      {/* Query-level error banner (mock fallback kicks in too but we still
          surface the failure so the user knows the data is cached/mock). */}
      {weeklyError && weekly.length === 0 && (
        <ErrorBanner
          className="mb-4"
          title="주간 영양 데이터 로드 실패"
          onRetry={() => refetchWeekly()}
        />
      )}

      {/* Stat Cards — uniform grid so mobile wrap is clean */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        <StatCard
          icon="🔥"
          label="Avg Calories"
          ko="평균 칼로리"
          value={`${stats.avgCal}kcal`}
          sub="일일 권장: 700kcal"
          color={
            stats.avgCal > 750 ? "var(--color-error)" : "var(--color-success)"
          }
        />
        <StatCard
          icon="🥩"
          label="Avg Protein"
          ko="평균 단백질"
          value={`${stats.avgProtein}g`}
          sub="권장: 25-35g"
          color={
            stats.avgProtein < 20
              ? "var(--color-error)"
              : "var(--color-success)"
          }
        />
        <StatCard
          icon={stats.balance.emoji}
          label="Balance"
          ko="영양 밸런스"
          value={stats.balance.text}
          color={stats.balance.color}
        />
        <StatCard
          icon="📅"
          label="Logged Days"
          ko="기록일수"
          value={`${stats.eatenCount}/5일`}
          sub="이번 주 기준"
        />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4 mb-6">
        <div className="lg:col-span-3">
          <CalorieTrend data={weekly} />
        </div>
        <div className="lg:col-span-2">
          <MacroDonut macros={stats.macros} />
        </div>
      </div>

      {/* Daily bars */}
      <DailyBreakdown data={weekly} />
    </div>
  );
}
