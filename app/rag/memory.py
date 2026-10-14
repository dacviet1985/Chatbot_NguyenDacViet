from __future__ import annotations

from collections import deque
from dataclasses import dataclass


@dataclass(slots=True)
class MemoryMessage:
    role: str
    content: str


class ConversationMemory:
    """Stores recent conversation turns per session."""

    def __init__(self, window_size: int) -> None:
        self.window_size = window_size
        self._store: dict[str, deque[MemoryMessage]] = {}

    def get_history(self, session_id: str) -> list[dict[str, str]]:
        history = self._store.get(session_id, deque())
        return [{"role": item.role, "content": item.content} for item in history]

    def add_message(self, session_id: str, role: str, content: str) -> None:
        if session_id not in self._store:
            self._store[session_id] = deque(maxlen=self.window_size)
        self._store[session_id].append(MemoryMessage(role=role, content=content))

    def clear(self, session_id: str) -> None:
        self._store.pop(session_id, None)

    def render_for_prompt(self, session_id: str) -> str:
        history = self._store.get(session_id, deque())
        return "\n".join(f"{item.role}: {item.content}" for item in history)
