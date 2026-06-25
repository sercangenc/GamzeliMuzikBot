from collections import deque
from typing import Optional


class QueueManager:
    def __init__(self):
        self._queues: dict[int, deque] = {}

    def _ensure(self, chat_id: int):
        if chat_id not in self._queues:
            self._queues[chat_id] = deque()

    def add(self, chat_id: int, track: dict):
        self._ensure(chat_id)
        self._queues[chat_id].append(track)

    def get_current(self, chat_id: int) -> Optional[dict]:
        self._ensure(chat_id)
        if self._queues[chat_id]:
            return self._queues[chat_id][0]
        return None

    def peek_next(self, chat_id: int) -> Optional[dict]:
        self._ensure(chat_id)
        q = self._queues[chat_id]
        if len(q) >= 2:
            return list(q)[1]
        return None

    def pop_current(self, chat_id: int):
        self._ensure(chat_id)
        if self._queues[chat_id]:
            self._queues[chat_id].popleft()

    def get_queue(self, chat_id: int) -> list:
        self._ensure(chat_id)
        return list(self._queues[chat_id])

    def queue_size(self, chat_id: int) -> int:
        self._ensure(chat_id)
        return len(self._queues[chat_id])

    def clear(self, chat_id: int):
        self._queues[chat_id] = deque()
