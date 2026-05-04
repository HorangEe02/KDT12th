"""
A2 ABSA — BERT-SPC (Sentence Pair Classification) model.

Input format: [CLS] review_text [SEP] aspect_name [SEP]
Output: 3-class softmax over {positive, neutral, negative}

All heavy imports (torch, transformers) are deferred to `build_model()` so
the module is importable in test environments without those packages.
"""
from __future__ import annotations

from typing import Any, Optional


LABEL2ID = {"positive": 0, "neutral": 1, "negative": 2}
ID2LABEL = {v: k for k, v in LABEL2ID.items()}
NUM_LABELS = 3

DEFAULT_MODEL_NAME = "beomi/KcELECTRA-base-v2022"


def build_model(
    model_name: str = DEFAULT_MODEL_NAME,
    dropout: float = 0.3,
):
    """
    Construct an ABSAModel. Lazy imports so the module can be loaded without torch.
    """
    try:
        import torch.nn as nn
        from transformers import AutoModel
    except ImportError as e:
        raise ImportError(
            "ABSAModel requires torch + transformers. "
            "Install: pip install torch transformers"
        ) from e

    class ABSAModel(nn.Module):  # noqa: N801
        """BERT-SPC classifier for aspect-based sentiment analysis."""

        def __init__(self, backbone_name: str, dropout: float):
            super().__init__()
            self.backbone = AutoModel.from_pretrained(backbone_name)
            hidden = self.backbone.config.hidden_size
            self.dropout = nn.Dropout(dropout)
            self.classifier = nn.Linear(hidden, NUM_LABELS)

        def forward(
            self,
            input_ids,
            attention_mask,
            token_type_ids: Optional[Any] = None,
            labels: Optional[Any] = None,
        ):
            kwargs = {"input_ids": input_ids, "attention_mask": attention_mask}
            if token_type_ids is not None:
                kwargs["token_type_ids"] = token_type_ids
            outputs = self.backbone(**kwargs)
            cls = outputs.last_hidden_state[:, 0, :]
            logits = self.classifier(self.dropout(cls))

            loss = None
            if labels is not None:
                import torch.nn.functional as F
                loss = F.cross_entropy(logits, labels)

            return {"loss": loss, "logits": logits}

    return ABSAModel(model_name, dropout)


__all__ = ["build_model", "LABEL2ID", "ID2LABEL", "NUM_LABELS", "DEFAULT_MODEL_NAME"]
