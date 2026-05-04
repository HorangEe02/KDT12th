# `nlp_research/report/`

## benchmarks/
`evaluation/benchmark.py` 산출물. gitignored.

| 파일 | 생성자 | 내용 |
|---|---|---|
| `summary.md` | benchmark.py | A2/B2/E1 통합 표 (baseline · challenger · Δ) |
| `summary.json` | benchmark.py | 같은 내용의 JSON (CI parsing 용) |
| `a2_vs_a1.md` | compare_a2_vs_a1.py | overlap rate · mixed-sentiment recall · latency |
| `b2_vs_b1.md` | compare_b2_vs_b1.py | DISH F1 · allergen recall · latency |
| `e1_vs_popular.md` | compare_e1_vs_popular.py | LOO Hit@K · NDCG@10 · Coverage · Diversity |

## (선택) paper_draft.md
논문 초안. Phase 6 후속 단계에서 작성.
