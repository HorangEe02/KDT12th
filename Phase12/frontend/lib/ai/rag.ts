/**
 * 경량 RAG — ChromaDB/임베딩 없이 tips.json (45 items) 대상 BM25-lite 키워드 매칭.
 * 포팅 단순화: src/ai/rag.py
 */
import "server-only";
import type { Tip } from "@/lib/types";
import { loadTips } from "@/lib/data/loaders";

/** 단순 한국어 토크나이저: 2-gram character windows + whitespace */
function tokenize(s: string): string[] {
  const lower = s.toLowerCase().trim();
  const words = lower.split(/\s+/).filter(Boolean);
  const grams: string[] = [];
  for (const w of words) {
    grams.push(w);
    for (let i = 0; i < w.length - 1; i++) grams.push(w.slice(i, i + 2));
  }
  return grams;
}

interface ScoredTip extends Tip {
  score: number;
}

export async function searchTips(
  query: string,
  opts: { stadium?: string; topK?: number } = {},
): Promise<ScoredTip[]> {
  const { stadium, topK = 3 } = opts;
  const tips = await loadTips();
  const qTokens = tokenize(query);
  if (qTokens.length === 0) return [];

  const scored: ScoredTip[] = tips.map((tip) => {
    const text = `${tip.tip} ${tip.category ?? ""}`;
    const tokens = tokenize(text);
    let score = 0;
    for (const q of qTokens) {
      if (tokens.includes(q)) score += 1;
      if (q.length >= 2 && text.includes(q)) score += 0.5;
    }
    if (stadium && tip.stadium === stadium) score += 2;
    return { ...tip, score };
  });

  return scored
    .filter((t) => t.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, topK);
}
