"""Conversation context manager for multi-turn AI interactions.

This module manages conversation history to enable iterative refinement
of generated code through multiple AI interactions.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ContextManager:
    """Manages conversation context for multi-turn interactions.

    Maintains conversation history with automatic trimming to stay within
    context window limits.

    Attributes:
        max_messages: Maximum number of messages to retain
        max_tokens: Maximum total tokens in context (approximate)
        messages: Current conversation history
    """

    max_messages: int = 20
    max_tokens: int = 200000
    messages: list[dict[str, str]] = field(default_factory=list)

    def add_user_message(self, content: str) -> None:
        """Add user message to conversation history.

        Args:
            content: User message content
        """
        self.messages.append({"role": "user", "content": content})
        self._trim_context()

    def add_assistant_message(self, content: str) -> None:
        """Add assistant message to conversation history.

        Args:
            content: Assistant message content
        """
        self.messages.append({"role": "assistant", "content": content})
        self._trim_context()

    def add_system_message(self, content: str) -> None:
        """Add system message to conversation history.

        System messages are typically used for prompts and instructions.

        Args:
            content: System message content
        """
        self.messages.append({"role": "system", "content": content})
        self._trim_context()

    def get_messages(self) -> list[dict[str, str]]:
        """Get current conversation history.

        Returns:
            List of message dictionaries with 'role' and 'content'
        """
        return self.messages.copy()

    def clear(self) -> None:
        """Clear all conversation history."""
        self.messages.clear()

    def _trim_context(self) -> None:
        """Trim conversation history to stay within limits.

        Removes oldest messages (except system messages) if context exceeds
        max_messages or max_tokens limits.
        """
        # Keep system messages, trim oldest user/assistant messages
        if len(self.messages) > self.max_messages:
            # Separate system messages from conversation
            system_messages = [m for m in self.messages if m["role"] == "system"]
            conversation = [m for m in self.messages if m["role"] != "system"]

            # Keep only recent conversation
            trimmed_conversation = conversation[-(self.max_messages - len(system_messages)):]

            # Rebuild messages list
            self.messages = system_messages + trimmed_conversation

    def _estimate_tokens(self) -> int:
        """Estimate total tokens in conversation history.

        Uses rough approximation: 1 token ≈ 4 characters.

        Returns:
            Estimated token count
        """
        total_chars = sum(len(m["content"]) for m in self.messages)
        return total_chars // 4
