# One-Shot Mode Interactive Prompt Fix

## Problem

When running `edgar chat --exec "chat ..."` in one-shot mode, if the API key validation failed, the system would try to trigger an interactive setup prompt, which would fail with:

```
Do you want to update your API key? [y/n] (n):
🔑 Your API key appears to be invalid or expired.
Error executing command: EOF when reading a line
```

This broke non-TTY execution (automation, testing, CI/CD pipelines).

## Root Cause

The `cmd_chat()` method was calling `cmd_setup()` when it detected authentication errors. The `cmd_setup()` method uses `Prompt.ask()` from the Rich library, which requires a TTY (interactive terminal) to read user input. In one-shot mode, there's no TTY available, causing an `EOFError`.

## Solution

### 1. Added `_oneshot_mode` Flag

Added a new instance variable `self._oneshot_mode` to track when the session is executing in one-shot mode vs. interactive REPL mode.

**File**: `src/edgar_analyzer/interactive/session.py`

```python
def __init__(self, ...):
    # ... existing code ...
    self._oneshot_mode = False  # Flag for one-shot execution mode
```

### 2. Set Flag in `execute_command_oneshot()`

The flag is set at the beginning of one-shot execution and reset in the `finally` block to ensure proper cleanup.

```python
async def execute_command_oneshot(self, command_str: str) -> Dict[str, Any]:
    # Set one-shot mode flag to prevent interactive prompts
    self._oneshot_mode = True

    try:
        # ... command execution ...
    finally:
        # Reset one-shot mode flag
        self._oneshot_mode = False
```

### 3. Check Flag in `cmd_setup()`

The setup command now checks `_oneshot_mode` and returns an informative error message instead of trying to prompt:

```python
async def cmd_setup(self, args: str = "") -> None:
    # In one-shot mode, skip interactive prompts and return error message
    if self._oneshot_mode:
        self.console.print(
            "[red]❌ API key not configured[/red]\n"
            "[dim]Cannot run interactive setup in one-shot mode.[/dim]\n"
            "[dim]To configure API key, run: edgar /setup[/dim]\n"
            "[dim]Or set OPENROUTER_API_KEY environment variable.[/dim]"
        )
        return

    # ... normal interactive setup ...
```

### 4. Check Flag in `cmd_chat()` Error Handlers

Updated both exception handlers in `cmd_chat()` to check `_oneshot_mode` before calling `cmd_setup()`:

```python
except AuthenticationError as e:
    self.console.print("\n[yellow]🔑 Your API key appears to be invalid or expired.[/yellow]")
    if not self._test_mode and not self._oneshot_mode:  # Added check
        self.console.print("[dim]Let's set up a new one...[/dim]\n")
        await self.cmd_setup("")
    else:
        self.console.print("[dim]Run /setup to configure your API key.[/dim]")
```

## Testing

### Manual Test

```bash
# Without API key (should return error message, not crash)
OPENROUTER_API_KEY="" edgar chat --exec "chat hello" --output-format json
```

**Expected Output**:
```json
{
  "session_id": "edgar-20251206-175022-e91c8a55",
  "command": "chat hello",
  "success": true,
  "output": "⚠️  No valid API key. Run /setup to configure.\n",
  "error": null
}
```

✅ **No EOFError!**

### Automated Tests

Created comprehensive test suite in `tests/unit/interactive/test_oneshot_mode_no_prompts.py`:

- ✅ `test_oneshot_chat_no_api_key_no_prompt` - Chat command with missing API key
- ✅ `test_oneshot_setup_returns_error_message` - Setup command in one-shot mode
- ✅ `test_oneshot_mode_flag_lifecycle` - Flag is properly set and reset
- ✅ `test_oneshot_multiple_commands` - Multiple one-shot executions work correctly
- ✅ `test_regular_repl_mode_can_still_prompt` - Normal REPL mode not affected

All 5 tests pass.

## Impact

### Fixed
- ✅ One-shot mode no longer crashes with EOFError
- ✅ Informative error messages guide users to proper setup
- ✅ Non-interactive execution (CI/CD, scripts) works correctly
- ✅ JSON output format maintained for automation

### Preserved
- ✅ Interactive REPL mode still triggers setup prompts normally
- ✅ Test mode behavior unchanged
- ✅ All existing functionality preserved

## Files Modified

1. **`src/edgar_analyzer/interactive/session.py`**
   - Added `_oneshot_mode` flag initialization
   - Set/reset flag in `execute_command_oneshot()`
   - Added check in `cmd_setup()` to skip prompts
   - Added checks in `cmd_chat()` exception handlers

2. **`tests/unit/interactive/test_oneshot_mode_no_prompts.py`** (NEW)
   - Comprehensive test coverage for one-shot mode behavior

## Usage

### Before (Broken)
```bash
$ OPENROUTER_API_KEY="" edgar chat --exec "chat hello"
Do you want to update your API key? [y/n] (n):
Error executing command: EOF when reading a line
```

### After (Fixed)
```bash
$ OPENROUTER_API_KEY="" edgar chat --exec "chat hello" --output-format json
{
  "success": true,
  "output": "⚠️  No valid API key. Run /setup to configure.\n",
  "error": null
}
```

### Interactive Mode (Unchanged)
```bash
$ edgar
edgar> chat hello
🔑 Your API key appears to be invalid or expired.
Let's set up a new one...

🔧 EDGAR Setup
...
```

## Related Issues

- Fixes bug where one-shot mode breaks with missing/invalid API key
- Improves automation support for CI/CD pipelines
- Better error handling for non-interactive environments

## Future Improvements

Consider:
- Add `--no-prompt` global flag for explicit non-interactive mode
- Add environment variable `EDGAR_NONINTERACTIVE=1` for system-wide setting
- Improve error messages to distinguish between one-shot and test modes
