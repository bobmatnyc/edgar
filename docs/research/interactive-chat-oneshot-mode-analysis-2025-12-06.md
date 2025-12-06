# Interactive Chat One-Shot Command Mode - Architecture Analysis

**Research Date**: 2025-12-06
**Status**: Architecture Analysis Complete
**Complexity**: Medium (Existing session infrastructure in place)

---

## Executive Summary

Analyzed the current EDGAR interactive session architecture to design a one-shot command execution mode. The system already has robust session persistence via `~/.edgar/sessions/` with JSON serialization, but lacks session GUID generation and programmatic command execution capabilities.

**Key Findings**:
- ✅ Session save/restore infrastructure exists (`cmd_save_session`, `cmd_resume_session`)
- ✅ Command registry with async handlers (`self.commands` dictionary)
- ✅ REPL command execution flow well-documented (lines 213-299)
- ❌ No session GUID generation (uses user-provided names like "last")
- ❌ No programmatic command execution outside REPL loop
- ❌ No `--exec` or similar CLI parameter exists

---

## 1. Current Session Persistence Mechanism

### Storage Location
```python
# Location: ~/.edgar/sessions/
session_dir = Path.home() / ".edgar" / "sessions"
session_file = session_dir / f"{session_name}_session.json"
```

**Example session files**:
- `~/.edgar/sessions/last_session.json` (default auto-saved on exit)
- `~/.edgar/sessions/my_analysis_session.json` (user-named via `save my_analysis`)

### Session Data Structure
```python
{
    "project_path": str,                # "/path/to/project"
    "project_config": dict,             # ProjectConfig.model_dump()
    "analysis_results": dict,           # Patterns, schemas, confidence scores
    "generated_code_path": str,         # Path to generated extractor
    "extraction_count": int,            # Number of extracted records
    "timestamp": str                    # ISO 8601 datetime
}
```

**Key Observation**: No session ID/GUID field exists. Sessions identified by filename only.

---

## 2. Session GUID Generation (Currently Missing)

### Current Naming System
- **User-driven**: `save [name]` command (default: "last")
- **Filename-based**: `{name}_session.json`
- **No uniqueness guarantee**: Users can overwrite sessions with same name

### Proposed GUID System
```python
import uuid
from datetime import datetime

def _generate_session_id() -> str:
    """Generate unique session identifier."""
    # Format: edgar-{timestamp}-{short-uuid}
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    short_uuid = str(uuid.uuid4())[:8]
    return f"edgar-{timestamp}-{short_uuid}"

# Example: "edgar-20251206-142530-a3f8d9c2"
```

**Benefits**:
- Collision-free session identification
- Sortable by timestamp
- Human-readable prefix
- Short enough for CLI args

---

## 3. Key Methods to Modify for One-Shot Execution

### 3.1 Session Management Methods

**Current Save Method** (Lines 1369-1395):
```python
async def cmd_save_session(self, args: str = "") -> None:
    session_name = args.strip() or "last"
    # ... saves to {session_name}_session.json
```

**Required Changes**:
1. Auto-generate GUID if no name provided
2. Return session ID for CLI output
3. Add session metadata (creator, purpose)

**Proposed Modification**:
```python
async def cmd_save_session(self, args: str = "") -> str:
    """Save session and return session ID."""
    session_name = args.strip() or self._generate_session_id()
    session_data = {
        "session_id": session_name,  # NEW
        "project_path": str(self.project_path) if self.project_path else None,
        # ... rest of data
    }
    # ... save logic
    return session_name  # Return for CLI output
```

### 3.2 Command Execution Flow

**Current REPL Loop** (Lines 213-299):
- Synchronous prompt loop: `user_input = await session.prompt_async("edgar> ")`
- Command parsing: Slash commands (`/analyze`) vs natural language
- Command dispatch: `await self.commands[command](args)`
- No exit condition except "exit" command or Ctrl+D

**Key Insight**: Commands already async and isolated. No REPL dependency for execution.

