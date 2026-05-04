"""
B2 Food NER — KoELECTRA + token classification (optional CRF).

Tag set (13 BIO tags):
    O,
    B-DISH / I-DISH,
    B-INGREDIENT / I-INGREDIENT,
    B-FLAVOR / I-FLAVOR,
    B-TEXTURE / I-TEXTURE,
    B-COOKING / I-COOKING,
    B-ALLERGEN / I-ALLERGEN
"""
from __future__ import annotations

from typing import Any, Optional


LABELS = [
    "O",
    "B-DISH", "I-DISH",
    "B-INGREDIENT", "I-INGREDIENT",
    "B-FLAVOR", "I-FLAVOR",
    "B-TEXTURE", "I-TEXTURE",
    "B-COOKING", "I-COOKING",
    "B-ALLERGEN", "I-ALLERGEN",
]
NUM_LABELS = len(LABELS)
LABEL2ID = {lab: i for i, lab in enumerate(LABELS)}
ID2LABEL = {i: lab for lab, i in LABEL2ID.items()}

ENTITY_TYPES = [
    "DISH", "INGREDIENT", "FLAVOR", "TEXTURE", "COOKING", "ALLERGEN",
]

DEFAULT_MODEL_NAME = "monologg/koelectra-base-v3-discriminator"


def build_model(
    model_name: str = DEFAULT_MODEL_NAME,
    use_crf: bool = False,
    dropout: float = 0.1,
):
    """
    Construct a FoodNERModel. Lazy imports.

    Args:
        model_name: backbone HuggingFace id.
        use_crf: if True, adds a CRF head (requires `pytorch-crf`).
    """
    try:
        import torch.nn as nn
        from transformers import AutoModel
    except ImportError as e:
        raise ImportError(
            "FoodNERModel requires torch + transformers. "
            "Install: pip install torch transformers"
        ) from e

    class FoodNERModel(nn.Module):  # noqa: N801
        def __init__(self, backbone_name: str, use_crf: bool, dropout: float):
            super().__init__()
            self.backbone = AutoModel.from_pretrained(backbone_name)
            hidden = self.backbone.config.hidden_size
            self.dropout = nn.Dropout(dropout)
            self.classifier = nn.Linear(hidden, NUM_LABELS)
            self.use_crf = use_crf
            self.crf = None
            if use_crf:
                try:
                    from torchcrf import CRF
                    self.crf = CRF(NUM_LABELS, batch_first=True)
                except ImportError as e:
                    raise ImportError(
                        "use_crf=True requires `pytorch-crf`. "
                        "Install: pip install pytorch-crf"
                    ) from e

        def forward(
            self,
            input_ids,
            attention_mask,
            labels: Optional[Any] = None,
        ):
            outputs = self.backbone(
                input_ids=input_ids, attention_mask=attention_mask
            )
            sequence_output = self.dropout(outputs.last_hidden_state)
            logits = self.classifier(sequence_output)

            loss = None
            if labels is not None:
                if self.use_crf and self.crf is not None:
                    mask = attention_mask.bool()
                    loss = -self.crf(logits, labels, mask=mask, reduction="mean")
                else:
                    import torch.nn.functional as F
                    loss = F.cross_entropy(
                        logits.view(-1, logits.size(-1)),
                        labels.view(-1),
                        ignore_index=-100,
                    )
            return {"loss": loss, "logits": logits}

        def decode(self, input_ids, attention_mask) -> list[list[str]]:
            """Return BIO tag sequences per sample."""
            import torch
            with torch.no_grad():
                outputs = self.backbone(
                    input_ids=input_ids, attention_mask=attention_mask
                )
                logits = self.classifier(outputs.last_hidden_state)
                if self.use_crf and self.crf is not None:
                    paths = self.crf.decode(logits, mask=attention_mask.bool())
                else:
                    paths = logits.argmax(dim=-1).tolist()
            return [[ID2LABEL[int(t)] for t in seq] for seq in paths]

    return FoodNERModel(model_name, use_crf, dropout)


__all__ = [
    "build_model",
    "LABELS",
    "LABEL2ID",
    "ID2LABEL",
    "NUM_LABELS",
    "ENTITY_TYPES",
    "DEFAULT_MODEL_NAME",
]
