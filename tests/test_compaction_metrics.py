"""
Focused test for compaction metrics and token reduction verification.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cli_chatbot.core.controller import SimpleChatbotMemory


async def mock_llm_client(messages):
    """Mock LLM for summarization."""
    return """
{
  "summary": "Discussion about EDGAR executive compensation analysis.",
  "key_facts": ["Apple CIK: 0000320193", "Using XBRL extraction"],
  "decisions_made": ["Use BreakthroughXBRLService"],
  "entities": {"companies": ["Apple Inc."], "executives": ["Tim Cook"], "metrics": ["total_compensation"]},
  "unresolved_questions": [],
  "conversation_flow": ["User asked about Apple", "Controller provided CIK"]
}
"""


async def test_compaction_metrics():
    """Test that compaction correctly reduces token count."""
    print("=" * 70)
    print("COMPACTION METRICS VERIFICATION")
    print("=" * 70)
    print()

    # Create memory with low threshold
    memory = SimpleChatbotMemory(
        token_threshold=5000, recent_keep_count=10, llm_client=mock_llm_client
    )

    print("Step 1: Adding exchanges to exceed threshold...")
    # Add enough exchanges to exceed threshold
    for i in range(50):
        await memory.add_exchange(
            user_input=f"Query {i}: " + ("Tell me about executive compensation " * 10),
            controller_response=f"Response {i}: "
            + ("Here is detailed information about the data " * 20),
            context_used=[],
            scripts_executed=[],
        )

    # Capture BEFORE compaction
    tokens_before_compaction = memory.get_token_count()
    exchanges_before = len(memory.history)

    print(f"  Exchanges before: {exchanges_before}")
    print(f"  Tokens before: {tokens_before_compaction:,}")
    print(f"  Should compact: {memory.should_compact()}")
    print()

    # Trigger compaction
    print("Step 2: Performing compaction...")
    success = await memory.compact_memory()
    print(f"  Compaction success: {success}")
    print()

    # Capture AFTER compaction
    tokens_after_compaction = memory.get_token_count()
    exchanges_after = len(memory.history)

    print("Step 3: Measuring results...")
    print(f"  Exchanges after: {exchanges_after}")
    print(f"  Tokens after: {tokens_after_compaction:,}")
    print()

    # Calculate reduction
    token_reduction = tokens_before_compaction - tokens_after_compaction
    reduction_percent = (
        (token_reduction / tokens_before_compaction * 100)
        if tokens_before_compaction > 0
        else 0
    )

    print("Step 4: Token Reduction Analysis...")
    print(f"  Token reduction: {token_reduction:,} tokens")
    print(f"  Reduction percentage: {reduction_percent:.1f}%")
    print()

    # Verify results
    print("Step 5: Verification...")
    checks_passed = 0
    total_checks = 4

    # Check 1: Exchanges reduced
    if exchanges_after < exchanges_before:
        print(f"  ✅ Exchanges reduced: {exchanges_before} → {exchanges_after}")
        checks_passed += 1
    else:
        print(f"  ❌ Exchanges NOT reduced: {exchanges_before} → {exchanges_after}")

    # Check 2: Tokens reduced
    if tokens_after_compaction < tokens_before_compaction:
        print(
            f"  ✅ Tokens reduced: {tokens_before_compaction:,} → {tokens_after_compaction:,}"
        )
        checks_passed += 1
    else:
        print(
            f"  ❌ Tokens INCREASED: {tokens_before_compaction:,} → {tokens_after_compaction:,}"
        )

    # Check 3: Summary created
    if memory.conversation_summary:
        print(
            f"  ✅ Summary created with {len(memory.conversation_summary.get('key_facts', []))} key facts"
        )
        checks_passed += 1
    else:
        print(f"  ❌ No summary created")

    # Check 4: Reduction meets target
    if reduction_percent >= 30:  # At least 30% reduction
        print(f"  ✅ Reduction meets target: {reduction_percent:.1f}% >= 30%")
        checks_passed += 1
    else:
        print(f"  ⚠️  Reduction below target: {reduction_percent:.1f}% < 30%")

    print()
    print(f"RESULT: {checks_passed}/{total_checks} checks passed")

    if checks_passed == total_checks:
        print("✅ ALL CHECKS PASSED")
        return 0
    else:
        print("⚠️  SOME CHECKS FAILED")
        return 1


async def test_multiple_compactions():
    """Test multiple compaction cycles."""
    print("=" * 70)
    print("MULTIPLE COMPACTION CYCLES TEST")
    print("=" * 70)
    print()

    memory = SimpleChatbotMemory(
        token_threshold=3000,  # Even lower threshold
        recent_keep_count=10,
        llm_client=mock_llm_client,
    )

    print("Adding 100 exchanges in batches with compaction...")
    compaction_results = []

    for batch in range(5):
        print(f"\nBatch {batch + 1}:")

        # Add 20 exchanges
        for i in range(20):
            await memory.add_exchange(
                user_input=f"Batch {batch} Query {i}: "
                + ("executive compensation analysis " * 8),
                controller_response=f"Batch {batch} Response {i}: "
                + ("detailed analysis results " * 15),
                context_used=[],
                scripts_executed=[],
            )

        # Check if compaction needed
        tokens_before = memory.get_token_count()
        if memory.should_compact():
            print(f"  Tokens before compaction: {tokens_before:,}")
            success = await memory.compact_memory()
            tokens_after = memory.get_token_count()
            reduction = tokens_before - tokens_after
            print(f"  Compacted: {reduction:,} tokens saved")
            compaction_results.append(
                {
                    "batch": batch + 1,
                    "before": tokens_before,
                    "after": tokens_after,
                    "reduction": reduction,
                }
            )
        else:
            print(f"  No compaction needed (tokens: {tokens_before:,})")

    # Summary
    print()
    print("Compaction Summary:")
    for result in compaction_results:
        reduction_pct = (
            (result["reduction"] / result["before"] * 100)
            if result["before"] > 0
            else 0
        )
        print(
            f"  Batch {result['batch']}: {result['reduction']:,} tokens saved ({reduction_pct:.1f}%)"
        )

    print()
    final_stats = memory.get_compaction_stats()
    print(f"Final state:")
    print(f"  Total compactions: {final_stats['compaction_count']}")
    print(f"  Total summarized: {final_stats['total_summarized']} exchanges")
    print(f"  Current tokens: {final_stats['current_tokens']:,}")
    print(f"  Summary tokens: {final_stats['summary_tokens']:,}")

    if final_stats["compaction_count"] >= 2:
        print("\n✅ Multiple compactions working correctly")
        return 0
    else:
        print("\n⚠️  Expected multiple compactions")
        return 1


async def main():
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + "  COMPACTION METRICS & PERFORMANCE VERIFICATION".center(68) + "║")
    print("╚" + "═" * 68 + "╝")
    print("\n")

    # Test 1: Basic compaction metrics
    result1 = await test_compaction_metrics()
    print("\n")

    # Test 2: Multiple compactions
    result2 = await test_multiple_compactions()
    print("\n")

    # Overall result
    if result1 == 0 and result2 == 0:
        print("🎉 ALL COMPACTION TESTS PASSED")
        return 0
    else:
        print("⚠️  SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
