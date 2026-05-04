"""
A2 ABSA training script.

Usage:
    python -m nlp_research.models.absa.train \
        --config configs/absa.yaml \
        --data data/seed/absa_seed_50.jsonl \
        --output checkpoints/absa/v1

With --dry-run, runs a single epoch on 10 samples without saving weights
(used by CI smoke tests and by benchmark.py --smoke mode).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from nlp_research.models.absa.dataset import (
    ASPECT_KO,
    build_hf_dataset,
    load_absa_triples,
)
from nlp_research.models.absa.model import build_model
from nlp_research.training.data_loader import stratified_split
from nlp_research.training.metrics import compute_classification_metrics


def _load_yaml(path: Path) -> dict:
    import yaml
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Train A2 ABSA model")
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--data", type=Path, required=True, help="Seed JSONL path")
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--dry-run", action="store_true", help="Smoke test mode")
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    if not args.data.exists():
        print(f"[train] data file not found: {args.data}", file=sys.stderr)
        return 2

    config = _load_yaml(args.config)
    triples = load_absa_triples(args.data)
    print(f"[train] loaded {len(triples)} triples from {args.data}")
    if len(triples) < 10:
        print(
            "[train] WARNING: dataset is very small. "
            "For real training, label ≥ 500 reviews first.",
            file=sys.stderr,
        )

    train_items, val_items, test_items = stratified_split(
        triples, key="sentiment", ratios=(0.8, 0.1, 0.1)
    )
    print(
        f"[train] split: train={len(train_items)} val={len(val_items)} "
        f"test={len(test_items)}"
    )

    if args.dry_run:
        print("[train] --dry-run: skipping model load and HF Trainer.")
        # Exercise the public imports once so CI catches API drift
        _ = ASPECT_KO
        _ = build_model  # function reference
        summary = {
            "dry_run": True,
            "num_triples": len(triples),
            "train": len(train_items),
            "val": len(val_items),
            "test": len(test_items),
        }
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / "dry_run.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False)
        )
        return 0

    # --- Real training path (requires torch + transformers + datasets) ---
    try:
        import torch  # noqa: F401
        from transformers import Trainer, TrainingArguments, EarlyStoppingCallback
    except ImportError as e:
        print(
            "[train] torch + transformers required for real training. "
            "Install requirements.txt or pass --dry-run.",
            file=sys.stderr,
        )
        return 3

    model = build_model(
        model_name=config.get("model_name"),
        dropout=float(config.get("dropout", 0.3)),
    )
    train_ds, _ = build_hf_dataset(train_items, config["model_name"], config["max_length"])
    val_ds, _ = build_hf_dataset(val_items, config["model_name"], config["max_length"])
    test_ds, _ = build_hf_dataset(test_items, config["model_name"], config["max_length"])

    args.output.mkdir(parents=True, exist_ok=True)
    ta = TrainingArguments(
        output_dir=str(args.output),
        num_train_epochs=int(config.get("epochs", 5)),
        per_device_train_batch_size=int(config.get("batch_size", 16)),
        per_device_eval_batch_size=int(config.get("batch_size", 16)),
        learning_rate=float(config.get("learning_rate", 2e-5)),
        weight_decay=float(config.get("weight_decay", 0.01)),
        warmup_ratio=float(config.get("warmup_ratio", 0.1)),
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model=config.get("metric_for_best_model", "macro_f1"),
    )

    # transformers 5.x always uses safetensors which rejects non-contiguous
    # tensors. KcELECTRA's pretrained weights have a few non-contiguous
    # parameters; we wrap state_dict() to materialise contiguous copies
    # at save time without changing in-memory layout during training.
    _orig_state_dict = model.state_dict

    def _contiguous_state_dict(*a, **kw):
        sd = _orig_state_dict(*a, **kw)
        return {
            k: (v.contiguous() if hasattr(v, "is_contiguous") and not v.is_contiguous() else v)
            for k, v in sd.items()
        }

    model.state_dict = _contiguous_state_dict

    def _metrics(eval_pred):
        import numpy as np
        preds = np.argmax(eval_pred.predictions, axis=-1).tolist()
        labels = eval_pred.label_ids.tolist()
        return compute_classification_metrics(labels, preds)

    trainer = Trainer(
        model=model,
        args=ta,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        compute_metrics=_metrics,
        callbacks=[EarlyStoppingCallback(
            early_stopping_patience=int(config.get("early_stopping_patience", 2))
        )],
    )
    trainer.train()
    test_metrics = trainer.evaluate(test_ds)
    print("[train] test metrics:", json.dumps(test_metrics, indent=2))
    trainer.save_model(str(args.output / "best"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
