# CLI Commands Reference - EDGAR Platform

## Quick Reference

All commands are available through the `edgar-analyzer` CLI:

```bash
edgar-analyzer --help           # Show all commands
edgar-analyzer --cli            # Show help (bypass interactive mode)
```

---

## Project Management Commands

### Create Project

```bash
edgar-analyzer project create <name> [--template <template>]
```

**Description**: Create a new project from template

**Arguments**:
- `name`: Project name (alphanumeric, underscores, hyphens)

**Options**:
- `--template`: Template to use (default: minimal)
  - `weather`: OpenWeatherMap API example
  - `news_scraper`: Jina.ai web scraping example
  - `minimal`: Bare-bones starter template

**Example**:
```bash
edgar-analyzer project create my_weather_api --template weather
```

**Output**:
```
✅ Project created: my_weather_api
   Path: projects/my_weather_api

Next steps:
  1. Add examples to projects/my_weather_api/examples/
  2. Configure projects/my_weather_api/project.yaml
  3. Run: edgar-analyzer analyze-project projects/my_weather_api
```

---

### List Projects

```bash
edgar-analyzer project list [--format <format>]
```

**Description**: List all projects

**Options**:
- `--format`: Output format (default: table)
  - `table`: Human-readable table
  - `json`: JSON format for scripting

**Example (Table)**:
```bash
edgar-analyzer project list
```

**Output**:
```
Name                           Description                                        Path
------------------------------------------------------------------------------------------------------------------------
weather_api                    Extract weather data from OpenWeatherMap          projects/weather_api
employee_roster                Transform HR roster Excel data                     projects/employee_roster

Total: 2 projects
```

**Example (JSON)**:
```bash
edgar-analyzer project list --format json
```

**Output**:
```json
[
  {
    "name": "weather_api",
    "path": "projects/weather_api",
    "exists": true,
    "is_valid": true,
    "created_at": "2025-12-05T14:00:00",
    "modified_at": "2025-12-05T14:30:00",
    "metadata": {
      "description": "Extract weather data from OpenWeatherMap",
      "version": "1.0.0",
      "author": "Platform User",
      "tags": ["weather", "api"]
    }
  }
]
```

---

### Validate Project

```bash
edgar-analyzer project validate <name>
```

**Description**: Validate project configuration and structure

**Arguments**:
- `name`: Project name to validate

**Example**:
```bash
edgar-analyzer project validate my_api
```

**Output**:
```
============================================================
Validation Results for 'my_api'
============================================================

✅ Project is valid!

⚠️  Warnings (1):
  - No example files found in examples/

💡 Recommendations (1):
  - Provide at least 2-3 examples for better transformation quality
```

**Exit Codes**:
- `0`: Project is valid
- `1`: Project has errors

---

### Delete Project

```bash
edgar-analyzer project delete <name> [--yes]
```

**Description**: Delete a project

**Arguments**:
- `name`: Project name to delete

**Options**:
- `--yes, -y`: Skip confirmation prompt

**Example (with confirmation)**:
```bash
edgar-analyzer project delete old_project
```

**Output**:
```
⚠️  This will permanently delete project 'old_project'
   Path: projects/old_project

Are you sure? [y/N]: y
✅ Project 'old_project' deleted successfully
```

**Example (skip confirmation)**:
```bash
edgar-analyzer project delete old_project --yes
```

---

## Workflow Commands

### Analyze Project

```bash
edgar-analyzer analyze-project <project_path>
```

**Description**: Analyze project examples and detect transformation patterns

**Process**:
1. Loads project configuration from `project.yaml`
2. Parses example files (JSON) to detect patterns
3. Generates schema analysis (source → target)
4. Saves results to `analysis_results.json`

**Arguments**:
- `project_path`: Path to project directory

**Example**:
```bash
edgar-analyzer analyze-project projects/employee_roster
```

**Output**:
```
📊 Analyzing 3 examples...
✅ Analysis complete!

   Patterns detected: 6
   Source fields: 7
   Target fields: 6

   Results saved to: projects/employee_roster/analysis_results.json

Next step: edgar-analyzer generate-code projects/employee_roster
```

**Requirements**:
- Project must have `project.yaml`
- Project must have `examples/*.json` files
- Examples must have `input` and `output` fields

---

### Generate Code

```bash
edgar-analyzer generate-code <project_path> [--validate|--no-validate]
```

**Description**: Generate extraction code from analyzed patterns

**Process**:
1. Loads project configuration and examples
2. Uses Sonnet 4.5 to generate Python code
3. Generates: `extractor.py`, `models.py`, `test_extractor.py`
4. Validates generated code (syntax, type hints, tests)
5. Saves code to `src/` directory

**Arguments**:
- `project_path`: Path to project directory

**Options**:
- `--validate / --no-validate`: Validate generated code (default: validate)

**Example**:
```bash
edgar-analyzer generate-code projects/employee_roster
```

**Output**:
```
🔧 Generating code for Employee Roster Extraction...
✅ Code generation complete!

   Generated files:
     - extractor.py (245 lines)
     - models.py (128 lines)
     - tests.py (167 lines)

   Output directory: projects/employee_roster/src
   Quality score: 95%

Next step: edgar-analyzer run-extraction projects/employee_roster
```

