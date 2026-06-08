import sys
from pathlib import Path

# 1. Update implementations.py
impl_path = Path("src/premonition/intelligence/agents/implementations.py")
content = impl_path.read_text(encoding="utf-8")

# Fix MonitoringAgent NoneType bug
content = content.replace(
    'hr = observation.get("HeartRate_mean", 80)',
    'hr = float(observation.get("HeartRate_mean") or 80.0)'
)
content = content.replace(
    'sys_bp = observation.get("SysBP_mean", 120)',
    'sys_bp = float(observation.get("SysBP_mean") or 120.0)'
)
content = content.replace(
    'temp = observation.get("Temp_mean", 37.0)',
    'temp = float(observation.get("Temp_mean") or 37.0)'
)

# Append NotificationAgent and MemoryAgent
agents_code = '''

class NotificationAgent(PremonitionAgent):
    def __init__(self):
        super().__init__("Notification Agent")
        
    async def observe(self, context):
        return context.get("pending_alerts", [])

    async def analyze(self, observation):
        high_priority = [a for a in observation if getattr(a, "severity", "") in ["RED", "BLACK"] or getattr(a, "alert_level", "") in ["RED", "BLACK"]]
        return {"dispatch_needed": len(high_priority) > 0, "count": len(high_priority)}

    async def decide(self, analysis):
        if analysis.get("dispatch_needed"):
            return {"requires_action": True, "action": f"Dispatch {analysis['count']} critical alerts", "reason": "High priority alerts pending", "confidence": 1.0}
        return {"requires_action": False}

    async def act(self, decision):
        return {"event": "notification_sent", "explanation": self.format_explanation(decision["reason"], decision["action"], decision["confidence"])}

    async def verify(self, action_result):
        return True


class MemoryAgent(PremonitionAgent):
    def __init__(self):
        super().__init__("Memory Agent")
        
    async def observe(self, context):
        return context.get("agent_decisions", [])

    async def analyze(self, observation):
        return {"store_needed": len(observation) > 0, "count": len(observation)}

    async def decide(self, analysis):
        if analysis.get("store_needed"):
            return {"requires_action": True, "action": f"Persist {analysis['count']} decisions", "reason": "Unsaved agent decisions", "confidence": 1.0}
        return {"requires_action": False}

    async def act(self, decision):
        return {"event": "memory_persisted", "explanation": self.format_explanation(decision["reason"], decision["action"], decision["confidence"])}

    async def verify(self, action_result):
        return True
'''
if "class NotificationAgent" not in content:
    content += agents_code
impl_path.write_text(content, encoding="utf-8")
print("Updated implementations.py")

# 2. Update __init__.py
init_path = Path("src/premonition/intelligence/agents/__init__.py")
init_content = init_path.read_text(encoding="utf-8")
if "NotificationAgent" not in init_content:
    init_content = init_content.replace(
        "    ExecutiveAgent,",
        "    ExecutiveAgent,\n    NotificationAgent,\n    MemoryAgent,"
    )
    init_path.write_text(init_content, encoding="utf-8")
print("Updated __init__.py")

# 3. Update monitoring.py
mon_path = Path("src/premonition/realtime/monitoring.py")
mon_content = mon_path.read_text(encoding="utf-8")

if "NotificationAgent" not in mon_content:
    mon_content = mon_content.replace(
        "MonitoringAgent, PredictionAgent, ClinicalAgent, EscalationAgent, ExecutiveAgent",
        "MonitoringAgent, PredictionAgent, ClinicalAgent, EscalationAgent, ExecutiveAgent, NotificationAgent, MemoryAgent"
    )
    
    mon_content = mon_content.replace(
        "self.executive_agent = ExecutiveAgent()",
        "self.executive_agent = ExecutiveAgent()\n        self.notification_agent = NotificationAgent()\n        self.memory_agent = MemoryAgent()"
    )
    
    mon_content = mon_content.replace(
        "for agent in [self.monitoring_agent, self.prediction_agent, self.clinical_agent, self.escalation_agent]:",
        "agent_context['pending_alerts'] = alerts\n        agent_context['agent_decisions'] = []\n        \n        for agent in [self.monitoring_agent, self.prediction_agent, self.clinical_agent, self.escalation_agent, self.notification_agent, self.memory_agent]:"
    )
    
    mon_path.write_text(mon_content, encoding="utf-8")
print("Updated monitoring.py")
