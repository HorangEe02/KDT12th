"""
LLM-based ABSA labeling via Ollama.

Reads unique reviews from Phase 5 DB, prompts an Ollama model to extract
aspect-sentiment pairs, and writes `{text, aspects, source: "gold_llm"}` JSONL.

Usage:
    python -m nlp_research.labeling.llm_label_absa \
        --db   lunch-optimizer/database/mini.db \
        --model qwen3.5:latest \
        --output nlp_research/data/labeled/absa/gold_llm.jsonl
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

OLLAMA_URL = "http://localhost:11434/api/generate"

ASPECTS = ("taste", "price", "service", "hygiene", "ambience")
SENTIMENTS = ("positive", "neutral", "negative")

PROMPT = """너는 한국어 음식점 리뷰 분석가다. 아래 리뷰에서 언급된 속성(aspect)과 각 속성의 감성(sentiment)을 JSON 배열로만 출력해라.

속성 종류 (5개 중에서만 선택):
- taste: 맛
- price: 가격
- service: 서비스/직원
- hygiene: 위생/청결
- ambience: 분위기/인테리어/소음

감성 종류:
- positive, neutral, negative

규칙:
1. 언급된 속성만 포함 (유추 금지)
2. 같은 리뷰에 여러 속성이 있으면 모두 포함
3. 반드시 JSON 배열만 출력, 설명/주석 금지
4. 예시 형식: [ObjectWithAspectAndSentiment, ...]

리뷰: "__TEXT__"

JSON:"""


def ollama_generate(model: str, prompt: str, timeout: int = 60) -> str:
    body = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 500},
    }).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_URL, data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data.get("response", "")


_JSON_ARRAY_RE = re.compile(r"\[\s*\{.*?\}\s*\]", re.DOTALL)


def parse_aspects(raw: str) -> list[dict]:
    """Extract first JSON array from LLM output and validate each item."""
    m = _JSON_ARRAY_RE.search(raw)
    if not m:
        return []
    try:
        items = json.loads(m.group(0))
    except json.JSONDecodeError:
        return []
    cleaned = []
    for it in items:
        if not isinstance(it, dict):
            continue
        asp = it.get("aspect")
        sent = it.get("sentiment")
        if asp in ASPECTS and sent in SENTIMENTS:
            cleaned.append({"aspect": asp, "sentiment": sent})
    # dedupe by aspect (keep first)
    seen = set()
    out = []
    for it in cleaned:
        if it["aspect"] in seen:
            continue
        seen.add(it["aspect"])
        out.append(it)
    return out


def load_unique_reviews(db_path: Path) -> list[str]:
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute("SELECT DISTINCT text FROM reviews ORDER BY text").fetchall()
    finally:
        conn.close()
    return [r[0] for r in rows]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", type=Path, required=True)
    ap.add_argument("--model", default="exaone3.5:latest")
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--limit", type=int, default=0, help="0 = all")
    args = ap.parse_args()

    if not args.db.exists():
        print(f"[llm_label] DB not found: {args.db}", file=sys.stderr)
        return 2

    reviews = load_unique_reviews(args.db)
    if args.limit:
        reviews = reviews[: args.limit]
    print(f"[llm_label] {len(reviews)} unique reviews, model={args.model}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    n_ok = n_empty = n_err = 0
    t0 = time.time()
    with args.output.open("w", encoding="utf-8") as f:
        for i, text in enumerate(reviews, 1):
            try:
                raw = ollama_generate(args.model, PROMPT.replace("__TEXT__", text))
                aspects = parse_aspects(raw)
            except (urllib.error.URLError, TimeoutError) as e:
                print(f"[{i}/{len(reviews)}] ERROR: {e}", file=sys.stderr)
                n_err += 1
                continue
            if not aspects:
                n_empty += 1
                print(f"[{i}/{len(reviews)}] EMPTY: {text[:30]}…")
                continue
            row = {"text": text, "aspects": aspects, "source": "gold_llm"}
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            n_ok += 1
            if i % 10 == 0:
                elapsed = time.time() - t0
                print(f"[{i}/{len(reviews)}] ok={n_ok} empty={n_empty} err={n_err} "
                      f"elapsed={elapsed:.1f}s")

    print(f"[llm_label] done: ok={n_ok} empty={n_empty} err={n_err}")
    print(f"[llm_label] wrote → {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