**Requirements**:
- `OPENROUTER_API_KEY` environment variable must be set
- Project must have been analyzed first (or have examples)

**Environment Setup**:
```bash
export OPENROUTER_API_KEY=your_key_here
# Or add to .env.local:
echo "OPENROUTER_API_KEY=your_key_here" >> .env.local
```

---

### Run Extraction

```bash
edgar-analyzer run-extraction <project_path> [--output-format <format>]
```

**Description**: Run the generated extraction code

**Process**:
1. Dynamically imports generated `extractor.py`
2. Runs extraction on configured data sources
3. Saves results to `output/` directory

**Arguments**:
- `project_path`: Path to project directory

**Options**:
- `--output-format`: Output format (default: json)
  - `json`: JSON format
  - `csv`: CSV format
  - `excel`: Excel format (.xlsx)

**Example (JSON)**:
```bash
edgar-analyzer run-extraction projects/employee_roster
```

**Output**:
```
🚀 Running extraction for Employee Roster Extraction...
✅ Extraction complete! Results saved to projects/employee_roster/output/results.json

   Records extracted: 150
```

**Example (CSV)**:
```bash
edgar-analyzer run-extraction projects/employee_roster --output-format csv
```

**Requirements**:
- Code must have been generated first
- `src/extractor.py` must exist
- Data sources must be accessible

---

## Complete Workflow Example

Here's a complete end-to-end workflow:

```bash
# 1. Create project
edgar-analyzer project create weather_data --template weather

# 2. Add examples (manually)
# Edit projects/weather_data/examples/london.json
# Edit projects/weather_data/examples/tokyo.json
# Edit projects/weather_data/examples/paris.json

# 3. Configure project (optional)
# Edit projects/weather_data/project.yaml

# 4. Validate project
edgar-analyzer project validate weather_data

# 5. Analyze examples
edgar-analyzer analyze-project projects/weather_data

# 6. Generate code
export OPENROUTER_API_KEY=your_key_here
edgar-analyzer generate-code projects/weather_data

# 7. Run extraction
edgar-analyzer run-extraction projects/weather_data --output-format csv

# 8. Check results
cat projects/weather_data/output/results.csv
```

---

## Environment Variables

### Required

**OPENROUTER_API_KEY**
- Required for: `generate-code` command
- Get key from: https://openrouter.ai/
- Set via: `.env.local` or `export OPENROUTER_API_KEY=...`

### Optional

**EDGAR_ARTIFACTS_DIR**
- Purpose: External artifacts directory base path
- Default: `./projects` (in-repo)
- Example: `export EDGAR_ARTIFACTS_DIR=~/edgar_projects`
- Benefits: Clean repo, unlimited storage, shared access

**LOG_LEVEL**
- Purpose: Control logging verbosity
- Default: `INFO`
- Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

---

## Troubleshooting

### "OPENROUTER_API_KEY not set"
```bash
# Set in .env.local (recommended)
echo "OPENROUTER_API_KEY=your_key_here" >> .env.local

# Or export in shell
export OPENROUTER_API_KEY=your_key_here
```

### "project.yaml not found"
Ensure you're in the correct directory or provide absolute path:
```bash
edgar-analyzer analyze-project /absolute/path/to/project
```

### "No example files found"
Add at least 2-3 JSON examples:
```bash
# Create examples
mkdir -p projects/my_project/examples
cat > projects/my_project/examples/example1.json <<EOF
{
  "input": {"field": "value"},
  "output": {"transformed_field": "value"}
}
EOF
```

### "Validation errors for ProjectConfig"
Old projects may use simplified schema. Create new project for updated format:
```bash
edgar-analyzer project create my_new_project --template minimal
```

---

## Testing

Run the test suite to verify all commands:

```bash
./test_cli_commands.sh
```

**Expected Output**:
```
===============================================
EDGAR Platform CLI Commands Test Suite
===============================================

=== 1. Help Commands ===
✅ PASS - Main help
✅ PASS - Project group help
... (16 total tests)

===============================================
Test Results Summary
===============================================
Passed: 16
Failed: 0

✅ All tests passed!
```

---

## Related Documentation

- [Quick Start Guide](docs/guides/QUICK_START.md)
- [Excel Transform Guide](docs/guides/EXCEL_FILE_TRANSFORM.md)
- [PDF Transform Guide](docs/guides/PDF_FILE_TRANSFORM.md)
- [External Artifacts Guide](docs/guides/EXTERNAL_ARTIFACTS.md)
- [Platform API Reference](docs/api/PLATFORM_API.md)
- [ProjectManager API](docs/api/PROJECT_MANAGER_API.md)

---

## Implementation Details

**File**: `src/edgar_analyzer/main_cli.py`

**Services Used**:
- `extract_transform_platform.services.project_manager.ProjectManager`
- `edgar_analyzer.services.example_parser.ExampleParser`
- `edgar_analyzer.services.code_generator.CodeGeneratorService`

**Ticket**: 1M-631 (Critical Blocker - CLI Commands Implementation)

**Status**: ✅ **COMPLETE** - All commands implemented and tested
