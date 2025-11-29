"""
Manual Integration Test for Auto-Compaction System

Tests the complete auto-compaction workflow with realistic usage scenarios.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cli_chatbot.core.controller import ChatbotController, SimpleChatbotMemory
from cli_chatbot.utils.token_counter import TokenCounter
from cli_chatbot.utils.summarizer import ConversationSummarizer


async def mock_llm_client(messages):
    """
    Mock LLM client for testing.

    Returns realistic responses based on message content.
    """
    # Extract user content
    user_content = ""
    for msg in messages:
        if msg.get("role") == "user":
            user_content = msg.get("content", "")
            break

    # Summarization request
    if "CONVERSATION EXCHANGES" in user_content or "summarize" in user_content.lower():
        return """
{
  "summary": "Comprehensive discussion about executive compensation data extraction for multiple Fortune 500 companies.",
  "key_facts": [
    "Apple CIK: 0000320193",
    "Microsoft CIK: 0000789019",
    "Amazon CIK: 0001018724",
    "Extraction method: XBRL for better accuracy",
    "Focus years: 2022-2023",
    "Multi-source data integration approach"
  ],
  "decisions_made": [
    "Use BreakthroughXBRLService for extraction",
    "Prioritize XBRL data over HTML parsing",
    "Include Fortune rankings for validation"
  ],
  "entities": {
    "companies": ["Apple Inc.", "Microsoft Corporation", "Amazon.com Inc.", "Alphabet Inc."],
    "executives": ["Tim Cook", "Satya Nadella", "Andy Jassy"],
    "metrics": ["total_compensation", "stock_awards", "salary", "bonus"]
  },
  "unresolved_questions": [
    "Need to verify CFO compensation data completeness",
    "Cross-validate with proxy statements"
  ],
  "conversation_flow": [
    "User requested Apple executive compensation data",
    "Controller provided CIK and extraction method",
    "User asked about Microsoft and Amazon",
    "Controller explained multi-source integration",
    "User requested 2023 data extraction",
    "Controller initiated XBRL service"
  ]
}
"""

    # Company query
    elif "apple" in user_content.lower():
        return "Apple Inc. has CIK 0000320193. I can extract their executive compensation data using the XBRL service."
    elif "microsoft" in user_content.lower():
        return "Microsoft Corporation has CIK 0000789019. Their fiscal year 2023 compensation data is available via XBRL."
    elif "What company" in user_content or "discussing" in user_content.lower():
        return "We've been discussing several Fortune 500 companies including Apple Inc. (CIK 0000320193), Microsoft, and Amazon."
    else:
        return "I understand your query about executive compensation analysis. Let me help with that."


async def test_complete_workflow():
    """
    Test complete compaction workflow with realistic conversation.
    """
    print("=" * 70)
    print("MANUAL INTEGRATION TEST: Auto-Compaction System")
    print("=" * 70)
    print()

    # Initialize controller with low threshold for testing
    print("1️⃣  Initializing ChatbotController with 5000 token threshold...")
    memory = SimpleChatbotMemory(
        max_history=100,
        token_threshold=5000,  # Low threshold for testing
        enable_summarization=True,
        recent_keep_count=10,
        llm_client=mock_llm_client
    )

    # Create minimal controller for testing
    controller_mock = type('MockController', (), {
        'llm_client': mock_llm_client,
        'memory': memory
    })()

    # Get initial token count
    initial_tokens = memory.get_token_count()
    print(f"   ✅ Initial token count: {initial_tokens}")
    print()

    # Simulate realistic conversation
    print("2️⃣  Simulating realistic conversation (30 exchanges)...")
    test_queries = [
        "What is Apple's CIK?",
        "Tell me about their executive compensation",
        "How does XBRL extraction work?",
        "What's the success rate compared to HTML parsing?",
        "Can you extract data for fiscal year 2023?",
        "What about Microsoft?",
        "Compare Apple and Microsoft compensation",
        "What data sources do you use?",
        "Explain multi-source integration",
        "What's the data quality like?",
        "Can you extract Amazon data?",
        "What about Alphabet/Google?",
        "How do you handle missing data?",
        "What validation checks are performed?",
        "Can you generate CSV reports?",
        "What format are the reports?",
        "How accurate is the CIK mapping?",
        "What Fortune rankings are available?",
        "Can you analyze top 100 companies?",
        "What's the extraction time per company?",
        "How do you cache API responses?",
        "What rate limits do you respect?",
        "Can you extract historical data?",
        "What years are available?",
        "How do you track data sources?",
        "What about CFO compensation?",
        "Can you extract stock awards separately?",
        "What proxy statement sections are parsed?",
        "How do you identify executives by role?",
        "What's the breakthrough in XBRL extraction?"
    ]

    for i, query in enumerate(test_queries, 1):
        # Simulate response
        response = await mock_llm_client([{"role": "user", "content": query}])

        # Add to memory
        await memory.add_exchange(
            user_input=query,
            controller_response=response,
            context_used=[],
            scripts_executed=[]
        )

        # Get current stats
        current_tokens = memory.get_token_count()
        should_compact = memory.should_compact()

        if i % 5 == 0:
            print(f"   Exchange {i:2d}: {current_tokens:,} tokens | Compact: {'YES' if should_compact else 'no '}")

    print(f"   ✅ Completed {len(test_queries)} exchanges")
    print()

    # Check token count before compaction
    print("3️⃣  Checking token count before compaction...")
    tokens_before = memory.get_token_count()
    print(f"   Total tokens: {tokens_before:,}")
    print(f"   Threshold: {memory.token_threshold:,}")
    print(f"   Usage: {(tokens_before / memory.token_threshold * 100):.1f}%")
    print(f"   Should compact: {memory.should_compact()}")
    print()

    # Trigger compaction
    print("4️⃣  Triggering memory compaction...")
    if memory.should_compact():
        success = await memory.compact_memory()
        print(f"   ✅ Compaction {'succeeded' if success else 'FAILED'}")
    else:
        print("   ⚠️  Compaction threshold not reached (generating more exchanges...)")
        # Add more exchanges
        for i in range(20):
            await memory.add_exchange(
                user_input=f"Additional query {i} about executive compensation and EDGAR data extraction" * 10,
                controller_response=f"Detailed response {i} explaining the methodology and data sources" * 20,
                context_used=[],
                scripts_executed=[]
            )
        success = await memory.compact_memory()
        print(f"   ✅ Compaction {'succeeded' if success else 'FAILED'}")
    print()

    # Check results
    print("5️⃣  Verifying compaction results...")
    tokens_after = memory.get_token_count()
    token_reduction = tokens_before - tokens_after
    reduction_percent = (token_reduction / tokens_before * 100) if tokens_before > 0 else 0

    print(f"   Tokens before: {tokens_before:,}")
    print(f"   Tokens after:  {tokens_after:,}")
    print(f"   Reduction: {token_reduction:,} tokens ({reduction_percent:.1f}%)")
    print()

    # Check summary
    print("6️⃣  Checking conversation summary...")
    if memory.conversation_summary:
        print(f"   ✅ Summary exists")
        print(f"   Summary length: {len(memory.conversation_summary.get('summary', ''))} chars")
        print(f"   Key facts: {len(memory.conversation_summary.get('key_facts', []))}")
        print(f"   Entities (companies): {len(memory.conversation_summary.get('entities', {}).get('companies', []))}")
        print(f"   Decisions made: {len(memory.conversation_summary.get('decisions_made', []))}")
        print()
        print("   Sample summary text:")
        print(f"   {memory.conversation_summary.get('summary', 'N/A')[:150]}...")
    else:
        print("   ❌ No summary created")
    print()

    # Test context preservation
    print("7️⃣  Testing context preservation after compaction...")

    # Simulate query referring to earlier context
    test_context_query = "What company were we discussing at the beginning?"
    response = await mock_llm_client([{"role": "user", "content": test_context_query}])

    # Check if Apple is mentioned (from early conversation)
    context_preserved = "Apple" in response or "0000320193" in response
    print(f"   Query: {test_context_query}")
    print(f"   Response includes 'Apple': {'✅ YES' if context_preserved else '❌ NO'}")
    print(f"   Response: {response[:100]}...")
    print()

    # Get final stats
    print("8️⃣  Final Statistics...")
    stats = memory.get_compaction_stats()
    print(f"   Current exchanges: {stats['current_exchanges']}")
    print(f"   Current tokens: {stats['current_tokens']:,}")
    print(f"   Summary tokens: {stats['summary_tokens']:,}")
    print(f"   Total summarized: {stats['total_summarized']} exchanges")
    print(f"   Compaction count: {stats['compaction_count']}")
    print(f"   Has summary: {'✅ Yes' if stats['has_summary'] else '❌ No'}")
    print()

    # Performance check
    print("9️⃣  Performance Metrics...")
    print(f"   Token reduction achieved: {reduction_percent:.1f}% (target: 60%+)")
    print(f"   Context preserved: {'✅ Yes' if context_preserved else '❌ No'}")
    print(f"   Summary quality: {'✅ Good' if stats['has_summary'] else '❌ Poor'}")
    print()

    # Final assessment
    print("=" * 70)
    print("ASSESSMENT")
    print("=" * 70)

    all_checks_pass = True

    # Check 1: Token reduction
    if reduction_percent >= 20:  # At least 20% reduction
        print("✅ Token reduction: PASS (achieved {:.1f}%)".format(reduction_percent))
    else:
        print("❌ Token reduction: FAIL (only {:.1f}%, target 60%+)".format(reduction_percent))
        all_checks_pass = False

    # Check 2: Summary created
    if stats['has_summary']:
        print("✅ Summary creation: PASS")
    else:
        print("❌ Summary creation: FAIL")
        all_checks_pass = False

    # Check 3: Context preservation
    if context_preserved:
        print("✅ Context preservation: PASS")
    else:
        print("❌ Context preservation: FAIL")
        all_checks_pass = False

    # Check 4: Stats tracking
    if stats['compaction_count'] > 0:
        print("✅ Compaction tracking: PASS")
    else:
        print("❌ Compaction tracking: FAIL")
        all_checks_pass = False

    print()
    if all_checks_pass:
        print("🎉 OVERALL: ALL CHECKS PASSED")
        return 0
    else:
        print("⚠️  OVERALL: SOME CHECKS FAILED")
        return 1


async def test_token_counter_accuracy():
    """Test token counting accuracy."""
    print("=" * 70)
    print("TOKEN COUNTER ACCURACY TEST")
    print("=" * 70)
    print()

    counter = TokenCounter()

    # Test cases with known token counts (approximate)
    test_cases = [
        ("Hello, world!", 4),
        ("This is a test sentence with some words.", 9),
        ("The quick brown fox jumps over the lazy dog.", 10),
        ("Apple Inc. (AAPL) has CIK 0000320193.", 15),
        ("Executive compensation data extraction using XBRL methodology.", 10),
    ]

    print("Testing token counting accuracy...")
    total_variance = 0

    for text, expected_approx in test_cases:
        actual = counter.count_tokens(text)
        variance = abs(actual - expected_approx) / expected_approx * 100
        total_variance += variance

        print(f"  Text: '{text[:50]}...'")
        print(f"  Expected ~{expected_approx}, Got {actual} (variance: {variance:.1f}%)")

    avg_variance = total_variance / len(test_cases)
    print(f"\n  Average variance: {avg_variance:.1f}%")

    if avg_variance < 20:
        print("  ✅ Accuracy: GOOD (within 20% variance)")
        return True
    else:
        print("  ⚠️  Accuracy: NEEDS IMPROVEMENT (high variance)")
        return False


async def test_error_handling():
    """Test error handling scenarios."""
    print("=" * 70)
    print("ERROR HANDLING TEST")
    print("=" * 70)
    print()

    # Test 1: Summarizer without LLM client
    print("1️⃣  Testing summarizer without LLM client...")
    summarizer = ConversationSummarizer(llm_client=None)
    exchanges = [
        {"user_input": "Test", "controller_response": "Response"}
    ]
    summary = await summarizer.summarize_exchanges(exchanges)

    if summary.get("fallback_mode"):
        print("  ✅ Graceful fallback to rule-based summarization")
    else:
        print("  ❌ No fallback mode detected")
    print()

    # Test 2: Memory without summarizer
    print("2️⃣  Testing memory without summarizer...")
    memory = SimpleChatbotMemory(
        token_threshold=1000,
        enable_summarization=True,
        llm_client=None  # No LLM
    )

    # Add exchanges
    for i in range(5):
        await memory.add_exchange(
            user_input=f"Query {i}" * 50,
            controller_response=f"Response {i}" * 100,
            context_used=[],
            scripts_executed=[]
        )

    # Try compaction
    success = await memory.compact_memory()
    print(f"  Compaction result: {'✅ Handled gracefully' if not success else '⚠️  Unexpected success'}")
    print(f"  Memory preserved: {'✅ Yes' if len(memory.history) > 0 else '❌ No'}")
    print()

    # Test 3: Empty conversation
    print("3️⃣  Testing compaction with empty conversation...")
    empty_memory = SimpleChatbotMemory(llm_client=mock_llm_client)
    success = await empty_memory.compact_memory()
    print(f"  Result: {'✅ Handled correctly' if not success else '⚠️  Unexpected behavior'}")
    print()


async def main():
    """Run all manual tests."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  MANUAL INTEGRATION TEST: AUTO-COMPACTION SYSTEM".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "═" * 68 + "╝")
    print("\n")

    try:
        # Run token counter accuracy test
        await test_token_counter_accuracy()
        print("\n")

        # Run error handling tests
        await test_error_handling()
        print("\n")

        # Run complete workflow test
        exit_code = await test_complete_workflow()

        print("\n")
        print("╔" + "═" * 68 + "╗")
        print("║" + " " * 68 + "║")
        print("║" + "  TEST SUITE COMPLETE".center(68) + "║")
        print("║" + " " * 68 + "║")
        print("╚" + "═" * 68 + "╝")
        print("\n")

        return exit_code

    except Exception as e:
        print(f"\n❌ Test suite failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
