"use client";

import HealthStrip from "@/components/insights/HealthStrip";
import SentimentOverview from "@/components/insights/SentimentOverview";
import ABSARadarPanel from "@/components/insights/ABSARadarPanel";
import MenuNormalizerPlayground from "@/components/insights/MenuNormalizerPlayground";
import RAGStatsCard from "@/components/insights/RAGStatsCard";
import RoadmapCard from "@/components/insights/RoadmapCard";

export default function InsightsPage() {
  return (
    <div>
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-heading font-bold text-text-primary uppercase tracking-tight">
            NLP Insights
          </h1>
          <p className="text-xs text-text-tertiary uppercase tracking-[0.1em] mt-0.5">
            Module Status · Performance · Roadmap
          </p>
          <p
            className="text-[11px] text-text-tertiary mt-0.5"
            style={{ fontFamily: "var(--font-ko)" }}
          >
            NLP 4개 모듈의 상태와 성능을 한눈에 확인합니다
          </p>
        </div>
      </div>

      {/* Health Strip (full width) */}
      <HealthStrip />

      {/* Insights Grid — 2col on lg, RoadmapCard spans full width */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <SentimentOverview />
        <ABSARadarPanel />
        <MenuNormalizerPlayground />
        <RAGStatsCard />
        <div className="lg:col-span-2">
          <RoadmapCard />
        </div>
      </div>
    </div>
  );
}
