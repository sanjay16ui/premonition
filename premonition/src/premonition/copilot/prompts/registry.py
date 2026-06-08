"""Prompt template registry — enterprise-grade clinical AI prompts v2.0."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PromptTemplate:
    name: str
    version: str
    system: str
    template: str
    variables: list[str] = field(default_factory=list)
    description: str = ""

    def render(self, **kwargs: Any) -> tuple[str, str]:
        rendered = self.template
        for key, value in kwargs.items():
            rendered = rendered.replace(f"{{{key}}}", str(value))
        return self.system, rendered


class PromptTemplateRegistry:
    """Registry of versioned clinical AI prompt templates."""

    def __init__(self) -> None:
        self._templates: dict[str, PromptTemplate] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        defaults = [
            PromptTemplate(
                "chat", "2.1.0",
                (
                    "You are PREMONITION, a Clinical AI Copilot for ICU physicians. "
                    "Respond ONLY in this exact format — no preamble, no filler:\n\n"
                    "Risk: [LOW|MODERATE|HIGH|CRITICAL] — [score if known]\n"
                    "Reason: [1-2 sentences citing exact vitals or SHAP factors]\n"
                    "Action: [1-2 specific, immediate clinical steps]\n\n"
                    "Maximum 100 words total. Use clinical abbreviations. Never repeat the question."
                ),
                "Context:\n{context}\n\nQuery: {message}\n\nRespond in the Risk/Reason/Action format only.",
                ["context", "message"],
                "Concise structured chat — Risk/Reason/Action, max 100 words",
            ),
            PromptTemplate(
                "patient_summary", "2.0.0",
                (
                    "You are a senior ICU physician generating structured clinical documentation.\n"
                    "Generate a comprehensive patient summary using ONLY the real patient data provided.\n"
                    "NEVER use generic text blocks. If data is missing, write 'Data unavailable'.\n"
                    "Every field must be populated with actual values from the context."
                ),
                """Generate a comprehensive ICU Patient Summary for Patient {patient_id}.

Patient Data:
{context}

Output EXACTLY this structure with real values (absolutely no templates):

## PATIENT SUMMARY — Patient {patient_id}

### 1. Patient ID
Patient {patient_id}

### 2. Current Risk Level
Determine from data: LOW / MODERATE / HIGH / CRITICAL. State the exact percentage.

### 3. Vital Sign Trends
Analyze heart rate, SpO2, BP, temp, and RR based on the data. If missing, write 'Data unavailable'.

### 4. Key Abnormal Findings
List any values outside normal clinical range. If none, write 'Data unavailable'.

### 5. Clinical Interpretation
Explain what the risk score and vitals mean clinically.

### 6. AI Assessment
Explain what the ML model detected and top SHAP-contributing features.

### 7. Recommended Actions
Provide evidence-based interventions or monitoring actions.

