import sqlite3
import json
import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class StorageAdapter:
    def get(self, collection: str, key: str) -> Optional[dict]:
        raise NotImplementedError
    
    def set(self, collection: str, key: str, value: dict):
        raise NotImplementedError
        
    def list(self, collection: str) -> List[dict]:
        raise NotImplementedError

class HybridMemoryStore(StorageAdapter):
    """Hybrid fast-access and persistent storage abstraction."""
    def __init__(self, db_path: str = "premonition_memory.sqlite"):
        self.redis_mock: Dict[str, Dict[str, dict]] = {}
        self.db_path = db_path
        self._init_sqlite()

    def _init_sqlite(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    '''CREATE TABLE IF NOT EXISTS memory (
                        collection TEXT,
                        key TEXT,
                        data TEXT,
                        updated_at TIMESTAMP,
                        PRIMARY KEY (collection, key)
                    )'''
                )
        except Exception as e:
            logger.error(f"Failed to initialize SQLite memory: {e}")

    def get(self, collection: str, key: str) -> Optional[dict]:
        # Fast access
        if collection in self.redis_mock and key in self.redis_mock[collection]:
            return self.redis_mock[collection][key]
        
        # Fallback to persistent
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute("SELECT data FROM memory WHERE collection=? AND key=?", (collection, key))
                row = cur.fetchone()
                if row:
                    data = json.loads(row[0])
                    if collection not in self.redis_mock:
                        self.redis_mock[collection] = {}
                    self.redis_mock[collection][key] = data
                    return data
        except Exception as e:
            logger.error(f"SQLite get error: {e}")
            
        return None

    def set(self, collection: str, key: str, value: dict):
        if collection not in self.redis_mock:
            self.redis_mock[collection] = {}
        self.redis_mock[collection][key] = value
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO memory (collection, key, data, updated_at) VALUES (?, ?, ?, ?)",
                    (collection, key, json.dumps(value), datetime.utcnow().isoformat())
                )
        except Exception as e:
            logger.error(f"SQLite set error: {e}")

    def list(self, collection: str) -> List[dict]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute("SELECT data FROM memory WHERE collection=?", (collection,))
                return [json.loads(row[0]) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"SQLite list error: {e}")
            return []

class AgentMemory:
    """Manages long-term storage of agentic observations and actions."""
    def __init__(self):
        self.store = HybridMemoryStore()

    def record_patient_state(self, patient_id: str, state: dict):
        self.store.set("patient_memory", patient_id, state)
        
    def record_alert(self, alert_id: str, alert_data: dict):
        self.store.set("alert_memory", alert_id, alert_data)
        
    def record_decision(self, agent_name: str, patient_id: str, decision: dict):
        decision_id = str(uuid.uuid4())
        self.store.set("decision_memory", decision_id, {
            "agent": agent_name,
            "patient_id": patient_id,
            "decision": decision,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    def record_outcome(self, patient_id: str, outcome_data: dict):
        outcome_id = str(uuid.uuid4())
        self.store.set("outcome_memory", outcome_id, {
            "patient_id": patient_id,
            "outcome": outcome_data,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    def record_conversation(self, thread_id: str, conversation_data: dict):
        self.store.set("conversation_memory", thread_id, conversation_data)

# Global memory instance
memory_system = AgentMemory()
