
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict


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
    episode_id: str
    content: str
    entity_type: str
    entity_id: str
    created_at: datetime
    source: str
    reason: str
    confidence: float
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
