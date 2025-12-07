"""Quick test to verify OpenRouter API connectivity."""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from edgar_analyzer.clients.openrouter_client import OpenRouterClient


async def test_api():
    """Test basic OpenRouter API call."""
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        print("❌ OPENROUTER_API_KEY not set")
        return False

    print(f"✅ API Key found: {api_key[:20]}...")

    # Try different model identifiers
    models_to_try = [
        "anthropic/claude-sonnet-4.5",
        "anthropic/claude-3.5-sonnet",
        "anthropic/claude-sonnet-3.5",
    ]

    for model in models_to_try:
        print(f"\n{'='*60}")
        print(f"Testing model: {model}")
        print(f"{'='*60}")

        try:
            client = OpenRouterClient(api_key=api_key, model=model)

            response = await client.chat_completion(
                messages=[
                    {"role": "user", "content": "Reply with just 'OK' if you can read this."}
                ],
                temperature=0.1,
                max_tokens=10,
            )

            print(f"✅ SUCCESS!")
            print(f"   Response: {response}")
            print(f"   Model: {model}")
            return True

        except Exception as e:
            print(f"❌ FAILED: {type(e).__name__}: {str(e)[:100]}")
            continue

    print("\n❌ All models failed")
    return False


if __name__ == "__main__":
    success = asyncio.run(test_api())
    sys.exit(0 if success else 1)
