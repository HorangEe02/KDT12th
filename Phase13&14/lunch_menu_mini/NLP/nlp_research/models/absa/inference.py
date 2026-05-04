"""
A2 ABSA inferencer.

Lazy-loads a trained ABSAModel and exposes `predict(text, aspects=None)` that
returns per-aspect sentiment predictions. Without trained weights, the fallback
`DummyABSAInferencer` returns deterministic random predictions — useful for
smoke tests and /nlp/v2/sentiment/{id} endpoint stubs.
"""
from __future__ import annotations

import random
from pathlib import Path
from typing import Any, Optional

from nlp_research.models.absa.dataset import ASPECT_KO
from nlp_research.models.absa.model import DEFAULT_MODEL_NAME, ID2LABEL, LABEL2ID


class ABSAInferencer:
    """Real inferencer — requires torch + transformers + trained weights."""

    def __init__(
        self,
        model_path: str | Path,
        tokenizer_name: str = DEFAULT_MODEL_NAME,
        max_length: int = 128,
        device: str = "auto",
    ):
        try:
            import torch
            from transformers import AutoTokenizer
        except ImportError as e:
            raise ImportError(
                "ABSAInferencer requires torch + transformers."
            ) from e

        from nlp_research.models.absa.model import build_model

        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
        self.model = build_model(tokenizer_name)
        state = _load_state_dict(Path(model_path))
        self.model.load_state_dict(state)
        self.model.eval()
        self.device = self._resolve_device(device)
        self.model.to(self.device)
        self.max_length = max_length

    @staticmethod
    def _resolve_device(device: str) -> str:
        if device != "auto":
            return device
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return "mps"
        except Exception:
            pass
        return "cpu"

    def predict(
        self,
        text: str,
        aspects: Optional[list[str]] = None,
    ) -> list[dict[str, Any]]:
        """Batch all aspects into a single forward pass.

        On CPU this turns 5 sequential KcELECTRA forwards (~10s/each) into one
        batched forward (~2s total). Tokenized with padding="longest" so the
        sequence length is driven by the actual text rather than max_length.
        """
        import torch

        aspects = aspects or list(ASPECT_KO.keys())
        if not aspects:
            return []

        texts = [text] * len(aspects)
        aspect_kos = [ASPECT_KO.get(a, a) for a in aspects]

        with torch.no_grad():
            enc = self.tokenizer(
                texts,
                aspect_kos,
                padding="longest",
                truncation=True,
                max_length=self.max_length,
                return_tensors="pt",
            ).to(self.device)
            out = self.model(**enc)
            logits = out["logits"]  # (n_aspects, num_labels)
            probs = torch.softmax(logits, dim=-1)
            idx = probs.argmax(dim=-1).tolist()
            probs_list = probs.tolist()

        results: list[dict[str, Any]] = []
        for asp, i, p in zip(aspects, idx, probs_list):
            results.append(
                {
                    "aspect": asp,
                    "sentiment": ID2LABEL[int(i)],
                    "confidence": round(float(p[int(i)]), 4),
                }
            )
        return results


class DummyABSAInferencer:
    """
    Deterministic random predictor used when no weights are available.
    Used by benchmark.py --smoke and v2 router placeholders.
    """

    def __init__(self, seed: int = 42):
        self._rng = random.Random(seed)

    def predict(
        self, text: str, aspects: Optional[list[str]] = None
    ) -> list[dict[str, Any]]:
        aspects = aspects or list(ASPECT_KO.keys())
        labels = list(LABEL2ID.keys())
        return [
            {
                "aspect": asp,
                "sentiment": self._rng.choice(labels),
                "confidence": round(self._rng.uniform(0.5, 0.95), 4),
            }
            for asp in aspects
        ]


# NLP/nlp_research/models/absa/inference.py → parents[2] = NLP/nlp_research/
# Checkpoints land at NLP/nlp_research/checkpoints/absa/...
_NLP_RESEARCH_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_CKPT_DIRS = (
    _NLP_RESEARCH_ROOT / "checkpoints" / "absa" / "best",
    _NLP_RESEARCH_ROOT / "checkpoints" / "absa" / "v1" / "best",
    _NLP_RESEARCH_ROOT / "checkpoints" / "absa" / "v1",
)


def _has_weights(p: Path) -> bool:
    return (p / "pytorch_model.bin").exists() or (p / "model.safetensors").exists()


def _load_state_dict(p: Path):
    """Load a state dict from either legacy .bin or safetensors format."""
    import torch
    bin_path = p / "pytorch_model.bin"
    if bin_path.exists():
        return torch.load(bin_path, map_location="cpu")
    safe_path = p / "model.safetensors"
    if safe_path.exists():
        from safetensors.torch import load_file
        return load_file(str(safe_path), device="cpu")
    raise FileNotFoundError(f"no model.safetensors or pytorch_model.bin in {p}")


def _auto_discover() -> Optional[Path]:
    import os
    env = os.getenv("NLP_V2_ABSA_CKPT")
    if env and Path(env).exists():
        return Path(env)
    for p in _DEFAULT_CKPT_DIRS:
        if _has_weights(p):
            return p
    return None


def load_inferencer(
    model_path: Optional[str | Path] = None,
) -> ABSAInferencer | DummyABSAInferencer:
    """Return a real inferencer if a checkpoint exists (explicit path,
    $NLP_V2_ABSA_CKPT, or checkpoints/absa/{best,v1/best,v1}/), else the dummy."""
    path = Path(model_path) if model_path else _auto_discover()
    if path and path.exists() and _has_weights(path):
        try:
            return ABSAInferencer(path)
        except Exception:
            pass
    return DummyABSAInferencer()


__all__ = ["ABSAInferencer", "DummyABSAInferencer", "load_inferencer"]
