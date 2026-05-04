"use client";

import { useNLPHealth } from "@/lib/queries";
import { Activity } from "lucide-react";

type ModuleState = "ok" | "skip" | "pending" | "err";

function classify(v: string): ModuleState {
  if (v === "ok") return "ok";
  if (v === "skipped") return "skip";
  if (v.startsWith("error")) return "err";
  return "pending";
}

const COLORS: Record<ModuleState, string> = {
  ok: "text-success border-success/40 bg-success/10",
  skip: "text-text-tertiary border-outline/20 bg-surface-2",
  pending: "text-warning border-warning/40 bg-warning/10",
  err: "text-error border-error/40 bg-error/10",
};

export default function HealthStrip() {
  const { data, isLoading, error } = useNLPHealth();

  return (
    <div className="bg-surface-1 border border-outline/15 rounded-sm p-4 mb-4">
      <div className="flex items-center gap-2 mb-3">
        <Activity size={14} className="text-primary" />
        <span className="text-[11px] font-bold uppercase tracking-[0.1em] text-text-secondary">
          NLP Module Health
        </span>
        <span
          className="text-[10px] text-text-tertiary"
          style={{ fontFamily: "var(--font-ko)" }}
        >
          모듈별 준비 상태
        </span>
        <span className="ml-auto text-[10px] font-mono text-text-tertiary">
          {data?.version ? `v${data.version}` : "—"}
        </span>
      </div>

      {isLoading && (
        <div className="text-xs text-text-tertiary">로딩 중…</div>
      )}
      {!isLoading && error != null && (
        <div className="text-xs text-error font-mono">
          /nlp/health 호출 실패 — NLP API(8001) 실행 중인지 확인
        </div>
      )}
      {!isLoading && data && (
        <div className="flex flex-wrap gap-1.5">
          {Object.entries(data.modules).map(([k, v]) => {
            const state = classify(v);
            return (
              <span
                key={k}
                title={v}
                className={`text-[10px] font-mono font-semibold px-2.5 py-1 border rounded-sm ${COLORS[state]}`}
              >
                {k}
                <span className="ml-1.5 opacity-70">·</span>
                <span className="ml-1">{state}</span>
              </span>
            );
          })}
        </div>
      )}
    </div>
  );
}
