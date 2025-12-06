#!/usr/bin/env python3
"""
Test the query() method for one-shot testing without terminal UI loop.

Verifies that:
1. query() method works for single queries
2. Session state persists across multiple queries
3. Silent mode suppresses output
4. No terminal loop is entered (non-blocking execution)
"""

import asyncio
import io
import os
import sys
from typing import Dict, List

import pytest

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from cli_chatbot import ChatbotController


class MockLLMClient:
    """Mock LLM client for testing."""

    def __init__(self):
        self.call_count = 0
        self.messages_history = []

    async def __call__(self, messages: List[Dict[str, str]]) -> str:
        """Mock LLM response based on message content."""
        self.call_count += 1
        self.messages_history.append(messages)

        # Extract the last user message
        user_messages = [msg for msg in messages if msg.get("role") == "user"]
        if not user_messages:
            return "Mock response: No user message found"

        last_message = user_messages[-1]["content"]

        # Return different responses based on query content
        if "apple" in last_message.lower() and "cik" in last_message.lower():
            return "Apple Inc. has CIK: 0000320193. This is the unique identifier used by the SEC EDGAR system to track Apple's filings."

        if "extract" in last_message.lower() and "2023" in last_message.lower():
            # This should reference the previous context about Apple
            if any("apple" in str(msg).lower() for msg in self.messages_history):
                return "Based on our previous discussion about Apple (CIK: 0000320193), I will extract their 2023 executive compensation data from SEC EDGAR filings."
            return "I need to know which company you want data for. Please provide a company name or CIK."

        if "test query" in last_message.lower():
            return "This is a test response for testing purposes."

        if "count" in last_message.lower() and "files" in last_message.lower():
            return (
                "I can analyze the project files. Let me check the codebase structure."
            )

        return f"Mock response for: {last_message[:50]}..."


@pytest.mark.asyncio
async def test_one_shot_query():
    """Test single query without loop (basic functionality)."""
    print("\n🧪 Test: One-shot query basic functionality")

    llm_client = MockLLMClient()
    controller = ChatbotController(
        llm_client=llm_client,
        application_root=os.path.dirname(__file__),
        scripting_enabled=False,  # Disable scripting for faster tests
    )

    # Execute one-shot query
    response = await controller.query("What is Apple's CIK?", silent=True)

    # Assertions
    assert response is not None, "Response should not be None"
    assert isinstance(response, str), "Response should be a string"
    assert len(response) > 0, "Response should not be empty"
    assert "0000320193" in response, "Response should contain Apple's CIK"
    assert llm_client.call_count == 1, "LLM should be called exactly once"

    print("✅ One-shot query works correctly")
    print(f"   Response preview: {response[:100]}...")


@pytest.mark.asyncio
async def test_session_continuation():
    """Test that session state persists across queries."""
    print("\n🧪 Test: Session continuation across queries")

    llm_client = MockLLMClient()
    controller = ChatbotController(
        llm_client=llm_client,
        application_root=os.path.dirname(__file__),
        scripting_enabled=False,
    )

    # First query - establish context
    response1 = await controller.query("What is Apple's CIK?", silent=True)
    assert response1 is not None
    assert "0000320193" in response1
    print(f"✅ First query successful: {response1[:80]}...")

    # Second query - should use context from first
    response2 = await controller.query(
        "Extract 2023 data for that company", silent=True
    )
    assert response2 is not None
    print(f"✅ Second query successful: {response2[:80]}...")

    # Verify session continuation
    # The second query should reference Apple without being told again
    assert (
        "apple" in response2.lower() or "0000320193" in response2
    ), "Second query should reference Apple from previous context"

    # Verify memory was updated
    memory_history = await controller.memory.get_conversation_history()
    assert len(memory_history) == 2, "Memory should contain both exchanges"
    assert memory_history[0]["user_input"] == "What is Apple's CIK?"
    assert memory_history[1]["user_input"] == "Extract 2023 data for that company"

    print("✅ Session continuation verified")
    print(f"   Memory contains {len(memory_history)} exchanges")


@pytest.mark.asyncio
async def test_silent_mode():
    """Test silent parameter suppresses output."""
    print("\n🧪 Test: Silent mode suppresses output")

    llm_client = MockLLMClient()
    controller = ChatbotController(
        llm_client=llm_client,
        application_root=os.path.dirname(__file__),
        scripting_enabled=False,
    )

    # Capture stdout
    captured = io.StringIO()
    original_stdout = sys.stdout

    try:
        sys.stdout = captured

        # Query with silent=True
        response = await controller.query("Test query", silent=True)

        sys.stdout = original_stdout
        output = captured.getvalue()

        # Assertions
        assert response is not None, "Response should still be returned in silent mode"
        assert "🤖 Controller:" not in output, "Silent mode should not print response"
        # Note: Logging may still output to stdout - we're primarily testing that
        # the controller response itself is not printed

        print("✅ Silent mode verified - controller response not printed")

        # Now test with silent=False
        captured = io.StringIO()
        sys.stdout = captured

        response2 = await controller.query("Test query 2", silent=False)

        sys.stdout = original_stdout
        output2 = captured.getvalue()

        assert response2 is not None
        assert "🤖 Controller:" in output2, "Non-silent mode should print response"

        print("✅ Non-silent mode verified - output produced")

    finally:
        sys.stdout = original_stdout


