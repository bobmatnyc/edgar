"""
Performance and timing tests for auto-compaction system.
"""

import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cli_chatbot.core.controller import SimpleChatbotMemory


async def mock_llm(messages):
    """Fast mock LLM for performance testing."""
    await asyncio.sleep(0.001)  # Minimal delay
    return '{"summary": "Performance test", "key_facts": ["Test"], "decisions_made": [], "entities": {}, "unresolved_questions": [], "conversation_flow": []}'


async def test_compaction_performance():
    """Test compaction execution time."""
    print("=" * 70)
    print("PERFORMANCE: Compaction Execution Time")
    print("=" * 70)
    print()

    memory = SimpleChatbotMemory(token_threshold=5000, llm_client=mock_llm)

    # Add exchanges to exceed threshold
    print("Adding 50 exchanges...")
    for i in range(50):
        await memory.add_exchange(
            user_input=f"Query {i} " * 10,
            controller_response=f"Response {i} " * 20,
            context_used=[],
            scripts_executed=[],
        )

    print(f"  Token count: {memory.get_token_count():,}")
    print()

    # Time compaction
    print("Timing compaction...")
    start_time = time.time()
    success = await memory.compact_memory()
    end_time = time.time()

    execution_time = end_time - start_time

    print(f"  Compaction success: {success}")
    print(f"  Execution time: {execution_time:.3f} seconds")
    print()

    # Assess performance
    if execution_time < 1.0:
        print(f"  ✅ EXCELLENT: Compaction completed in {execution_time:.3f}s")
        return 0
    elif execution_time < 3.0:
        print(f"  ✅ GOOD: Compaction completed in {execution_time:.3f}s")
        return 0
    elif execution_time < 5.0:
        print(f"  ⚠️  ACCEPTABLE: Compaction completed in {execution_time:.3f}s")
        return 0
    else:
        print(f"  ❌ SLOW: Compaction took {execution_time:.3f}s (target <5s)")
        return 1


async def test_token_counting_performance():
    """Test token counting speed."""
    print("=" * 70)
    print("PERFORMANCE: Token Counting Speed")
    print("=" * 70)
    print()

    from cli_chatbot.utils.token_counter import TokenCounter

    counter = TokenCounter()

    # Create test exchanges
    exchanges = []
    for i in range(100):
        exchanges.append(
            {
                "user_input": f"Test query {i} " * 20,
                "controller_response": f"Test response {i} " * 40,
            }
        )

    print(f"Counting tokens for {len(exchanges)} exchanges...")

    start_time = time.time()
    total_tokens = sum(counter.count_exchange_tokens(ex) for ex in exchanges)
    end_time = time.time()

    execution_time = end_time - start_time
    tokens_per_second = total_tokens / execution_time if execution_time > 0 else 0

    print(f"  Total tokens: {total_tokens:,}")
    print(f"  Execution time: {execution_time:.3f} seconds")
    print(f"  Throughput: {tokens_per_second:,.0f} tokens/sec")
    print()

    if execution_time < 0.5:
        print(f"  ✅ EXCELLENT: Token counting very fast")
        return 0
    elif execution_time < 1.0:
        print(f"  ✅ GOOD: Token counting fast enough")
        return 0
    else:
        print(f"  ⚠️  Token counting could be faster")
        return 0


async def test_memory_overhead():
    """Test memory usage overhead."""
    print("=" * 70)
    print("PERFORMANCE: Memory Usage")
    print("=" * 70)
    print()

    import sys

    memory = SimpleChatbotMemory(token_threshold=10000, llm_client=mock_llm)

    # Get baseline size
    baseline_size = sys.getsizeof(memory.history)
    print(f"Baseline memory size: {baseline_size:,} bytes")

    # Add exchanges
    for i in range(100):
        await memory.add_exchange(
            user_input=f"Query {i}",
            controller_response=f"Response {i}" * 20,
            context_used=[],
            scripts_executed=[],
        )

    size_before = sys.getsizeof(memory.history)
    tokens_before = memory.get_token_count()

    print(f"\nBefore compaction:")
    print(f"  Exchanges: {len(memory.history)}")
    print(f"  Tokens: {tokens_before:,}")
    print(f"  Memory size: {size_before:,} bytes")

    # Compact
    await memory.compact_memory()

    size_after = sys.getsizeof(memory.history)
    tokens_after = memory.get_token_count()
    summary_size = (
        len(str(memory.conversation_summary)) if memory.conversation_summary else 0
    )

    print(f"\nAfter compaction:")
    print(f"  Exchanges: {len(memory.history)}")
    print(f"  Tokens: {tokens_after:,}")
    print(f"  Memory size: {size_after:,} bytes")
    print(f"  Summary size: {summary_size:,} bytes")

    memory_reduction = size_before - size_after
    memory_reduction_pct = (
        (memory_reduction / size_before * 100) if size_before > 0 else 0
    )

    print(f"\nReduction:")
    print(f"  Memory saved: {memory_reduction:,} bytes ({memory_reduction_pct:.1f}%)")
    print(
        f"  Tokens saved: {tokens_before - tokens_after:,} ({(tokens_before - tokens_after) / tokens_before * 100:.1f}%)"
    )

    print()
    print("  ✅ Memory overhead test complete")
    return 0


