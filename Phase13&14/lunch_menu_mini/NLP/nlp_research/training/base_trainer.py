"""
BaseTrainer — abstract harness for A2/B2 fine-tuning.

This is a thin wrapper; concrete trainers (ABSATrainer, FoodNERTrainer) only
need to implement `_build_model`, `_build_dataset`, and `_compute_metrics`.
Heavy imports (torch, transformers, wandb) are deferred until `train()` is
called so the module is importable in any environment.
"""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional


def _load_yaml(path: str | Path) -> dict:
    import yaml
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


class BaseTrainer(ABC):
    """
    Abstract base for training scripts.

    Subclasses implement:
        _build_model(config) -> nn.Module
        _build_datasets(data_dir) -> (train_ds, val_ds, test_ds)
        _compute_metrics(eval_pred) -> dict

    The `train()` method orchestrates HuggingFace Trainer with early stopping,
    W&B (optional), and best-checkpoint saving.
    """

    def __init__(
        self,
        config_path: str | Path,
        data_dir: str | Path,
        output_dir: str | Path,
        dry_run: bool = False,
    ) -> None:
        self.config_path = Path(config_path)
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.dry_run = dry_run
        self.config = _load_yaml(self.config_path)
        self.device = self._select_device()

    # -------------------------------------------------------------------------
    # Public entry point
    # -------------------------------------------------------------------------
    def train(self) -> dict:
        """Run training; return best-epoch metrics dict."""
        # Lazy imports
        try:
            import torch  # noqa: F401
            from transformers import (  # noqa: F401
                Trainer, TrainingArguments, EarlyStoppingCallback
            )
        except ImportError as e:
            raise ImportError(
                "training requires torch + transformers. "
                "Install: pip install torch transformers datasets"
            ) from e

        from transformers import Trainer, TrainingArguments, EarlyStoppingCallback

        self.output_dir.mkdir(parents=True, exist_ok=True)
        model = self._build_model(self.config)
        train_ds, val_ds, test_ds = self._build_datasets(self.data_dir)

        if self.dry_run:
            train_ds = train_ds.select(range(min(10, len(train_ds))))
            val_ds = val_ds.select(range(min(5, len(val_ds))))
            epochs = 1
        else:
            epochs = int(self.config.get("epochs", 3))

        args = TrainingArguments(
            output_dir=str(self.output_dir),
            num_train_epochs=epochs,
            per_device_train_batch_size=int(self.config.get("batch_size", 16)),
            per_device_eval_batch_size=int(self.config.get("batch_size", 16)),
            learning_rate=float(self.config.get("learning_rate", 2e-5)),
            weight_decay=float(self.config.get("weight_decay", 0.01)),
            warmup_ratio=float(self.config.get("warmup_ratio", 0.1)),
            eval_strategy="epoch",
            save_strategy="epoch" if not self.dry_run else "no",
            logging_steps=10,
            load_best_model_at_end=not self.dry_run,
            metric_for_best_model=self.config.get("metric_for_best_model"),
            report_to="wandb" if os.getenv("WANDB_API_KEY") else "none",
        )

        trainer = Trainer(
            model=model,
            args=args,
            train_dataset=train_ds,
            eval_dataset=val_ds,
            compute_metrics=self._compute_metrics,
            callbacks=[EarlyStoppingCallback(
                early_stopping_patience=int(
                    self.config.get("early_stopping_patience", 2)
                )
            )] if not self.dry_run else [],
        )
        trainer.train()
        eval_result = trainer.evaluate(test_ds) if test_ds is not None else {}
        if not self.dry_run:
            trainer.save_model(str(self.output_dir / "best"))
        return eval_result

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------
    @staticmethod
    def _select_device() -> str:
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return "mps"
        except Exception:
            pass
        return "cpu"

    # -------------------------------------------------------------------------
    # Abstract
    # -------------------------------------------------------------------------
    @abstractmethod
    def _build_model(self, config: dict) -> Any: ...

    @abstractmethod
    def _build_datasets(self, data_dir: Path) -> tuple: ...

    @abstractmethod
    def _compute_metrics(self, eval_pred) -> dict: ...


__all__ = ["BaseTrainer"]
