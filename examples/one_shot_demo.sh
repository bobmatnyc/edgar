#!/bin/bash
#
# EDGAR One-Shot Command Mode Demo
#
# This script demonstrates the new one-shot command execution mode
# with session GUID persistence for automation and scripting.
#
# Usage: ./examples/one_shot_demo.sh

set -e  # Exit on error

echo "=================================================="
echo "EDGAR One-Shot Command Mode Demo"
echo "=================================================="
echo ""

# 1. Execute help command
echo "1. Executing 'help' command (text output):"
echo "---"
python -m edgar_analyzer chat --exec "help" | head -10
echo "..."
echo ""

# 2. Execute with JSON output
echo "2. Executing 'sessions' command (JSON output):"
echo "---"
SESSION_JSON=$(python -m edgar_analyzer chat --exec "sessions" --output-format json)
echo "$SESSION_JSON" | python3 -m json.tool | head -15
echo "..."
echo ""

# 3. Extract session ID from JSON
echo "3. Extracting session ID from JSON response:"
echo "---"
SESSION_ID=$(echo "$SESSION_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin)['session_id'])")
echo "Session ID: $SESSION_ID"
echo ""

# 4. Resume session and execute another command
echo "4. Resuming session and executing 'threshold' command:"
echo "---"
python -m edgar_analyzer chat --session "$SESSION_ID" --exec "threshold"
echo ""

# 5. List all saved sessions
echo "5. Listing all saved sessions:"
echo "---"
python -m edgar_analyzer chat --list-sessions | head -15
echo "..."
echo ""

# 6. Show session file
echo "6. Session file contents:"
echo "---"
SESSION_FILE=~/.edgar/sessions/${SESSION_ID}_session.json
if [ -f "$SESSION_FILE" ]; then
    echo "File: $SESSION_FILE"
    cat "$SESSION_FILE" | python3 -m json.tool | head -12
    echo "..."
else
    echo "Session file not found!"
fi
echo ""

# 7. Demonstrate error handling
echo "7. Testing error handling (unknown command):"
echo "---"
if python -m edgar_analyzer chat --exec "foobar" --output-format json 2>/dev/null; then
    echo "ERROR: Command should have failed!"
    exit 1
else
    echo "✓ Command failed as expected (exit code $?)"
fi
echo ""

echo "=================================================="
echo "Demo Complete!"
echo "=================================================="
echo ""
echo "Key Takeaways:"
echo "  ✓ Session GUIDs enable stateful workflows"
echo "  ✓ JSON output supports automation"
echo "  ✓ Sessions persist across commands"
echo "  ✓ Error handling works correctly"
echo ""
echo "See docs/guides/ONE_SHOT_MODE.md for full documentation"
