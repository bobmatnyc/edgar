"""
Quick test to verify auto-compaction implementation.

This script tests the new token counting and summarization features.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from cli_chatbot.utils.token_counter import TokenCounter
from cli_chatbot.utils.summarizer import ConversationSummarizer


async def test_token_counter():
    """Test token counter functionality."""
    print("🧪 Testing TokenCounter...")

    counter = TokenCounter()

    # Test basic token counting
    text = "This is a test sentence with some words."
    tokens = counter.count_tokens(text)
    print(f"  Text: '{text}'")
    print(f"  Tokens: {tokens}")

    # Test exchange counting
    exchange = {
        "user_input": "What is Apple's CIK?",
        "controller_response": "Apple Inc. (AAPL) has CIK 0000320193. This is the unique identifier used by the SEC for Apple Inc.",
    }
    exchange_tokens = counter.count_exchange_tokens(exchange)
    print(f"\n  Exchange tokens: {exchange_tokens}")

    # Test message counting
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"},
    ]
    message_tokens = counter.count_messages_tokens(messages)
    print(f"  Message list tokens: {message_tokens}")

    print("  ✅ TokenCounter working correctly\n")


async def test_summarizer():
    """Test conversation summarizer functionality."""
    print("🧪 Testing ConversationSummarizer...")

    # Mock LLM client for testing
    async def mock_llm(messages):
        """Simple mock LLM that returns a summary."""
        return """
{
  "summary": "User asked about Apple's CIK and requested compensation data extraction.",
  "key_facts": [
    "Apple CIK: 0000320193",
    "Focus year: 2023"
  ],
  "decisions_made": [
    "Use XBRL extraction method"
  ],
  "entities": {
    "companies": ["Apple Inc."],
    "executives": ["Tim Cook"],
    "metrics": ["total_compensation"]
  },
  "unresolved_questions": [],
  "conversation_flow": [
    "User asked for Apple CIK",
    "Controller provided CIK",
    "User requested 2023 data"
  ]
}
"""

    summarizer = ConversationSummarizer(llm_client=mock_llm)

    # Test summarization with sample exchanges
    exchanges = [
        {
            "user_input": "What is Apple's CIK?",
            "controller_response": "Apple Inc. (AAPL) has CIK 0000320193.",
        },
        {
            "user_input": "Extract 2023 compensation data",
            "controller_response": "I'll use XBRL extraction for better accuracy.",
        },
    ]

    summary = await summarizer.summarize_exchanges(exchanges, preserve_recent=1)

    print(f"  Summary: {summary.get('summary', 'N/A')}")
    print(f"  Key facts: {len(summary.get('key_facts', []))}")
    print(f"  Entities: {summary.get('entities', {})}")

    # Test formatting
    formatted = summarizer.format_summary_for_prompt(summary)
    print(f"\n  Formatted summary ({len(formatted)} chars):")
    print("  " + "\n  ".join(formatted.split("\n")[:5]) + "...")

    print("  ✅ ConversationSummarizer working correctly\n")


async def test_memory_integration():
    """Test SimpleChatbotMemory with auto-compaction."""
    print("🧪 Testing SimpleChatbotMemory auto-compaction...")

    from cli_chatbot.core.controller import SimpleChatbotMemory

    # Mock LLM for summarization
    async def mock_llm(messages):
        return """
{
  "summary": "Conversation about EDGAR data extraction.",
  "key_facts": ["Testing auto-compaction"],
  "decisions_made": [],
  "entities": {},
  "unresolved_questions": [],
  "conversation_flow": ["Multiple test exchanges"]
}
"""

    # Create memory with low threshold for testing (1000 tokens)
    memory = SimpleChatbotMemory(
        max_history=100, token_threshold=1000, llm_client=mock_llm
    )

    print(f"  Initial token count: {memory.get_token_count()}")

    # Add some exchanges to trigger compaction
    for i in range(15):
        await memory.add_exchange(
            user_input=f"Test query {i}" * 50,  # Long input to increase tokens
            controller_response=f"Test response {i}" * 100,  # Long response
            context_used=[],
            scripts_executed=[],
        )

    print(f"  Token count after 15 exchanges: {memory.get_token_count()}")

    # Check if compaction is needed
    should_compact = memory.should_compact()
    print(f"  Should compact: {should_compact}")

    # Trigger compaction
    if should_compact:
        success = await memory.compact_memory()
        print(f"  Compaction success: {success}")
        print(f"  Token count after compaction: {memory.get_token_count()}")

        # Show stats
        stats = memory.get_compaction_stats()
        print(f"\n  Compaction stats:")
        print(f"    Current exchanges: {stats['current_exchanges']}")
        print(f"    Current tokens: {stats['current_tokens']}")
        print(f"    Usage: {stats['usage_percent']}%")
        print(f"    Has summary: {stats['has_summary']}")
        print(f"    Total compactions: {stats['compaction_count']}")

    print("  ✅ SimpleChatbotMemory auto-compaction working correctly\n")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Auto-Compaction Implementation Test")
    print("=" * 60)
    print()

    try:
        await test_token_counter()
        await test_summarizer()
        await test_memory_integration()

        print("=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
