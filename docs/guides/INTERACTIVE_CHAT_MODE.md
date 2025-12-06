# Interactive Chat Mode - User Guide

The EDGAR platform includes an **Auggie-style interactive chat mode** for iterative data extraction workflows. This guide covers all features and usage patterns.

## Quick Start

Start an interactive session:
```bash
edgar-analyzer chat --project projects/weather_test/
```

## Available Commands

### Project Management
- `load <path>` - Load project configuration
- `show` - Display current project status
- `examples` - List loaded examples with structure preview
- `save [name]` - Save session state (default: "last")
- `resume [name]` - Restore saved session (default: "last")
- `sessions` - List all saved sessions

### Analysis & Pattern Detection
- `analyze` - Analyze examples and detect transformation patterns
- `patterns` - Show detected patterns with confidence scores
- `confidence <0.0-1.0>` - Adjust confidence threshold and re-analyze
- `threshold` - Show current confidence threshold

### Code Generation & Execution
- `generate` - Generate Python extraction code from patterns
- `validate` - Validate generated code quality with ConstraintEnforcer
- `extract` - Execute generated code and show results

### Utilities
- `help` - Show all available commands
- `exit` - Exit session (auto-saves to "last")

## Natural Language Understanding

Ask questions in natural language:

```
edgar> What patterns did you detect?
→ Interpreted as: patterns

edgar> Show me the examples
→ Interpreted as: examples

edgar> Can you analyze the project?
→ Interpreted as: analyze
```

## Complete Workflow Example

```bash
# Start session
edgar-analyzer chat --project projects/employee_roster/

# Interactive workflow
edgar> show
┌────────────────────────┬─────────────────┐
│ Property               │ Value           │
├────────────────────────┼─────────────────┤
│ Name                   │ employee_roster │
│ Data Source            │ excel           │
│ Examples               │ 3               │
└────────────────────────┴─────────────────┘

edgar> analyze
⠋ Analyzing examples...
✅ Analysis complete
┌──────────────────┬───────┐
│ Patterns Detected│ 5     │
│ Input Fields     │ 7     │
│ Output Fields    │ 5     │
└──────────────────┴───────┘

edgar> patterns
┌──────────────────┬────────────┬──────────────────┬────────────┐
│ Type             │ Confidence │ Source → Target  │ Details    │
├──────────────────┼────────────┼──────────────────┼────────────┤
│ FIELD_MAPPING    │ 100.0%     │ emp_id → id      │ Direct     │
│ CONCATENATION    │ 95.0%      │ first+last →     │ String     │
│                  │            │ full_name        │ concat     │
│ TYPE_CONVERSION  │ 90.0%      │ salary → salary  │ int→float  │
└──────────────────┴────────────┴──────────────────┴────────────┘

edgar> generate
⠋ Generating extraction code...
✅ Code generation complete!
[Syntax-highlighted Python code preview]

edgar> validate
⠋ Validating generated code...
✅ Code validation passed!
┌──────────────────────┬───────┐
│ Valid                │ True  │
│ Total Violations     │ 0     │
└──────────────────────┴───────┘

edgar> extract
🚀 Running extraction...
✅ Extracted 100 records
┌─────┬───────────────┬──────────┐
│ id  │ full_name     │ salary   │
├─────┼───────────────┼──────────┤
│ 001 │ John Doe      │ 95000.0  │
│ 002 │ Jane Smith    │ 105000.0 │
└─────┴───────────────┴──────────┘

edgar> save my_work
✅ Session saved: my_work

edgar> exit
Session auto-saved
```

## Session Management

### Saving Sessions
```bash
edgar> save project_alpha
✅ Session saved: project_alpha
```

Sessions are stored in `~/.edgar/sessions/` as JSON files.

### Resuming Sessions
```bash
# From command line
edgar-analyzer chat --resume project_alpha

# Or from within session
edgar> resume project_alpha
✅ Session resumed: project_alpha
```

