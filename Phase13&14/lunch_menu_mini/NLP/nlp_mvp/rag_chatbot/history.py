"""
멀티턴 대화 이력 관리.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ConversationHistory:
    """최근 N턴 또는 M자 제한으로 pruning."""

    max_turns: int = 5
    max_chars: int = 6000
    messages: list[dict[str, str]] = field(default_factory=list)

    def add_user(self, content: str) -> None:
        self.messages.append({"role": "user", "content": content})
        self._prune()

    def add_assistant(self, content: str) -> None:
        self.messages.append({"role": "assistant", "content": content})
        self._prune()

    def clear(self) -> None:
        self.messages.clear()

    def _prune(self) -> None:
        # 턴 수 기준 (user+assistant 쌍)
        while len(self.messages) > self.max_turns * 2:
            self.messages.pop(0)
        # 문자 수 기준
        total = sum(len(m["content"]) for m in self.messages)
        while total > self.max_chars and self.messages:
            removed = self.messages.pop(0)
            total -= len(removed["content"])

    def __len__(self) -> int:
        return len(self.messages)
