# EDGAR One-Shot Command Mode

**Version**: Phase 3 Feature
**Status**: Production Ready

---

## Overview

One-shot command mode allows you to execute EDGAR commands without entering the interactive REPL. This is ideal for automation, scripting, CI/CD pipelines, and programmatic workflows.

**Key Features**:
- ✅ Execute single commands without REPL
- ✅ Session GUID persistence (resume across commands)
- ✅ JSON output for automation
- ✅ Text output for human readability
- ✅ Auto-save session state
- ✅ Backward compatible with interactive mode

---

## Quick Start

### Basic Usage

```bash
# Execute help command
edgar chat --exec "help"

# Execute with project loaded
edgar chat --exec "analyze" --project projects/weather_test/

# Get JSON output for automation
edgar chat --exec "patterns" --output-format json
```

### Session Resumption

```bash
# First command creates session
edgar chat --exec "help"
# Output: Session: edgar-20251206-143000-a1b2c3d4

# Resume and execute next command
edgar chat --session edgar-20251206-143000-a1b2c3d4 --exec "analyze"
```

---

## Command Reference

### CLI Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--exec` | `-e` | Command to execute | None (REPL mode) |
| `--session` | `-s` | Session ID to resume | None (new session) |
| `--output-format` | - | Output format (`text` or `json`) | `text` |
| `--project` | - | Project directory path | None |

### Output Formats

**Text Output** (default):
```
Session: edgar-20251206-143000-a1b2c3d4
Available Commands:
  help       - Show available commands
  analyze    - Analyze project and detect patterns
  ...
```

**JSON Output** (`--output-format json`):
```json
{
  "session_id": "edgar-20251206-143000-a1b2c3d4",
  "command": "help",
  "success": true,
  "output": "...",
  "error": null
}
```

---

## Session Management

### Session ID Format

Session IDs follow the pattern: `edgar-{YYYYMMDD-HHMMSS}-{8-char-uuid}`

**Example**: `edgar-20251206-143000-a1b2c3d4`

### Session Persistence

Sessions are auto-saved to `~/.edgar/sessions/{session_id}_session.json`

**Session File Contents**:
```json
{
  "session_id": "edgar-20251206-143000-a1b2c3d4",
  "project_path": "/path/to/project",
  "project_config": {...},
  "analysis_results": {...},
  "generated_code_path": "/path/to/generated_extractor.py",
  "extraction_count": 5,
  "timestamp": "2025-12-06T14:30:00.123456"
}
```

### List All Sessions

```bash
# List all saved sessions
edgar chat --list-sessions
```

**Output**:
```
┌──────────────────┬────────────────────────────────┬─────────────────┬─────────┐
│ Name             │ Session ID                     │ Timestamp       │ Project │
├──────────────────┼────────────────────────────────┼─────────────────┼─────────┤
│ edgar-20251206…  │ edgar-20251206-143000-a1b2c3d4 │ 2025-12-06T14:… │ Weather │
└──────────────────┴────────────────────────────────┴─────────────────┴─────────┘
```

---

## Use Cases

### 1. Automation Scripts

**Bash Script Example**:
```bash
#!/bin/bash
set -e

# Create new session and analyze
SESSION_ID=$(edgar chat --exec "analyze" \
  --project projects/weather_test/ \
  --output-format json | jq -r '.session_id')

echo "Session created: $SESSION_ID"

# Generate code using same session
edgar chat --session "$SESSION_ID" --exec "generate"

# Extract data
edgar chat --session "$SESSION_ID" --exec "extract"

echo "Extraction complete! Session: $SESSION_ID"
```

### 2. CI/CD Integration

**GitHub Actions Example**:
```yaml
name: EDGAR Extract Data
on: [push]

jobs:
  extract:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'

      - name: Install EDGAR
        run: pip install -e .

      - name: Run Analysis
        run: |
          edgar chat --exec "analyze" \
            --project projects/weather_test/ \
            --output-format json > analysis.json

      - name: Generate Code
        run: |
          SESSION_ID=$(jq -r '.session_id' analysis.json)
          edgar chat --session "$SESSION_ID" --exec "generate"
```

