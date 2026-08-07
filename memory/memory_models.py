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
    entity_id: str | None
    entity_id: int
    source: str
    reason: str

    episode_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    confidence: float = 1.0
    metadata: Dict = field(default_factory=dict)


@dataclass
class SemanticFact:
    predicate: str
    value: str
    entity_type: str
    entity_id: str | None

    confidence: float

    fact_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    version: int = 1
    valid_from: datetime = field(default_factory=datetime.now)
    valid_until: datetime | None = None
    expires_at: datetime | None = None
