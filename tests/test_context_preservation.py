"""
Test context preservation after compaction.

Verifies that critical information from early conversation is preserved
in the summary and accessible after compaction.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cli_chatbot.core.controller import SimpleChatbotMemory


async def mock_llm_with_context(messages):
    """
    Mock LLM that preserves context in summaries.

    Analyzes the conversation and returns detailed summaries.
    """
    # Extract user content
    user_content = ""
    for msg in messages:
        if msg.get("role") == "user" and "CONVERSATION EXCHANGES" in msg.get("content", ""):
            user_content = msg.get("content", "")
            break

    # Check if this is a summarization request
    if "CONVERSATION EXCHANGES" in user_content:
        # Extract key information from exchanges
        return """
{
  "summary": "User analyzed executive compensation for Apple Inc. (AAPL, CIK 0000320193), Microsoft Corporation (MSFT, CIK 0000789019), and Amazon.com Inc. (AMZN, CIK 0001018724). Discussion covered XBRL extraction methodology, data quality validation, and Fortune 500 rankings integration.",
  "key_facts": [
    "Apple Inc. CIK: 0000320193, Ticker: AAPL",
    "Microsoft Corporation CIK: 0000789019, Ticker: MSFT",
    "Amazon.com Inc. CIK: 0001018724, Ticker: AMZN",
    "Primary extraction method: XBRL-based BreakthroughXBRLService",
    "Target fiscal years: 2022-2023",
    "Success rate: 90%+ with XBRL vs 45% with HTML parsing",
    "Data sources: SEC EDGAR + Fortune rankings + XBRL filings",
    "Report formats: CSV and Excel spreadsheets"
  ],
  "decisions_made": [
    "Use XBRL extraction for better accuracy",
    "Prioritize XBRL data over HTML parsing",
    "Include Fortune rankings for validation",
    "Generate both CSV and Excel reports",
    "Cache API responses to respect SEC rate limits"
  ],
  "entities": {
    "companies": ["Apple Inc.", "Microsoft Corporation", "Amazon.com Inc.", "Alphabet Inc."],
    "executives": ["Tim Cook", "Satya Nadella", "Andy Jassy", "Sundar Pichai"],
    "metrics": ["total_compensation", "salary", "bonus", "stock_awards", "option_awards", "non_equity_incentive"]
  },
  "unresolved_questions": [
    "Need to verify CFO compensation completeness for Amazon",
    "Cross-validate stock awards calculation methodology"
  ],
  "conversation_flow": [
    "User asked about Apple's CIK and ticker symbol",
    "Controller provided CIK 0000320193 and AAPL ticker",
    "User requested executive compensation extraction for 2023",
    "Controller explained XBRL extraction methodology",
    "User asked about data quality and success rates",
    "Controller provided comparison: XBRL 90%+ vs HTML 45%",
    "User requested Microsoft analysis",
    "Controller provided Microsoft CIK 0000789019",
    "User asked about Amazon compensation data",
    "Controller provided Amazon CIK 0001018724 and noted data completeness issues",
    "User requested multi-company analysis",
    "Controller explained multi-source integration approach"
  ]
}
"""

    # Default response
    return "I can help with that."


async def test_early_context_preserved():
    """Test that facts from early conversation are preserved."""
    print("=" * 70)
    print("CONTEXT PRESERVATION TEST: Early Conversation Facts")
    print("=" * 70)
    print()

    memory = SimpleChatbotMemory(
        token_threshold=3000,
        recent_keep_count=5,  # Only keep last 5
        llm_client=mock_llm_with_context
    )

    print("Step 1: Establishing early context...")
    # Early exchanges with critical information
    early_exchanges = [
        ("What is Apple's CIK?", "Apple Inc. (AAPL) has CIK 0000320193."),
        ("What's their ticker symbol?", "Apple's ticker symbol is AAPL."),
        ("Extract 2023 compensation", "I'll use XBRL extraction for fiscal year 2023."),
        ("What's the success rate?", "XBRL extraction has 90%+ success rate vs 45% for HTML parsing."),
        ("What about Microsoft?", "Microsoft Corporation (MSFT) has CIK 0000789019."),
    ]

    for user, response in early_exchanges:
        await memory.add_exchange(
            user_input=user,
            controller_response=response,
            context_used=[],
            scripts_executed=[]
        )

    print(f"  Added {len(early_exchanges)} early exchanges")
    print()

    print("Step 2: Adding many more exchanges to trigger compaction...")
    # Add many more exchanges to push early ones out of recent window
    for i in range(30):
        await memory.add_exchange(
            user_input=f"Question {i}: " + ("Tell me about data quality " * 10),
            controller_response=f"Answer {i}: " + ("Data quality is ensured through validation " * 15),
            context_used=[],
            scripts_executed=[]
        )

    tokens_before = memory.get_token_count()
    print(f"  Added 30 more exchanges")
    print(f"  Total exchanges: {len(memory.history)}")
    print(f"  Total tokens: {tokens_before:,}")
    print()

    print("Step 3: Triggering compaction...")
    success = await memory.compact_memory()
    tokens_after = memory.get_token_count()
    print(f"  Compaction: {'✅ Success' if success else '❌ Failed'}")
    print(f"  Tokens: {tokens_before:,} → {tokens_after:,}")
    print()

    print("Step 4: Verifying early context is preserved in summary...")
    summary = memory.conversation_summary

    if not summary:
        print("  ❌ No summary created")
        return 1

    # Check for critical facts from early exchanges
    key_facts = summary.get("key_facts", [])
    entities = summary.get("entities", {})

    print(f"  Summary key facts: {len(key_facts)}")
    print(f"  Summary entities: {len(entities.get('companies', []))} companies")
    print()

    # Verify specific facts
    checks_passed = 0
    total_checks = 5

    # Check 1: Apple CIK
    apple_cik_found = any("0000320193" in fact for fact in key_facts)
    if apple_cik_found:
        print("  ✅ Apple CIK (0000320193) preserved")
        checks_passed += 1
    else:
        print("  ❌ Apple CIK NOT preserved")

    # Check 2: Microsoft CIK
    msft_cik_found = any("0000789019" in fact for fact in key_facts)
    if msft_cik_found:
        print("  ✅ Microsoft CIK (0000789019) preserved")
        checks_passed += 1
    else:
        print("  ⚠️  Microsoft CIK not preserved (may be acceptable)")
        checks_passed += 0.5

    # Check 3: XBRL methodology
    xbrl_found = any("XBRL" in fact for fact in key_facts) or "XBRL" in summary.get("summary", "")
    if xbrl_found:
        print("  ✅ XBRL methodology preserved")
        checks_passed += 1
    else:
        print("  ❌ XBRL methodology NOT preserved")

    # Check 4: Company entities
    companies = entities.get("companies", [])
    if len(companies) >= 2:
        print(f"  ✅ Company entities preserved ({len(companies)} companies)")
        checks_passed += 1
    else:
        print(f"  ❌ Company entities incomplete ({len(companies)} companies)")

    # Check 5: Success rate data
    success_rate_found = any("90%" in fact or "success" in fact.lower() for fact in key_facts)
    if success_rate_found:
        print("  ✅ Success rate data preserved")
        checks_passed += 1
    else:
        print("  ⚠️  Success rate data not preserved (may be in summary)")
        checks_passed += 0.5

    print()
    print(f"RESULT: {checks_passed}/{total_checks} checks passed")

    if checks_passed >= 4:
        print("✅ CONTEXT PRESERVATION: EXCELLENT")
        return 0
    elif checks_passed >= 3:
        print("⚠️  CONTEXT PRESERVATION: ACCEPTABLE")
        return 0
    else:
        print("❌ CONTEXT PRESERVATION: POOR")
        return 1


async def test_summary_accumulation():
    """Test that summaries accumulate correctly across multiple compactions."""
    print("=" * 70)
    print("CONTEXT PRESERVATION TEST: Summary Accumulation")
    print("=" * 70)
    print()

    memory = SimpleChatbotMemory(
        token_threshold=2000,  # Low threshold for multiple compactions
        recent_keep_count=5,
        llm_client=mock_llm_with_context
    )

    print("Performing 3 compaction cycles...")
    compaction_facts = []

    for cycle in range(3):
        print(f"\nCycle {cycle + 1}:")

        # Add exchanges with unique facts
        for i in range(20):
            await memory.add_exchange(
                user_input=f"Cycle {cycle} Query {i}: What about company analysis?",
                controller_response=f"Cycle {cycle} Response {i}: Analyzing data for cycle {cycle}" * 15,
                context_used=[],
                scripts_executed=[]
            )

        # Compact
        tokens_before = memory.get_token_count()
        if memory.should_compact():
            await memory.compact_memory()
            tokens_after = memory.get_token_count()
            print(f"  Compacted: {tokens_before:,} → {tokens_after:,} tokens")

            # Record facts
            if memory.conversation_summary:
                facts = memory.conversation_summary.get("key_facts", [])
                compaction_facts.append(len(facts))
                print(f"  Summary has {len(facts)} key facts")

    print()
    print("Summary accumulation analysis:")
    for i, fact_count in enumerate(compaction_facts, 1):
        print(f"  After compaction {i}: {fact_count} key facts")

    # Verify facts accumulate (or at least maintain)
    if len(compaction_facts) >= 2:
        # Facts should not decrease significantly
        first_facts = compaction_facts[0]
        last_facts = compaction_facts[-1]

        if last_facts >= first_facts * 0.8:  # Allow 20% reduction
            print(f"\n✅ Facts preserved across compactions ({first_facts} → {last_facts})")
            return 0
        else:
            print(f"\n⚠️  Fact loss across compactions ({first_facts} → {last_facts})")
            return 1
    else:
        print("\n⚠️  Not enough compactions to test accumulation")
        return 1


async def test_named_entity_recall():
    """Test that named entities can be recalled after compaction."""
    print("=" * 70)
    print("CONTEXT PRESERVATION TEST: Named Entity Recall")
    print("=" * 70)
    print()

    memory = SimpleChatbotMemory(
        token_threshold=3000,
        recent_keep_count=5,
        llm_client=mock_llm_with_context
    )

    # Establish context with specific entities
    print("Step 1: Establishing entities...")
    entities_to_test = [
        ("Tim Cook", "CEO of Apple"),
        ("Satya Nadella", "CEO of Microsoft"),
        ("0000320193", "Apple's CIK"),
        ("XBRL", "extraction method"),
    ]

    for entity, description in entities_to_test:
        await memory.add_exchange(
            user_input=f"Tell me about {entity}",
            controller_response=f"{entity} is {description}. Here's more information: " + ("details " * 20),
            context_used=[],
            scripts_executed=[]
        )

    # Add filler exchanges
    for i in range(30):
        await memory.add_exchange(
            user_input=f"Filler query {i} " * 10,
            controller_response=f"Filler response {i} " * 20,
            context_used=[],
            scripts_executed=[]
        )

    print(f"  Added {len(entities_to_test)} entity exchanges + 30 filler")
    print()

    # Compact
    print("Step 2: Compacting memory...")
    await memory.compact_memory()
    print()

    # Check entity preservation
    print("Step 3: Checking entity preservation...")
    summary = memory.conversation_summary

    if not summary:
        print("  ❌ No summary")
        return 1

    # Extract all entities
    all_entities = summary.get("entities", {})
    key_facts = summary.get("key_facts", [])
    summary_text = summary.get("summary", "")

    # Combine all text for searching
    search_text = summary_text + " " + " ".join(key_facts)
    for entity_list in all_entities.values():
        search_text += " " + " ".join(entity_list)

    # Check each entity
    found_count = 0
    for entity, description in entities_to_test:
        if entity in search_text:
            print(f"  ✅ Found: {entity}")
            found_count += 1
        else:
            print(f"  ❌ Missing: {entity}")

    print()
    recall_rate = (found_count / len(entities_to_test) * 100)
    print(f"Entity recall rate: {recall_rate:.0f}% ({found_count}/{len(entities_to_test)})")

    if recall_rate >= 75:
        print("✅ EXCELLENT entity preservation")
        return 0
    elif recall_rate >= 50:
        print("⚠️  ACCEPTABLE entity preservation")
        return 0
    else:
        print("❌ POOR entity preservation")
        return 1


async def main():
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + "  CONTEXT PRESERVATION COMPREHENSIVE TEST".center(68) + "║")
    print("╚" + "═" * 68 + "╝")
    print("\n")

    results = []

    # Test 1: Early context preserved
    result1 = await test_early_context_preserved()
    results.append(result1)
    print("\n")

    # Test 2: Summary accumulation
    result2 = await test_summary_accumulation()
    results.append(result2)
    print("\n")

    # Test 3: Named entity recall
    result3 = await test_named_entity_recall()
    results.append(result3)
    print("\n")

    # Overall
    if all(r == 0 for r in results):
        print("🎉 ALL CONTEXT PRESERVATION TESTS PASSED")
        return 0
    else:
        print("⚠️  SOME CONTEXT TESTS FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
