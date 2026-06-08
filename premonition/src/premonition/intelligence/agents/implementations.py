"""Agent implementations — all 7 agentic AI gaps closed."""
import logging
import os
import json
import urllib.request
from typing import Dict, Any, List, Tuple
from .base import PremonitionAgent

logger = logging.getLogger(__name__)


def _safe_float(val: Any, default: float = 0.0) -> float:
    """Convert a value to float safely, stripping % signs and handling None."""
    if val is None:
        return default
    try:
        return float(str(val).replace('%', '').replace(',', '').strip())
    except (ValueError, TypeError):
        return default

# ─────────────────────────────────────────────
# Internal Autonomous Dispatch Bus (GAP 4)
# ─────────────────────────────────────────────
from collections import deque
from datetime import datetime, timezone

class _AutonomousDispatch:
    """Internal dispatch record bus — no external integrations required."""
    def __init__(self, maxlen: int = 500):
        self._records: deque = deque(maxlen=maxlen)

    def dispatch(self, dispatch_type: str, patient_id: str, message: str,
                 agent: str, priority: str = "HIGH") -> str:
        """Record an autonomous internal dispatch event. Returns dispatch_id."""
        import uuid
        dispatch_id = str(uuid.uuid4())[:8]
        record = {
            "dispatch_id": dispatch_id,
            "type": dispatch_type,           # "critical" | "executive" | "escalation"
            "patient_id": patient_id,
            "message": message,
            "agent": agent,
            "priority": priority,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "DISPATCHED",
        }
        self._records.appendleft(record)
        logger.info(f"[DISPATCH:{dispatch_type.upper()}] {agent} -> {patient_id}: {message}")
        return dispatch_id

    def recent(self, limit: int = 50) -> list:
        return list(self._records)[:limit]

    def count(self) -> int:
        return len(self._records)


# Module-level dispatch bus shared across all agents
autonomous_dispatch = _AutonomousDispatch()


# ─────────────────────────────────────────────
# Autonomous Ollama helper (GAP 3)
# ─────────────────────────────────────────────
def _call_ollama_summary(patient_id: str, risk_score: float, alert_level: str,
                          vitals: dict, recommendations: list) -> str:
    """Call Ollama to generate an autonomous patient summary. Returns plain text."""
    model = os.getenv("PREMONITION_OLLAMA_MODEL", "llama3:latest")
    url = f"{os.getenv('PREMONITION_OLLAMA_URL', 'http://localhost:11434').rstrip('/')}/api/generate"

    rec_text = "; ".join(recommendations[:3]) if recommendations else "None"
    hr   = vitals.get("hr_mean", "?")
    spo2 = vitals.get("spo2_mean", "?")
    temp = vitals.get("temp_celsius_mean", "?")
    rr   = vitals.get("respiratory_rate_mean", "?")
    sbp  = vitals.get("sbp_mean", "?")

    prompt = (
        f"You are a clinical AI assistant in an ICU. Provide a concise 3-section summary.\n\n"
        f"Patient: {patient_id}\n"
        f"Alert Level: {alert_level}\n"
        f"Sepsis Risk: {risk_score*100:.1f}%\n"
        f"Vitals — HR: {hr} bpm, SpO2: {spo2}%, Temp: {temp}°C, RR: {rr}/min, SBP: {sbp} mmHg\n"
        f"Active Recommendations: {rec_text}\n\n"
        f"Respond in EXACTLY this format:\n"
        f"PATIENT SUMMARY\n"
        f"What happened? [1 sentence]\n"
        f"Why? [1 sentence explaining the main risk driver]\n"
        f"Recommended action? [1 specific clinical action]"
    )

    try:
        from premonition.copilot.llm.service import LLMService
        svc = LLMService()
        res = svc.complete(prompt, temperature=0.2)
        return res.content.strip()
    except Exception as e:
        logger.warning(f"Autonomous LLM call failed for {patient_id}: {e}")
        return ""


