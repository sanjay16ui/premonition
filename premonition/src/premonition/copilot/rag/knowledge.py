"""Knowledge base manager."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from premonition.utils.paths import ensure_dir


@dataclass
class KnowledgeDocument:
    id: str
    title: str
    doc_type: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    ingested_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    chunk_count: int = 0


class KnowledgeBaseManager:
    """Manage ingested knowledge documents."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = ensure_dir(data_dir / "copilot" / "knowledge")
        self._index_file = self.data_dir / "documents.json"
        self._docs: dict[str, KnowledgeDocument] = {}
        self._load()

    def _load(self) -> None:
        if self._index_file.exists():
            data = json.loads(self._index_file.read_text(encoding="utf-8"))
            for item in data:
                doc = KnowledgeDocument(**item)
                self._docs[doc.id] = doc

    def _save(self) -> None:
        data = [
            {
                "id": d.id, "title": d.title, "doc_type": d.doc_type,
                "content": d.content, "metadata": d.metadata,
                "ingested_at": d.ingested_at, "chunk_count": d.chunk_count,
            }
            for d in self._docs.values()
        ]
        self._index_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def add(self, title: str, content: str, doc_type: str = "text", metadata: dict | None = None, chunk_count: int = 0) -> KnowledgeDocument:
        doc_id = str(uuid.uuid4())
        doc = KnowledgeDocument(
            id=doc_id, title=title, doc_type=doc_type,
            content=content, metadata=metadata or {}, chunk_count=chunk_count,
        )
        self._docs[doc_id] = doc
        self._save()
        return doc

    def get(self, doc_id: str) -> KnowledgeDocument | None:
        return self._docs.get(doc_id)

    def list_documents(self) -> list[dict[str, Any]]:
        return [
            {"id": d.id, "title": d.title, "doc_type": d.doc_type, "chunk_count": d.chunk_count, "ingested_at": d.ingested_at}
            for d in self._docs.values()
        ]

    def count(self) -> int:
        return len(self._docs)
