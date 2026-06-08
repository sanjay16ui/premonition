"""AI audit logging and memory tests."""

from __future__ import annotations

from premonition.copilot.audit.ai_audit import AIAuditLogger
from premonition.copilot.memory.conversation import AIConversationMemory


class TestAIAuditLogger:
    def test_log_record(self, tmp_path):
        logger = AIAuditLogger(tmp_path)
        record = logger.log("admin@test", "chat", "chat@1.0.0", "mock-local", "query", "response text",
                            citations=[{"source_id": "s1"}], retrieval_trace=["retrieved:s1:0.9"])
        assert record.id
        assert record.actor == "admin@test"

    def test_query_by_action(self, tmp_path):
        logger = AIAuditLogger(tmp_path)
        logger.log("u1", "chat", "v1", "mock", "q", "r")
        logger.log("u1", "explain_prediction", "v1", "mock", "q", "r")
        chats = logger.query(action="chat")
        assert len(chats) == 1

    def test_writes_jsonl(self, tmp_path):
        logger = AIAuditLogger(tmp_path)
        logger.log("u1", "chat", "v1", "mock", "q", "r")
        files = list((tmp_path / "copilot" / "audit").glob("*.jsonl"))
        assert len(files) >= 1


class TestConversationMemory:
    def test_create_conversation(self, tmp_path):
        mem = AIConversationMemory(tmp_path)
        conv = mem.create("Test Chat", "user1")
        assert conv.id
        assert conv.title == "Test Chat"

    def test_add_messages(self, tmp_path):
        mem = AIConversationMemory(tmp_path)
        conv = mem.create()
        mem.add_message(conv.id, "user", "Hello")
        mem.add_message(conv.id, "assistant", "Hi there")
        updated = mem.get(conv.id)
        assert len(updated.messages) == 2

    def test_list_conversations(self, tmp_path):
        mem = AIConversationMemory(tmp_path)
        mem.create(user_id="u1")
        mem.create(user_id="u2")
        assert len(mem.list_conversations("u1")) == 1

    def test_context_string(self, tmp_path):
        mem = AIConversationMemory(tmp_path)
        conv = mem.create()
        mem.add_message(conv.id, "user", "What is sepsis?")
        ctx = mem.get_context_string(conv.id)
        assert "sepsis" in ctx

    def test_persistence(self, tmp_path):
        mem = AIConversationMemory(tmp_path)
        conv = mem.create()
        mem.add_message(conv.id, "user", "persist test")
        mem2 = AIConversationMemory(tmp_path)
        loaded = mem2.get(conv.id)
        assert loaded is not None
        assert len(loaded.messages) == 1