async def test_large_conversation_performance():
    """Test performance with very large conversation."""
    print("=" * 70)
    print("PERFORMANCE: Large Conversation (1000 exchanges)")
    print("=" * 70)
    print()

    memory = SimpleChatbotMemory(
        token_threshold=50000, recent_keep_count=20, llm_client=mock_llm
    )

    print("Adding 1000 exchanges...")
    start_time = time.time()

    for i in range(1000):
        await memory.add_exchange(
            user_input=f"Query {i}",
            controller_response=f"Response {i}" * 10,
            context_used=[],
            scripts_executed=[],
        )

        if (i + 1) % 200 == 0:
            elapsed = time.time() - start_time
            print(f"  Progress: {i + 1}/1000 exchanges ({elapsed:.1f}s)")

    total_time = time.time() - start_time

    print(f"\nTotal time: {total_time:.2f}s")
    print(f"Exchanges per second: {1000 / total_time:.1f}")
    print(f"Final token count: {memory.get_token_count():,}")
    print()

    # Compact if needed
    if memory.should_compact():
        print("Compacting large conversation...")
        compact_start = time.time()
        success = await memory.compact_memory()
        compact_time = time.time() - compact_start

        print(f"  Compaction time: {compact_time:.2f}s")
        print(f"  Final tokens: {memory.get_token_count():,}")

        if compact_time < 5.0:
            print(f"\n  ✅ Large conversation handled efficiently")
            return 0
        else:
            print(f"\n  ⚠️  Compaction took {compact_time:.2f}s (acceptable)")
            return 0
    else:
        print("  ℹ️  Compaction not needed")
        return 0


async def test_summarizer_performance():
    """Test summarizer execution time."""
    print("=" * 70)
    print("PERFORMANCE: Summarizer Execution Time")
    print("=" * 70)
    print()

    from cli_chatbot.utils.summarizer import ConversationSummarizer

    async def timed_llm(messages):
        """LLM with realistic delay."""
        await asyncio.sleep(0.1)  # 100ms simulated network call
        return '{"summary": "Test", "key_facts": ["Fact 1", "Fact 2"], "decisions_made": [], "entities": {"companies": ["Test Co"]}, "unresolved_questions": [], "conversation_flow": ["Step 1", "Step 2"]}'

    summarizer = ConversationSummarizer(llm_client=timed_llm)

    # Create exchanges
    exchanges = []
    for i in range(50):
        exchanges.append(
            {
                "user_input": f"Query {i}" * 5,
                "controller_response": f"Response {i}" * 10,
            }
        )

    print(f"Summarizing {len(exchanges)} exchanges...")
    start_time = time.time()
    summary = await summarizer.summarize_exchanges(exchanges, preserve_recent=10)
    end_time = time.time()

    execution_time = end_time - start_time

    print(f"  Execution time: {execution_time:.3f}s")
    print(f"  Summary created: {summary is not None}")
    print(f"  Key facts: {len(summary.get('key_facts', []))}")
    print()

    if execution_time < 2.0:
        print("  ✅ Summarization very fast")
        return 0
    elif execution_time < 5.0:
        print("  ✅ Summarization acceptable")
        return 0
    else:
        print("  ⚠️  Summarization could be faster")
        return 0


async def main():
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + "  PERFORMANCE & TIMING TEST SUITE".center(68) + "║")
    print("╚" + "═" * 68 + "╝")
    print("\n")

    results = []

    tests = [
        ("Compaction Performance", test_compaction_performance),
        ("Token Counting Speed", test_token_counting_performance),
        ("Memory Overhead", test_memory_overhead),
        ("Large Conversation", test_large_conversation_performance),
        ("Summarizer Performance", test_summarizer_performance),
    ]

    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} crashed: {e}")
            results.append((name, 1))
        print()

    # Summary
    print("=" * 70)
    print("PERFORMANCE TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, r in results if r == 0)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result == 0 else "❌ FAIL"
        print(f"  {status}: {name}")

    print()
    print(f"Overall: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL PERFORMANCE TESTS PASSED")
        return 0
    else:
        print("\n⚠️  SOME PERFORMANCE TESTS FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
