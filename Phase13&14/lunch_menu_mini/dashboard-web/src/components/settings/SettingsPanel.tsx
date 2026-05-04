"use client";

import { useState, useEffect, useCallback } from "react";
import { useTheme } from "next-themes";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  X,
  Sun,
  Moon,
  Languages,
  AlertCircle,
  Check,
  Loader2,
  Cpu,
} from "lucide-react";
import { useOllamaModels, useNLPSettings } from "@/lib/queries";
import { apiFetchNLP } from "@/lib/api";
import type {
  ModelRole,
  SettingsUpdateRequest,
  SettingsUpdateResponse,
} from "@/lib/types";
import PreferencesSection from "./PreferencesSection";

/**
 * Settings slide-over (M9).
 *
 * - Theme toggle (dark / light)
 * - LLM model dropdown — reads /nlp/models, PUTs /nlp/settings/model
 *   Separate role selector (chat / report / both)
 * - AI response language toggle — localStorage backed
 * - Default user id input — localStorage backed
 */
// Phase 14: ollama "provider:model" 접두사 + gemini 모델 인식
const CHAT_MODEL_PREFIXES = [
  "qwen3",
  "qwen2.5",
  "gemma3",
  "gemma4",
  "llama3",
  "exaone",
  "nemotron",
  "gemini",
];
function isChatModel(name: string): boolean {
  const lower = name.toLowerCase();
  // strip "provider:" prefix
  const bare = lower.includes(":") ? lower.split(":").slice(1).join(":") : lower;
  return CHAT_MODEL_PREFIXES.some((p) => bare.startsWith(p) || lower.startsWith(p));
}

function providerBadgeClass(provider?: string): string {
  return provider === "gemini"
    ? "bg-tertiary/15 text-tertiary border-tertiary/30"
    : "bg-secondary/15 text-secondary border-secondary/30";
}

