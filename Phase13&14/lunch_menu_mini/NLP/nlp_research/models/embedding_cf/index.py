"""
Vector index — FAISS with brute-force fallbacks.

Three backends share the same API:
    build(vectors, ids)
    search(query_vec, top_k) -> (ids, scores)
    save(path) / load(path)
    add(new_vec, new_id)

Backend selection (`make_index(dim, prefer_faiss=...)`):
    - FAISSIndex: best, requires faiss-cpu
    - NumpyBruteForceIndex: numpy-vectorized
    - PyBruteForceIndex: pure-Python (used when numpy is unavailable)
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


# =============================================================================
# Pure-Python fallback (no numpy required)
# =============================================================================
class PyBruteForceIndex:
    """
    Cosine-similarity index using nothing but stdlib. Slow but dependency-free.
    Vectors are stored as list[list[float]].
    """

    def __init__(self, dim: int):
        self.dim = dim
        self._vecs: list[list[float]] = []
        self._ids: list[Any] = []

    @staticmethod
    def _normalize(v: list[float]) -> list[float]:
        s = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / s for x in v]

    def build(self, vectors, ids: list[Any]) -> None:
        if len(vectors) != len(ids):
            raise ValueError("length mismatch")
        rows: list[list[float]] = []
        for v in vectors:
            row = list(v)
            if len(row) != self.dim:
                raise ValueError(f"vector dim mismatch: {len(row)} vs {self.dim}")
            rows.append(self._normalize(row))
        self._vecs = rows
        self._ids = list(ids)

    def add(self, new_vec, new_id) -> None:
        row = self._normalize(list(new_vec))
        if len(row) != self.dim:
            raise ValueError(f"vector dim mismatch: {len(row)} vs {self.dim}")
        self._vecs.append(row)
        self._ids.append(new_id)

    def search(self, query_vec, top_k: int = 10) -> tuple[list[Any], list[float]]:
        if not self._vecs:
            return [], []
        q = self._normalize(list(query_vec))
        scored = [
            (i, sum(a * b for a, b in zip(self._vecs[i], q)))
            for i in range(len(self._vecs))
        ]
        scored.sort(key=lambda x: -x[1])
        top = scored[:top_k]
        return [self._ids[i] for i, _ in top], [float(s) for _, s in top]

    def save(self, path: str | Path) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.with_suffix(".json").open("w", encoding="utf-8") as f:
            json.dump({"dim": self.dim, "ids": self._ids, "vecs": self._vecs}, f)

    @classmethod
    def load(cls, path: str | Path, dim: int) -> "PyBruteForceIndex":
        p = Path(path).with_suffix(".json")
        if not p.exists():
            raise FileNotFoundError(p)
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        idx = cls(dim=int(data.get("dim", dim)))
        idx._vecs = [list(v) for v in data.get("vecs", [])]
        idx._ids = list(data.get("ids", []))
        return idx

    def __len__(self) -> int:
        return len(self._ids)


# =============================================================================
# Numpy-vectorized index
# =============================================================================
class NumpyBruteForceIndex:
    """Cosine-similarity index using numpy. Requires numpy."""

    def __init__(self, dim: int):
        try:
            import numpy as np  # noqa: F401
        except ImportError as e:
            raise ImportError(
                "NumpyBruteForceIndex requires numpy. "
                "Install: pip install numpy, or use PyBruteForceIndex."
            ) from e
        self.dim = dim
        self._vecs = None  # np.ndarray (N, dim)
        self._ids: list[Any] = []

    def build(self, vectors, ids: list[Any]) -> None:
        import numpy as np
        if len(vectors) != len(ids):
            raise ValueError(
                f"length mismatch: {len(vectors)} vectors vs {len(ids)} ids"
            )
        arr = np.asarray(vectors, dtype="float32")
        if arr.ndim != 2 or arr.shape[1] != self.dim:
            raise ValueError(f"expected (N, {self.dim}) array, got {arr.shape}")
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self._vecs = arr / norms
        self._ids = list(ids)

    def add(self, new_vec, new_id) -> None:
        import numpy as np
        v = np.asarray(new_vec, dtype="float32").reshape(1, -1)
        norm = np.linalg.norm(v) or 1.0
        v = v / norm
        if self._vecs is None:
            self._vecs = v
            self._ids = [new_id]
        else:
            self._vecs = np.vstack([self._vecs, v])
            self._ids.append(new_id)

    def search(self, query_vec, top_k: int = 10) -> tuple[list[Any], list[float]]:
        import numpy as np
        if self._vecs is None or len(self._ids) == 0:
            return [], []
        q = np.asarray(query_vec, dtype="float32").reshape(-1)
        norm = np.linalg.norm(q) or 1.0
        q = q / norm
        scores = self._vecs @ q
        idx = np.argsort(-scores)[:top_k]
        return [self._ids[i] for i in idx], [float(scores[i]) for i in idx]

    def save(self, path: str | Path) -> None:
        import numpy as np
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        np.savez(
            p.with_suffix(".npz"),
            vecs=self._vecs
            if self._vecs is not None
            else np.zeros((0, self.dim), dtype="float32"),
            ids=np.array(self._ids, dtype=object),
        )

    @classmethod
    def load(cls, path: str | Path, dim: int) -> "NumpyBruteForceIndex":
        import numpy as np
        p = Path(path).with_suffix(".npz")
        if not p.exists():
            raise FileNotFoundError(p)
        data = np.load(p, allow_pickle=True)
        idx = cls(dim=dim)
        if data["vecs"].shape[0] > 0:
            idx._vecs = data["vecs"].astype("float32")
            idx._ids = list(data["ids"].tolist())
        return idx

    def __len__(self) -> int:
        return len(self._ids)


# =============================================================================
# FAISS-backed index
# =============================================================================
class FAISSIndex:
    """FAISS `IndexFlatIP` with L2-normalized vectors → cosine similarity."""

    def __init__(self, dim: int):
        try:
            import faiss  # noqa: F401
        except ImportError as e:
            raise ImportError(
                "FAISSIndex requires faiss-cpu. Install: pip install faiss-cpu"
            ) from e
        import faiss
        self.dim = dim
        self._index = faiss.IndexFlatIP(dim)
        self._ids: list[Any] = []

    def build(self, vectors, ids: list[Any]) -> None:
        import faiss
        import numpy as np
        if len(vectors) != len(ids):
            raise ValueError("length mismatch")
        arr = np.asarray(vectors, dtype="float32").copy()
        faiss.normalize_L2(arr)
        self._index.reset()
        self._index.add(arr)
        self._ids = list(ids)

    def add(self, new_vec, new_id) -> None:
        import faiss
        import numpy as np
        v = np.asarray(new_vec, dtype="float32").reshape(1, -1).copy()
        faiss.normalize_L2(v)
        self._index.add(v)
        self._ids.append(new_id)

    def search(self, query_vec, top_k: int = 10) -> tuple[list[Any], list[float]]:
        import faiss
        import numpy as np
        if len(self._ids) == 0:
            return [], []
        q = np.asarray(query_vec, dtype="float32").reshape(1, -1).copy()
        faiss.normalize_L2(q)
        scores, idx = self._index.search(q, min(top_k, len(self._ids)))
        return (
            [self._ids[i] for i in idx[0] if i >= 0],
            [float(s) for s in scores[0]],
        )

    def save(self, path: str | Path) -> None:
        import faiss
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, str(p.with_suffix(".faiss")))
        with p.with_suffix(".ids.json").open("w", encoding="utf-8") as f:
            json.dump(self._ids, f, ensure_ascii=False)

    @classmethod
    def load(cls, path: str | Path, dim: int) -> "FAISSIndex":
        import faiss
        idx = cls(dim=dim)
        idx._index = faiss.read_index(str(Path(path).with_suffix(".faiss")))
        with Path(path).with_suffix(".ids.json").open("r", encoding="utf-8") as f:
            idx._ids = json.load(f)
        return idx

    def __len__(self) -> int:
        return len(self._ids)


# =============================================================================
# Factory
# =============================================================================
def _has_module(name: str) -> bool:
    try:
        __import__(name)
        return True
    except ImportError:
        return False


def make_index(dim: int, prefer_faiss: str | bool = "auto"):
    """
    Factory: pick the best available backend.

    `prefer_faiss`:
        - "auto" (default): try faiss → numpy → pure-Python
        - True: require faiss
        - False: skip faiss, try numpy → pure-Python
    """
    if prefer_faiss is True:
        return FAISSIndex(dim)

    if prefer_faiss == "auto" and _has_module("faiss"):
        return FAISSIndex(dim)

    if _has_module("numpy"):
        return NumpyBruteForceIndex(dim)

    return PyBruteForceIndex(dim)


__all__ = [
    "PyBruteForceIndex",
    "NumpyBruteForceIndex",
    "FAISSIndex",
    "make_index",
]
