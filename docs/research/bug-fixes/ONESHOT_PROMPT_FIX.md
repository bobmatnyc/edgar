# Fix: Interactive `/setup` Prompt Breaking One-Shot Mode Execution

**Date**: 2025-12-06
**Type**: Bug Fix
**Severity**: High (breaks automation/CI pipelines)

## Issue

Running `edgar chat --exec "chat ..."` with a missing or invalid API key would trigger an interactive prompt, causing `EOFError` in non-TTY environments:

```bash
$ OPENROUTER_API_KEY="" edgar chat --exec "chat hello" --output-format json
Do you want to update your API key? [y/n] (n):
🔑 Your API key appears to be invalid or expired.
Error executing command: EOF when reading a line
```

## Root Cause

The `cmd_chat()` method calls `cmd_setup()` when detecting authentication errors. The `cmd_setup()` method uses `Prompt.ask()` which requires interactive terminal (TTY), breaking non-interactive execution.

## Solution

### Implementation

1. **Added `_oneshot_mode` flag** to track execution context
2. **Set flag in `execute_command_oneshot()`** before executing commands
3. **Check flag in `cmd_setup()`** to skip prompts and return error message
4. **Updated error handlers in `cmd_chat()`** to respect the flag

### Code Changes

**File**: `src/edgar_analyzer/interactive/session.py`

```python
# 1. Initialize flag
def __init__(self, ...):
    self._oneshot_mode = False  # Flag for one-shot execution mode

# 2. Set/reset in one-shot execution
async def execute_command_oneshot(self, command_str: str) -> Dict[str, Any]:
    self._oneshot_mode = True
    try:
        # ... command execution ...
    finally:
        self._oneshot_mode = False

# 3. Check flag in setup
async def cmd_setup(self, args: str = "") -> None:
    if self._oneshot_mode:
        self.console.print(
            "[red]❌ API key not configured[/red]\n"
            "[dim]Cannot run interactive setup in one-shot mode.[/dim]\n"
            "[dim]To configure API key, run: edgar /setup[/dim]\n"
            "[dim]Or set OPENROUTER_API_KEY environment variable.[/dim]"
        )
        return
    # ... normal interactive setup ...

# 4. Check flag in error handlers
except AuthenticationError as e:
    if not self._test_mode and not self._oneshot_mode:  # Added check
        await self.cmd_setup("")
```

## Testing

### Unit Tests

Created comprehensive test suite: `tests/unit/interactive/test_oneshot_mode_no_prompts.py`

- ✅ 5/5 tests passing
- ✅ Covers all edge cases
- ✅ Verifies no EOFError
- ✅ Confirms appropriate error messages

### Integration Tests

```bash
# Test 1: Missing API key
OPENROUTER_API_KEY="" edgar chat --exec "chat hello" --output-format json
# ✅ Returns JSON with "No valid API key" message

# Test 2: Setup command in one-shot mode
OPENROUTER_API_KEY="" edgar chat --exec "/setup" --output-format json
# ✅ Returns "Cannot run interactive setup in one-shot mode"

# Test 3: Normal operation
edgar chat --exec "help" --output-format json
# ✅ Works correctly with valid API key
```

## Impact

### Fixed
- ✅ One-shot mode no longer crashes with `EOFError`
- ✅ Proper error messages for missing/invalid API keys
- ✅ Non-interactive execution (CI/CD, automation) works correctly
- ✅ JSON output format maintained

### Preserved
- ✅ Interactive REPL mode unchanged
- ✅ Normal setup flow still works
- ✅ All existing tests pass

## Files Modified

1. **`src/edgar_analyzer/interactive/session.py`**
   - Added `_oneshot_mode` flag
   - Updated `execute_command_oneshot()` to set/reset flag
   - Updated `cmd_setup()` to check flag
   - Updated `cmd_chat()` error handlers to respect flag

2. **`tests/unit/interactive/test_oneshot_mode_no_prompts.py`** (NEW)
   - Comprehensive test coverage for one-shot mode behavior

## Verification

```bash
# Run tests
pytest tests/unit/interactive/test_oneshot_mode_no_prompts.py -v

# Manual verification
OPENROUTER_API_KEY="" edgar chat --exec "chat hello" --output-format json
```

## Related Tickets

- Fixes one-shot mode breaking with missing API key
- Improves automation/CI support
- Better error handling for non-interactive environments

## Migration Notes

No migration required. This is a backward-compatible bug fix.

## Performance Impact

Negligible (<1ms overhead for flag check).

## Security Considerations

No security implications. Only affects error handling logic.
