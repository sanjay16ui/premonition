"""Base agent class — Observe → Analyze → Decide → Act → Verify → Remember loop."""
from abc import ABC, abstractmethod
import logging
import uuid
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class PremonitionAgent(ABC):
    """Base class for autonomous healthcare agents."""

    def __init__(self, name: str):
        self.name = name
        self.id = str(uuid.uuid4())
        from premonition.intelligence.memory.core import memory_system
        self.memory = memory_system

    async def run_cycle(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Runs the standard Observe → Analyze → Decide → Act → Verify → Remember loop."""
        patient_id = context.get("patient_id", "system")

        # Inject prior outcome feedback into context for all agents
        prior = self._fetch_prior_outcome(patient_id)
        if prior:
            context["prior_outcome"] = prior

        try:
            observation = await self.observe(context)
            analysis = await self.analyze(observation)
            decision = await self.decide(analysis)

            if decision.get("requires_action"):
                action_result = await self.act(decision)

                # GAP 1: Real verify() — returns (success: bool, detail: str)
                verified, verify_detail = await self.verify(action_result)

                # GAP 2: Record outcome in OutcomeMemory unconditionally
                outcome_text = (
                    f"{self.name} verified: {verify_detail}"
                    if verified
                    else f"{self.name} verification FAILED: {verify_detail}"
                )
                self._record_outcome(patient_id, "PASS" if verified else "FAIL", outcome_text)

                # Record decision to memory
                self.memory.record_decision(
                    self.name,
                    patient_id,
                    decision
                )

                action_result["verified"] = verified
                action_result["verify_detail"] = verify_detail
                return action_result

            return {"status": "no_action"}

        except Exception as e:
            logger.error(f"Agent {self.name} failed cycle: {e}")
            return {"status": "error", "error": str(e)}

    def _fetch_prior_outcome(self, patient_id: str) -> Optional[str]:
        """GAP 7: Fetch most recent verified outcome for this patient."""
        try:
            from premonition.intelligence.memory.store import AgentMemoryStore
            from pathlib import Path
            import os
            logs_dir = Path(os.getenv("PREMONITION_LOGS_DIR", "logs"))
            store = AgentMemoryStore(logs_dir / "agent_memory.db")
            timeline = store.get_patient_timeline(patient_id, limit=5)
            # Find most recent outcome record
            for entry in timeline:
                if entry.get("type") == "outcome":
                    return entry.get("result", "")
            # Fall back to most recent decision summary
            for entry in timeline:
                if entry.get("type") == "agent_decision":
                    return f"Previous {entry['agent']}: {entry['action']}"
        except Exception:
            pass
        return None

    def _record_outcome(self, patient_id: str, result: str, feedback: str) -> None:
        """GAP 2: Persist outcome to OutcomeMemory table."""
        try:
            from premonition.intelligence.memory.store import AgentMemoryStore
            from pathlib import Path
            import os
            logs_dir = Path(os.getenv("PREMONITION_LOGS_DIR", "logs"))
            store = AgentMemoryStore(logs_dir / "agent_memory.db")
            store.record_outcome(patient_id, result, feedback)
        except Exception as e:
            logger.warning(f"Failed to record outcome for {patient_id}: {e}")

    @abstractmethod
    async def observe(self, context: Dict[str, Any]) -> Any:
        pass

    @abstractmethod
    async def analyze(self, observation: Any) -> Any:
        pass

    @abstractmethod
    async def decide(self, analysis: Any) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def act(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def verify(self, action_result: Dict[str, Any]) -> tuple[bool, str]:
        """Returns (success, detail_message)."""
        pass

    def format_explanation(self, reason: str, action: str, confidence: float) -> dict:
        """Standard format for agent explainability."""
        return {
            "agent": self.name,
            "reason": reason,
            "action": action,
            "confidence": f"{int(confidence * 100)}%"
        }
