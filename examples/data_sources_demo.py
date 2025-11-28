"""
Data Source Abstraction Layer - Usage Examples

Demonstrates how to use the various data sources with built-in
caching, rate limiting, and retry logic.
"""

import asyncio
import os
from pathlib import Path

from edgar_analyzer.data_sources import (
    APIDataSource,
    FileDataSource,
    JinaDataSource,
    URLDataSource,
)


async def demo_api_source():
    """Demonstrate API data source usage."""
    print("\n" + "=" * 60)
    print("API DATA SOURCE DEMO")
    print("=" * 60)

    # Example 1: GitHub API (no auth required for public endpoints)
    print("\n1. Fetching from GitHub API:")
    github = APIDataSource(
        base_url="https://api.github.com",
        rate_limit_per_minute=60,  # GitHub allows 60/hour for unauthenticated
    )

    user_data = await github.fetch(endpoint="users/github")
    print(f"   User: {user_data.get('login')}")
    print(f"   Name: {user_data.get('name')}")
    print(f"   Public Repos: {user_data.get('public_repos')}")

    # Example 2: Authenticated API (OpenRouter)
    api_key = os.getenv("OPENROUTER_API_KEY")
    if api_key and api_key != "sk-or-v1-test123456789":  # Skip placeholder
        print("\n2. Fetching from OpenRouter API:")
        openrouter = APIDataSource(
            base_url="https://openrouter.ai/api/v1",
            auth_token=api_key,
            rate_limit_per_minute=60,
        )

        models = await openrouter.fetch(endpoint="models")
        print(f"   Available models: {len(models.get('data', []))}")
        if models.get("data"):
            print(f"   First model: {models['data'][0].get('id')}")
    else:
        print("\n2. Skipping OpenRouter demo (no API key configured)")

    # Example 3: Cache demonstration
    print("\n3. Demonstrating cache (second fetch should be instant):")
    import time

    start = time.time()
    await github.fetch(endpoint="users/github")
    elapsed1 = time.time() - start

    start = time.time()
    await github.fetch(endpoint="users/github")  # Cached
    elapsed2 = time.time() - start

    print(f"   First fetch: {elapsed1:.3f}s")
    print(f"   Cached fetch: {elapsed2:.3f}s (speedup: {elapsed1/elapsed2:.1f}x)")


async def demo_jina_source():
    """Demonstrate Jina data source for web content extraction."""
    print("\n" + "=" * 60)
    print("JINA DATA SOURCE DEMO")
    print("=" * 60)

    api_key = os.getenv("JINA_API_KEY")

    jina = JinaDataSource(api_key=api_key)

    print(f"\n1. Jina configuration:")
    print(f"   Tier: {'Paid' if api_key else 'Free'}")
    print(f"   Rate limit: {jina.rate_limit_per_minute}/min")

    # Extract content from example.com
    print("\n2. Extracting content from example.com:")
    result = await jina.fetch("https://example.com")
    print(f"   Title: {result['title']}")
    print(f"   Content length: {len(result['content'])} chars")
    print(f"   First 100 chars: {result['content'][:100]}...")


async def demo_file_source():
    """Demonstrate file data source."""
    print("\n" + "=" * 60)
    print("FILE DATA SOURCE DEMO")
    print("=" * 60)

    # Create temporary test files
    import tempfile
    import json

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Example 1: JSON file
        print("\n1. Reading JSON file:")
        json_file = tmpdir_path / "test.json"
        json_file.write_text(json.dumps({"name": "Alice", "age": 30, "city": "NYC"}))

        file_source = FileDataSource(json_file)
        data = await file_source.fetch()
        print(f"   Data: {data}")

        # Example 2: Text file
        print("\n2. Reading text file:")
        text_file = tmpdir_path / "test.txt"
        text_file.write_text("Hello, World!\nThis is a test file.")

        text_source = FileDataSource(text_file)
        result = await text_source.fetch()
        print(f"   Content: {result['content'][:50]}...")
        print(f"   Line count: {result['line_count']}")

        # Example 3: Validation
        print("\n3. File validation:")
        is_valid = await file_source.validate_config()
        print(f"   File exists and readable: {is_valid}")

        missing_source = FileDataSource(tmpdir_path / "nonexistent.json")
        is_valid = await missing_source.validate_config()
        print(f"   Nonexistent file valid: {is_valid}")


async def demo_url_source():
    """Demonstrate URL data source."""
    print("\n" + "=" * 60)
    print("URL DATA SOURCE DEMO")
    print("=" * 60)

    url_source = URLDataSource()

    # Example 1: JSON endpoint
    print("\n1. Fetching JSON from public API:")
    ip_data = await url_source.fetch("https://api.ipify.org?format=json")
    print(f"   Your IP: {ip_data.get('ip')}")

    # Example 2: Plain text
    print("\n2. Fetching plain text:")
    text_result = await url_source.fetch("https://www.ietf.org/rfc/rfc2616.txt")
    print(f"   Content type: {text_result['content_type']}")
    print(f"   Content length: {text_result['content_length']} bytes")
    print(f"   First 100 chars: {text_result['content'][:100]}...")


async def demo_cache_and_stats():
    """Demonstrate caching and statistics."""
    print("\n" + "=" * 60)
    print("CACHE AND STATISTICS DEMO")
    print("=" * 60)

    api = APIDataSource(
        base_url="https://api.github.com",
        cache_enabled=True,
        cache_ttl_seconds=3600,
        rate_limit_per_minute=60,
    )

    # Make multiple requests
    print("\n1. Making multiple requests:")
    await api.fetch(endpoint="users/torvalds")
    await api.fetch(endpoint="users/gvanrossum")
    await api.fetch(endpoint="users/torvalds")  # Cached

    # Check cache stats
    stats = api.get_cache_stats()
    print(f"   Cache enabled: {stats['enabled']}")
    print(f"   Cached entries: {stats['size']}")
    print(f"   Cache TTL: {stats['ttl_seconds']}s")

    # Clear cache
    print("\n2. Clearing cache:")
    cleared = api.clear_cache()
    print(f"   Entries cleared: {cleared}")

    stats = api.get_cache_stats()
    print(f"   Cached entries after clear: {stats['size']}")


async def main():
    """Run all demos."""
    print("\n╔══════════════════════════════════════════════════════════╗")
    print("║  DATA SOURCE ABSTRACTION LAYER - USAGE EXAMPLES         ║")
    print("╚══════════════════════════════════════════════════════════╝")

    try:
        await demo_api_source()
        await demo_jina_source()
        await demo_file_source()
        await demo_url_source()
        await demo_cache_and_stats()

        print("\n" + "=" * 60)
        print("ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