export default function SettingsPanel({ onClose }: { onClose: () => void }) {
  const { theme, setTheme } = useTheme();
  const queryClient = useQueryClient();
  const [mounted, setMounted] = useState(false);
  const [language, setLanguage] = useState<"en" | "ko" | "both">("both");
  const [userId, setUserId] = useState("1");
  const [selectedModel, setSelectedModel] = useState("");
  const [role, setRole] = useState<ModelRole>("chat");

  const { data: modelsData, error: modelsError } = useOllamaModels();
  const { data: settingsData } = useNLPSettings();

  useEffect(() => {
    setMounted(true);
    const savedLang = localStorage.getItem("p11_language_pref");
    if (savedLang === "en" || savedLang === "ko" || savedLang === "both") {
      setLanguage(savedLang);
    }
    const savedUser = localStorage.getItem("p11_user_id");
    if (savedUser) setUserId(savedUser);
  }, []);

  // Sync selected model from backend on first load
  useEffect(() => {
    if (selectedModel) return;
    const fromServer =
      role === "report"
        ? settingsData?.report_model || modelsData?.active_report
        : settingsData?.chat_model || modelsData?.active_chat;
    if (fromServer) setSelectedModel(fromServer);
  }, [selectedModel, role, settingsData, modelsData]);

  const handleLanguageChange = useCallback((lang: "en" | "ko" | "both") => {
    setLanguage(lang);
    localStorage.setItem("p11_language_pref", lang);
  }, []);

  const handleUserIdChange = useCallback((v: string) => {
    setUserId(v);
    localStorage.setItem("p11_user_id", v);
  }, []);

  // Apply model mutation — PUT /nlp/settings/model
  const applyMutation = useMutation({
    mutationFn: (payload: SettingsUpdateRequest) =>
      apiFetchNLP<SettingsUpdateResponse>("/nlp/settings/model", {
        method: "PUT",
        body: JSON.stringify(payload),
      }),
    onSuccess: () => {
      // Refresh everything that depends on the active model
      queryClient.invalidateQueries({ queryKey: ["nlp", "settings"] });
      queryClient.invalidateQueries({ queryKey: ["nlp", "models"] });
      queryClient.invalidateQueries({ queryKey: ["nlp", "health"] });
      queryClient.invalidateQueries({ queryKey: ["nlp", "chatbot", "stats"] });
    },
  });

  const allModels = modelsData?.models ?? [];
  const chatModels = allModels.filter((m) => isChatModel(m.name));
  const displayModels = chatModels.length > 0 ? chatModels : allModels;

  // Phase 14: role 별 활성 모델
  const activeModel =
    role === "report"
      ? settingsData?.report_model ?? modelsData?.active_report ?? ""
      : role === "tools"
        ? settingsData?.tools_model ?? modelsData?.active_tools ?? ""
        : settingsData?.chat_model ?? modelsData?.active_chat ?? "";
  const isDirty = selectedModel && selectedModel !== activeModel;

  // (provider별 표시는 아래 chat/report/tools 인디케이터 카드에서 처리)

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-background/40 backdrop-blur-sm z-50"
        onClick={onClose}
      />

      {/* Panel */}
      <div className="fixed top-0 right-0 h-full w-80 bg-surface-1 border-l border-outline/15 z-50 flex flex-col overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-outline/10">
          <div>
            <h2 className="text-sm font-heading font-bold text-text-primary uppercase tracking-[0.06em]">
              Settings
            </h2>
            <p
              className="text-[10px] text-text-tertiary mt-0.5"
              style={{ fontFamily: "var(--font-ko)" }}
            >
              설정
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-text-tertiary hover:text-text-primary transition-colors"
          >
            <X size={16} />
          </button>
        </div>

        <div className="p-5 space-y-6">
          {/* Theme */}
          <div>
            <h4 className="text-[10px] font-bold text-text-secondary uppercase tracking-[0.1em] mb-3">
              Appearance{" "}
              <span
                className="text-[9px] font-normal normal-case tracking-normal text-text-tertiary opacity-80"
                style={{ fontFamily: "var(--font-ko)" }}
              >
                테마
              </span>
            </h4>
            {mounted && (
              <div className="flex gap-2">
                <button
                  onClick={() => setTheme("dark")}
                  className={`flex-1 flex items-center justify-center gap-2 py-2.5 border text-[11px] font-bold uppercase transition-colors ${
                    theme === "dark"
                      ? "border-primary/30 bg-primary/10 text-primary"
                      : "border-outline/15 text-text-tertiary hover:text-text-secondary"
                  }`}
                >
                  <Moon size={14} />
                  Dark
                </button>
                <button
                  onClick={() => setTheme("light")}
                  className={`flex-1 flex items-center justify-center gap-2 py-2.5 border text-[11px] font-bold uppercase transition-colors ${
                    theme === "light"
                      ? "border-primary/30 bg-primary/10 text-primary"
                      : "border-outline/15 text-text-tertiary hover:text-text-secondary"
                  }`}
                >
                  <Sun size={14} />
                  Light
                </button>
              </div>
            )}
          </div>

          {/* LLM Model */}
          <div>
            <h4 className="text-[10px] font-bold text-text-secondary uppercase tracking-[0.1em] mb-3">
              <Cpu size={12} className="inline mr-1.5 -mt-0.5" />
              LLM Model{" "}
              <span
                className="text-[9px] font-normal normal-case tracking-normal text-text-tertiary opacity-80"
                style={{ fontFamily: "var(--font-ko)" }}
              >
                Gemini · Ollama 모델 선택
              </span>
            </h4>

            {/* Current chat/report/tools indicators (Phase 14: provider 뱃지 포함) */}
            <div className="space-y-1 mb-3 text-[10px] font-mono">
              {([
                {
                  label: "chat",
                  model: settingsData?.chat_model || modelsData?.active_chat || "—",
                  provider:
                    settingsData?.chat_provider ||
                    modelsData?.active_chat_provider,
                },
                {
                  label: "report",
                  model:
                    settingsData?.report_model ||
                    modelsData?.active_report ||
                    "—",
                  provider:
                    settingsData?.report_provider ||
                    modelsData?.active_report_provider,
                },
                {
                  label: "tools",
                  model:
                    settingsData?.tools_model ||
                    modelsData?.active_tools ||
                    "—",
                  provider:
                    settingsData?.tools_provider ||
                    modelsData?.active_tools_provider,
                },
              ] as const).map((row) => (
                <div
                  key={row.label}
                  className="flex items-center justify-between px-2.5 py-1.5 bg-surface-2 border border-outline/10 gap-2"
                >
                  <span className="text-text-tertiary shrink-0">{row.label}</span>
                  <div className="flex items-center gap-1.5 min-w-0">
                    {row.provider && (
                      <span
                        className={`px-1.5 py-0.5 text-[8px] font-bold uppercase border ${providerBadgeClass(row.provider)}`}
                      >
                        {row.provider}
                      </span>
                    )}
                    <span className="text-text-primary truncate max-w-[140px]">
                      {row.model}
                    </span>
                  </div>
                </div>
              ))}
            </div>

            {/* Role toggle (Phase 14: tools, all 추가) */}
            <div className="grid grid-cols-5 gap-1 mb-2">
              {(["chat", "report", "tools", "both", "all"] as const).map((r) => (
                <button
                  key={r}
                  onClick={() => {
                    setRole(r);
                    applyMutation.reset();
                  }}
                  className={`py-1.5 text-[10px] font-bold uppercase tracking-wider border transition-colors ${
                    role === r
                      ? "border-primary/40 bg-primary/10 text-primary"
                      : "border-outline/15 text-text-tertiary hover:text-text-secondary"
                  }`}
                  title={
                    r === "both"
                      ? "chat + report"
                      : r === "all"
                        ? "chat + report + tools"
                        : r
                  }
                >
                  {r}
                </button>
              ))}
            </div>

            {displayModels.length > 0 ? (
              <div className="space-y-2">
                <select
                  value={selectedModel || activeModel || displayModels[0].name}
                  onChange={(e) => {
                    setSelectedModel(e.target.value);
                    applyMutation.reset();
                  }}
                  className="w-full bg-surface-2 border border-outline/15 px-3 py-2 text-xs text-text-secondary outline-none rounded-sm focus:border-primary/40 font-mono"
                >
                  {displayModels.map((m) => {
                    const tag = m.provider ? `[${m.provider}] ` : "";
                    return (
                      <option key={m.name} value={m.name}>
                        {tag}{m.name} {m.size ? `(${m.size})` : ""}
                      </option>
                    );
                  })}
                </select>

                {chatModels.length > 0 && chatModels.length < allModels.length && (
                  <p className="text-[9px] text-text-tertiary">
                    {chatModels.length}/{allModels.length} 대화 적합 모델 표시
                  </p>
                )}

                {isDirty && (
                  <button
                    onClick={() =>
                      applyMutation.mutate({ model: selectedModel, role })
                    }
                    disabled={applyMutation.isPending}
                    className="w-full flex items-center justify-center gap-2 py-2 bg-primary text-background text-[11px] font-bold uppercase hover:bg-primary-dark transition-colors disabled:opacity-50"
                  >
                    {applyMutation.isPending ? (
                      <>
                        <Loader2 size={12} className="animate-spin" />{" "}
                        Applying…
                      </>
                    ) : (
                      <>
                        <Check size={12} /> Apply to {role}
                      </>
                    )}
                  </button>
                )}

                {applyMutation.isSuccess && (
                  <p className="text-[10px] text-success flex items-center gap-1">
                    <Check size={10} /> {applyMutation.data.role} ={" "}
                    {applyMutation.data.model}
                  </p>
                )}
                {applyMutation.isError && (
                  <div className="text-[10px] text-error flex items-start gap-1.5">
                    <AlertCircle size={12} className="flex-shrink-0 mt-0.5" />
                    <div>
                      <p>Failed to apply model</p>
                      <p className="text-[9px] text-text-tertiary mt-0.5 font-mono break-all">
                        {String(applyMutation.error)}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-[10px] text-text-tertiary flex items-start gap-1.5">
                <AlertCircle size={12} className="flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-mono">
                    {modelsError ? "/nlp/models 호출 실패" : "모델 목록 없음"}
                  </p>
                  <p
                    className="mt-1"
                    style={{ fontFamily: "var(--font-ko)" }}
                  >
                    NLP API(포트 8001)가 실행 중인지 확인하세요.
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Personalization (Phase 3) */}
          <div className="pt-4 border-t border-outline/10">
            <PreferencesSection />
          </div>

          {/* AI Language */}
          <div>
            <h4 className="text-[10px] font-bold text-text-secondary uppercase tracking-[0.1em] mb-3">
              <Languages size={12} className="inline mr-1.5 -mt-0.5" />
              AI Language{" "}
              <span
                className="text-[9px] font-normal normal-case tracking-normal text-text-tertiary opacity-80"
                style={{ fontFamily: "var(--font-ko)" }}
              >
                AI 응답 언어
              </span>
            </h4>
            <div className="flex gap-1.5">
              {(
                [
                  { value: "en", label: "English" },
                  { value: "ko", label: "한국어" },
                  { value: "both", label: "Both" },
                ] as const
              ).map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => handleLanguageChange(opt.value)}
                  className={`flex-1 py-2 border text-[11px] font-bold uppercase transition-colors ${
                    language === opt.value
                      ? "border-primary/30 bg-primary/10 text-primary"
                      : "border-outline/15 text-text-tertiary hover:text-text-secondary"
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Default User ID */}
          <div>
            <h4 className="text-[10px] font-bold text-text-secondary uppercase tracking-[0.1em] mb-3">
              Default User ID{" "}
              <span
                className="text-[9px] font-normal normal-case tracking-normal text-text-tertiary opacity-80"
                style={{ fontFamily: "var(--font-ko)" }}
              >
                기본 사용자
              </span>
            </h4>
            <input
              type="number"
              min={1}
              value={userId}
              onChange={(e) => handleUserIdChange(e.target.value)}
              className="w-full bg-surface-2 border border-outline/15 px-3 py-2 text-xs text-text-secondary outline-none rounded-sm focus:border-primary/40 font-mono"
            />
            <p
              className="text-[9px] text-text-tertiary mt-1.5"
              style={{ fontFamily: "var(--font-ko)" }}
            >
              Nutrition / Concierge 탭에서 사용됩니다.
            </p>
          </div>

          {/* Scoring Weights Info */}
          <div>
            <h4 className="text-[10px] font-bold text-text-secondary uppercase tracking-[0.1em] mb-3">
              Scoring Weights (v1){" "}
              <span
                className="text-[9px] font-normal normal-case tracking-normal text-text-tertiary opacity-80"
                style={{ fontFamily: "var(--font-ko)" }}
              >
                가중치
              </span>
            </h4>
            <div className="space-y-2">
              {[
                { label: "Distance", value: "30%", color: "var(--color-primary)" },
                { label: "Weather", value: "20%", color: "var(--color-secondary)" },
                { label: "Nutrition", value: "20%", color: "var(--color-tertiary)" },
                { label: "Team Pref", value: "30%", color: "var(--color-success)" },
              ].map((w) => (
                <div key={w.label} className="flex items-center gap-3">
                  <span className="text-[10px] text-text-tertiary w-24">
                    {w.label}
                  </span>
                  <div className="flex-1 h-1.5 bg-surface-3 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full"
                      style={{ width: w.value, background: w.color }}
                    />
                  </div>
                  <span className="text-[10px] font-mono text-text-secondary w-8 text-right">
                    {w.value}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Version */}
          <div className="pt-4 border-t border-outline/10">
            <div className="space-y-1 text-[10px] font-mono text-text-tertiary">
              <div>오늘 뭐 먹지 · v0.5</div>
              <div>Next.js 16 + React 19</div>
              <div>FastAPI · NLP 11 endpoints</div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
