"""Prompt management system with version tracking."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from premonition.copilot.prompts.registry import PromptTemplateRegistry


class PromptManager:
    """Render prompts and track usage for audit."""

    def __init__(self, registry: PromptTemplateRegistry | None = None) -> None:
        self.registry = registry or PromptTemplateRegistry()
        self._usage_log: list[dict[str, Any]] = []

    def render(self, template_name: str, **variables: Any) -> tuple[str, str, str]:
        template = self.registry.get(template_name)
        system, prompt = template.render(**variables)
        version = f"{template.name}@{template.version}"
        self._usage_log.append({
            "template": template_name,
            "version": version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "variables": list(variables.keys()),
        })
        return system, prompt, version

    def get_usage_log(self, limit: int = 50) -> list[dict[str, Any]]:
        return self._usage_log[-limit:]
