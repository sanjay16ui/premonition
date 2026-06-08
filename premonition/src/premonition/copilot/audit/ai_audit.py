"""AI audit logging."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from premonition.utils.paths import ensure_dir


@dataclass
class AIAuditRecord:
    id: str
    actor: str
    action: str
    prompt_version: str
    model: str
    query: str
    response_preview: str
    citations: list[dict[str, Any]] = field(default_factory=list)
    retrieval_trace: list[str] = field(default_factory=list)
    conversation_id: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "actor": self.actor, "action": self.action,
            "prompt_version": self.prompt_version, "model": self.model,
            "query": self.query, "response_preview": self.response_preview,
            "citations": self.citations, "retrieval_trace": self.retrieval_trace,
            "conversation_id": self.conversation_id, "timestamp": self.timestamp,
        }


class AIAuditLogger:
    """Audit every AI response with retrieval trace and citations."""

    def __init__(self, logs_dir: Path) -> None:
        self.logs_dir = ensure_dir(logs_dir / "copilot" / "audit")
        self._records: list[AIAuditRecord] = []

    def log(
        self,
        actor: str,
        action: str,
        prompt_version: str,
        model: str,
        query: str,
        response: str,
        citations: list[dict] | None = None,
        retrieval_trace: list[str] | None = None,
        conversation_id: str | None = None,
    ) -> AIAuditRecord:
        record = AIAuditRecord(
            id=str(uuid.uuid4()),
            actor=actor,
            action=action,
            prompt_version=prompt_version,
            model=model,
            query=query[:500],
            response_preview=response[:300],
            citations=citations or [],
            retrieval_trace=retrieval_trace or [],
            conversation_id=conversation_id,
        )
        self._records.append(record)
        log_file = self.logs_dir / f"audit_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.jsonl"
        with log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record.to_dict()) + "\n")
        return record

    def query(self, action: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        records = self._records
        if action:
            records = [r for r in records if r.action == action]
        return [r.to_dict() for r in records[-limit:]]
