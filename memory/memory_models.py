
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict
import uuid


@dataclass
class MemoryItem:
    id: str
    content: str
    speaker: str
    timestamp: datetime
    importance: float
    metadata: Dict = field(default_factory=dict)


@dataclass
class Episode:
    content: str
    entity_type: str
    entity_id: int
    source: str
    reason: str

    episode_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    confidence: float = 1.0
    metadata: Dict = field(default_factory=dict)


@dataclass
class SemanticFact:
    fact_id: str
    predicate: str
    value: str
    entity_type: str
    entity_id: str
    version: int
    valid_from: datetime
    valid_until: datetime | None
    confidence: float
