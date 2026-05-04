"""retriever.py 단위 테스트 — 평탄화 로직만 단독 테스트."""
from __future__ import annotations

# Retriever 클래스 자체는 chromadb 의존이라 lazy import 됨.
# 정적 메서드 _flatten 만 직접 import 가능한지 확인 후 테스트.
from nlp_mvp.rag_chatbot.retriever import Retriever


class TestFlatten:
    def test_basic(self):
        chroma_result = {
            "documents": [["doc1", "doc2"]],
            "metadatas": [[{"a": 1}, {"b": 2}]],
            "distances": [[0.1, 0.2]],
        }
        result = Retriever._flatten(chroma_result)
        assert len(result) == 2
        assert result[0]["text"] == "doc1"
        assert result[0]["metadata"] == {"a": 1}
        assert result[0]["distance"] == 0.1
        assert result[1]["text"] == "doc2"

    def test_empty(self):
        result = Retriever._flatten({})
        assert result == []

    def test_none_metadata(self):
        chroma_result = {
            "documents": [["doc1"]],
            "metadatas": [[None]],
            "distances": [[0.5]],
        }
        result = Retriever._flatten(chroma_result)
        assert len(result) == 1
        assert result[0]["metadata"] == {}

    def test_missing_keys(self):
        result = Retriever._flatten({"documents": [["x"]], "metadatas": [[None]], "distances": [[0]]})
        assert result[0]["text"] == "x"
