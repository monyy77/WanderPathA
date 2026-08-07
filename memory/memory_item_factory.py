'''
HumanMessage
        │
        ▼
MemoryItemFactory
        │
        ▼
MemoryItem
        │
        ▼
ShortTermMemory

'''

from datetime import datetime
import uuid

from langchain_core.messages import BaseMessage

from memory.memory_models import MemoryItem


class MemoryItemFactory:

    @staticmethod
    def from_message(
        message: BaseMessage,
        importance: float = 0.5,
        metadata: dict | None = None,
    ) -> MemoryItem:

        return MemoryItem(
            id=str(uuid.uuid4()),
            content=message.content,
            speaker=message.type,
            timestamp=datetime.now(),
            importance=importance,
            metadata=metadata or {},
        )