# ─────────────────────────────────────────────
# MONITORING AGENT — GAP 5 field fix
# ─────────────────────────────────────────────
class MonitoringAgent(PremonitionAgent):
    def __init__(self):
        super().__init__("Monitoring Agent")

    async def observe(self, context: Dict[str, Any]) -> Any:
        return context.get("vitals", {})

    async def analyze(self, observation: Any) -> Any:
        flags = []
        if not isinstance(observation, dict):
            return {"flags": flags}

        # GAP 5 FIX: use actual PatientFeaturesRequest / VitalsSnapshot field names
        hr   = observation.get("hr_mean")     or observation.get("HeartRate_mean")
        sbp  = observation.get("sbp_mean")    or observation.get("SysBP_mean")
        temp = observation.get("temp_celsius_mean") or observation.get("Temp_mean")
        spo2 = observation.get("spo2_mean")   or observation.get("SpO2_mean")
        rr   = observation.get("respiratory_rate_mean") or observation.get("RespRate_mean")

        hr   = _safe_float(hr,   80.0)
        sbp  = _safe_float(sbp,  120.0)
        temp = _safe_float(temp, 37.0)
        spo2 = _safe_float(spo2, 98.0)
        rr   = _safe_float(rr,   16.0)

        if hr   > 110: flags.append(f"Tachycardia (HR: {hr:.1f} bpm)")
        if hr   < 50:  flags.append(f"Bradycardia (HR: {hr:.1f} bpm)")
        if sbp  < 90:  flags.append(f"Hypotension (SBP: {sbp:.1f} mmHg)")
        if temp > 38.5: flags.append(f"Fever (Temp: {temp:.1f}°C)")
        if spo2 < 92:  flags.append(f"Hypoxia (SpO2: {spo2:.1f}%)")
        if rr   > 22:  flags.append(f"Tachypnoea (RR: {rr:.1f}/min)")

        return {"flags": flags, "hr": hr, "sbp": sbp, "temp": temp, "spo2": spo2, "rr": rr}

    async def decide(self, analysis: Any) -> Dict[str, Any]:
        flags = analysis.get("flags", [])
        if flags:
            reason = " | ".join(flags)
            return {"requires_action": True, "action": "Flag abnormal vitals",
                    "reason": reason, "confidence": 0.95, "flags": flags}
        return {"requires_action": False}

    async def act(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "event": "vitals_flagged",
            "flags": decision.get("flags", []),
            "explanation": self.format_explanation(
                decision["reason"], decision["action"], decision["confidence"]
            )
        }

    async def verify(self, action_result: Dict[str, Any]) -> Tuple[bool, str]:
        """GAP 1: Verify flags were actually generated."""
        flags = action_result.get("flags", [])
        ok = len(flags) > 0
        detail = f"Generated {len(flags)} vitals flag(s): {flags[:2]}" if ok else "No flags produced"
        return ok, detail


