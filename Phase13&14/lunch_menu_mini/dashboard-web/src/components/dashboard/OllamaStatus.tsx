"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useNLPHealth, useNLPSettings, useOllamaModels } from "@/lib/queries";

/**
 * Ollama / NLP module status card.
 *
 * - Reads /nlp/health → module statuses
 * - Reads /nlp/models → list of installed models (approximate RAM footprint)
 */
export default function OllamaStatus() {
  const queryClient = useQueryClient();
  const { data: health, isLoading } = useNLPHealth();
  const { data: models } = useOllamaModels();
  const { data: settings } = useNLPSettings();

  const ok = health?.status === "ok";
  const modules = health?.modules ?? {};

  const activeModel =
    settings?.chat_model ||
    models?.active_chat ||
    models?.models?.[0]?.name ||
    "—";
  const reportModel =
    settings?.report_model || models?.active_report || "—";

  // Rough RAM estimate — sum of installed model sizes (strings like "4.1GB")
  const parseGb = (s?: string): number => {
    if (!s) return 0;
    const m = /([\d.]+)\s*GB/i.exec(s);
    return m ? parseFloat(m[1]) : 0;
  };
  const usedGb = (models?.models ?? []).reduce(
    (acc, m) => acc + parseGb(m.size),
    0
  );
  const totalGb = 16;
  const ramPct = totalGb > 0 ? (usedGb / totalGb) * 100 : 0;

  const handleReload = () => {
    queryClient.invalidateQueries({ queryKey: ["nlp"] });
  };

  return (
    <div className="bento-card relative overflow-hidden h-full">
      <h3 className="text-sm font-heading font-bold text-text-primary uppercase tracking-[0.06em] mb-1">
        System Status (NLP)
      </h3>
      <p
        className="text-[10px] text-text-tertiary mb-4"
        style={{ fontFamily: "var(--font-ko)" }}
      >
        시스템 상태
      </p>

      {/* Connection */}
      <div className="flex items-center gap-3 mb-5">
        <div
          className={`w-[10px] h-[10px] rounded-full ${
            ok
              ? "bg-primary shadow-[0_0_8px_rgba(232,89,60,0.6)]"
              : "bg-error shadow-[0_0_8px_rgba(255,113,108,0.6)]"
          }`}
        />
        <span
          className={`text-xs font-heading font-semibold uppercase ${
            ok ? "text-primary" : "text-error"
          }`}
        >
          {isLoading ? "Checking…" : ok ? "Connected" : "Disconnected"}
        </span>
      </div>

      {/* Models */}
      <div className="mb-5 space-y-3">
        <div>
          <span className="text-[10px] text-text-tertiary uppercase tracking-[0.08em] font-bold">
            Chat Model
          </span>
          <div className="text-sm font-semibold text-text-primary font-mono mt-1 truncate">
            {activeModel}
          </div>
        </div>
        <div>
          <span className="text-[10px] text-text-tertiary uppercase tracking-[0.08em] font-bold">
            Report Model
          </span>
          <div className="text-sm font-semibold text-text-secondary font-mono mt-1 truncate">
            {reportModel}
          </div>
        </div>
      </div>

      {/* RAM gauge */}
      <div>
        <div className="flex justify-between text-[10px] uppercase tracking-[0.1em] font-bold mb-1.5">
          <span className="text-text-secondary">Models on disk</span>
          <span className="text-primary">
            {usedGb.toFixed(1)}GB / ~{totalGb}GB
          </span>
        </div>
        <div className="h-[10px] bg-surface-3 border border-outline/20 p-[2px]">
          <div
            className="h-full bg-primary transition-all duration-500"
            style={{ width: `${Math.min(ramPct, 100)}%` }}
          />
        </div>
      </div>

      {/* Module chips */}
      <div className="mt-5 flex flex-wrap gap-1.5">
        {Object.entries(modules).map(([k, v]) => {
          const state =
            v === "ok" ? "ok" : v === "skipped" ? "skip" : v.startsWith("error") ? "err" : "pending";
          const color =
            state === "ok"
              ? "text-success border-success/40"
              : state === "err"
              ? "text-error border-error/40"
              : state === "skip"
              ? "text-text-tertiary border-outline/20"
              : "text-warning border-warning/40";
          return (
            <span
              key={k}
              className={`text-[9px] font-mono font-semibold px-2 py-0.5 border rounded-sm ${color}`}
              title={v}
            >
              {k}
            </span>
          );
        })}
      </div>

      {/* Reload */}
      <button
        onClick={handleReload}
        className="mt-5 w-full py-2 border border-outline/30 text-[10px] font-bold uppercase tracking-wider text-text-secondary hover:text-text-primary hover:border-outline/50 transition-colors"
      >
        Refresh Status
        <span
          className="block text-[9px] font-normal normal-case tracking-normal opacity-60 mt-0.5"
          style={{ fontFamily: "var(--font-ko)" }}
        >
          상태 새로고침
        </span>
      </button>
    </div>
  );
}
