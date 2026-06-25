"""Intent classifier — routes messages to the right agent path.

Classification is keyword-based + heuristic to avoid LLM latency.
Casual messages get a fast-path response. Admin/agent/continuation
messages flow to the streaming loop.
"""

from __future__ import annotations

import re
from typing import Literal

Intent = Literal["casual", "admin", "agent", "continuation"]

# Patterns that indicate a casual (non-task) message
_CASUAL_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^(hi|hello|hey|hey there|good morning|good evening|good afternoon)\b", re.IGNORECASE),
    re.compile(r"^(thanks|thank you|thx|ty|appreciate it)\b", re.IGNORECASE),
    re.compile(r"^(ok|okay|k|sure|alright|got it|i see)\b", re.IGNORECASE),
    re.compile(r"^(bye|goodbye|see you|cya|later)\b", re.IGNORECASE),
    re.compile(r"^(how are you|what's up|sup|how's it going)\b", re.IGNORECASE),
    re.compile(r"^(nice|great|awesome|cool|perfect)\s*$", re.IGNORECASE),
    re.compile(r"^(lol|haha|lmfao|rofl)\b", re.IGNORECASE),
]

# Patterns that indicate an admin / system command
_ADMIN_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^\s*/\w+", re.IGNORECASE),  # Starts with /
    re.compile(r"^(status|health|ping|version)\b", re.IGNORECASE),
    re.compile(r"^(reload|restart|shutdown|stop)\b", re.IGNORECASE),
    re.compile(r"(show|list|get)\s+(logs|metrics|config)", re.IGNORECASE),
]

# Minimum message length for "agent" classification (shorter messages
# that aren't casual/admin are treated as agent, since they're likely
# commands like "summarize this" or "what is X")
_AGENT_MIN_LENGTH = 3


def classify_intent(message: str) -> Intent:
    """Classify a user message into one of four intent categories.

    Classification order:
    1. Casual — greetings, thanks, acknowledgments
    2. Admin — system commands, status checks, configuration
    3. Continuation — follow-up to previous task (has "continue" or references prior context)
    4. Agent — full task execution (default for substantive messages)
    """
    stripped = message.strip()
    if not stripped:
        return "agent"

    # Check patterns in priority order
    for pattern in _CASUAL_PATTERNS:
        if pattern.match(stripped):
            return "casual"

    for pattern in _ADMIN_PATTERNS:
        if pattern.match(stripped):
            return "admin"

    # Continuation: messages that reference prior work
    if re.search(r"\b(continue|keep going|go on|next|more|again)\b", stripped, re.IGNORECASE):
        return "continuation"

    # Short substantive messages are still agent tasks
    if len(stripped) >= _AGENT_MIN_LENGTH:
        return "agent"

    # Fallback
    return "agent"


def casual_response(message: str) -> str:
    """Return a fast-path response for casual messages.

    No LLM call needed — pre-defined responses by pattern category.
    """
    stripped = message.strip().lower()

    if re.match(r"^(hi|hello|hey|hey there)", stripped):
        return "Hello! How can I help you today?"

    if re.match(r"^(good morning|good evening|good afternoon)", stripped):
        return "Good day! What can I do for you?"

    if re.match(r"^(thanks|thank you|thx|ty)", stripped):
        return "You're welcome! Let me know if you need anything else."

    if re.match(r"^(ok|okay|k|sure|alright|got it|i see)", stripped):
        return "Got it. Anything else I can help with?"

    if re.match(r"^(bye|goodbye|see you)", stripped):
        return "Goodbye! Feel free to come back anytime."

    if re.match(r"^(how are you|what's up|sup|how's it going)", stripped):
        return "I'm doing well, thanks for asking! Ready to help."

    if re.match(r"^(nice|great|awesome|cool|perfect)\s*$", stripped):
        return "Great to hear! What would you like to do next?"

    if re.match(r"^(lol|haha)", stripped):
        return "😊"

    return "I understand. What would you like me to do?"
