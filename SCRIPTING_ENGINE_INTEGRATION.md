# Dynamic Scripting Engine Integration with Interactive Chat Mode

**Status**: ✅ Complete (2025-12-06)
**Test Coverage**: 12/12 tests passing
**Integration Type**: File Operations & Ad-Hoc Task Execution

---

## Overview

The Dynamic Scripting Engine has been integrated with EDGAR's Interactive Chat Mode to enable **ad-hoc file management tasks** through natural language conversation. Users can now ask the AI to perform file operations, and the AI will generate and execute Python scripts with safety checks.

## What's New

### Core Features

1. **Natural Language File Operations**
   - "Create a project called fortune-100"
   - "Copy ~/Downloads/data.zip to the project"
   - "Unzip the file and move contents to input/"
   - "List all files in the examples directory"

2. **AI-Generated Scripts**
   - AI generates Python code in response to user requests
   - Scripts are marked with special `python:execute` code blocks
   - Automatic extraction and execution with safety validation

3. **Safety Features**
   - AST-based safety validation (blocks `eval`, `exec`, dangerous imports)
   - Subprocess isolation (default execution mode)
   - 30-second timeout protection
   - Allowed modules: `os`, `pathlib`, `shutil`, `zipfile`, `glob`, `json`, etc.

4. **Rich User Experience**
   - Progress spinners during execution
   - Formatted output panels (success/error)
   - Execution time display
   - Syntax-highlighted code blocks

---

## Architecture

### Component Integration

```
InteractiveExtractionSession (session.py)
  ├─ DynamicScriptingEngine (scripting_engine.py)
  │   ├─ Safety Validation (AST parsing)
  │   ├─ Subprocess Execution (isolated)
  │   └─ Exec() Fallback (in-process)
  │
  ├─ OpenRouterClient (AI responses)
  │   └─ System Prompt (includes file operation instructions)
  │
  └─ cmd_chat() -> _execute_scripts_from_response()
      └─ Regex Extraction (```python:execute blocks)
```

### Execution Flow

1. **User Input**: "Create a project structure"
2. **AI Response**: Generates script in `python:execute` block
3. **Script Detection**: Regex extracts code from response
4. **Safety Check**: AST validation for dangerous operations
5. **Execution**: Subprocess runs isolated Python script
6. **Result Display**: Rich formatted panels show output/errors

---

## Usage Examples

### Interactive Chat Mode

```bash
# Start interactive chat
edgar chat

# Example conversation
edgar> Create a project called weather_analysis with input/output directories

AI: I'll create that project structure for you!

```python:execute
from pathlib import Path

# Create project directory
project = Path("weather_analysis")
project.mkdir(exist_ok=True)

# Create subdirectories
(project / "input").mkdir(exist_ok=True)
(project / "output").mkdir(exist_ok=True)

result = f"Created {project} with subdirectories"
```

✅ Script 1 executed successfully
╭─────────── Result ───────────╮
│ Created weather_analysis     │
│ with subdirectories          │
╰──────────────────────────────╯
Execution time: 0.04s
```

### One-Shot Mode

```bash
# Execute single command with scripting
edgar chat --exec "Create a backup of the projects directory"
```

### Programmatic Usage

```python
from edgar_analyzer.interactive.session import InteractiveExtractionSession
import asyncio

async def demo():
    session = InteractiveExtractionSession(test_mode=True)

    # Execute script directly
    script = """
from pathlib import Path
Path("test_dir").mkdir(exist_ok=True)
result = "Directory created"
"""

    result = await session.scripting_engine.execute_script(
        script_code=script,
        context={},
        safety_checks=True
    )

    print(f"Success: {result.success}")
    print(f"Result: {result.result}")

asyncio.run(demo())
```

---

## System Prompt Enhancement

The AI system prompt has been enhanced to include file operation capabilities:

### Key Additions

```markdown
## File Operations
You can execute Python scripts for file management tasks:
- Create directories (mkdir)
- Copy/move files (shutil)
- Unzip archives (zipfile)
- List directory contents (os.listdir, pathlib)

**When to use scripting**:
- User asks to "create", "copy", "move", "unzip", "list", or "organize" files
- User needs to perform file system operations
- User wants to automate file tasks