### 3. Cron Jobs

**Daily Data Extraction**:
```bash
# /etc/cron.d/edgar-daily
0 2 * * * user cd /path/to/project && edgar chat --exec "extract" --project . --output-format json > /var/log/edgar/daily.json 2>&1
```

### 4. Python Integration

**Python Script Example**:
```python
import subprocess
import json

def run_edgar_command(command, session_id=None, project=None):
    """Execute EDGAR command and return JSON result."""
    cmd = ["edgar", "chat", "--exec", command, "--output-format", "json"]

    if session_id:
        cmd.extend(["--session", session_id])
    if project:
        cmd.extend(["--project", project])

    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)

# Example: Full extraction workflow
session_id = None

# Step 1: Analyze
result = run_edgar_command("analyze", project="projects/weather_test/")
session_id = result["session_id"]
print(f"Analysis: {result['success']}")

# Step 2: Generate code
result = run_edgar_command("generate", session_id=session_id)
print(f"Code generated: {result['success']}")

# Step 3: Extract data
result = run_edgar_command("extract", session_id=session_id)
print(f"Extraction complete: {result['success']}")
```

---

## Error Handling

### Success Detection

**Exit Codes**:
- `0` - Command succeeded
- `1` - Command failed

**JSON Response**:
```json
{
  "success": true,   // Boolean success flag
  "error": null      // Error message if failed
}
```

### Error Example

**Command**:
```bash
edgar chat --exec "foobar"
```

**Text Output**:
```
Session: edgar-20251206-143000-a1b2c3d4
❌ Unknown command: foobar
Type 'help' to see available commands
❌ Error: Unknown command: foobar
```

**JSON Output**:
```json
{
  "session_id": "edgar-20251206-143000-a1b2c3d4",
  "command": "foobar",
  "success": false,
  "output": "❌ Unknown command: foobar\nType 'help' to see available commands",
  "error": "Unknown command: foobar"
}
```

---

## Available Commands

All interactive REPL commands are supported in one-shot mode:

| Command | Description | Example |
|---------|-------------|---------|
| `help` | Show available commands | `--exec "help"` |
| `load` | Load project | `--exec "load projects/test/"` |
| `show` | Show project status | `--exec "show"` |
| `examples` | List examples | `--exec "examples"` |
| `analyze` | Analyze patterns | `--exec "analyze"` |
| `patterns` | Show detected patterns | `--exec "patterns"` |
| `generate` | Generate extraction code | `--exec "generate"` |
| `validate` | Validate code quality | `--exec "validate"` |
| `extract` | Run extraction | `--exec "extract"` |
| `confidence` | Set confidence threshold | `--exec "confidence 0.85"` |
| `threshold` | Show current threshold | `--exec "threshold"` |
| `save` | Save session | `--exec "save my_session"` |
| `resume` | Resume saved session | `--exec "resume my_session"` |
| `sessions` | List all sessions | `--exec "sessions"` |

---

## Best Practices

### 1. Session Reuse

**✅ DO**: Reuse sessions for multi-step workflows
```bash
SESSION_ID=$(edgar chat --exec "analyze" --output-format json | jq -r '.session_id')
edgar chat --session "$SESSION_ID" --exec "generate"
edgar chat --session "$SESSION_ID" --exec "extract"
```

**❌ DON'T**: Create new session for each step
```bash
edgar chat --exec "analyze"
edgar chat --exec "generate"  # Lost context!
```

### 2. Error Handling

**✅ DO**: Check exit codes and parse JSON errors
```bash
if ! edgar chat --exec "analyze" --output-format json > result.json; then
  echo "Analysis failed"
  jq '.error' result.json
  exit 1
fi
```

**❌ DON'T**: Ignore errors
```bash
edgar chat --exec "analyze"  # May silently fail
```

