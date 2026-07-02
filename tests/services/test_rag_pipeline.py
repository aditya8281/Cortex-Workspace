"""Tests for RAGPipeline."""

import pytest
from sqlalchemy.orm import Session

from backend.app.services.intelligence.rag_pipeline import RAGPipeline


@pytest.fixture()
def mock_retrieval():
    class Mock:
        def retrieve(self, query, repo_id=None, limit=10, sources=None, **kwargs):
            from backend.app.services.intelligence.hybrid_retrieval import RetrievalResult

            return [
                RetrievalResult(
                    content="def calculate_sum(a, b): return a + b",
                    source="vector",
                    score=0.9,
                    file_path="math.py",
                    language="python",
                ),
                RetrievalResult(
                    content="# Math Operations\n\nBasic arithmetic functions.",
                    source="fulltext",
                    score=0.7,
                    file_path="docs/math.md",
                ),
            ]

    return Mock()


@pytest.fixture()
def mock_conv_service():
    class Mock:
        def get_context_messages(self, conversation_id, max_tokens=32000):
            from backend.app.models.interaction.conversation import ConversationMessage

            return [
                ConversationMessage(id=1, conversation_id=1, role="user", content="Hello", tokens=1),
                ConversationMessage(id=2, conversation_id=1, role="assistant", content="Hi there!", tokens=2),
            ]

        def get_messages(self, conversation_id, limit=50):
            from backend.app.models.interaction.conversation import ConversationMessage

            return [
                ConversationMessage(
                    id=1, conversation_id=1, role="user", content="How do I add numbers in Python?", tokens=3
                ),
                ConversationMessage(
                    id=2,
                    conversation_id=1,
                    role="assistant",
                    content="Use the calculate_sum function from math.py which takes two arguments and returns their sum using the + operator.",
                    tokens=5,
                ),
                ConversationMessage(id=3, conversation_id=1, role="user", content="Thanks!", tokens=1),
                ConversationMessage(id=4, conversation_id=1, role="assistant", content="You're welcome!", tokens=2),
            ]

    return Mock()


@pytest.fixture()
def rag(db_session: Session, mock_retrieval, mock_conv_service):
    return RAGPipeline(db_session, retrieval=mock_retrieval, conversation_service=mock_conv_service)


def test_retrieve_context(rag: RAGPipeline):
    ctx = rag.retrieve_context("how to add numbers")
    assert ctx.source_count >= 1
    assert ctx.total_tokens > 0
    assert "[1]" in ctx.formatted_context


def test_retrieve_context_empty():
    class EmptyRetrieval:
        def retrieve(self, **kw):
            return []

    pipeline = RAGPipeline.__new__(RAGPipeline)
    pipeline._retrieval = EmptyRetrieval()
    ctx = pipeline.retrieve_context("nonexistent")
    assert ctx.source_count == 0
    assert ctx.formatted_context == ""


def test_build_messages(rag: RAGPipeline):
    messages = rag.build_messages(1, "how to add numbers")
    assert messages[0]["role"] == "system"
    assert "calculate_sum" in messages[0]["content"]
    assert messages[-1]["role"] == "user"
    assert messages[-1]["content"] == "how to add numbers"


def test_build_messages_includes_history(rag: RAGPipeline):
    messages = rag.build_messages(1, "hello")
    roles = [m["role"] for m in messages]
    assert "user" in roles
    assert "assistant" in roles


def test_consolidate(rag: RAGPipeline):
    facts = rag.consolidate(1)
    assert len(facts) >= 1
    assert "Q:" in facts[0]
    assert "A:" in facts[0]


def test_consolidate_too_few_messages(rag: RAGPipeline):
    class ShortConv:
        def get_messages(self, cid, limit=50):
            from backend.app.models.interaction.conversation import ConversationMessage

            return [ConversationMessage(id=1, conversation_id=1, role="user", content="hi", tokens=1)]

    rag._conv_service = ShortConv()  # type: ignore[assignment]
    facts = rag.consolidate(1)
    assert len(facts) == 0


def test_context_token_limit():
    from backend.app.services.intelligence.hybrid_retrieval import RetrievalResult

    class ManyResults:
        def retrieve(self, **kw):
            return [
                RetrievalResult(content="x " * 500, source="vector", score=0.9, file_path=f"f{i}.py") for i in range(20)
            ]

    pipeline = RAGPipeline.__new__(RAGPipeline)
    pipeline._retrieval = ManyResults()
    ctx = pipeline.retrieve_context("test", max_tokens=500)
    assert ctx.total_tokens <= 600