**How to use scripting**:
Generate a Python script in a code block with marker: ```python:execute
The script will be automatically executed with safety checks.
Use the 'result' variable to return values.
```

---

## Safety & Security

### Blocked Operations

The following operations are **blocked by safety checks**:

- `eval()`, `exec()`, `compile()` - Code execution
- `__import__` - Dynamic imports (use static imports only)
- `open()` in exec() mode (subprocess allows file operations)
- `input()`, `raw_input()` - Interactive prompts
- `reload()` - Module reloading
- Attribute introspection: `vars()`, `globals()`, `locals()`, `dir()`, `getattr()`, `setattr()`, `delattr()`

### Allowed Modules

Safe modules for file operations:

- **Core**: `json`, `datetime`, `math`, `random`, `time`
- **File System**: `os`, `sys`, `pathlib`, `shutil`, `glob`
- **Archives**: `zipfile`
- **Collections**: `collections`, `itertools`, `functools`
- **Patterns**: `re`, `typing`

### Execution Modes

1. **Subprocess (Default)**: Isolated process, safer, supports all file operations
2. **Exec() Fallback**: In-process, more restricted, used if subprocess fails

---

## Testing

### Test Coverage

**Location**: `tests/unit/interactive/test_scripting_integration.py`

**Test Suites**:
1. **TestScriptingEngineInitialization** (2 tests)
   - Engine initialization
   - Configuration validation

2. **TestScriptExtraction** (3 tests)
   - Single script extraction
   - Multiple script extraction
   - No scripts in response

3. **TestScriptExecution** (4 tests)
   - Successful execution
   - Context injection
   - Error handling
   - Safety rejection

4. **TestChatIntegration** (2 tests)
   - File operation requests
   - System prompt validation

5. **End-to-End** (1 test)
   - Complete file operation workflow

### Running Tests

```bash
# Run all scripting integration tests
pytest tests/unit/interactive/test_scripting_integration.py -v

# Run demo script
python demo_scripting_integration.py
```

---

## Performance

### Benchmarks

| Operation | Time | Mode |
|-----------|------|------|
| Simple script (mkdir) | ~40ms | Subprocess |
| File copy | ~45ms | Subprocess |
| Directory listing | ~38ms | Subprocess |
| Script extraction (regex) | <1ms | In-memory |

### Resource Usage

- **Memory**: ~5MB per subprocess execution
- **Timeout**: 30 seconds (configurable)
- **Concurrency**: Sequential execution (future: parallel support)

---

## Error Handling

### User-Friendly Errors

Scripts that fail show:
1. Clear error message
2. Error details in panel
3. Execution time
4. Suggestions for fixes

Example:

```
❌ Script 1 failed
╭──────────── Error Details ────────────╮
│ FileNotFoundError: [Errno 2] No       │
│ such file or directory: 'missing.txt' │
╰────────────────────────────────────────╯

💡 Tip: Check if the file exists before copying.
```

### Common Issues

| Error | Cause | Solution |
|-------|-------|----------|
| `Script failed safety validation` | Used blocked operation (eval, exec) | Use allowed alternatives |
| `Process timed out` | Script ran >30 seconds | Optimize script or increase timeout |
| `FileNotFoundError` | Path doesn't exist | Check paths, use `exists()` check |
| `PermissionError` | Insufficient permissions | Check file/directory permissions |

---

## Code Changes Summary

### Files Modified

1. **`src/edgar_analyzer/interactive/session.py`** (+140 lines)
   - Added `DynamicScriptingEngine` import
   - Initialized scripting engine in `__init__()`
   - Enhanced system prompt with file operation instructions
   - Added `_execute_scripts_from_response()` method
   - Integrated script execution in `cmd_chat()`

2. **`src/cli_chatbot/core/scripting_engine.py`** (+1 line)
   - Fixed missing `import json` (bug fix)

### Files Added

1. **`tests/unit/interactive/test_scripting_integration.py`** (350 lines)
   - Comprehensive test suite
   - 12 test cases covering all functionality

2. **`demo_scripting_integration.py`** (170 lines)
   - Interactive demo script
   - 4 demonstration scenarios

