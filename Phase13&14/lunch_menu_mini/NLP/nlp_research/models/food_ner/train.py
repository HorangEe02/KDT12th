"""
B2 Food NER training script.

Usage:
    python -m nlp_research.models.food_ner.train \
        --config configs/food_ner.yaml \
        --data data/seed/food_ner_seed_50.jsonl \
        --output checkpoints/food_ner/v1
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from nlp_research.models.food_ner.dataset import (
    build_hf_dataset,
    load_food_ner_jsonl,
)
from nlp_research.models.food_ner.model import ID2LABEL, LABELS, build_model
from nlp_research.training.data_loader import stratified_split


def _load_yaml(path: Path) -> dict:
    import yaml
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Train B2 Food NER model")
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--dry-run", action="store_true")
    return ap.parse_args()


def _stratify_key(row: dict) -> str:
    """Use the most-frequent non-O tag as the stratification key."""
    tags = [t for t in row.get("tags", []) if t != "O"]
    if not tags:
        return "O"
    return max(set(tags), key=tags.count)


def main() -> int:
    args = parse_args()
    if not args.data.exists():
        print(f"[train] data not found: {args.data}", file=sys.stderr)
        return 2

    config = _load_yaml(args.config)
    rows = load_food_ner_jsonl(args.data)
    print(f"[train] loaded {len(rows)} sentences from {args.data}")
    if len(rows) < 10:
        print(
            "[train] WARNING: dataset is very small. Label ≥1,000 sentences "
            "for production training.",
            file=sys.stderr,
        )

    keyed = [{**r, "_strat": _stratify_key(r)} for r in rows]
    train_items, val_items, test_items = stratified_split(
        keyed, key="_strat", ratios=(0.8, 0.1, 0.1)
    )
    for items in (train_items, val_items, test_items):
        for it in items:
            it.pop("_strat", None)
    print(
        f"[train] split: train={len(train_items)} val={len(val_items)} "
        f"test={len(test_items)}"
    )

    if args.dry_run:
        print("[train] --dry-run: skipping HF Trainer")
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / "dry_run.json").write_text(
            json.dumps(
                {
                    "dry_run": True,
                    "n_rows": len(rows),
                    "labels": LABELS,
                    "use_crf": bool(config.get("use_crf", False)),
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0

    try:
        import torch  # noqa: F401
        from transformers import (
            DataCollatorForTokenClassification,
            EarlyStoppingCallback,
            Trainer,
            TrainingArguments,
        )
    except ImportError:
        print(
            "[train] torch + transformers required. Install requirements.txt "
            "or use --dry-run.",
            file=sys.stderr,
        )
        return 3

    from nlp_research.training.metrics import compute_ner_metrics

    model = build_model(
        model_name=config["model_name"],
        use_crf=bool(config.get("use_crf", False)),
    )
    train_ds, tokenizer = build_hf_dataset(
        train_items, config["model_name"], config.get("max_length", 256)
    )
    val_ds, _ = build_hf_dataset(
        val_items, config["model_name"], config.get("max_length", 256)
    )
    test_ds, _ = build_hf_dataset(
        test_items, config["model_name"], config.get("max_length", 256)
    )

    args.output.mkdir(parents=True, exist_ok=True)
    ta = TrainingArguments(
        output_dir=str(args.output),
        num_train_epochs=int(config.get("epochs", 10)),
        per_device_train_batch_size=int(config.get("batch_size", 32)),
        per_device_eval_batch_size=int(config.get("batch_size", 32)),
        learning_rate=float(config.get("learning_rate", 5e-5)),
        weight_decay=float(config.get("weight_decay", 0.01)),
        warmup_ratio=float(config.get("warmup_ratio", 0.1)),
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model=config.get("metric_for_best_model", "entity_f1"),
    )

    # See ABSA train.py for the rationale — wrap state_dict to ensure
    # contiguous tensors at save time (transformers 5.x safetensors-only).
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
        preds = np.argmax(eval_pred.predictions, axis=-1)
        labels = eval_pred.label_ids
        true_seqs, pred_seqs = [], []
        for p_seq, l_seq in zip(preds, labels):
            tp, tt = [], []
            for p, l in zip(p_seq, l_seq):
                if l == -100:
                    continue
                tp.append(ID2LABEL[int(p)])
                tt.append(ID2LABEL[int(l)])
            true_seqs.append(tt)
            pred_seqs.append(tp)
        return compute_ner_metrics(true_seqs, pred_seqs)

    # transformers 5.x renamed `tokenizer=` to `processing_class=`. Fall back
    # to the legacy kwarg if running on 4.x.
    import inspect as _inspect
    _tr_kwargs = {
        "model": model,
        "args": ta,
        "train_dataset": train_ds,
        "eval_dataset": val_ds,
        "data_collator": DataCollatorForTokenClassification(tokenizer),
        "compute_metrics": _metrics,
        "callbacks": [EarlyStoppingCallback(
            early_stopping_patience=int(config.get("early_stopping_patience", 2))
        )],
    }
    _tr_params = _inspect.signature(Trainer.__init__).parameters
    if "processing_class" in _tr_params:
        _tr_kwargs["processing_class"] = tokenizer
    elif "tokenizer" in _tr_params:
        _tr_kwargs["tokenizer"] = tokenizer
    trainer = Trainer(**_tr_kwargs)
    trainer.train()
    test_metrics = trainer.evaluate(test_ds)
    print("[train] test metrics:", json.dumps(test_metrics, indent=2))
    trainer.save_model(str(args.output / "best"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