**Proposed One-Shot Executor**:
```python
async def execute_command_oneshot(self, command: str, args: str = "") -> dict:
    """Execute single command without REPL loop.

    Args:
        command: Command name (e.g., "analyze", "generate")
        args: Command arguments

    Returns:
        {
            "status": "success" | "error",
            "output": str,           # Captured console output
            "result": Any,           # Command return value
            "session_id": str        # Auto-generated or existing
        }
    """
    # Execute command
    if command not in self.commands:
        return {"status": "error", "output": f"Unknown command: {command}"}

    # Capture console output (redirect self.console)
    output_buffer = StringIO()
    old_console = self.console
    self.console = Console(file=output_buffer)

    try:
        result = await self.commands[command](args)
        output = output_buffer.getvalue()

        # Auto-save session after command
        session_id = await self.cmd_save_session("")  # Auto-generates GUID

        return {
            "status": "success",
            "output": output,
            "result": result,
            "session_id": session_id
        }
    except Exception as e:
        return {
            "status": "error",
            "output": output_buffer.getvalue(),
            "error": str(e)
        }
    finally:
        self.console = old_console
```

---

## 4. Proposed CLI Interface Changes

### 4.1 New CLI Parameters for `chat` Command

**Location**: `src/edgar_analyzer/main_cli.py` (Lines 864-965)

**Current Signature**:
```python
@cli.command()
@click.option('--project', type=click.Path(exists=True))
@click.option('--resume', type=str, default=None)
@click.option('--list-sessions', is_flag=True)
def chat(ctx, project, resume, list_sessions):
    # Starts REPL loop
    await session.start()
```

**Proposed Enhancement**:
```python
@cli.command()
@click.option('--project', type=click.Path(exists=True))
@click.option('--resume', type=str, default=None)
@click.option('--list-sessions', is_flag=True)
@click.option('--exec', type=str, help='Execute command and return session ID')
@click.option('--session', type=str, help='Session ID to resume for --exec')
@click.option('--output-format', type=click.Choice(['json', 'text']), default='text')
def chat(ctx, project, resume, list_sessions, exec, session, output_format):
    """
    Interactive chat mode with optional one-shot execution.

    Examples:
        # Interactive (REPL)
        edgar chat

        # One-shot: new session
        edgar chat --exec "analyze"
        # Output: Session: edgar-20251206-142530-a3f8d9c2, Status: complete

        # One-shot: resume existing session
        edgar chat --session edgar-20251206-142530-a3f8d9c2 --exec "generate"
    """
    if exec:
        # One-shot mode
        await _execute_oneshot(exec, session, project, output_format)
    else:
        # Interactive mode (existing behavior)
        await session.start()
```

### 4.2 One-Shot Execution Helper

```python
async def _execute_oneshot(command: str, session_id: str, project: str, output_format: str):
    """Execute single command in one-shot mode."""

    # Create or resume session
    if session_id:
        session = InteractiveExtractionSession()
        await session.cmd_resume_session(session_id)
    else:
        project_path = Path(project) if project else None
        session = InteractiveExtractionSession(project_path=project_path)

    # Execute command
    parts = command.split(maxsplit=1)
    cmd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    result = await session.execute_command_oneshot(cmd, args)

    # Output results
    if output_format == 'json':
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo(f"Session: {result['session_id']}")
        click.echo(f"Status: {result['status']}")
        if result['status'] == 'success':
            click.echo(f"\n{result['output']}")
        else:
            click.echo(f"Error: {result.get('error', 'Unknown error')}")
```

---

## 5. Command Execution Flow Analysis

### Current REPL Flow (Lines 213-266)

```
1. REPL Prompt
   └─> await session.prompt_async("edgar> ")

2. Input Parsing
   ├─> Slash command (/analyze)
   │   └─> Direct dispatch: self.commands[command](args)
   │
   ├─> Natural language ("What patterns did you detect?")
   │   └─> LLM parsing: _parse_natural_language()
   │       └─> Command mapping: patterns → cmd_show_patterns
   │
   └─> Traditional (analyze)
       └─> Direct dispatch: self.commands[command](args)

3. Command Execution
   └─> await self.commands[command](args)
       ├─> Returns None (most commands)
       └─> Returns "exit" (exit command only)

4. Loop Condition
   └─> if result == "exit": break
```

**Key Observations**:
- Commands are **async functions** with signature: `async def cmd_X(self, args: str) -> Optional[str]`
- Commands use `self.console.print()` for output (Rich Console)
- Commands modify session state directly (`self.analysis_results = ...`)
- No return values except "exit" string

---

## 6. Existing `--exec` or Similar Functionality