### 8. Confidence Score
State the model's confidence in its prediction.""",
                ["patient_id", "context"],
                "Enterprise ICU patient summary — 8 structured sections, no fill-in-the-blanks",
            ),
            PromptTemplate(
                "handover", "2.0.0",
                (
                    "You are a senior ICU charge nurse generating a formal shift handover report.\n"
                    "Use ONLY real patient data provided. If data is missing, write 'Data unavailable'.\n"
                    "Never use template text or fictional names."
                ),
                """Generate a formal ICU Shift Handover Report.

Patient Data for this Shift:
{context}

Report Timestamp: {timestamp}

Output EXACTLY this structure with real data (no templates):

## ICU SHIFT HANDOVER REPORT
**Date/Time:** {timestamp}
**Prepared by:** PREMONITION Agentic AI System
**Classification:** CONFIDENTIAL — CLINICAL USE ONLY

---

### Current condition
List the patient status and most recent vitals.

### Recent events
List any escalations or critical alerts during the shift.

### Risks
List patients by risk level percentage.

### Pending tasks
List specific pending clinical actions.

### Escalation recommendations
Specify exact vital thresholds that trigger escalation.

### Monitoring priorities
List the priorities for the incoming clinical team.""",
                ["context", "timestamp"],
                "Enterprise shift handover with real patient data",
            ),
            PromptTemplate(
                "explain_prediction", "2.0.0",
                (
                    "You are a clinical AI explainability engine translating ML model outputs into clear clinical language.\n"
                    "Convert probabilities into LOW, MODERATE, HIGH, or CRITICAL.\n"
                    "Never output undefined classifications. Never use templates."
                ),
                """Generate a Prediction Explanation for Patient {patient_id}.

ML Model Output:
- Sepsis Risk Score: {risk_score}
- Prediction Label: {prediction_label}
- Model Confidence: {confidence}%
- Top SHAP Contributing Factors: {factors}
- Vital Trends: {vital_trends}

Clinical Context:
{context}

Output EXACTLY this structure:

## PREDICTION EXPLANATION — Patient {patient_id}

### Risk score
Provide the risk score and convert to: LOW, MODERATE, HIGH, or CRITICAL.

### Why model predicted this
Explain the physiological significance of the prediction.

### Top contributing factors
List each SHAP factor with its clinical meaning and direction.

### Trend analysis
Describe how vitals are trending based on the context.

### Recommended intervention
Suggest an evidence-based immediate action or monitoring plan.

### Confidence
Provide the model confidence level.""",
                ["patient_id", "risk_score", "prediction_label", "confidence", "factors", "vital_trends", "context"],
                "Enterprise prediction explanation — risk, confidence, SHAP factors, trends, interventions",
            ),
            PromptTemplate(
                "explain_alert", "2.0.0",
                (
                    "You are a clinical decision support AI explaining alerts with specific, actionable guidance.\n"
                    "Always cite the exact vital values that triggered the alert."
                ),
                (
                    "Alert Level: {alert_level}\n"
                    "Sepsis Risk Score: {risk_score}%\n"
                    "Patient Clinical Data: {details}\n\n"
                    "Provide a structured alert explanation:\n"
                    "1. TRIGGER: exact vital values\n"
                    "2. IMMEDIATE ACTIONS: specific clinical interventions\n"
                    "3. MONITORING: which parameters to track\n"
                    "4. ESCALATION CRITERIA: exact conditions\n"
                    "5. EVIDENCE BASIS: reference clinical guideline"
                ),
                ["alert_level", "risk_score", "details"],
                "Alert explanation with specific triggers, interventions, and guidelines",
            ),
            PromptTemplate(
                "executive_summary", "2.0.0",
                (
                    "You are the Chief Medical Officer's AI assistant generating executive clinical intelligence reports.\n"
                    "Use data from the context. If missing, write 'Data unavailable'."
                ),
                (
                    "Hospital ICU Metrics and Status:\n{context}\n\n"
                    "Generate a structured Executive Clinical Intelligence Report:\n\n"
                    "## EXECUTIVE SUMMARY — PREMONITION AI\n\n"
                    "### 1. ICU STATUS OVERVIEW\n"
                    "Summarize current ICU state.\n\n"
                    "### 2. CRITICAL PATIENT ANALYSIS\n"
                    "Count and characterize critical/high-risk patients.\n\n"
                    "### 3. SYSTEM PERFORMANCE METRICS\n"
                    "Report AI model accuracy, alert response times, etc.\n\n"
                    "### 4. RISK TRAJECTORY\n"
                    "24-hour forecast: predicted patient deterioration curve.\n\n"
                    "### 5. EXECUTIVE RECOMMENDED ACTIONS\n"
                    "Top 3 operational decisions for senior leadership."
                ),
                ["context"],
                "Executive hospital intelligence report with strategic insights",
            ),
            PromptTemplate(
                "recommendations", "2.0.0",
                (
                    "You are a clinical decision support system generating evidence-based recommendations.\n"
                    "Rank interventions by urgency. Cite specific guidelines. If data is missing, write 'Data unavailable'."
                ),
                (
                    "Patient Risk Score: {risk_score}%\n"
                    "Top SHAP Factors: {factors}\n"
                    "Current Recommendations: {recommendations}\n\n"
                    "Generate ranked, evidence-based clinical recommendations:\n\n"
                    "**URGENT (Do Now):** Intervention addressing the highest-risk factor.\n"
                    "**HIGH (Within 30 min):** Second priority intervention.\n"
                    "**ROUTINE (Within 2 hrs):** Monitoring and standard care adjustment.\n"
                    "**PREVENTIVE:** Actions to prevent further deterioration.\n\n"
                    "For each recommendation, include: Rationale | Expected Outcome | Monitoring Parameter"
                ),
                ["risk_score", "factors", "recommendations"],
                "Ranked evidence-based recommendations with urgency levels",
            ),
        ]
        for t in defaults:
            self.register(t)

    def register(self, template: PromptTemplate) -> None:
        self._templates[template.name] = template

    def get(self, name: str) -> PromptTemplate:
        if name not in self._templates:
            raise KeyError(f"Prompt template '{name}' not found")
        return self._templates[name]

    def list_templates(self) -> list[dict[str, str]]:
        return [
            {"name": t.name, "version": t.version, "description": t.description}
            for t in self._templates.values()
        ]