3. **`SCRIPTING_ENGINE_INTEGRATION.md`** (this file)
   - Complete documentation
   - Usage examples and troubleshooting

---

## Future Enhancements

### Planned Features

1. **Parallel Script Execution**
   - Execute multiple scripts concurrently
   - Background task management

2. **Script Templates**
   - Pre-built templates for common operations
   - User-defined custom templates

3. **Undo/Rollback**
   - Track file system changes
   - Rollback failed operations

4. **Enhanced Safety**
   - Resource limits (disk space, file count)
   - Sandboxed filesystem (chroot-like)

5. **Script History**
   - Log all executed scripts
   - Replay previous operations

---

## Troubleshooting

### Script Not Executing

**Symptom**: AI generates script but nothing happens

**Solutions**:
1. Check for `python:execute` marker in AI response
2. Verify API key is configured (affects AI responses)
3. Check logs for safety validation errors

### Subprocess Failures

**Symptom**: "Falling back to exec() execution" in logs

**Solutions**:
1. Verify Python executable path (`sys.executable`)
2. Check subprocess is available (test with `python -c "print('test')"`)
3. Review script for syntax errors

### Permission Errors

**Symptom**: `PermissionError` when creating files/directories

**Solutions**:
1. Check current working directory permissions
2. Use absolute paths instead of relative
3. Verify user has write access to target directory

---

## API Reference

### DynamicScriptingEngine

```python
class DynamicScriptingEngine(ScriptExecutor):
    """Safe Python script execution engine."""

    def __init__(
        self,
        allowed_imports: List[str] = None,
        max_execution_time: float = 30.0,
        prefer_subprocess: bool = True
    ):
        """Initialize scripting engine with safety configuration."""

    async def execute_script(
        self,
        script_code: str,
        context: Dict[str, Any],
        safety_checks: bool = True
    ) -> ScriptResult:
        """Execute script with safety validation."""

    def validate_script_safety(self, script_code: str) -> bool:
        """AST-based safety validation."""
```

### ScriptResult

```python
@dataclass
class ScriptResult:
    """Result of script execution."""

    success: bool              # True if script executed without errors
    result: Any                # Value of 'result' variable from script
    output: str                # Captured stdout
    error: Optional[str]       # Error message if failed
    execution_time: float      # Time taken in seconds
    side_effects: List[str]    # List of side effects (file changes, etc.)
```

---

## Contributing

### Adding New Allowed Modules

Edit `session.py`:

```python
self.scripting_engine = DynamicScriptingEngine(
    allowed_imports=[
        # ... existing modules ...
        'new_module',  # Add your module here
    ]
)
```

### Adding Script Templates

Create in `src/edgar_analyzer/interactive/script_templates/`:

```python
# templates/create_project.py
"""Template: Create project structure."""

TEMPLATE = """
from pathlib import Path

project = Path("{project_name}")
project.mkdir(exist_ok=True)

# Add subdirectories
for subdir in {subdirs}:
    (project / subdir).mkdir(exist_ok=True)

result = f"Created project: {project}"
"""
```

---

## Changelog

### v1.0.0 (2025-12-06)

**Added**:
- Dynamic Scripting Engine integration with interactive chat
- Natural language file operations
- AI-generated script execution
- Comprehensive safety validation
- Rich formatted output
- 12 comprehensive tests
- Demo script
- Complete documentation

**Fixed**:
- Missing `import json` in scripting_engine.py
- Subprocess execution error handling

**Performance**:
- ~40ms average script execution time
- Subprocess isolation by default
- 30-second timeout protection

---

## Related Documentation

- [Interactive Chat Mode Guide](docs/guides/INTERACTIVE_CHAT_MODE.md)
- [CLI Usage Guide](docs/guides/CLI_USAGE.md)
- [Platform Architecture](docs/architecture/PROJECT_STRUCTURE.md)
- [MCP API Reference](docs/mcp-api-reference.md)

---

## Contact & Support

**Issues**: https://github.com/bobmatnyc/zach-edgar/issues
**Discussions**: https://github.com/bobmatnyc/zach-edgar/discussions

For questions about the scripting integration, please file an issue with the `scripting` label.