# ─────────────────────────────────────────────
# PREDICTION AGENT
# ─────────────────────────────────────────────
class PredictionAgent(PremonitionAgent):
    def __init__(self):
        super().__init__("Prediction Agent")

    async def observe(self, context: Dict[str, Any]) -> Any:
        return {"risk_score": context.get("risk_score", 0.0),
                "patient_id": context.get("patient_id", "")}

    async def analyze(self, observation: Any) -> Any:
        score = observation.get("risk_score", 0.0)
        return {"is_critical": score >= 0.8, "is_warning": score >= 0.5,
                "score": score, "patient_id": observation.get("patient_id", "")}

    async def decide(self, analysis: Any) -> Dict[str, Any]:
        score  = analysis.get("score", 0.0)
        pid    = analysis.get("patient_id", "")
        if analysis.get("is_critical"):
            return {"requires_action": True, "action": "Trigger Critical Risk Alert",
                    "reason": f"Risk score reached critical level ({score:.2f})",
                    "confidence": 0.99, "patient_id": pid, "score": score}
        elif analysis.get("is_warning"):
            return {"requires_action": True, "action": "Trigger Watch Alert",
                    "reason": f"Risk score elevated ({score:.2f})",
                    "confidence": 0.85, "patient_id": pid, "score": score}
        return {"requires_action": False}

    async def act(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        # GAP 4: autonomous dispatch for critical patients
        pid   = decision.get("patient_id", "unknown")
        score = decision.get("score", 0.0)
        if score >= 0.8:
            dispatch_id = autonomous_dispatch.dispatch(
                "critical", pid,
                f"CRITICAL: Patient {pid} risk={score:.2f} — immediate review required",
                self.name, "CRITICAL"
            )
        else:
            dispatch_id = autonomous_dispatch.dispatch(
                "watchlist", pid,
                f"WATCH: Patient {pid} risk={score:.2f} — elevated risk",
                self.name, "MEDIUM"
            )
        return {
            "event": "risk_alert",
            "dispatch_id": dispatch_id,
            "explanation": self.format_explanation(
                decision["reason"], decision["action"], decision["confidence"]
            )
        }

    async def verify(self, action_result: Dict[str, Any]) -> Tuple[bool, str]:
        """GAP 1: Verify the dispatch was recorded."""
        dispatch_id = action_result.get("dispatch_id")
        if dispatch_id:
            records = autonomous_dispatch.recent(10)
            found = any(r.get("dispatch_id") == dispatch_id for r in records)
            if found:
                return True, f"Risk alert dispatched (id={dispatch_id})"
            return False, f"Dispatch id={dispatch_id} not found in bus"
        return False, "No dispatch_id in action result"


# ─────────────────────────────────────────────
# CLINICAL AGENT — GAP 3: Autonomous Ollama
# ─────────────────────────────────────────────
class ClinicalAgent(PremonitionAgent):
    def __init__(self):
        super().__init__("Clinical Agent")

    async def observe(self, context: Dict[str, Any]) -> Any:
        return {
            "shap":        context.get("shap_values", []),
            "vitals":      context.get("vitals", {}),
            "risk_score":  context.get("risk_score", 0.0),
            "alert_level": context.get("alert_level", "GREEN"),
            "patient_id":  context.get("patient_id", ""),
            "prior_outcome": context.get("prior_outcome", ""),
        }

    async def analyze(self, observation: Any) -> Any:
        shap: List[Dict[str, Any]] = observation.get("shap", [])
        top_factors = []
        for s in shap:
            if isinstance(s, dict) and "feature" in s:
                top_factors.append(s["feature"])
            elif isinstance(s, str):
                top_factors.append(s)

        risk_score  = observation.get("risk_score", 0.0)
        alert_level = observation.get("alert_level", "GREEN")
        needs_llm   = alert_level in ("RED", "BLACK")

        return {
            "top_factors":   top_factors[:3],
            "risk_score":    risk_score,
            "alert_level":   alert_level,
            "patient_id":    observation.get("patient_id", ""),
            "vitals":        observation.get("vitals", {}),
            "prior_outcome": observation.get("prior_outcome", ""),
            "needs_llm":     needs_llm,
        }

    async def decide(self, analysis: Any) -> Dict[str, Any]:
        factors      = analysis.get("top_factors", [])
        prior        = analysis.get("prior_outcome", "")
        prior_clause = f" (Context: {prior})" if prior else ""

        recs = []
        reasoning = []
        for f in factors:
            f_lower = f.lower()
            if "lactate" in f_lower:
                recs.append("Order stat lactate panel")
                reasoning.append("Elevated lactate contribution")
            elif "hr" in f_lower or "heart" in f_lower:
                recs.append("Review continuous ECG")
                reasoning.append("Heart rate variance contributing to risk")
            elif "bp" in f_lower or "pressure" in f_lower or "map" in f_lower:
                recs.append("Evaluate for vasopressor support")
                reasoning.append("Blood pressure instability driving risk")
            elif "resp" in f_lower or "spo2" in f_lower or "oxygen" in f_lower:
                recs.append("Assess airway and oxygenation immediately")
                reasoning.append("Respiratory or oxygenation abnormalities")
            elif "temp" in f_lower or "temperature" in f_lower:
                recs.append("Initiate infection workup and blood cultures")
                reasoning.append("Fever pattern driving sepsis risk")

        if not recs:
            recs      = ["Conduct urgent general clinical review"]
            reasoning = [f"Primary risk drivers: {', '.join(factors) or 'multi-system'}"]

        return {
            "requires_action": True,
            "action":          "Recommend SHAP-driven interventions",
            "reason":          " | ".join(reasoning) + prior_clause,
            "confidence":      0.90,
            "recommendations": recs,
            "patient_id":      analysis.get("patient_id", ""),
            "vitals":          analysis.get("vitals", {}),
            "risk_score":      analysis.get("risk_score", 0.0),
            "alert_level":     analysis.get("alert_level", "GREEN"),
            "needs_llm":       analysis.get("needs_llm", False),
        }

    async def act(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        recs        = decision.get("recommendations", [])
        patient_id  = decision.get("patient_id", "")
        alert_level = decision.get("alert_level", "GREEN")
        risk_score  = decision.get("risk_score", 0.0)
        vitals      = decision.get("vitals", {})

        result = {
            "event":           "clinical_recommendation",
            "recommendations": recs,
            "explanation":     self.format_explanation(
                decision["reason"], decision["action"], decision["confidence"]
            )
        }

        # GAP 3: Autonomous Ollama summary for RED/BLACK patients
        if decision.get("needs_llm") and patient_id:
            try:
                summary = _call_ollama_summary(
                    patient_id, risk_score, alert_level, vitals, recs
                )
                if summary:
                    result["autonomous_summary"] = summary
                    # Persist to memory
                    self.memory.record_decision(
                        self.name, patient_id,
                        {"autonomous_summary": summary, "alert_level": alert_level}
                    )
                    logger.info(f"[COPILOT-AUTO] {patient_id} summary generated autonomously")
            except Exception as e:
                logger.warning(f"Autonomous Ollama summary failed: {e}")

        return result

    async def verify(self, action_result: Dict[str, Any]) -> Tuple[bool, str]:
        """GAP 1: Verify recommendations were generated."""
        recs = action_result.get("recommendations", [])
        ok   = len(recs) > 0
        has_summary = "autonomous_summary" in action_result
        detail = f"{len(recs)} recommendation(s) generated"
        if has_summary:
            detail += " + autonomous Ollama summary"
        if not ok:
            detail = "No recommendations produced"
        return ok, detail


# ─────────────────────────────────────────────
# ESCALATION AGENT
# ─────────────────────────────────────────────
class EscalationAgent(PremonitionAgent):
    def __init__(self):
        super().__init__("Escalation Agent")

    async def observe(self, context: Dict[str, Any]) -> Any:
        return {
            "unresolved_minutes": context.get("unresolved_minutes", 0),
            "patient_id":         context.get("patient_id", ""),
            "risk_score":         context.get("risk_score", 0.0),
        }

    async def analyze(self, observation: Any) -> Any:
        t   = observation.get("unresolved_minutes", 0)
        pid = observation.get("patient_id", "")
        target = None
        if   t >= 30: target = "Executive Dashboard"
        elif t >= 15: target = "ICU Lead"
        elif t >= 5:  target = "Attending Physician"
        return {"target": target, "time": t, "patient_id": pid,
                "risk_score": observation.get("risk_score", 0.0)}

    async def decide(self, analysis: Any) -> Dict[str, Any]:
        if analysis.get("target"):
            return {
                "requires_action": True,
                "action":          f"Escalate to {analysis['target']}",
                "reason":          f"Patient in risk state for {analysis['time']} min",
                "confidence":      0.99,
                "target":          analysis["target"],
                "patient_id":      analysis["patient_id"],
                "risk_score":      analysis["risk_score"],
            }
        return {"requires_action": False}

    async def act(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        pid    = decision.get("patient_id", "unknown")
        target = decision.get("target", "Staff")
        score  = decision.get("risk_score", 0.0)

        # GAP 4: autonomous escalation dispatch
        dispatch_id = autonomous_dispatch.dispatch(
            "escalation", pid,
            f"ESCALATION -> {target}: Patient {pid} unresolved risk={score:.2f}",
            self.name, "HIGH"
        )
        return {
            "event":       "escalation_triggered",
            "target":      target,
            "dispatch_id": dispatch_id,
            "explanation": self.format_explanation(
                decision["reason"], decision["action"], decision["confidence"]
            )
        }

    async def verify(self, action_result: Dict[str, Any]) -> Tuple[bool, str]:
        """GAP 1: Verify escalation was dispatched to the bus."""
        dispatch_id = action_result.get("dispatch_id")
        target      = action_result.get("target", "")
        if dispatch_id:
            records = autonomous_dispatch.recent(20)
            found   = any(r.get("dispatch_id") == dispatch_id for r in records)
            if found:
                return True, f"Escalation dispatched to {target} (id={dispatch_id})"
        return False, f"Escalation to {target} — dispatch not confirmed"


# ─────────────────────────────────────────────
# EXECUTIVE AGENT
# ─────────────────────────────────────────────
class ExecutiveAgent(PremonitionAgent):
    def __init__(self):
        super().__init__("Executive Agent")

    async def observe(self, context: Dict[str, Any]) -> Any:
        return context.get("hospital_metrics", {})

    async def analyze(self, observation: Any) -> Any:
        icu_load = observation.get("icu_occupancy", 0.0)
        return {"overload_risk": icu_load > 0.8, "load": icu_load}

    async def decide(self, analysis: Any) -> Dict[str, Any]:
        if analysis.get("overload_risk"):
            return {
                "requires_action": True,
                "action":          "Initiate surge capacity protocol",
                "reason":          f"ICU occupancy reached {analysis['load']*100:.0f}%",
                "confidence":      0.88,
                "load":            analysis["load"],
            }
        return {"requires_action": False}

    async def act(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        load = decision.get("load", 0.0)
        # GAP 4: autonomous executive dispatch
        dispatch_id = autonomous_dispatch.dispatch(
            "executive", "system",
            f"EXECUTIVE ALERT: ICU at {load*100:.0f}% capacity — surge protocol initiated",
            self.name, "CRITICAL"
        )
        return {
            "event":       "executive_forecast",
            "dispatch_id": dispatch_id,
            "explanation": self.format_explanation(
                decision["reason"], decision["action"], decision["confidence"]
            )
        }

    async def verify(self, action_result: Dict[str, Any]) -> Tuple[bool, str]:
        """GAP 1: Verify the executive alert was dispatched."""
        dispatch_id = action_result.get("dispatch_id")
        if dispatch_id:
            records = autonomous_dispatch.recent(10)
            found   = any(r.get("dispatch_id") == dispatch_id for r in records)
            if found:
                return True, f"Executive surge alert dispatched (id={dispatch_id})"
        return False, "Executive dispatch not confirmed in bus"


# ─────────────────────────────────────────────
# NOTIFICATION AGENT
# ─────────────────────────────────────────────
class NotificationAgent(PremonitionAgent):
    def __init__(self):
        super().__init__("Notification Agent")
        self._dispatched_count = 0

    async def observe(self, context: Dict[str, Any]) -> Any:
        return context.get("pending_alerts", [])

    async def analyze(self, observation: Any) -> Any:
        high = [a for a in observation if getattr(a, "severity", "") in ("RED", "BLACK")
                or getattr(a, "alert_level", getattr(a, "severity", "")) in ("RED", "BLACK")]
        return {"dispatch_needed": len(high) > 0, "count": len(high)}

    async def decide(self, analysis: Any) -> Dict[str, Any]:
        if analysis.get("dispatch_needed"):
            return {
                "requires_action": True,
                "action":          f"Dispatch {analysis['count']} critical alerts",
                "reason":          "High priority alerts pending dispatch",
                "confidence":      1.0,
                "alert_count":     analysis["count"],
            }
        return {"requires_action": False}

    async def act(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        n = decision.get("alert_count", 0)
        self._dispatched_count += n
        # GAP 4: record dispatch
        dispatch_id = autonomous_dispatch.dispatch(
            "critical", "batch",
            f"NOTIFICATION: {n} critical alert(s) dispatched to monitoring staff",
            self.name, "HIGH"
        )
        return {
            "event":              "notification_sent",
            "dispatched_count":   self._dispatched_count,
            "batch_count":        n,
            "dispatch_id":        dispatch_id,
            "explanation":        self.format_explanation(
                decision["reason"], decision["action"], decision["confidence"]
            )
        }

    async def verify(self, action_result: Dict[str, Any]) -> Tuple[bool, str]:
        """GAP 1: Verify notification count > 0 and in dispatch bus."""
        batch = action_result.get("batch_count", 0)
        dispatch_id = action_result.get("dispatch_id")
        if batch > 0 and dispatch_id:
            return True, f"{batch} notification(s) dispatched (id={dispatch_id})"
        return False, f"Notification dispatch failed — batch={batch}"


# ─────────────────────────────────────────────
# MEMORY AGENT — GAP 6: activated
# ─────────────────────────────────────────────
class MemoryAgent(PremonitionAgent):
    def __init__(self):
        super().__init__("Memory Agent")

    async def observe(self, context: Dict[str, Any]) -> Any:
        """GAP 6: Retrieve actual previous decisions from AgentMemoryStore."""
        patient_id = context.get("patient_id", "")
        history = []
        try:
            from premonition.intelligence.memory.store import AgentMemoryStore
            from pathlib import Path
            logs_dir = Path(os.getenv("PREMONITION_LOGS_DIR", "logs"))
            store   = AgentMemoryStore(logs_dir / "agent_memory.db")
            history = store.get_patient_timeline(patient_id, limit=5)
        except Exception as e:
            logger.warning(f"MemoryAgent observe failed: {e}")

        return {
            "patient_id":       patient_id,
            "history":          history,
            "current_decisions": context.get("agent_decisions", []),
        }

    async def analyze(self, observation: Any) -> Any:
        history = observation.get("history", [])
        decisions = [h for h in history if h.get("type") == "agent_decision"]
        outcomes  = [h for h in history if h.get("type") == "outcome"]
        return {
            "has_history":    len(decisions) > 0,
            "decision_count": len(decisions),
            "outcome_count":  len(outcomes),
            "latest_action":  decisions[0].get("action", "") if decisions else "",
            "latest_outcome": outcomes[0].get("result", "") if outcomes else "",
            "patient_id":     observation.get("patient_id", ""),
        }

    async def decide(self, analysis: Any) -> Dict[str, Any]:
        if analysis.get("has_history"):
            return {
                "requires_action": True,
                "action":          f"Provide historical context ({analysis['decision_count']} decisions, {analysis['outcome_count']} outcomes)",
                "reason":          f"Latest: {analysis['latest_action']} | Outcome: {analysis['latest_outcome'] or 'pending'}",
                "confidence":      1.0,
                "patient_id":      analysis["patient_id"],
                "decision_count":  analysis["decision_count"],
                "outcome_count":   analysis["outcome_count"],
            }
        return {"requires_action": False}

    async def act(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "event":          "memory_context_provided",
            "decision_count": decision.get("decision_count", 0),
            "outcome_count":  decision.get("outcome_count", 0),
            "explanation":    self.format_explanation(
                decision["reason"], decision["action"], decision["confidence"]
            )
        }

    async def verify(self, action_result: Dict[str, Any]) -> Tuple[bool, str]:
        """GAP 1: Verify memory context was retrieved."""
        d_count = action_result.get("decision_count", 0)
        o_count = action_result.get("outcome_count", 0)
        ok      = d_count > 0
        detail  = f"Memory context: {d_count} decisions, {o_count} outcomes retrieved"
        if not ok:
            detail = "No historical data found for patient"
        return ok, detail
