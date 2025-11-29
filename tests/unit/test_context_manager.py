"""Unit tests for ContextManager."""

import pytest

from edgar.services.context_manager import ContextManager


class TestContextManager:
    """Test suite for ContextManager."""

    @pytest.fixture
    def context(self) -> ContextManager:
        """Create ContextManager instance."""
        return ContextManager(max_messages=5)

    def test_initialization(self, context: ContextManager) -> None:
        """Test context manager initializes correctly."""
        assert context.max_messages == 5
        assert len(context.messages) == 0

    def test_add_user_message(self, context: ContextManager) -> None:
        """Test adding user message."""
        context.add_user_message("Hello")
        assert len(context.messages) == 1
        assert context.messages[0]["role"] == "user"
        assert context.messages[0]["content"] == "Hello"

    def test_add_assistant_message(self, context: ContextManager) -> None:
        """Test adding assistant message."""
        context.add_assistant_message("Hi there")
        assert len(context.messages) == 1
        assert context.messages[0]["role"] == "assistant"
        assert context.messages[0]["content"] == "Hi there"

    def test_add_system_message(self, context: ContextManager) -> None:
        """Test adding system message."""
        context.add_system_message("System prompt")
        assert len(context.messages) == 1
        assert context.messages[0]["role"] == "system"
        assert context.messages[0]["content"] == "System prompt"

    def test_get_messages(self, context: ContextManager) -> None:
        """Test getting messages returns copy."""
        context.add_user_message("Test")
        messages = context.get_messages()
        messages.append({"role": "user", "content": "Modified"})
        assert len(context.messages) == 1  # Original unchanged

    def test_clear_messages(self, context: ContextManager) -> None:
        """Test clearing all messages."""
        context.add_user_message("Test 1")
        context.add_user_message("Test 2")
        context.clear()
        assert len(context.messages) == 0

    def test_trim_context_by_count(self, context: ContextManager) -> None:
        """Test context trimming by message count."""
        # Add more messages than max_messages
        for i in range(10):
            context.add_user_message(f"Message {i}")

        # Should keep only max_messages (5)
        assert len(context.messages) <= context.max_messages

    def test_system_messages_preserved(self, context: ContextManager) -> None:
        """Test system messages are preserved during trimming."""
        context.add_system_message("Important system message")

        # Add many user messages to trigger trimming
        for i in range(10):
            context.add_user_message(f"Message {i}")

        # System message should still be present
        system_messages = [m for m in context.messages if m["role"] == "system"]
        assert len(system_messages) == 1
        assert system_messages[0]["content"] == "Important system message"
