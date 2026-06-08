"""Multi-step agent workflow engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class WorkflowStep:
    name: str
    action: Callable[..., Any]
    description: str = ""


@dataclass
class WorkflowResult:
    steps_completed: list[str] = field(default_factory=list)
    outputs: dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error: str | None = None


class MultiStepAgentWorkflowEngine:
    """Execute multi-step copilot workflows."""

    def run(self, steps: list[WorkflowStep], initial_context: dict[str, Any] | None = None) -> WorkflowResult:
        result = WorkflowResult()
        context = dict(initial_context or {})
        for step in steps:
            try:
                output = step.action(context)
                result.steps_completed.append(step.name)
                result.outputs[step.name] = output
                if isinstance(output, dict):
                    context.update(output)
            except Exception as exc:
                result.success = False
                result.error = f"Step '{step.name}' failed: {exc}"
                break
        return result

    def patient_analysis_workflow(self, patient_id: str, copilot_service: Any) -> WorkflowResult:
        steps = [
            WorkflowStep("retrieve_context", lambda ctx: {"patient_id": patient_id}),
            WorkflowStep("patient_summary", lambda ctx: copilot_service.patient_summary(
                __import__("premonition.copilot.schemas", fromlist=["PatientSummaryRequest"]).PatientSummaryRequest(patient_id=ctx["patient_id"]),
                actor="workflow",
            ).model_dump()),
            WorkflowStep("risk_check", lambda ctx: {"summary_ready": True}),
        ]
        return self.run(steps)