### Listing Sessions
```bash
# From command line
edgar-analyzer chat --list-sessions

# Or from within session
edgar> sessions
┌────────────────┬─────────────────────┬─────────────────┐
│ Name           │ Timestamp           │ Project         │
├────────────────┼─────────────────────┼─────────────────┤
│ project_alpha  │ 2025-12-06 10:30:00 │ employee_roster │
│ last           │ 2025-12-06 11:45:00 │ weather_test    │
└────────────────┴─────────────────────┴─────────────────┘
```

## Confidence Threshold Tuning

Adjust pattern detection sensitivity:

```bash
edgar> threshold
Current confidence threshold: 70.0%

edgar> confidence 0.85
✅ Confidence threshold: 70.0% → 85.0%
Re-analyzing with new threshold...
✅ Analysis complete

Pattern Changes:
┌────────────────┬────────┬───────┐
│ Metric         │ Before │ After │
├────────────────┼────────┼───────┤
│ Pattern Count  │ 5      │ 3     │
│ Threshold      │ 70.0%  │ 85.0% │
│ Change         │        │ -2    │
└────────────────┴────────┴───────┘
```

## Keyboard Shortcuts

- **Tab** - Auto-complete commands
- **Ctrl+R** - Search command history
- **Ctrl+C** - Cancel current input
- **Ctrl+D** or `exit` - Exit session

## Tips & Best Practices

1. **Save regularly**: Use `save <name>` for important milestones
2. **Start with low confidence**: Begin at 0.6-0.7 to see all patterns
3. **Validate before extract**: Always run `validate` after `generate`
4. **Use natural language**: Ask questions naturally for easier workflows
5. **Review patterns**: Check `patterns` before code generation

## Troubleshooting

### "No project loaded"
**Solution**: Run `load <path>` to load a project first

### "Run 'analyze' first"
**Solution**: Analysis must complete before code generation

### "Code validation failed"
**Solution**: Check pattern confidence and example quality

### Session not found
**Solution**: Use `sessions` to list available saved sessions

## Advanced Usage

### Batch Processing
```bash
# Create script: batch_extract.sh
#!/bin/bash

for project in projects/*/; do
    edgar-analyzer chat --project "$project" <<EOF
analyze
generate
validate
extract
save ${project##*/}
exit
EOF
done
```

### Automation Mode
```bash
# Non-interactive: pipe commands
echo -e "analyze\ngenerate\nextract\nexit" | edgar-analyzer chat --project projects/test/
```

## Natural Language Capabilities

The interactive chat mode understands common phrases and questions:

### Pattern Analysis
- "What patterns did you detect?"
- "Show me the patterns"
- "List all transformation patterns"

### Examples
- "Show me the examples"
- "What examples do we have?"
- "List the examples"

### Actions
- "Analyze the project"
- "Generate the code"
- "Run the extraction"
- "Validate the code"

### Configuration
- "What's the confidence threshold?"
- "Set confidence to 0.85"
- "Show current confidence"

## Performance

### Command Response Times
- Command dispatch: <1ms
- Pattern analysis: <2s for 10 examples
- Code generation: <3s
- Natural language parsing: <500ms
- Session save/restore: <100ms

### Scalability
- Tested with projects up to 100 examples
- History file handles 10,000+ commands
- Session files remain under 1MB

## Next Steps

- See [PATTERN_DETECTION.md](PATTERN_DETECTION.md) for pattern types
- See [EXCEL_FILE_TRANSFORM.md](EXCEL_FILE_TRANSFORM.md) for Excel workflows
- See [PROJECT_MANAGER_API.md](../api/PROJECT_MANAGER_API.md) for API reference

## Related Documentation

- [Quick Start Guide](QUICK_START.md) - Platform overview
- [CLI Usage](CLI_USAGE.md) - Traditional CLI commands
- [Platform Migration](PLATFORM_MIGRATION.md) - Migration guide
- [External Artifacts](EXTERNAL_ARTIFACTS.md) - Project storage
