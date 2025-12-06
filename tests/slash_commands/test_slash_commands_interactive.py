#!/usr/bin/env python3
"""
Interactive test for slash commands.

Run this to manually test slash command behavior in a real session.
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from edgar_analyzer.interactive.session import InteractiveExtractionSession


async def simulate_repl_input(session, test_inputs):
    """Simulate REPL loop with test inputs."""

    print("\n" + "=" * 70)
    print("SIMULATING INTERACTIVE SESSION WITH SLASH COMMANDS")
    print("=" * 70 + "\n")

    for user_input in test_inputs:
        print(f"User input: '{user_input}'")
        print("-" * 70)

        if not user_input:
            print("  → (empty input, skipped)\n")
            continue

        # Simulate the REPL logic
        if user_input.startswith("/"):
            # System command - direct routing (bypass NL parsing)
            parts = user_input[1:].split(maxsplit=1)
            command = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""

            print(f"  🔧 Detected slash command: /{command}")

            # Execute command directly
            if command in session.commands:
                print(f"  ✅ Executing command: {command}('{args}')")
                if command == "help":
                    await session.cmd_help(args)
                elif command == "exit":
                    result = await session.cmd_exit(args)
                    print(f"  🚪 Exit signal received: {result}")
                    break
                else:
                    print(f"  ➡️  Would execute: {command} command")
            else:
                # Unknown slash command - show error (don't route to AI)
                print(f"  ❌ Unknown command: /{command}")
                print(f"  💬 Shows error (NOT routed to AI)")
                session.console.print(f"[red]❌ Unknown command: /{command}[/red]")
                session.console.print(
                    "[dim]Type '/help' to see available commands[/dim]"
                )
        else:
            # Check if input looks like natural language
            word_count = len(user_input.split())
            is_natural = (
                word_count > 3
                or "?" in user_input
                or (user_input and user_input[0].isupper())
            )

            if is_natural:
                print(f"  🗣️  Natural language detected")
                print(f"  ➡️  Would route to AI chat: '{user_input}'")
            else:
                # Traditional command parsing
                parts = user_input.split(maxsplit=1)
                command = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""

                if command in session.commands:
                    print(f"  ✅ Traditional command: {command}('{args}')")
                    if command == "help":
                        await session.cmd_help(args)
                    elif command == "exit":
                        result = await session.cmd_exit(args)
                        print(f"  🚪 Exit signal received: {result}")
                        break
                else:
                    print(f"  🗣️  Unknown command → routes to AI chat")

        print()


async def main():
    """Run interactive simulation."""

    # Create session (suppress some logs)
    import logging

    logging.getLogger("structlog").setLevel(logging.WARNING)

    session = InteractiveExtractionSession()

    # Test inputs covering all scenarios
    test_inputs = [
        # Slash commands
        "/help",
        "/exit",
        "/load projects/test/",
        "/analyze",
        "/patterns",
        "/unknown",  # Unknown slash command
        # Traditional commands (backward compat)
        "help",
        "analyze",
        "patterns",
        # Natural language
        "What patterns did you detect?",
        "Show me the examples",
        "Hello, how are you?",
        # Edge cases
        "",  # Empty
        "/",  # Just slash
    ]

    await simulate_repl_input(session, test_inputs)

    print("\n" + "=" * 70)
    print("✅ SIMULATION COMPLETE")
    print("=" * 70 + "\n")

    print("Summary of slash command behavior:")
    print("  • /command → Direct routing to system command")
    print("  • /unknown → Shows error, NOT routed to AI")
    print("  • command → Traditional routing (backward compatible)")
    print("  • Natural text → Routed to AI chat")
    print()


if __name__ == "__main__":
    asyncio.run(main())