**Result**: ❌ **None found**

**Searched Locations**:
- `main_cli.py`: All CLI commands and options
- `session.py`: Interactive session class
- Click decorators: No `--exec`, `--execute`, `--command`, `--run` options

**Similar Features**:
1. `--resume <name>`: Restores session but still enters REPL
2. `--project <path>`: Auto-loads project but still enters REPL
3. `--list-sessions`: Displays sessions and exits (closest to one-shot)

**Gap**: No way to execute commands programmatically without interactive input.

---

## 7. Implementation Roadmap

### Phase 1: Session GUID Generation
**Files**: `src/edgar_analyzer/interactive/session.py`

1. Add `session_id` field to session data structure
2. Implement `_generate_session_id()` method
3. Modify `cmd_save_session()` to auto-generate GUID
4. Update `cmd_list_sessions()` to show session IDs

**Estimated Effort**: 2-3 hours

### Phase 2: One-Shot Command Executor
**Files**: `src/edgar_analyzer/interactive/session.py`

1. Implement `execute_command_oneshot()` method
2. Add console output capture mechanism
3. Add auto-save after command execution
4. Test with all existing commands

**Estimated Effort**: 4-5 hours

### Phase 3: CLI Integration
**Files**: `src/edgar_analyzer/main_cli.py`

1. Add `--exec` and `--session` options to `chat` command
2. Implement `_execute_oneshot()` helper function
3. Add JSON and text output formatters
4. Update help documentation

**Estimated Effort**: 3-4 hours

### Phase 4: Testing & Documentation
**Files**: `tests/unit/interactive/test_oneshot.py`, `docs/guides/`

1. Unit tests for session GUID generation
2. Integration tests for one-shot execution
3. CLI examples in user guide
4. Update CLAUDE.md with new features

**Estimated Effort**: 3-4 hours

**Total Estimated Effort**: 12-16 hours

---

## 8. Example Usage Scenarios

### Scenario 1: New Project Analysis
```bash
# Start new session, run analysis, get session ID
edgar chat --project projects/weather/ --exec "analyze"

# Output:
# Session: edgar-20251206-142530-a3f8d9c2
# Status: success
#
# ✅ Analysis complete
#
#    Patterns detected: 12
#    Input fields: 8
#    Output fields: 6
#    Examples analyzed: 3
```

### Scenario 2: Resume and Continue
```bash
# Resume session, generate code
edgar chat --session edgar-20251206-142530-a3f8d9c2 --exec "generate"

# Output:
# Session: edgar-20251206-142530-a3f8d9c2
# Status: success
#
# ✅ Code generation complete!
# Saved to: projects/weather/generated_extractor.py
```

### Scenario 3: Multi-Command Pipeline
```bash
# Create project (one-shot)
edgar project create fortune-100 --template minimal

# Copy data
cp ~/Downloads/fortune-100.xlsx projects/fortune-100/input/

# Analyze (one-shot)
SESSION=$(edgar chat --project projects/fortune-100/ --exec "analyze" | grep "Session:" | cut -d' ' -f2)

# Generate code (one-shot with session)
edgar chat --session $SESSION --exec "generate"

# Run extraction (one-shot with session)
edgar chat --session $SESSION --exec "extract"
```

### Scenario 4: JSON Output for Scripting
```bash
# Get JSON output for parsing
edgar chat --project projects/weather/ --exec "patterns" --output-format json

# Output:
{
  "session_id": "edgar-20251206-142530-a3f8d9c2",
  "status": "success",
  "output": "...",
  "result": null
}
```

---

## 9. Session Metadata Recommendations

**Current Session Data** (Lines 1374-1381):
```python
{
    "project_path": str,
    "project_config": dict,
    "analysis_results": dict,
    "generated_code_path": str,
    "extraction_count": int,
    "timestamp": str
}
```

**Proposed Enhancements**:
```python
{
    "session_id": str,                  # NEW: GUID
    "created_at": str,                  # NEW: ISO 8601 creation time
    "updated_at": str,                  # NEW: Last modification time
    "execution_mode": str,              # NEW: "interactive" | "oneshot"
    "command_history": [                # NEW: Executed commands
        {"command": "analyze", "timestamp": "...", "status": "success"},
        {"command": "generate", "timestamp": "...", "status": "success"}
    ],
    "project_path": str,
    "project_config": dict,
    "analysis_results": dict,
    "generated_code_path": str,
    "extraction_count": int,
    "timestamp": str                    # DEPRECATED: Use created_at
}
```

