"""Local/mock LLM provider for testing and offline use."""

from __future__ import annotations

import re

from premonition.copilot.llm.base import LLMProvider, LLMResponse


class MockLLMProvider(LLMProvider):
    """Template-based local LLM — no external API calls."""

    @property
    def name(self) -> str:
        return "mock-local"

    def is_available(self) -> bool:
        return True

    def complete(self, prompt: str, system: str | None = None, temperature: float = 0.3) -> LLMResponse:
        content = self._generate(prompt, system)
        return LLMResponse(content=content, model=self.name, tokens_used=len(content.split()))

    def _generate(self, prompt: str, system: str | None) -> str:
        prompt_lower = prompt.lower()
        context_match = re.search(r"context:\s*(.+?)(?:\n\nuser:|$)", prompt, re.DOTALL | re.IGNORECASE)
        context = context_match.group(1).strip() if context_match else ""

        if "handover" in prompt_lower or "shift" in prompt_lower:
            return self._handover_response(context)
        if "executive" in prompt_lower or "kpi" in prompt_lower:
            return self._executive_response(context)
        if "alert" in prompt_lower:
            return self._alert_response(context)
        if "shap" in prompt_lower or "explain" in prompt_lower or "factor" in prompt_lower:
            return self._explain_response(context)
        if "summary" in prompt_lower or "patient" in prompt_lower:
            return self._patient_summary(context)
        if "recommend" in prompt_lower:
            return self._recommendation_response(context)
        return self._chat_response(prompt, context)

    def _explain_response(self, ctx: str) -> str:
        factors = [l.strip("- ") for l in ctx.split("\n") if l.strip().startswith("-")]
        factor_text = ", ".join(factors[:5]) if factors else "elevated vitals and comorbidities"
        return (
            f"Based on the ML model analysis, the elevated sepsis risk is primarily driven by "
            f"{factor_text}. The SHAP explanation indicates these features contributed most to the "
            f"prediction score. Clinical correlation with Sepsis-3 criteria is recommended."
        )

    def _patient_summary(self, ctx: str) -> str:
        return (
            "Patient Status Summary:\n"
            f"{ctx[:500] if ctx else 'No additional context available.'}\n\n"
            "The patient requires continued monitoring with attention to trending vitals "
            "and sepsis early-warning indicators."
        )

    def _handover_response(self, ctx: str) -> str:
        return (
            "SHIFT HANDOVER NOTES\n"
            "====================\n"
            f"{ctx[:800] if ctx else 'No patients flagged for handover.'}\n\n"
            "Action items: Review high-risk patients, verify antibiotic timelines, "
            "confirm lactate results for flagged cases."
        )

    def _executive_response(self, ctx: str) -> str:
        return (
            "Executive Hospital Status:\n"
            f"{ctx[:600] if ctx else 'System operating normally.'}\n\n"
            "Key priorities: maintain sepsis detection rate, monitor ICU capacity, "
            "and review alert response metrics."
        )

    def _alert_response(self, ctx: str) -> str:
        return (
            f"Alert Explanation: The current alert was triggered based on the following signals:\n"
            f"{ctx[:400] if ctx else 'Elevated risk score with clinical rule triggers.'}\n\n"
            "Recommended action: escalate per hospital sepsis protocol."
        )

    def _recommendation_response(self, ctx: str) -> str:
        return (
            "Clinical Recommendations (ranked by priority):\n"
            "1. Obtain blood cultures before antibiotics\n"
            "2. Measure serum lactate\n"
            "3. Initiate fluid resuscitation if hypotensive\n"
            f"\nContext: {ctx[:200] if ctx else 'Based on current risk assessment.'}"
        )

    def _chat_response(self, prompt: str, ctx: str) -> str:
        user_q = prompt.split("User:")[-1].strip() if "User:" in prompt else prompt[-200:]
        sources = f" Referenced {ctx.count(chr(10)) + 1} context lines." if ctx else ""
        return (
            f"Based on available PREMONITION platform data, regarding your question about "
            f"'{user_q[:100]}': the clinical AI copilot has analyzed predictions, monitoring "
            f"data, and knowledge base sources.{sources} "
            "Please verify all recommendations with clinical judgment."
        )
