"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { Type, Loader2 } from "lucide-react";
import { apiFetchNLP } from "@/lib/api";
import { useMenuStats } from "@/lib/queries";
import type { MenuNormalizeOut, NormalizeMethod } from "@/lib/types";

const METHOD_COLORS: Record<NormalizeMethod, string> = {
  rule: "var(--color-success)",
  levenshtein: "#3B8BD4",
  embedding: "var(--color-tertiary)",
  none: "var(--color-text-tertiary)",
  error: "var(--color-error)",
};

function methodLabel(m: NormalizeMethod): string {
  return {
    rule: "RULE",
    levenshtein: "LEV",
    embedding: "EMB",
    none: "NONE",
    error: "ERR",
  }[m];
}

export default function MenuNormalizerPlayground() {
  const [raw, setRaw] = useState("매콤한 돼지 불백");
  const [result, setResult] = useState<MenuNormalizeOut | null>(null);

  const { data: stats } = useMenuStats();

  const normalize = useMutation({
    mutationFn: (name: string) =>
      apiFetchNLP<MenuNormalizeOut>("/nlp/menu/normalize", {
        method: "POST",
        body: JSON.stringify({ raw_name: name }),
      }),
    onSuccess: (data) => setResult(data),
  });

  const run = () => {
    if (!raw.trim() || normalize.isPending) return;
    normalize.mutate(raw.trim());
  };

  const pieData = stats?.by_method
    ? Object.entries(stats.by_method).map(([k, v]) => ({
        name: k,
        value: v,
        color: METHOD_COLORS[k as NormalizeMethod] || "#888",
      }))
    : [];

  return (
    <div className="bg-surface-1 border border-outline/15 rounded-sm p-5 h-full">
      <div className="flex items-center gap-2 mb-1">
        <Type size={16} className="text-primary" />
        <h3 className="text-base font-heading font-bold text-text-primary uppercase tracking-[0.04em]">
          Menu Normalizer
        </h3>
      </div>
      <p
        className="text-[11px] text-text-tertiary mb-4"
        style={{ fontFamily: "var(--font-ko)" }}
      >
        B1 — 규칙 + Levenshtein + Sentence-BERT 하이브리드 정규화
      </p>

      {/* Input row */}
      <div className="flex gap-2 mb-3">
        <input
          type="text"
          value={raw}
          onChange={(e) => setRaw(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") run();
          }}
          placeholder="메뉴명 입력 (예: 매콤한 돼지 불백)"
          className="flex-1 bg-surface-2 border border-outline/20 px-3 py-2 text-sm rounded-sm outline-none focus:border-primary/40 text-text-primary"
          style={{ fontFamily: "var(--font-ko)" }}
        />
        <button
          onClick={run}
          disabled={normalize.isPending || !raw.trim()}
          className="flex items-center gap-1.5 px-4 py-2 text-xs font-bold uppercase tracking-wider bg-primary text-background rounded-sm hover:bg-primary-dark transition-colors disabled:opacity-40"
        >
          {normalize.isPending ? (
            <Loader2 size={12} className="animate-spin" />
          ) : (
            "정규화"
          )}
        </button>
      </div>

      {/* Result */}
      {result && (
        <div className="bg-surface-2 border border-outline/15 rounded-sm p-3 mb-4 text-xs">
          <div className="flex items-center gap-2 mb-1.5">
            <span
              className="text-[9px] font-mono font-bold px-2 py-0.5 border rounded-sm"
              style={{
                color: METHOD_COLORS[result.method],
                borderColor: `color-mix(in srgb, ${METHOD_COLORS[result.method]} 35%, transparent)`,
                background: `color-mix(in srgb, ${METHOD_COLORS[result.method]} 12%, transparent)`,
              }}
            >
              {methodLabel(result.method)}
            </span>
            <span className="text-text-tertiary text-[10px] font-mono">
              conf {(result.confidence * 100).toFixed(0)}% · {result.latency_ms}ms
            </span>
          </div>
          <div className="text-text-tertiary">
            cleaned:{" "}
            <span
              className="text-text-primary font-semibold"
              style={{ fontFamily: "var(--font-ko)" }}
            >
              {result.cleaned || "—"}
            </span>
          </div>
          <div className="text-text-tertiary mt-1">
            matched:{" "}
            <span
              className="text-text-primary font-semibold"
              style={{ fontFamily: "var(--font-ko)" }}
            >
              {result.matched_name || "매칭 실패"}
            </span>
          </div>
        </div>
      )}

      {normalize.isError && (
        <div className="text-xs text-error font-mono mb-3">
          {String(normalize.error)}
        </div>
      )}

      {/* Stats donut */}
      {pieData.length > 0 && stats && (
        <div className="border-t border-dashed border-outline/20 pt-3">
          <div className="text-[10px] font-bold text-text-secondary uppercase tracking-[0.1em] mb-2">
            Cumulative · {stats.total} calls · hit rate{" "}
            <span className="text-primary">
              {(stats.hit_rate * 100).toFixed(0)}%
            </span>
          </div>
          <ResponsiveContainer width="100%" height={150}>
            <PieChart>
              <Pie
                data={pieData}
                dataKey="value"
                nameKey="name"
                innerRadius={30}
                outerRadius={55}
              >
                {pieData.map((d, i) => (
                  <Cell key={i} fill={d.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  background: "var(--color-surface-2)",
                  border: "1px solid var(--color-outline)",
                  borderRadius: 6,
                  fontSize: 11,
                }}
              />
              <Legend wrapperStyle={{ fontSize: 10 }} iconSize={8} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
