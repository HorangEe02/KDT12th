"use client";

import { Map, Check, Circle } from "lucide-react";

interface RoadmapStep {
  label: string;
  ko: string;
  done: boolean;
  current?: boolean;
}

const STEPS: RoadmapStep[] = [
  { label: "Step 0 · shared (db / logger / ollama)", ko: "공용 유틸", done: true },
  { label: "Step 1 · A1 Sentiment (KcELECTRA)", ko: "리뷰 감성 모델", done: true },
  { label: "Step 2 · B1 Menu Normalizer", ko: "메뉴 정규화 (104종)", done: true },
  { label: "Step 3 · D3 RAG Chatbot", ko: "RAG 상담", done: true },
  { label: "Step 4 · D5 NLG Weekly Report", ko: "주간 리포트", done: true },
  { label: "Step 5 · FastAPI + Next.js 통합", ko: "통합 레이어", done: true },
  { label: "M9 · /nlp/models + runtime model swap", ko: "모델 선택 (Gemini)", done: true },
  // Phase 13&14
  { label: "Phase 13 · Auth + RBAC + Admin Console", ko: "JWT 인증·관리자 콘솔", done: true },
  { label: "Phase 13 · Firebase Hosting + Cloudflare Tunnel", ko: "외부 데모 배포", done: true },
  { label: "Phase 14 · 자연어 영양 입력 + 식약처 dual-provider", ko: "Nutrition NL + data.go.kr", done: true },
  {
    label: "Phase 15 · 감성 분석 데이터 활성화 + Insights UI 마무리",
    ko: "Sentiment 시드 + UX",
    done: true,
  },
  {
    label: "Phase 16 · A2 ABSA / B2 Food NER 학습 가중치",
    ko: "KcELECTRA ABSA macro_f1=0.98 + KoELECTRA NER trained",
    done: true,
  },
  {
    label: "Phase 17 · E1 Embedding CF Recommender 활성화",
    ko: "협업 필터링 (사용자×식당 임베딩) + 라우터 backend=embedding_cf",
    done: true,
  },
  {
    label: "Phase 18 · 라벨링 데이터 확장 + NER F1 향상",
    ko: "100→600 샘플, entity_f1 0.68→0.97 (모든 클래스 커버)",
    done: true,
  },
];

export default function RoadmapCard() {
  return (
    <div className="bg-surface-1 border border-outline/15 rounded-sm p-5 h-full">
      <div className="flex items-center gap-2 mb-1">
        <Map size={16} className="text-tertiary" />
        <h3 className="text-base font-heading font-bold text-text-primary uppercase tracking-[0.04em]">
          AI NLP Roadmap
        </h3>
      </div>
      <p
        className="text-[11px] text-text-tertiary mb-4"
        style={{ fontFamily: "var(--font-ko)" }}
      >
        Mini NLP 진행 단계
      </p>

      <div className="space-y-1">
        {STEPS.map((s, i) => (
          <div
            key={i}
            className={`flex items-start gap-3 py-2 px-2 rounded-sm border-l-2 ${
              s.current
                ? "border-primary bg-primary/5"
                : s.done
                ? "border-success/50"
                : "border-outline/20"
            }`}
          >
            <div
              className={`mt-0.5 w-4 h-4 rounded-full flex items-center justify-center flex-shrink-0 ${
                s.done
                  ? "bg-success/80 text-background"
                  : "border border-outline/30 bg-surface-2 text-text-tertiary"
              }`}
            >
              {s.done ? <Check size={10} strokeWidth={3} /> : <Circle size={6} />}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-[12px] font-semibold text-text-primary">
                {s.label}
                {s.current && (
                  <span className="ml-2 text-[9px] font-mono text-primary uppercase">
                    CURRENT
                  </span>
                )}
              </div>
              <div
                className="text-[10px] text-text-tertiary"
                style={{ fontFamily: "var(--font-ko)" }}
              >
                {s.ko}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
