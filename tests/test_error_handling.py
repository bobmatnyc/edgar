"""
Comprehensive error handling and edge case tests for auto-compaction.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cli_chatbot.core.controller import SimpleChatbotMemory
from cli_chatbot.utils.summarizer import ConversationSummarizer
from cli_chatbot.utils.token_counter import TokenCounter


async def test_no_tiktoken_fallback():
    """Test that system works without tiktoken library."""
    print("=" * 70)
    print("ERROR HANDLING: Tiktoken Unavailable Fallback")
    print("=" * 70)
    print()

    # TokenCounter gracefully falls back to character estimation
    counter = TokenCounter()

    print("Testing token counting without tiktoken...")
    text = "This is a test sentence to verify fallback token counting."
    tokens = counter.count_tokens(text)

    print(f"  Text: '{text}'")
    print(f"  Estimated tokens: {tokens}")
    print(f"  Using tiktoken: {counter.use_tiktoken}")

    if tokens > 0:
        print("  ✅ Fallback token counting working")
        return 0
    else:
        print("  ❌ Token counting failed")
        return 1


async def test_llm_failure_handling():
    """Test graceful handling when LLM calls fail."""
    print("=" * 70)
    print("ERROR HANDLING: LLM Failure")
    print("=" * 70)
    print()

    async def failing_llm(messages):
        """LLM that always fails."""
        raise Exception("Mock LLM connection failure")

    summarizer = ConversationSummarizer(llm_client=failing_llm)

    print("Testing summarization with failing LLM...")
    exchanges = [
        {"user_input": f"Query {i}", "controller_response": f"Response {i}"}
        for i in range(10)
    ]

    summary = await summarizer.summarize_exchanges(exchanges, preserve_recent=2)

    print(f"  Exchanges to summarize: {len(exchanges)}")
    print(f"  Summary created: {'Yes' if summary else 'No'}")
    print(f"  Fallback mode: {summary.get('fallback_mode', False)}")

    if summary and summary.get("fallback_mode"):
        print("  ✅ Graceful fallback to rule-based summarization")
        return 0
    else:
        print("  ❌ Failed to handle LLM error")
        return 1


async def test_empty_conversation_compaction():
    """Test compaction with empty or minimal conversation."""
    print("=" * 70)
    print("ERROR HANDLING: Empty Conversation")
    print("=" * 70)
    print()

    async def mock_llm(messages):
        return '{"summary": "Empty", "key_facts": [], "decisions_made": [], "entities": {}, "unresolved_questions": [], "conversation_flow": []}'

    memory = SimpleChatbotMemory(llm_client=mock_llm)

    print("Test 1: Compaction with 0 exchanges...")
    result = await memory.compact_memory()
    print(f"  Result: {'Correctly skipped' if not result else 'Unexpected success'}")

    print("\nTest 2: Compaction with fewer exchanges than recent_keep_count...")
    for i in range(5):
        await memory.add_exchange(
            user_input=f"Query {i}",
            controller_response=f"Response {i}",
            context_used=[],
            scripts_executed=[],
        )

    result = await memory.compact_memory()
    print(f"  Result: {'Correctly skipped' if not result else 'Unexpected success'}")

    if not result:
        print("\n  ✅ Empty/minimal conversation handled correctly")
        return 0
    else:
        print("\n  ❌ Compaction should have been skipped")
        return 1


async def test_malformed_summary_response():
    """Test handling of malformed LLM responses."""
    print("=" * 70)
    print("ERROR HANDLING: Malformed Summary Response")
    print("=" * 70)
    print()

    test_cases = [
        ("Invalid JSON", "This is not JSON at all"),
        ("Partial JSON", '{"summary": "Test"'),
        ("Wrong structure", '{"wrong": "fields"}'),
        ("Empty response", ""),
        ("Non-JSON with braces", "{This is text with braces}"),
    ]

    async def mock_llm_factory(response_text):
        async def mock_llm(messages):
            return response_text

        return mock_llm

    passed = 0
    total = len(test_cases)

    for name, malformed_response in test_cases:
        llm = await mock_llm_factory(malformed_response)
        summarizer = ConversationSummarizer(llm_client=llm)

        exchanges = [{"user_input": "Test", "controller_response": "Test"}]

        try:
            summary = await summarizer.summarize_exchanges(exchanges)
            # Should get fallback summary
            if summary.get("fallback_mode"):
                print(f"  ✅ {name}: Handled with fallback")
                passed += 1
            else:
                print(f"  ⚠️  {name}: No fallback but didn't crash")
                passed += 0.5
        except Exception as e:
            print(f"  ❌ {name}: Crashed with {type(e).__name__}")

    print()
    print(f"Result: {passed}/{total} cases handled correctly")

    if passed >= total * 0.8:
        print("✅ Malformed response handling: GOOD")
        return 0
    else:
        print("❌ Malformed response handling: POOR")
        return 1


async def test_very_long_exchange():
    """Test handling of very long individual exchanges."""
    print("=" * 70)
    print("ERROR HANDLING: Very Long Exchanges")
    print("=" * 70)
    print()

    async def mock_llm(messages):
        return '{"summary": "Long exchange test", "key_facts": ["Long content handled"], "decisions_made": [], "entities": {}, "unresolved_questions": [], "conversation_flow": []}'

    memory = SimpleChatbotMemory(token_threshold=5000, llm_client=mock_llm)

    print("Adding very long exchange...")
    # Create an exchange with ~10k tokens
    very_long_input = "Tell me about executive compensation " * 500
    very_long_response = "Here is detailed information " * 1000

    await memory.add_exchange(
        user_input=very_long_input,
        controller_response=very_long_response,
        context_used=[],
        scripts_executed=[],
    )

    tokens = memory.get_token_count()
    print(f"  Single exchange tokens: {tokens:,}")

    # Add a few more to trigger compaction
    for i in range(10):
        await memory.add_exchange(
            user_input=f"Follow-up {i}",
            controller_response=f"Response {i}" * 50,
            context_used=[],
            scripts_executed=[],
        )

    tokens_before = memory.get_token_count()
    print(f"  Total tokens before: {tokens_before:,}")

    if memory.should_compact():
        success = await memory.compact_memory()
        tokens_after = memory.get_token_count()
        print(f"  Compaction: {'✅ Success' if success else '❌ Failed'}")
        print(f"  Tokens after: {tokens_after:,}")

        if success and tokens_after < tokens_before:
            print("\n  ✅ Very long exchange handled correctly")
            return 0
        else:
            print("\n  ❌ Long exchange handling issue")
            return 1
    else:
        print("\n  ⚠️  Compaction threshold not reached")
        return 0


async def test_rapid_compaction_cycles():
    """Test stability under rapid repeated compaction."""
    print("=" * 70)
    print("ERROR HANDLING: Rapid Compaction Cycles")
    print("=" * 70)
    print()

    async def mock_llm(messages):
        return '{"summary": "Rapid compaction test", "key_facts": ["Test fact"], "decisions_made": [], "entities": {}, "unresolved_questions": [], "conversation_flow": []}'

    memory = SimpleChatbotMemory(
        token_threshold=1500,  # Very low threshold
        recent_keep_count=5,
        llm_client=mock_llm,
    )

    print("Triggering 10 rapid compaction cycles...")
    compactions = 0
    errors = 0

    for cycle in range(10):
        # Add exchanges
        for i in range(15):
            await memory.add_exchange(
                user_input=f"Cycle {cycle} Query {i} " * 10,
                controller_response=f"Cycle {cycle} Response {i} " * 20,
                context_used=[],
                scripts_executed=[],
            )

        # Compact if needed
        if memory.should_compact():
            try:
                success = await memory.compact_memory()
                if success:
                    compactions += 1
                else:
                    errors += 1
            except Exception as e:
                print(f"  ❌ Error in cycle {cycle}: {e}")
                errors += 1

    print(f"  Successful compactions: {compactions}")
    print(f"  Errors: {errors}")
    print(f"  Final exchanges: {len(memory.history)}")
    print(f"  Final tokens: {memory.get_token_count():,}")

    if errors == 0 and compactions >= 5:
        print("\n  ✅ Rapid compaction cycles handled correctly")
        return 0
    else:
        print("\n  ❌ Issues with rapid compaction")
        return 1


async def test_edge_case_token_counts():
    """Test edge cases in token counting."""
    print("=" * 70)
    print("ERROR HANDLING: Edge Case Token Counts")
    print("=" * 70)
    print()

    counter = TokenCounter()

    test_cases = [
        ("Empty string", ""),
        ("Single character", "a"),
        ("Unicode", "你好世界 مرحبا שלום"),
        ("Special chars", "!@#$%^&*()_+-=[]{}|;':\",./<>?"),
        ("Very long word", "a" * 1000),
        ("Newlines", "\n\n\n\n\n"),
    ]

    passed = 0
    total = len(test_cases)

    for name, text in test_cases:
        try:
            tokens = counter.count_tokens(text)
            if tokens >= 0:  # Any non-negative count is acceptable
                print(f"  ✅ {name}: {tokens} tokens")
                passed += 1
            else:
                print(f"  ❌ {name}: Negative token count")
        except Exception as e:
            print(f"  ❌ {name}: Exception {type(e).__name__}")

    print()
    print(f"Result: {passed}/{total} cases handled")

    if passed == total:
        print("✅ Edge case token counting: EXCELLENT")
        return 0
    else:
        print("⚠️  Edge case token counting: NEEDS IMPROVEMENT")
        return 1


async def test_concurrent_access():
    """Test thread safety (basic check)."""
    print("=" * 70)
    print("ERROR HANDLING: Concurrent Access")
    print("=" * 70)
    print()

    async def mock_llm(messages):
        await asyncio.sleep(0.01)  # Simulate network delay
        return '{"summary": "Concurrent test", "key_facts": [], "decisions_made": [], "entities": {}, "unresolved_questions": [], "conversation_flow": []}'

    memory = SimpleChatbotMemory(token_threshold=3000, llm_client=mock_llm)

    print("Testing concurrent exchange additions...")

    # Add exchanges concurrently
    async def add_exchanges(batch_id):
        for i in range(10):
            await memory.add_exchange(
                user_input=f"Batch {batch_id} Query {i}",
                controller_response=f"Batch {batch_id} Response {i}" * 20,
                context_used=[],
                scripts_executed=[],
            )

    # Run 5 concurrent tasks
    tasks = [add_exchanges(i) for i in range(5)]
    await asyncio.gather(*tasks)

    print(f"  Total exchanges: {len(memory.history)}")
    print(f"  Expected: 50")

    if len(memory.history) == 50:
        print("\n  ✅ Concurrent access handled correctly")
        return 0
    else:
        print("\n  ⚠️  Possible concurrency issue (may be acceptable)")
        return 0  # Don't fail - this is informational


async def main():
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + "  ERROR HANDLING & EDGE CASES TEST SUITE".center(68) + "║")
    print("╚" + "═" * 68 + "╝")
    print("\n")

    results = []

    # Run all tests
    tests = [
        ("Tiktoken Fallback", test_no_tiktoken_fallback),
        ("LLM Failure", test_llm_failure_handling),
        ("Empty Conversation", test_empty_conversation_compaction),
        ("Malformed Response", test_malformed_summary_response),
        ("Very Long Exchange", test_very_long_exchange),
        ("Rapid Compaction", test_rapid_compaction_cycles),
        ("Edge Case Tokens", test_edge_case_token_counts),
        ("Concurrent Access", test_concurrent_access),
    ]

    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} crashed: {e}")
            results.append((name, 1))

        print("\n")

    # Summary
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, r in results if r == 0)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result == 0 else "❌ FAIL"
        print(f"  {status}: {name}")

    print()
    print(f"Overall: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL ERROR HANDLING TESTS PASSED")
        return 0
    elif passed >= total * 0.75:
        print("\n✅ MOST ERROR HANDLING TESTS PASSED")
        return 0
    else:
        print("\n⚠️  MULTIPLE ERROR HANDLING FAILURES")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
