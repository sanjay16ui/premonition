"""LLM provider and prompt management tests."""

from __future__ import annotations

import pytest

from premonition.copilot.llm.azure import AzureOpenAIProvider
from premonition.copilot.llm.mock import MockLLMProvider
from premonition.copilot.llm.openai import OpenAIProvider
from premonition.copilot.llm.service import LLMService
from premonition.copilot.prompts.manager import PromptManager
from premonition.copilot.prompts.registry import PromptTemplateRegistry


class TestMockLLM:
    def test_complete_returns_content(self):
        p = MockLLMProvider()
        r = p.complete("Explain sepsis prediction with factors")
        assert len(r.content) > 20
        assert r.model == "mock-local"

    def test_handover_template(self):
        p = MockLLMProvider()
        r = p.complete("Generate shift handover notes for ICU")
        assert "HANDOVER" in r.content.upper() or "handover" in r.content.lower()

    def test_executive_template(self):
        p = MockLLMProvider()
        r = p.complete("Generate executive KPI summary")
        assert "executive" in r.content.lower() or "hospital" in r.content.lower()

    def test_alert_template(self):
        p = MockLLMProvider()
        r = p.complete("Explain this alert for patient")
        assert "alert" in r.content.lower()

    def test_is_available(self):
        assert MockLLMProvider().is_available()


class TestProviderInterfaces:
    def test_openai_not_available_without_key(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        p = OpenAIProvider()
        assert not p.is_available()

    def test_azure_not_available_without_config(self, monkeypatch):
        monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
        monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
        p = AzureOpenAIProvider()
        assert not p.is_available()

    def test_llm_service_defaults_mock(self):
        svc = LLMService()
        assert svc.provider.name in ["mock-local", "groq", "ollama"]


class TestPromptRegistry:
    def test_default_templates_registered(self):
        reg = PromptTemplateRegistry()
        templates = reg.list_templates()
        names = {t["name"] for t in templates}
        assert "chat" in names
        assert "explain_prediction" in names
        assert "handover" in names

    def test_render_chat_template(self):
        reg = PromptTemplateRegistry()
        t = reg.get("chat")
        system, prompt = t.render(context="test ctx", message="hello")
        assert "hello" in prompt
        assert len(system) > 10

    def test_render_explain_prediction(self):
        reg = PromptTemplateRegistry()
        t = reg.get("explain_prediction")
        _, prompt = t.render(risk_score=0.7, prediction_label="sepsis_alert", factors="- hr_mean")
        assert "0.7" in prompt

    def test_unknown_template_raises(self):
        reg = PromptTemplateRegistry()
        with pytest.raises(KeyError):
            reg.get("nonexistent")


class TestPromptManager:
    def test_render_tracks_usage(self):
        mgr = PromptManager()
        system, prompt, version = mgr.render("chat", context="ctx", message="hi")
        log = mgr.get_usage_log()
        assert len(log) == 1
        assert log[0]["template"] == "chat"
        assert "@" in version

    def test_version_format(self):
        mgr = PromptManager()
        _, _, version = mgr.render("patient_summary", patient_id="p1", context="data")
        assert version.startswith("patient_summary@")
