import re
import logging
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)

class TaskClassifier:
    """
    Lightweight, fast rule-based classifier that categorizes developer prompts
    into distinct tasks to enable intelligent model routing.
    """

    CATEGORIES = {
        "chat": "Chat",
        "search": "Search",
        "coding": "Coding",
        "repository_analysis": "Repository Analysis",
        "architecture_review": "Architecture Review",
        "planning": "Planning",
        "research": "Research",
        "debugging": "Debugging",
        "multi_file_modification": "Multi-file Modification",
        "long_context": "Long Context"
    }

    # Regex definitions for keyword matching
    CODE_KEYWORDS = re.compile(
        r"\b(def|class|function|export|import|struct|impl|fn|interface|const|let|var|code|snippet|implementation|syntax|programming|script|write\s+a\s+function|write\s+code)\b|"
        r"\.(py|js|ts|tsx|rs|go|c|cpp|h|java|sh|html|css|json|yml|yaml|toml)\b",
        re.IGNORECASE
    )

    DEBUGGING_KEYWORDS = re.compile(
        r"\b(traceback|exception|error|failed|exit\s+code|stack\s+trace|bug|crash|fix\s+the\s+bug|fix\s+this\s+error|why\s+is\s+this\s+failing|assertionerror|keyerror|typeerror|valueerror|runtimeerror)\b",
        re.IGNORECASE
    )

    REPOSITORY_ANALYSIS_KEYWORDS = re.compile(
        r"\b(repository|codebase|project\s+structures?|scan\s+project|index\s+folder|analyze\s+codebase|scan\s+codebase|find\s+all\s+occurrences|dependencies)\b",
        re.IGNORECASE
    )

    ARCHITECTURE_REVIEW_KEYWORDS = re.compile(
        r"\b(architecture|design\s+patterns?|system\s+design|uml|diagrams?|folder\s+layouts?|project\s+architectures?|coupling|cohesion|architectural)\b",
        re.IGNORECASE
    )

    PLANNING_KEYWORDS = re.compile(
        r"\b(plan|planning|implementation\s+plans?|roadmaps?|step-by-step|milestones?|todo\s+lists?|actions\s+list)\b",
        re.IGNORECASE
    )

    SEARCH_KEYWORDS = re.compile(
        r"\b(find\s+files?|search\s+files?|look\s+up|locate\s+files?|grep|ripgrep|search\s+for|find\s+in\s+workspace)\b",
        re.IGNORECASE
    )

    RESEARCH_KEYWORDS = re.compile(
        r"\b(explain\s+how|research|what\s+is\s+the\s+difference|tell\s+me\s+about|concept\s+of|history\s+of|explain\s+concept|documentation|reference)\b",
        re.IGNORECASE
    )

    MULTI_FILE_KEYWORDS = re.compile(
        r"\b(modify\s+multiple|edit\s+multiple|change\s+files|apply\s+changes\s+to|across\s+files|refactor\s+project|rename\s+across|multi-file)\b",
        re.IGNORECASE
    )

    @classmethod
    def classify(cls, query: str, history: List[Dict[str, str]] = None) -> Tuple[str, str]:
        """
        Classifies the incoming developer query.
        Returns a tuple of (category_key, reason_string).
        """
        # 1. Long Context Check (History + Query length)
        history_length = sum(len(turn.get("content", "")) for turn in (history or []))
        total_len = len(query) + history_length
        num_turns = len(history or [])

        if total_len > 12000 or num_turns > 12:
            return "long_context", f"Context payload size ({total_len} chars, {num_turns} turns) requires long context support"

        query_lower = query.lower()

        # 2. Multi-file Modification check
        if cls.MULTI_FILE_KEYWORDS.search(query_lower):
            return "multi_file_modification", "Matches intent to edit or change multiple files in parallel"

        # 3. Debugging check
        if cls.DEBUGGING_KEYWORDS.search(query_lower):
            return "debugging", "Detected traceback, error patterns, or bug-fixing request"

        # 4. Coding check
        if cls.CODE_KEYWORDS.search(query_lower):
            return "coding", "Detected code symbols, language extensions, or function creation prompt"

        # 5. Repository Analysis check
        if cls.REPOSITORY_ANALYSIS_KEYWORDS.search(query_lower):
            return "repository_analysis", "Query requests scanning, indexing, or full repository profiling"

        # 6. Architecture Review check
        if cls.ARCHITECTURE_REVIEW_KEYWORDS.search(query_lower):
            return "architecture_review", "Prompt inquires about folder structure, architecture design, or project layout"

        # 7. Planning check
        if cls.PLANNING_KEYWORDS.search(query_lower):
            return "planning", "Identified planning intent or requests for step-by-step roadmap"

        # 8. Search check
        if cls.SEARCH_KEYWORDS.search(query_lower):
            return "search", "Matches file finding or searching patterns in workspace"

        # 9. Research check
        if cls.RESEARCH_KEYWORDS.search(query_lower):
            return "research", "Detected informational queries, concept explanation, or research requests"

        # 10. Fallback to Chat
        return "chat", "Heuristics classify prompt as standard conversational chat"
