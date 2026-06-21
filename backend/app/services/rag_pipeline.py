"""RAG Conversation Pipeline — retrieves context before LLM calls."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from backend.app.services.conversation_service import ConversationService, estimate_tokens
from backend.app.services.hybrid_retrieval import HybridRetrievalV2, RetrievalResult

logger = logging.getLogger(__name__)

MAX_CONTEXT_TOKENS = 4000
MAX_CONTEXT_RESULTS = 8


@dataclass
class RAGContext:
    results: list[RetrievalResult]
    formatted_context: str
    total_tokens: int
    source_count: int


class RAGPipeline:
    """Retrieves relevant knowledge and injects it into conversation context."""

    def __init__(
        self,
        db: Session,
        retrieval: HybridRetrievalV2 | None = None,
        conversation_service: ConversationService | None = None,
    ):
        self._db = db
        self._retrieval = retrieval or HybridRetrievalV2(db)
        self._conv_service = conversation_service or ConversationService(db)

    def retrieve_context(
        self,
        query: str,
        repo_id: int | None = None,
        max_tokens: int = MAX_CONTEXT_TOKENS,
        max_results: int = MAX_CONTEXT_RESULTS,
    ) -> RAGContext:
        results = self._retrieval.retrieve(
            query=query,
            repo_id=repo_id,
            limit=max_results,
            sources=["vector", "fulltext"],
        )

        formatted_parts = []
        total_tokens = 0
        source_count = 0

        for i, result in enumerate(results):
            ref = f"[{i + 1}] {result.file_path or 'knowledge'}"
            if result.language:
                ref += f" ({result.language})"
            ref += f"\n{result.content[:500]}"

            ref_tokens = estimate_tokens(ref)
            if total_tokens + ref_tokens > max_tokens:
                break

            formatted_parts.append(ref)
            total_tokens += ref_tokens
            source_count += 1

        formatted_context = "\n\n---\n\n".join(formatted_parts) if formatted_parts else ""

        return RAGContext(
            results=results[:source_count],
            formatted_context=formatted_context,
            total_tokens=total_tokens,
            source_count=source_count,
        )

    def build_messages(
        self,
        conversation_id: int,
        user_message: str,
        repo_id: int | None = None,
        max_history_tokens: int = 28000,
    ) -> list[dict]:
        context = self.retrieve_context(user_message, repo_id)

        history = self._conv_service.get_context_messages(
            conversation_id, max_tokens=max_history_tokens
        )

        messages = []

        system_parts = ["You are Cortex, a helpful AI assistant with access to the user's codebase and knowledge."]
        if context.formatted_context:
            system_parts.append(
                f"Relevant context from the codebase:\n\n{context.formatted_context}"
            )
            system_parts.append(
                "\nUse this context to answer the user's question. "
                "Cite sources using [1], [2], etc. when referencing specific files."
            )

        messages.append({"role": "system", "content": "\n\n".join(system_parts)})

        for msg in history:
            messages.append({"role": msg.role, "content": msg.content})

        messages.append({"role": "user", "content": user_message})

        return messages

    def consolidate(
        self,
        conversation_id: int,
        user_id: int | None = None,
    ) -> list[str]:
        messages = self._conv_service.get_messages(conversation_id, limit=20)
        if len(messages) < 4:
            return []

        facts = []
        for i in range(0, len(messages) - 1, 2):
            if messages[i].role == "user" and messages[i + 1].role == "assistant":
                user_content = messages[i].content
                assistant_content = messages[i + 1].content

                if len(user_content) > 20 and len(assistant_content) > 50:
                    fact = f"Q: {user_content[:200]}\nA: {assistant_content[:300]}"
                    facts.append(fact)

        return facts[:5]


_rag_pipeline: RAGPipeline | None = None


def get_rag_pipeline(db: Session) -> RAGPipeline:
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline(db)
    return _rag_pipeline
