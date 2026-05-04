"""
Phase 6 — Unified benchmark entrypoint.

Runs A2/B2/E1 comparisons and writes a single summary.md + summary.json.

Usage:
    # Hermetic dry-run (no model downloads, ~1 second):
    python -m nlp_research.evaluation.benchmark --module all --smoke

    # Real run (requires installed models + labelled data):
    python -m nlp_research.evaluation.benchmark --module all --sample-size 100
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from nlp_research.evaluation import (
    compare_a2_vs_a1,
    compare_b2_vs_b1,
    compare_e1_vs_popular,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "report" / "benchmarks"


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Phase 6 unified benchmark")
    ap.add_argument(
        "--module",
        choices=("a2", "b2", "e1", "all"),
        default="all",
    )
    ap.add_argument("--smoke", action="store_true", help="dummy weights, tiny sample")
    ap.add_argument("--sample-size", type=int, default=50)
    ap.add_argument("--seed-users", type=int, default=8)
    ap.add_argument("--use-sbert", action="store_true")
    ap.add_argument("--from-db", action="store_true")
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    return ap.parse_args()


def _row(module: str, metric: str, baseline: float, challenger: float) -> dict:
    return {
        "module": module,
        "metric": metric,
        "baseline": round(baseline, 4),
        "challenger": round(challenger, 4),
        "delta": round(challenger - baseline, 4),
    }


def run(args) -> dict[str, Any]:
    out_dir: Path = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    summary: dict[str, Any] = {
        "smoke": args.smoke,
        "results": {},
        "table": [],
    }

    if args.module in ("a2", "all"):
        seed = ROOT / "data" / "seed" / "absa_seed_50.jsonl"
        a2_result = compare_a2_vs_a1.run_comparison(
            seed_path=seed,
            sample_size=args.sample_size,
            smoke=args.smoke,
        )
        summary["results"]["a2"] = a2_result
        compare_a2_vs_a1.write_markdown(a2_result, out_dir / "a2_vs_a1.md")
        # Baseline = A1 majority overlap as 0.5 reference
        # (we treat overlap_rate>0.5 as a "win" for A2 — fully informative metric)
        summary["table"].append(_row("A2", "overlap_rate", 0.5, a2_result["overlap_rate"]))
        summary["table"].append(
            _row("A2", "mixed_recall", 0.0, a2_result["mixed_sentiment_recall"])
        )
        summary["table"].append(
            _row("A2", "latency_ms (a1)", a2_result["a1_latency_ms"], a2_result["a2_latency_ms"])
        )

    if args.module in ("b2", "all"):
        seed = ROOT / "data" / "seed" / "food_ner_seed_50.jsonl"
        b2_result = compare_b2_vs_b1.run_comparison(
            seed_path=seed,
            sample_size=args.sample_size,
            smoke=args.smoke,
        )
        summary["results"]["b2"] = b2_result
        compare_b2_vs_b1.write_markdown(b2_result, out_dir / "b2_vs_b1.md")
        summary["table"].append(
            _row("B2", "f1", b2_result["b1"]["f1"], b2_result["b2"]["f1"])
        )
        summary["table"].append(
            _row("B2", "recall", b2_result["b1"]["recall"], b2_result["b2"]["recall"])
        )
        summary["table"].append(
            _row(
                "B2",
                "allergen_recall",
                b2_result["b1"]["allergen_recall"],
                b2_result["b2"]["allergen_recall"],
            )
        )

    if args.module in ("e1", "all"):
        e1_result = compare_e1_vs_popular.run_comparison(
            seed_users=args.seed_users,
            smoke=args.smoke,
            use_sbert=args.use_sbert,
            from_db=args.from_db,
        )
        summary["results"]["e1"] = e1_result
        compare_e1_vs_popular.write_markdown(e1_result, out_dir / "e1_vs_popular.md")
        pop = e1_result.get("popular", {})
        e1m = e1_result.get("e1", {})
        summary["table"].append(
            _row("E1", "hit@5", pop.get("hit@5", 0.0), e1m.get("hit@5", 0.0))
        )
        summary["table"].append(
            _row("E1", "ndcg@10", pop.get("ndcg@10", 0.0), e1m.get("ndcg@10", 0.0))
        )
        summary["table"].append(
            _row("E1", "coverage", pop.get("coverage", 0.0), e1m.get("coverage", 0.0))
        )

    return summary


def write_summary(summary: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    lines = [
        "# Phase 6 Benchmark Summary",
        "",
        f"- smoke mode: **{summary['smoke']}**",
        "",
        "| Module | Metric | Baseline | Challenger | Δ |",
        "|---|---|---|---|---|",
    ]
    for row in summary["table"]:
        lines.append(
            f"| {row['module']} | {row['metric']} | "
            f"{row['baseline']:.4f} | {row['challenger']:.4f} | "
            f"{row['delta']:+.4f} |"
        )
    lines.append("")
    lines.append("## Per-module artefacts")
    for name in ("a2_vs_a1", "b2_vs_b1", "e1_vs_popular"):
        path = out_dir / f"{name}.md"
        if path.exists():
            lines.append(f"- [{name}.md](./{name}.md)")
    (out_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    summary = run(args)
    write_summary(summary, args.output_dir)
    print(f"[benchmark] wrote {args.output_dir}/summary.md")
    print(f"[benchmark] wrote {args.output_dir}/summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