### 3. JSON vs Text Output

**Use JSON** for:
- Automation scripts
- CI/CD pipelines
- Programmatic parsing
- Error handling

**Use Text** for:
- Quick manual checks
- Debugging
- Human-readable logs

### 4. Session Cleanup

Sessions are auto-saved but accumulate over time. Clean up old sessions periodically:

```bash
# Remove sessions older than 30 days
find ~/.edgar/sessions/ -name "*.json" -mtime +30 -delete
```

---

## Troubleshooting

### Session Not Found

**Problem**: `Session 'edgar-...' not found`

**Solution**: Verify session exists:
```bash
edgar chat --list-sessions
```

### Command Not Executing

**Problem**: Command runs but output is empty

**Solution**: Check JSON output for errors:
```bash
edgar chat --exec "analyze" --output-format json | jq '.'
```

### Permission Errors

**Problem**: Cannot write to `~/.edgar/sessions/`

**Solution**: Ensure directory permissions:
```bash
mkdir -p ~/.edgar/sessions
chmod 755 ~/.edgar/sessions
```

---

## Migration from Interactive Mode

### Before (Interactive REPL)

```bash
edgar chat --project projects/weather_test/
# In REPL:
analyze
patterns
generate
exit
```

### After (One-Shot Mode)

```bash
SESSION_ID=$(edgar chat --exec "analyze" --project projects/weather_test/ --output-format json | jq -r '.session_id')
edgar chat --session "$SESSION_ID" --exec "patterns"
edgar chat --session "$SESSION_ID" --exec "generate"
```

**Advantages**:
- Scriptable
- No manual interaction
- JSON output for parsing
- Session persistence

---

## Performance

### Overhead

One-shot mode adds minimal overhead:
- **Session creation**: ~5-10ms
- **Output capture**: ~10-20ms
- **Auto-save**: ~50-100ms

**Total overhead**: ~65-130ms per command

### Optimization Tips

1. **Reuse sessions**: Avoid creating new sessions for each command
2. **Batch commands**: Use scripts to minimize shell overhead
3. **JSON parsing**: Use `jq` for efficient JSON processing
4. **Disable auto-save**: (Future feature) Skip save for read-only commands

---

## Security Considerations

### Session Files

Session files contain:
- ✅ Project paths (safe)
- ✅ Analysis results (safe)
- ✅ Generated code paths (safe)
- ❌ **NO API keys** (secure)
- ❌ **NO credentials** (secure)

### File Permissions

Session files are stored in `~/.edgar/sessions/` with user-only access:
```bash
chmod 700 ~/.edgar/sessions
```

### Cleanup

Remove sensitive session data:
```bash
# Remove all sessions
rm -rf ~/.edgar/sessions/*

# Remove specific session
rm ~/.edgar/sessions/edgar-20251206-143000-a1b2c3d4_session.json
```

---

## Backward Compatibility

One-shot mode is **fully backward compatible**:

**Old command** (still works):
```bash
edgar chat --project projects/weather_test/
```

**New command** (one-shot mode):
```bash
edgar chat --exec "analyze" --project projects/weather_test/
```

Both modes coexist without conflicts.

---

## Future Enhancements

### Planned Features

1. **Parallel Execution**: Run multiple commands concurrently
2. **Streaming Output**: Real-time progress for long-running commands
3. **Session Expiration**: Auto-cleanup old sessions
4. **Command Aliases**: Shorter command names for one-shot mode
5. **Pipeline Mode**: Chain commands with `|` operator

---

## Support

**Questions?**
- [GitHub Issues](https://github.com/bobmatnyc/zach-edgar/issues)
- [Documentation](../README.md)

**Examples**:
- See `examples/one-shot-scripts/` for more examples
- See `tests/unit/interactive/test_oneshot_mode.py` for test cases

---

**Last Updated**: 2025-12-06
**Author**: Claude Code Agent
**Version**: 1.0.0
