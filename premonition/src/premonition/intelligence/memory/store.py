"""Agent Memory Store for persistent history across restarts."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class PatientMemory(Base):
    __tablename__ = "patient_memory"
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    event_type = Column(String, nullable=False)
    details = Column(Text, nullable=False)  # JSON string

class AlertMemory(Base):
    __tablename__ = "alert_memory"
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    alert_level = Column(String, nullable=False)
    reason = Column(Text, nullable=False)

class DecisionMemory(Base):
    __tablename__ = "decision_memory"
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String, index=True, nullable=False)
    agent_name = Column(String, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    action = Column(String, nullable=False)
    reasoning = Column(Text, nullable=False)
    confidence = Column(String, nullable=True)

class OutcomeMemory(Base):
    __tablename__ = "outcome_memory"
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String, index=True, nullable=False)
    decision_id = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    result = Column(String, nullable=False)
    feedback = Column(Text, nullable=True)


class AgentMemoryStore:
    """Thread-safe persistent agent memory using SQLite."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{self.db_path}", connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def record_decision(self, patient_id: str, agent_name: str, action: str, reasoning: str, confidence: float = 0.0) -> None:
        with self.SessionLocal() as session:
            decision = DecisionMemory(
                patient_id=patient_id,
                agent_name=agent_name,
                action=action,
                reasoning=reasoning,
                confidence=str(confidence)
            )
            session.add(decision)
            session.commit()

    def record_alert(self, patient_id: str, alert_level: str, reason: str) -> None:
        with self.SessionLocal() as session:
            alert = AlertMemory(
                patient_id=patient_id,
                alert_level=alert_level,
                reason=reason
            )
            session.add(alert)
            session.commit()

    def record_patient_event(self, patient_id: str, event_type: str, details: Dict[str, Any]) -> None:
        with self.SessionLocal() as session:
            mem = PatientMemory(
                patient_id=patient_id,
                event_type=event_type,
                details=json.dumps(details)
            )
            session.add(mem)
            session.commit()

    def record_outcome(self, patient_id: str, result: str, feedback: str = "", decision_id: int = None) -> None:
        with self.SessionLocal() as session:
            outcome = OutcomeMemory(
                patient_id=patient_id,
                result=result,
                feedback=feedback,
                decision_id=decision_id
            )
            session.add(outcome)
            session.commit()

    def get_patient_timeline(self, patient_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch unified timeline of decisions and alerts for a patient."""
        with self.SessionLocal() as session:
            decisions = session.query(DecisionMemory).filter(DecisionMemory.patient_id == patient_id).all()
            alerts = session.query(AlertMemory).filter(AlertMemory.patient_id == patient_id).all()
            
            timeline = []
            for d in decisions:
                timeline.append({
                    "type": "agent_decision",
                    "agent": d.agent_name,
                    "action": d.action,
                    "reasoning": d.reasoning,
                    "confidence": float(str(d.confidence).replace('%', '').strip()) if d.confidence else 0.0,
                    "timestamp": d.timestamp.isoformat()
                })
            for a in alerts:
                timeline.append({
                    "type": "alert",
                    "alert_level": a.alert_level,
                    "reason": a.reason,
                    "timestamp": a.timestamp.isoformat()
                })
            
            # Sort descending by timestamp
            timeline.sort(key=lambda x: x["timestamp"], reverse=True)
            return timeline[:limit]
