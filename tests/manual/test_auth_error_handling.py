#!/usr/bin/env python3
"""
Manual test script for authentication error handling in interactive chat mode.

This script demonstrates that authentication errors automatically trigger the setup flow.

Test Scenarios:
1. AuthenticationError exception → triggers setup
2. Error message with "401" → triggers setup
3. Error message with "User not found" → triggers setup
4. Other errors → shows generic error message

Usage:
    # Test with invalid API key (will trigger setup)
    OPENROUTER_API_KEY=invalid python test_auth_error_handling.py

    # Test with valid API key (will work normally)
    python test_auth_error_handling.py
"""

import asyncio
from unittest.mock import MagicMock, patch

from openai import AuthenticationError

from edgar_analyzer.interactive.session import InteractiveExtractionSession


async def test_auth_error_exception():
    """Test that AuthenticationError exception triggers setup."""
    print("\n🧪 Test 1: AuthenticationError exception")
    print("=" * 60)

    session = InteractiveExtractionSession()

    # Mock the console to capture output
    mock_console = MagicMock()
    session.console = mock_console

    # Mock cmd_setup to avoid user input
    setup_called = False

    async def mock_setup(args):
        nonlocal setup_called
        setup_called = True
        print("✅ Setup flow was triggered!")

    session.cmd_setup = mock_setup

    # Mock OpenRouter client to raise AuthenticationError
    if session.openrouter_client:
        with patch.object(
            session.openrouter_client,
            "chat_completion",
            side_effect=AuthenticationError(
                message="User not found.",
                response=MagicMock(status_code=401),
                body={"error": {"message": "User not found.", "code": 401}},
            ),
        ):
            # Trigger the error
            await session.cmd_chat("hello")

    # Verify setup was called
    assert setup_called, "Setup should have been called for AuthenticationError"

    # Check console output
    console_calls = [str(call) for call in mock_console.print.call_args_list]
    print(f"\n📝 Console output ({len(console_calls)} messages):")
    for call in console_calls:
        if "API key" in call or "setup" in call.lower():
            print(f"  - {call[:100]}")

    print("✅ Test 1 PASSED: AuthenticationError triggers setup\n")


async def test_401_in_error_message():
    """Test that error message containing '401' triggers setup."""
    print("\n🧪 Test 2: Error message with '401'")
    print("=" * 60)

    session = InteractiveExtractionSession()

    # Mock the console
    mock_console = MagicMock()
    session.console = mock_console

    # Mock cmd_setup
    setup_called = False

    async def mock_setup(args):
        nonlocal setup_called
        setup_called = True
        print("✅ Setup flow was triggered!")

    session.cmd_setup = mock_setup

    # Mock OpenRouter client to raise generic error with 401 in message
    if session.openrouter_client:
        with patch.object(
            session.openrouter_client,
            "chat_completion",
            side_effect=Exception(
                "Error code: 401 - {'error': {'message': 'User not found.', 'code': 401}}"
            ),
        ):
            await session.cmd_chat("hello")

    # Verify setup was called
    assert setup_called, "Setup should have been called for 401 error"
    print("✅ Test 2 PASSED: 401 in error message triggers setup\n")


async def test_other_error():
    """Test that non-auth errors show generic message."""
    print("\n🧪 Test 3: Non-auth error")
    print("=" * 60)

    session = InteractiveExtractionSession()

    # Mock the console
    mock_console = MagicMock()
    session.console = mock_console

    # Mock cmd_setup - should NOT be called
    setup_called = False

    async def mock_setup(args):
        nonlocal setup_called
        setup_called = True

    session.cmd_setup = mock_setup

    # Mock OpenRouter client to raise non-auth error
    if session.openrouter_client:
        with patch.object(
            session.openrouter_client,
            "chat_completion",
            side_effect=Exception("Network timeout error"),
        ):
            await session.cmd_chat("hello")

    # Verify setup was NOT called
    assert not setup_called, "Setup should NOT be called for non-auth errors"

    # Check that generic error message was shown
    console_calls = [str(call) for call in mock_console.print.call_args_list]
    has_generic_error = any(
        "encountered an issue" in str(call) for call in console_calls
    )
    assert has_generic_error, "Should show generic error message"

    print("✅ Test 3 PASSED: Non-auth error shows generic message\n")


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Testing Authentication Error Handling")
    print("=" * 60)

    try:
        await test_auth_error_exception()
        await test_401_in_error_message()
        await test_other_error()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1

    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
