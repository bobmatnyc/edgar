# Auto-Trigger Setup on Authentication Errors

**Date**: 2025-12-06
**File**: `src/edgar_analyzer/interactive/session.py`
**Issue**: Confusing 401 error messages when API key is invalid

## Problem

When users typed a message in interactive chat mode with an invalid API key, they saw this confusing error:

```
edgar> hello
⠹ Thinking...
⚠️  I encountered an issue: Error code: 401 - {'error': {'message': 'User not found.', 'code': 401}}
Try asking in a different way, or use 'help' to see available commands.
```

Users didn't understand what "User not found" meant or how to fix it.

## Solution

Modified error handling to automatically trigger the setup workflow when authentication errors are detected.

### Implementation Details

1. **Import AuthenticationError**: Added `from openai import AuthenticationError` to imports
2. **Enhanced cmd_chat() error handling**: Added specific handling for `AuthenticationError`
3. **Message-based detection**: Also checks for "401", "authentication", or "User not found" in error messages
4. **Propagated auth errors**: Auth errors in `_parse_natural_language()` now propagate to caller
5. **REPL loop handling**: Added auth error handling in main REPL loop

### Code Changes

#### Three Catch Points

1. **cmd_chat() method** (lines 577-600):
```python
except AuthenticationError as e:
    # Auth error - trigger setup flow
    self.console.print("\n[yellow]🔑 Your API key appears to be invalid or expired.[/yellow]")
    self.console.print("[dim]Let's set up a new one...[/dim]\n")
    await self.cmd_setup("")
```

2. **_parse_natural_language() method** (lines 680-683):
```python
except AuthenticationError as e:
    # Auth error during NL parsing - propagate to be handled by caller
    logger.warning("auth_error_during_nl_parsing", error=str(e))
    raise
```

3. **Main REPL loop** (lines 271-288):
```python
except AuthenticationError as e:
    # Auth error in REPL loop - trigger setup
    self.console.print("\n[yellow]🔑 Your API key appears to be invalid or expired.[/yellow]")
    self.console.print("[dim]Let's set up a new one...[/dim]\n")
    await self.cmd_setup("")
```

## User Experience

### Before (Confusing)
```
edgar> hello
⠹ Thinking...
⚠️  I encountered an issue: Error code: 401 - {'error': {'message': 'User not found.', 'code': 401}}
Try asking in a different way, or use 'help' to see available commands.
```

### After (Helpful)
```
edgar> hello
⠹ Thinking...

🔑 Your API key appears to be invalid or expired.
Let's set up a new one...

🔧 EDGAR Setup

To use AI features, you need an OpenRouter API key.
Get one at: https://openrouter.ai/keys

Enter your OpenRouter API key (or 'cancel'):
```

## Testing

Created comprehensive test suite in `test_auth_error_handling.py`:
- ✅ Test 1: AuthenticationError exception triggers setup
- ✅ Test 2: Error message with "401" triggers setup
- ✅ Test 3: Non-auth errors show generic message

All tests pass.

## Error Detection Strategy

The fix uses a two-level detection strategy:

1. **Exception Type**: Catches `openai.AuthenticationError` directly
2. **Message Content**: Checks for auth indicators in error message:
   - "401" (HTTP status code)
   - "authentication" (case-insensitive)
   - "User not found" (OpenRouter specific)

This ensures both OpenRouter-specific errors and generic 401 errors are caught.

## Benefits

1. **Better UX**: Users immediately understand the problem is with their API key
2. **Guided Fix**: Setup flow walks them through getting a new key
3. **No Dead Ends**: Users don't get stuck with cryptic error messages
4. **Progressive Disclosure**: Only shows setup when needed
5. **Resilient**: Handles both typed exceptions and message-based detection

## Related Files

- Source: `src/edgar_analyzer/interactive/session.py`
- Tests: `test_auth_error_handling.py`
- Related: `src/extract_transform_platform/ai/openrouter_client.py`