---

## 10. Risks and Mitigations

### Risk 1: Console Output Capture
**Issue**: Rich Console uses terminal control codes, may not serialize to JSON cleanly

**Mitigation**:
- Add `no_color=True` mode for one-shot execution
- Capture structured data separately from display output
- Return both "display" and "data" in result dict

### Risk 2: Session State Pollution
**Issue**: One-shot commands modify session state, may leave incomplete state

**Mitigation**:
- Auto-save after every successful command
- Add rollback mechanism for failed commands
- Clear distinction between "dirty" and "clean" sessions

### Risk 3: Command Dependencies
**Issue**: Some commands require prior steps (e.g., `generate` requires `analyze`)

**Mitigation**:
- Add validation in `execute_command_oneshot()` to check prerequisites
- Return clear error messages: "Command 'generate' requires analysis first"
- Optionally auto-execute dependencies (with user confirmation)

---

## 11. Related Features to Consider

### Auto-Retry on Failure
```bash
edgar chat --exec "analyze" --retry 3 --retry-delay 5
```

### Command Chaining
```bash
edgar chat --exec "analyze && generate && validate"
```

### Background Execution
```bash
edgar chat --exec "extract --async" --background
# Returns immediately with session ID
# Check status: edgar chat --session <id> --status
```

### Session Cleanup
```bash
edgar chat --cleanup-old-sessions --days 30
```

---

## 12. Testing Strategy

### Unit Tests
1. `test_generate_session_id()` - GUID uniqueness and format
2. `test_execute_command_oneshot()` - Command execution isolation
3. `test_console_output_capture()` - Rich Console capture
4. `test_session_auto_save()` - Auto-save after command

### Integration Tests
1. `test_oneshot_analyze()` - Full analysis workflow
2. `test_oneshot_resume()` - Resume and execute
3. `test_oneshot_error_handling()` - Failed command handling
4. `test_cli_exec_option()` - Click option parsing

### End-to-End Tests
1. `test_new_project_workflow()` - Create → Analyze → Generate → Extract
2. `test_resume_workflow()` - Multi-step resume across commands
3. `test_json_output()` - JSON serialization and parsing

---

## Conclusion

The EDGAR interactive session architecture is **well-structured for one-shot command integration**. Key infrastructure already exists (session persistence, command registry, async handlers), requiring only:

1. **Session GUID generation** (simple UUID-based approach)
2. **Programmatic command executor** (output capture + auto-save)
3. **CLI parameter additions** (`--exec`, `--session`, `--output-format`)

**Complexity Assessment**: **Medium** (12-16 hours estimated)

**Recommended Next Steps**:
1. Implement Phase 1 (GUID generation) as standalone PR
2. Test GUID approach with existing `save`/`resume` commands
3. Implement Phase 2 (one-shot executor) with unit tests
4. Integrate Phase 3 (CLI) after executor validation

---

## Appendix: Command Registry Reference

**Location**: Lines 142-162

```python
self.commands = {
    "help": self.cmd_help,
    "setup": self.cmd_setup,
    "config": self.cmd_setup,           # alias
    "load": self.cmd_load_project,
    "show": self.cmd_show,
    "analyze": self.cmd_analyze,
    "patterns": self.cmd_show_patterns,
    "examples": self.cmd_show_examples,
    "generate": self.cmd_generate_code,
    "validate": self.cmd_validate_code,
    "extract": self.cmd_run_extraction,
    "save": self.cmd_save_session,
    "resume": self.cmd_resume_session,
    "sessions": self.cmd_list_sessions,
    "confidence": self.cmd_set_confidence,
    "threshold": self.cmd_get_confidence,
    "chat": self.cmd_chat,
    "ask": self.cmd_chat,               # alias
    "exit": self.cmd_exit,
}
```

**Total Commands**: 19 (including aliases)
**All Async**: ✅ Yes
**All Testable**: ✅ Yes (no REPL dependency)

---

**Research Completed**: 2025-12-06 14:30 PST
**Researcher**: Claude Code (Research Agent)
**File Location**: `docs/research/interactive-chat-oneshot-mode-analysis-2025-12-06.md`