@pytest.mark.asyncio
async def test_no_loop_entered():
    """Verify query() doesn't enter interactive loop."""
    print("\n🧪 Test: No terminal loop entered")

    llm_client = MockLLMClient()
    controller = ChatbotController(
        llm_client=llm_client,
        application_root=os.path.dirname(__file__),
        scripting_enabled=False,
    )

    # This should return immediately, not block waiting for input
    start_time = asyncio.get_event_loop().time()

    try:
        response = await asyncio.wait_for(
            controller.query("Test query", silent=True),
            timeout=10.0,  # 10 second timeout
        )
        end_time = asyncio.get_event_loop().time()

        # Assertions
        assert response is not None, "Query should return a response"
        execution_time = end_time - start_time
        assert execution_time < 10.0, "Query should complete before timeout"

        print(f"✅ No terminal loop - completed in {execution_time:.2f} seconds")
        print("   (Fast execution indicates no blocking input)")

    except asyncio.TimeoutError:
        pytest.fail("query() timed out - likely entered blocking terminal loop")


@pytest.mark.asyncio
async def test_multiple_sequential_queries():
    """Test multiple queries in sequence to verify stability."""
    print("\n🧪 Test: Multiple sequential queries")

    llm_client = MockLLMClient()
    controller = ChatbotController(
        llm_client=llm_client,
        application_root=os.path.dirname(__file__),
        scripting_enabled=False,
    )

    queries = [
        "What is Apple's CIK?",
        "Count the Python files",
        "What are the main components?",
        "Show me the project structure",
    ]

    responses = []
    for i, query in enumerate(queries, 1):
        response = await controller.query(query, silent=True)
        assert response is not None, f"Query {i} should return a response"
        assert len(response) > 0, f"Query {i} should return non-empty response"
        responses.append(response)
        print(f"✅ Query {i}/{len(queries)} completed")

    # Verify all queries were processed
    assert len(responses) == len(queries), "All queries should be processed"
    assert llm_client.call_count == len(queries), "LLM should be called for each query"

    # Verify memory contains all exchanges
    memory_history = await controller.memory.get_conversation_history()
    assert len(memory_history) == len(queries), "Memory should contain all exchanges"

    print(f"✅ All {len(queries)} queries completed successfully")
    print(f"   Total LLM calls: {llm_client.call_count}")


@pytest.mark.asyncio
async def test_self_awareness_initialization():
    """Test that self-awareness is properly initialized."""
    print("\n🧪 Test: Self-awareness initialization")

    llm_client = MockLLMClient()
    controller = ChatbotController(
        llm_client=llm_client,
        application_root=os.path.dirname(__file__),
        scripting_enabled=False,
    )

    # Self-awareness should be None initially
    assert (
        controller._self_awareness is None
    ), "Self-awareness should be None before first query"

    # Execute query - should initialize self-awareness
    response = await controller.query("Test query", silent=True)
    assert response is not None

    # Self-awareness should now be initialized
    assert (
        controller._self_awareness is not None
    ), "Self-awareness should be initialized after query"

    # Self-awareness is a ContextInfo object, not a string
    # Check that it has the expected attributes
    assert hasattr(
        controller._self_awareness, "content"
    ), "Self-awareness should have content attribute"
    assert hasattr(
        controller._self_awareness, "source"
    ), "Self-awareness should have source attribute"

    # Verify it contains actual self-awareness content
    awareness_content = str(controller._self_awareness.content)
    assert len(awareness_content) > 0, "Self-awareness content should not be empty"
    assert (
        "controller" in awareness_content.lower()
    ), "Self-awareness should reference controller"

    print("✅ Self-awareness properly initialized")
    print(f"   Self-awareness content length: {len(awareness_content)} characters")
    print(f"   Self-awareness source: {controller._self_awareness.source}")


@pytest.mark.asyncio
async def test_query_return_value():
    """Test that query() returns the correct response string."""
    print("\n🧪 Test: Query return value correctness")

    llm_client = MockLLMClient()
    controller = ChatbotController(
        llm_client=llm_client,
        application_root=os.path.dirname(__file__),
        scripting_enabled=False,
    )

    # Execute query
    response = await controller.query("What is Apple's CIK?", silent=True)

    # Verify return value
    assert isinstance(response, str), "Return value should be a string"
    assert len(response) > 0, "Return value should not be empty"

    # The response should be the formatted LLM response
    # It should contain the actual answer (not just metadata)
    assert (
        "cik" in response.lower() or "0000320193" in response
    ), "Response should contain CIK information"

    print("✅ Query return value is correct")
    print(f"   Response: {response[:100]}...")


def run_tests():
    """Run all tests and report results."""
    print("=" * 60)
    print("🚀 Testing query() Method - One-Shot Query Functionality")
    print("=" * 60)

    # Run pytest with verbose output
    pytest.main([__file__, "-v", "-s"])


if __name__ == "__main__":
    run_tests()
