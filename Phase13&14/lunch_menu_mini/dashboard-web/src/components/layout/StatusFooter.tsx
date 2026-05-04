"use client";

import { useNLPHealth } from "@/lib/queries";
import { DEFAULT_USER_ID, LUNCH_API, NLP_API } from "@/lib/api";

export default function StatusFooter() {
  const { data: health } = useNLPHealth();

  const nlpOk = health?.status === "ok";
  const modules = health?.modules ?? {};
  const ragOk =
    modules["rag_chatbot_index"] === "ok" ||
    modules["rag_chatbot_index"] === "skipped";
  const dbOk = modules["db"] === "ok";

  return (
    <footer className="hidden md:flex fixed bottom-0 left-0 right-0 z-50 h-10 bg-background border-t border-outline/15 items-center justify-center gap-8 px-6 font-mono text-[10px] text-text-tertiary">
      <span>
        <span className={nlpOk ? "text-success" : "text-error"}>●</span>{" "}
        NLP API:{" "}
        <span className="text-text-primary font-semibold">
          {health?.status ?? "…"}
        </span>
      </span>
      <span title={`LUNCH: ${LUNCH_API} · NLP: ${NLP_API} · USER: ${DEFAULT_USER_ID}`}>
        LUNCH API:{" "}
        <span className="text-text-secondary">{LUNCH_API}</span>
      </span>
      <span>
        DB{" "}
        <span className={`font-semibold ${dbOk ? "text-success" : "text-text-tertiary"}`}>
          {dbOk ? "ONLINE" : "PENDING"}
        </span>
      </span>
      <span>
        RAG{" "}
        <span className={`font-semibold ${ragOk ? "text-success" : "text-text-tertiary"}`}>
          {ragOk ? "READY" : "WARMING"}
        </span>
      </span>
      <span>
        USER{" "}
        <span className="text-text-secondary">#{DEFAULT_USER_ID}</span>
      </span>
    </footer>
  );
}
