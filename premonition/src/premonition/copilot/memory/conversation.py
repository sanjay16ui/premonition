"""AI conversation memory."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from premonition.copilot.schemas import ChatMessage
from premonition.tenant.context import get_tenant_context
from premonition.utils.paths import ensure_dir


@dataclass
class Conversation:
    id: str
    title: str
    messages: list[ChatMessage] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    user_id: str = "anonymous"
    metadata: dict[str, Any] = field(default_factory=dict)


class AIConversationMemory:
    """Persist and retrieve conversation history."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = ensure_dir(data_dir / "copilot" / "conversations")
        self._conversations: dict[str, Conversation] = {}
        self._load_all()

    def _load_all(self) -> None:
        for f in self.data_dir.glob("*.json"):
            data = json.loads(f.read_text(encoding="utf-8"))
            msgs = [ChatMessage(**m) for m in data.get("messages", [])]
            self._conversations[data["id"]] = Conversation(
                id=data["id"], title=data["title"], messages=msgs,
                created_at=data["created_at"], updated_at=data["updated_at"],
                user_id=data.get("user_id", "anonymous"),
                metadata=data.get("metadata", {}),
            )

    def _save(self, conv: Conversation) -> None:
        path = self.data_dir / f"{conv.id}.json"
        data = {
            "id": conv.id, "title": conv.title,
            "messages": [m.model_dump() for m in conv.messages],
            "created_at": conv.created_at, "updated_at": conv.updated_at,
            "user_id": conv.user_id, "metadata": conv.metadata,
        }
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def create(self, title: str = "New conversation", user_id: str = "anonymous") -> Conversation:
        conv_id = str(uuid.uuid4())
        conv = Conversation(id=conv_id, title=title, user_id=user_id)
        self._conversations[conv_id] = conv
        self._save(conv)
        return conv

    def get(self, conv_id: str) -> Conversation | None:
        return self._conversations.get(conv_id)

    def add_message(self, conv_id: str, role: str, content: str) -> ChatMessage:
        conv = self._conversations.get(conv_id)
        if not conv:
            raise KeyError(f"Conversation {conv_id} not found")
        msg = ChatMessage(role=role, content=content)
        conv.messages.append(msg)
        conv.updated_at = datetime.now(timezone.utc).isoformat()
        if len(conv.messages) == 1 and role == "user":
            conv.title = content[:60] + ("..." if len(content) > 60 else "")
        self._save(conv)
        return msg

    def get_context_string(self, conv_id: str, last_n: int = 6) -> str:
        conv = self._conversations.get(conv_id)
        if not conv:
            return ""
        recent = conv.messages[-last_n:]
        return "\n".join(f"{m.role}: {m.content}" for m in recent)

    def list_conversations(self, user_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        tenant_id = get_tenant_context().tenant_id
        convs = [
            c for c in self._conversations.values()
            if c.metadata.get("tenant_id", tenant_id) == tenant_id
        ]
        if user_id:
            convs = [c for c in convs if c.user_id == user_id]
        convs.sort(key=lambda c: c.updated_at, reverse=True)
        return [
            {"id": c.id, "title": c.title, "message_count": len(c.messages),
             "created_at": c.created_at, "updated_at": c.updated_at}
            for c in convs[:limit]
        ]
