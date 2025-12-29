"""Debug script to examine SCT extractor API response."""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from edgar_analyzer.clients.openrouter_client import OpenRouterClient


async def test_api_response():
    """Test the OpenRouter API response format."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ ERROR: OPENROUTER_API_KEY environment variable not set")
        sys.exit(1)

    print("✅ OpenRouter API key found")

    # Initialize client
    openrouter = OpenRouterClient(
        api_key=api_key,
        model="anthropic/claude-sonnet-4.5"
    )

    print(f"✅ OpenRouterClient initialized (model: {openrouter.model})")

    # Simple test prompt
    test_prompt = """Extract this data as JSON:

Company: Apple Inc.
CIK: 0000320193
CEO: Tim Cook
Salary: $3,000,000

Return JSON with fields: company_name, cik, ceo_name, salary"""

    print("\n" + "="*80)
    print("Testing chat_completion_json method")
    print("="*80)

    try:
        response = await openrouter.chat_completion_json(
            messages=[
                {
                    "role": "system",
                    "content": "You are a data extractor. Return only valid JSON."
                },
                {"role": "user", "content": test_prompt}
            ],
            temperature=0.1,
            max_tokens=500
        )

        print(f"\n✅ Response received (length: {len(response)} chars)")
        print("\n" + "="*80)
        print("RESPONSE CONTENT:")
        print("="*80)
        print(response)
        print("="*80)

        # Try to parse as JSON
        import json
        try:
            parsed = json.loads(response)
            print("\n✅ Successfully parsed as JSON!")
            print(f"   Keys: {list(parsed.keys())}")
            print(f"   Data: {parsed}")
        except json.JSONDecodeError as e:
            print(f"\n❌ Failed to parse as JSON: {e}")
            print(f"\n   First 200 chars: {repr(response[:200])}")
            print(f"   Last 200 chars: {repr(response[-200:])}")

    except Exception as e:
        print(f"\n❌ API call failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_api_response())
