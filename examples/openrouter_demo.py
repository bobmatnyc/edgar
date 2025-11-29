#!/usr/bin/env python3
"""Demo script showing OpenRouterClient usage.

This demonstrates:
1. Creating the client
2. Making a successful request
3. Handling errors gracefully

Note: This uses mocked responses. For real API calls, set OPENROUTER_API_KEY.
"""

import asyncio
from unittest.mock import Mock, patch, AsyncMock

from edgar.services.openrouter_client import (
    OpenRouterClient,
    OpenRouterAuthError,
    OpenRouterRateLimitError,
)


async def demo_successful_request():
    """Demonstrate successful API request with mocked response."""
    print("\n=== Demo 1: Successful Request ===")

    # Mock successful response
    mock_response = Mock()
    mock_response.is_success = True
    mock_response.json.return_value = {
        "id": "chatcmpl-demo-123",
        "object": "chat.completion",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Hello! I'm Claude Sonnet 4.5. How can I help you today?",
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 15,
            "completion_tokens": 25,
            "total_tokens": 40,
        },
    }

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client

        # Create client and make request
        client = OpenRouterClient(api_key="demo-key")
        response = await client.chat_completion(
            messages=[{"role": "user", "content": "Hello, who are you?"}],
            temperature=0.7,
            max_tokens=2000,
        )

        # Display results
        print(f"✅ Request successful!")
        print(f"Model: {response.get('model', 'N/A')}")
        print(f"Content: {response['choices'][0]['message']['content']}")
        print(f"Tokens used: {response['usage']['total_tokens']}")


async def demo_auth_error():
    """Demonstrate authentication error handling."""
    print("\n=== Demo 2: Authentication Error ===")

    # Mock auth error response
    mock_response = Mock()
    mock_response.is_success = False
    mock_response.status_code = 401
    mock_response.text = "Invalid API key"

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client

        client = OpenRouterClient(api_key="invalid-key")

        try:
            await client.chat_completion(
                messages=[{"role": "user", "content": "Test"}]
            )
        except OpenRouterAuthError as e:
            print(f"❌ Authentication failed (as expected)")
            print(f"Error: {e}")
            print("Note: Auth errors do NOT retry - they fail immediately")


async def demo_retry_recovery():
    """Demonstrate retry logic with recovery."""
    print("\n=== Demo 3: Retry Logic (Rate Limit Recovery) ===")

    # Mock rate limit then success
    mock_rate_limit = Mock()
    mock_rate_limit.is_success = False
    mock_rate_limit.status_code = 429
    mock_rate_limit.text = "Too many requests"

    mock_success = Mock()
    mock_success.is_success = True
    mock_success.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "Success after retry!",
                }
            }
        ],
    }

    with patch("httpx.AsyncClient") as mock_client_class, \
         patch("asyncio.sleep") as mock_sleep:
        mock_client = AsyncMock()
        # First call fails (429), second succeeds
        mock_client.post.side_effect = [mock_rate_limit, mock_success]
        mock_client_class.return_value.__aenter__.return_value = mock_client

        client = OpenRouterClient(api_key="demo-key")

        print("Attempting request...")
        print("First attempt: Rate limited (429)")
        print("Waiting 2 seconds before retry...")

        response = await client.chat_completion(
            messages=[{"role": "user", "content": "Test"}]
        )

        print(f"✅ Request succeeded after retry!")
        print(f"Content: {response['choices'][0]['message']['content']}")
        print(f"Total attempts: 2")
        print(f"Backoff delay used: 2 seconds")


async def demo_max_retries_exhausted():
    """Demonstrate max retries exhausted."""
    print("\n=== Demo 4: Max Retries Exhausted ===")

    # Mock persistent rate limit
    mock_response = Mock()
    mock_response.is_success = False
    mock_response.status_code = 429
    mock_response.text = "Too many requests"

    with patch("httpx.AsyncClient") as mock_client_class, \
         patch("asyncio.sleep"):
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client

        client = OpenRouterClient(api_key="demo-key")

        try:
            print("Attempting request...")
            print("Attempt 1: Rate limited (429) - waiting 2s")
            print("Attempt 2: Rate limited (429) - waiting 4s")
            print("Attempt 3: Rate limited (429) - max retries reached")

            await client.chat_completion(
                messages=[{"role": "user", "content": "Test"}]
            )
        except OpenRouterRateLimitError as e:
            print(f"❌ All retries exhausted (as expected)")
            print(f"Error: Rate limit exceeded")
            print(f"Total attempts: 3")
            print(f"Total backoff time: 6 seconds (2s + 4s)")


async def main():
    """Run all demos."""
    print("=" * 60)
    print("OpenRouter Client Demo")
    print("=" * 60)
    print("\nNOTE: These demos use mocked responses.")
    print("For real API calls, set OPENROUTER_API_KEY environment variable.")

    await demo_successful_request()
    await demo_auth_error()
    await demo_retry_recovery()
    await demo_max_retries_exhausted()

    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
