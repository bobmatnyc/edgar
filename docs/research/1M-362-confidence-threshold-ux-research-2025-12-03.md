# Interactive Confidence Threshold Selection UX - Research Document

**Research Date**: December 3, 2025
**Ticket**: [1M-362 - Add Interactive Confidence Threshold Selection UX](https://linear.app/1m-hyperdev/issue/1M-362/add-interactive-confidence-threshold-selection-ux)
**Researcher**: Research Agent
**Status**: Complete Requirements Analysis
**Document Version**: 1.0

---

## Executive Summary

This research document provides comprehensive analysis of requirements, technical design, and implementation strategy for ticket 1M-362: Interactive Confidence Threshold Selection UX. The feature enables users to select confidence thresholds during example-driven pattern learning workflows, replacing the current hardcoded approach.

### Key Findings

1. **Current State**: Confidence scoring exists (lines 119-122, 427-440 in `patterns.py`) with hardcoded thresholds (0.9 = high, 0.7 = medium)
2. **Integration Points**: ExampleParser → AIConfig → PromptTemplates → CodeGenerator → CLI
3. **User Preference**: User wants runtime prompting (from Phase 2 preferences: "Confidence threshold: User choice (prompted)")
4. **Implementation Complexity**: Medium (1 day estimate accurate) - requires CLI integration, config persistence, and pattern filtering
5. **Risk**: Low - existing infrastructure supports confidence scoring, only needs user-facing UI

### Recommended Approach

**Phase 1 (MVP)**: CLI prompt with Rich UI during `analyze-project` command
**Phase 2 (Enhancement)**: Confidence review screen before code generation
**Phase 3 (Polish)**: Project-level config persistence and preset management

---

## Table of Contents

1. [Ticket Requirements Analysis](#1-ticket-requirements-analysis)
2. [Current Implementation Review](#2-current-implementation-review)
3. [User Workflow Analysis](#3-user-workflow-analysis)
4. [Technical Architecture](#4-technical-architecture)
5. [UX Design Specifications](#5-ux-design-specifications)
6. [Implementation Plan](#6-implementation-plan)
7. [Risk Analysis](#7-risk-analysis)
8. [Success Criteria](#8-success-criteria)
9. [Appendices](#9-appendices)

---

## 1. Ticket Requirements Analysis

### 1.1 Ticket Overview

**Ticket ID**: 1M-362
**Title**: Add Interactive Confidence Threshold Selection UX
**Priority**: Medium
**Estimated Effort**: 1 day
**Tags**: user-preference, terminal-ui, parser, chatbot
**Parent Epic**: 4a248615-f1dd-4669-9f61-edec2d2355ac (EDGAR → General-Purpose Extract & Transform Platform)

### 1.2 Description

> Prompt user to select confidence threshold during pattern learning workflows (user preference: runtime choice vs hardcoded).

**User Preference Context**:
- **Current**: Hardcoded threshold (likely 0.7 based on codebase)
- **Preferred**: User prompted for threshold during workflow
- **Options**: Conservative (0.8), Balanced (0.7), Aggressive (0.6), Custom

### 1.3 Acceptance Criteria

The ticket specifies 7 acceptance criteria:

| # | Criterion | Status | Notes |
|---|-----------|--------|-------|
| 1 | CLI prompt for confidence threshold selection | ❌ Not Started | Core requirement |
| 2 | Preset options: Conservative (0.8), Balanced (0.7), Aggressive (0.6), Custom | ❌ Not Started | Rich menu required |
| 3 | Threshold applied to example parser pattern matching | ⚠️ Partial | Infrastructure exists, needs integration |
| 4 | Confidence scores displayed with color-coded feedback (high/medium/low) | ❌ Not Started | Rich formatting |
| 5 | User can review low-confidence patterns before applying | ❌ Not Started | New feature |
| 6 | Setting persisted to project configuration (optional) | ❌ Not Started | Config file update |
| 7 | Documentation updated with confidence threshold guide | ❌ Not Started | User documentation |

### 1.4 Implementation Notes from Ticket

> Integrate with the CLI chatbot controller to add interactive prompting during pattern learning workflows. Follow the existing prompt pattern used in project creation.

**Key Insights**:
- Reference existing pattern: project creation workflow
- Use Rich prompt library (already imported in setup.py)
- Integration point: CLI chatbot controller

---

## 2. Current Implementation Review

### 2.1 Confidence Scoring Infrastructure

#### 2.1.1 Pattern Model (extract_transform_platform/models/patterns.py)

**Confidence Field** (Lines 142-147):
```python
confidence: float = Field(
    ...,
    ge=0.0,
    le=1.0,
    description="Confidence score (0.0 to 1.0) based on example consistency"
)
```

**Confidence Level Property** (Lines 198-206):
```python
@property
def confidence_level(self) -> str:
    """Get human-readable confidence level."""
    if self.confidence >= 0.9:
        return "high"
    elif self.confidence >= 0.7:
        return "medium"
    else:
        return "low"
```

**Hardcoded Thresholds Identified**:
- **High**: ≥ 0.9 (90%)
- **Medium**: 0.7-0.89 (70-89%)
- **Low**: < 0.7 (< 70%)

#### 2.1.2 ParsedExamples Pattern Filtering (Lines 427-440)

```python
@property
def high_confidence_patterns(self) -> List[Pattern]:
    """Get patterns with confidence >= 0.9."""
    return [p for p in self.patterns if p.confidence >= 0.9]

@property
def medium_confidence_patterns(self) -> List[Pattern]:
    """Get patterns with 0.7 <= confidence < 0.9."""
    return [p for p in self.patterns if 0.7 <= p.confidence < 0.9]

@property
def low_confidence_patterns(self) -> List[Pattern]:
    """Get patterns with confidence < 0.7."""
    return [p for p in self.patterns if p.confidence < 0.7]
```

**Analysis**: These properties use hardcoded thresholds (0.9, 0.7). Need to make configurable.

#### 2.1.3 AIConfig Confidence Threshold Support (Lines 74-79)

```python
confidence_threshold: Optional[float] = Field(
    default=None,
    description="Minimum confidence threshold for pattern detection (0.0-1.0)",
    ge=0.0,
    le=1.0
)
```

**Status**: ✅ **Already Supported** - AIConfig has `confidence_threshold` field
**Current Behavior**: Reads from `AI_CONFIDENCE_THRESHOLD` environment variable
**Enhancement Needed**: Runtime user prompt to set this value

#### 2.1.4 PromptTemplates Confidence Integration (Lines 303-343)

```python
def render_pattern_detection(
    self,
    input_examples: List[Dict[str, Any]],
    output_examples: List[Dict[str, Any]],
    confidence_threshold: Optional[float] = None
) -> str:
    # ...
    if confidence_threshold is not None:
        prompt += f"\n\n**Minimum Confidence Threshold**: {confidence_threshold}\n"
        prompt += "Only include patterns with confidence >= this threshold.\n"
```

**Status**: ✅ **Already Supported** - PromptTemplates accepts `confidence_threshold` parameter
**Enhancement Needed**: Pass user-selected threshold through the call chain

### 2.2 ExampleParser Confidence Calculation

#### 2.2.1 Pattern Detection Logic (Lines 138-174)

**Key Function**: `identify_patterns(self, examples: List[ExampleConfig]) -> List[Pattern]`

**Confidence Calculation Method**: Based on consistency across examples
- Pattern applies to all examples → confidence = 1.0
- Pattern applies to subset → confidence = matches / total_examples

**Example** (Lines 243-265):
```python
def test_pattern_confidence_calculation(self, parser):
    """Test confidence score calculation."""
    # Pattern that works for 2 out of 3 examples
    examples = [
        ExampleConfig(input={"temp": 15.5}, output={"temperature": 15.5}),
        ExampleConfig(input={"temp": 22.3}, output={"temperature": 22.3}),
        ExampleConfig(input={"humidity": 80}, output={"temperature": None}),  # Inconsistent
    ]

    parsed = parser.parse_examples(examples)
    pattern = parsed.patterns[0]

    # Confidence should be 2/3 ≈ 0.67
    assert 0.65 <= pattern.confidence <= 0.70
```

**Insight**: Confidence scoring is **automatic** and **data-driven** - no manual configuration needed during pattern detection. User threshold filters patterns **after** detection.

### 2.3 Existing Rich Prompt Patterns

#### 2.3.1 Setup Command Interactive Wizard (setup.py)

**Pattern Found**: Lines 98-102
```python
value = Prompt.ask(
    f"Enter {display_name}",
    password=(key_name != "edgar"),
    default=current_config.get(key_name, "")
)
```

**Also Uses**: `Confirm.ask()` for boolean questions (Line 108)
```python
if updates and Confirm.ask("\nValidate API keys?", default=True):
    _validate_keys(updates)
```

**Rich Imports** (Line 10):
```python
from rich.prompt import Prompt, Confirm
```

**Missing**: `IntPrompt` or custom menu selection (need to add)

#### 2.3.2 Rich Console Features Available

From `setup.py` usage:
- ✅ `Console` - Rich console formatting
- ✅ `Table` - Tabular display (Line 165-186)
- ✅ `Prompt.ask()` - Text input with defaults
- ✅ `Confirm.ask()` - Boolean yes/no prompts
- ✅ Color formatting: `[green]`, `[yellow]`, `[red]`, `[cyan]`, `[dim]`, `[bold]`

**Missing for Menu Selection**:
- ❌ Need to add: numbered menu selection or `questionary` library
- ❌ Alternative: Use Prompt.ask with validation

### 2.4 Project Configuration Structure

#### 2.4.1 weather_api/project.yaml Example (Lines 1-100)

```yaml
project:
  name: weather_api_extractor
  description: Extract current weather data from OpenWeatherMap API
  version: 1.0.0
  author: Platform MVP Team
  tags:
    - weather
    - api
    - mvp

data_sources:
  - type: api
    name: openweathermap
    endpoint: https://api.openweathermap.org/data/2.5/weather
    # ... auth, cache, rate_limit config

examples:
  - input: {...}
    output: {...}
  # ... more examples
```

**Missing**: No `confidence_threshold` field in current schema
**Enhancement Needed**: Add optional `confidence_threshold` field to project YAML

---

## 3. User Workflow Analysis

### 3.1 Current Example-Driven Workflow

**Step 1**: Create project
```bash
edgar-analyzer project create my-api --template weather
```

**Step 2**: Add examples (manual file editing)
```bash
# User edits: projects/my-api/examples/example1.yaml
```

**Step 3**: Analyze project (pattern detection)
```bash
edgar-analyzer analyze-project projects/my-api/
```
**Missing**: ❌ **No confidence threshold prompt here**

**Step 4**: Generate code
```bash
edgar-analyzer generate-code projects/my-api/
```

**Step 5**: Run extraction
```bash
edgar-analyzer run-extraction projects/my-api/
```

### 3.2 Proposed Workflow with Confidence Threshold

**Step 1**: Create project (unchanged)
```bash
edgar-analyzer project create my-api --template weather
```

**Step 2**: Add examples (unchanged)
```bash
# User edits examples
```

**Step 3**: Analyze project **WITH confidence threshold prompt**
```bash
edgar-analyzer analyze-project projects/my-api/

# NEW PROMPT:
┌─────────────────────────────────────────────────────────────────┐
│ Pattern Detection Complete - Select Confidence Threshold        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Found 5 patterns:                                               │
│   • 3 high confidence (≥ 0.9)                                   │
│   • 1 medium confidence (0.7-0.89)                              │
│   • 1 low confidence (< 0.7)                                    │
│                                                                 │
│ Select minimum confidence threshold:                            │
│   [1] Conservative (0.8) - Only high confidence patterns        │
│   [2] Balanced (0.7)     - High + medium patterns (recommended)│
│   [3] Aggressive (0.6)   - All patterns including low          │
│   [4] Custom             - Enter custom threshold (0.0-1.0)    │
│                                                                 │
│ Choice [1-4]:                                                   │
└─────────────────────────────────────────────────────────────────┘
```

**Step 4**: Review filtered patterns (NEW)
```bash
# After selection, show filtered results:
┌─────────────────────────────────────────────────────────────────┐
│ Patterns Included (threshold: 0.7)                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ✅ city (field_mapping) - Confidence: 1.0 (high)                │
│ ✅ temperature_c (field_extraction) - Confidence: 0.95 (high)   │
│ ✅ conditions (array_first) - Confidence: 0.9 (high)            │
│ ✅ humidity_percent (field_mapping) - Confidence: 0.8 (medium)  │
│                                                                 │
│ Patterns Excluded:                                              │
│ ❌ wind_direction (calculation) - Confidence: 0.65 (low)        │
│                                                                 │
│ Continue with 4 patterns? [Y/n]:                                │
└─────────────────────────────────────────────────────────────────┘
```

**Step 5**: Generate code (with filtered patterns)
```bash
edgar-analyzer generate-code projects/my-api/
# Uses only patterns that passed threshold
```

### 3.3 Interaction Points

| Workflow Stage | Component | Current Behavior | Enhancement Needed |
|----------------|-----------|------------------|-------------------|
| **Project Creation** | `project.py:create()` | Creates project structure | ❌ None (threshold not relevant yet) |
| **Pattern Analysis** | `analyze-project` command | Runs ExampleParser | ✅ **Add confidence threshold prompt** |
| **Pattern Filtering** | ExampleParser | Returns all patterns | ✅ **Filter by user threshold** |
| **Pattern Review** | N/A | No review screen | ✅ **Add pattern review UI** |
| **Code Generation** | `generate-code` command | Uses all patterns | ✅ **Use filtered patterns only** |
| **Config Persistence** | `project.yaml` | No threshold field | ✅ **Add threshold field (optional)** |

### 3.4 User Decision Points

**Decision 1**: When to prompt for threshold?
- **Option A**: During `analyze-project` (after pattern detection) ✅ **RECOMMENDED**
- **Option B**: During `generate-code` (before code generation)
- **Option C**: Both (prompt twice for confirmation)

**Rationale for Option A**:
- User sees pattern distribution before deciding
- Can iterate on threshold without re-running analysis
- Follows "analyze → filter → generate" flow

**Decision 2**: Should threshold be saved to project config?
- **Option A**: Always save (automatic persistence) ❌ Not recommended
- **Option B**: Prompt user "Save threshold to project? [Y/n]" ✅ **RECOMMENDED**
- **Option C**: Never save (ephemeral only) ❌ Too inflexible

**Decision 3**: What to do with excluded patterns?
- **Option A**: Hide completely ❌ User loses visibility
- **Option B**: Show in separate "Excluded" section ✅ **RECOMMENDED**
- **Option C**: Show with warning but include in code gen ❌ Defeats purpose

---

## 4. Technical Architecture

### 4.1 Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interaction                         │
│                    (CLI - Rich UI Prompts)                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ 1. Run analyze-project
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ExampleParser Service                        │
│                  (Pattern Detection - No Changes)               │
│                                                                 │
│  Input: examples (from project.yaml)                            │
│  Output: ParsedExamples with ALL patterns + confidence scores   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ 2. Patterns detected
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              ConfidenceThresholdPrompt (NEW)                    │
│                    (Interactive Selection)                      │
│                                                                 │
│  • Display pattern distribution                                 │
│  • Prompt for threshold selection (preset or custom)            │
│  • Return selected threshold (0.0-1.0)                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ 3. User selects threshold
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              PatternFilterService (NEW)                         │
│                    (Filter by Threshold)                        │
│                                                                 │
│  Input: ParsedExamples, threshold                               │
│  Output: Filtered ParsedExamples (patterns ≥ threshold)         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ 4. Filtered patterns
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              PatternReviewScreen (NEW)                          │
│                  (Display Filtered Patterns)                    │
│                                                                 │
│  • Show included patterns (green)                               │
│  • Show excluded patterns (red, dimmed)                         │
│  • Confirm to proceed or adjust threshold                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ 5. User confirms
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              ProjectConfigPersistence (NEW)                     │
│                  (Optional Save to YAML)                        │
│                                                                 │
│  • Prompt: "Save threshold to project? [Y/n]"                   │
│  • If yes: Update project.yaml with confidence_threshold field  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ 6. Threshold saved (optional)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                CodeGeneratorService                             │
│              (Use Filtered Patterns - Enhancement)              │
│                                                                 │
│  Input: Filtered ParsedExamples, project config                 │
│  Output: Generated extractor code (only included patterns)      │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Data Flow

**Phase 1: Pattern Detection** (Existing - No Changes)
```
User Examples → ExampleParser → ParsedExamples
                                  ├── patterns (all)
                                  ├── high_confidence_patterns (≥0.9)
                                  ├── medium_confidence_patterns (0.7-0.89)
                                  └── low_confidence_patterns (<0.7)
```

**Phase 2: User Interaction** (NEW)
```
ParsedExamples → ConfidenceThresholdPrompt → User Selection
                                               ├── Preset: 0.8, 0.7, or 0.6
                                               └── Custom: user-entered float
```

**Phase 3: Pattern Filtering** (NEW)
```
ParsedExamples + Threshold → PatternFilterService → Filtered ParsedExamples
                                                      ├── included_patterns
                                                      └── excluded_patterns
```

**Phase 4: Code Generation** (Enhanced)
```
Filtered ParsedExamples → CodeGeneratorService → Generated Code
                                                  (only uses included patterns)
```

### 4.3 New Components Required

#### 4.3.1 ConfidenceThresholdPrompt (CLI UI)

**Location**: `src/edgar_analyzer/cli/prompts/confidence_threshold.py` (NEW)

**Responsibilities**:
- Display pattern distribution summary
- Show preset options with descriptions
- Handle custom threshold input with validation
- Return selected threshold (float 0.0-1.0)

**Dependencies**:
- `rich.console.Console`
- `rich.prompt.Prompt`
- `rich.table.Table`
- `rich.panel.Panel`

**Interface**:
```python
def prompt_confidence_threshold(
    parsed: ParsedExamples,
    default: str = "2"  # Balanced
) -> float:
    """Prompt user to select confidence threshold.

    Args:
        parsed: ParsedExamples with pattern distribution
        default: Default choice (1-4)

    Returns:
        Selected threshold (0.0-1.0)
    """
```

#### 4.3.2 PatternFilterService

**Location**: `src/extract_transform_platform/services/analysis/pattern_filter.py` (NEW)

**Responsibilities**:
- Filter patterns by threshold
- Separate included vs excluded patterns
- Maintain pattern metadata

**Interface**:
```python
class PatternFilterService:
    def filter_patterns(
        self,
        parsed: ParsedExamples,
        threshold: float
    ) -> FilteredParsedExamples:
        """Filter patterns by confidence threshold."""
```

**New Model**: `FilteredParsedExamples` (extends ParsedExamples)
```python
class FilteredParsedExamples(ParsedExamples):
    threshold: float
    included_patterns: List[Pattern]
    excluded_patterns: List[Pattern]
```

#### 4.3.3 PatternReviewScreen (CLI UI)

**Location**: `src/edgar_analyzer/cli/prompts/pattern_review.py` (NEW)

**Responsibilities**:
- Display included patterns (with color coding)
- Display excluded patterns (dimmed)
- Confirm user wants to proceed
- Option to adjust threshold

**Interface**:
```python
def review_patterns(
    filtered: FilteredParsedExamples
) -> bool:
    """Display pattern review screen and confirm.

    Returns:
        True if user confirms, False to adjust threshold
    """
```

#### 4.3.4 ProjectConfigPersistence Enhancement

**Location**: `src/extract_transform_platform/services/project_manager.py` (ENHANCE)

**Changes Required**:
1. Add `confidence_threshold` field to `ProjectConfig` model
2. Add method: `save_confidence_threshold(project_name: str, threshold: float)`
3. Update YAML serialization to include new field

### 4.4 Integration Points

#### 4.4.1 CLI Command: analyze-project

**Current Location**: `src/edgar_analyzer/cli/main.py` or `commands/project.py`

**Enhancement Required**:
```python
@project.command()
@click.argument("project_path")
@click.option("--threshold", type=float, default=None, help="Confidence threshold (0.0-1.0)")
@click.option("--no-interactive", is_flag=True, help="Skip interactive prompts")
def analyze_project(project_path: str, threshold: Optional[float], no_interactive: bool):
    """Analyze project and detect transformation patterns."""

    # 1. Load project config
    config = load_project_config(project_path)

    # 2. Run pattern detection (unchanged)
    parser = ExampleParser(SchemaAnalyzer())
    parsed = parser.parse_examples(config.examples)

    # 3. Interactive threshold selection (NEW)
    if not no_interactive and threshold is None:
        threshold = prompt_confidence_threshold(parsed, default="2")
    elif threshold is None:
        # Use saved threshold from project config, or default 0.7
        threshold = config.confidence_threshold or 0.7

    # 4. Filter patterns (NEW)
    filter_service = PatternFilterService()
    filtered = filter_service.filter_patterns(parsed, threshold)

    # 5. Review patterns (NEW)
    if not no_interactive:
        confirmed = review_patterns(filtered)
        if not confirmed:
            # User wants to adjust - loop back to step 3
            return

    # 6. Optionally save threshold (NEW)
    if not no_interactive:
        save = Confirm.ask("Save threshold to project config?", default=True)
        if save:
            project_manager.save_confidence_threshold(project_path, threshold)

    # 7. Save filtered patterns for code generation
    save_analysis_results(project_path, filtered)
```

#### 4.4.2 CLI Command: generate-code

**Current Behavior**: Reads analysis results, generates code

**Enhancement Required**:
- Use `filtered.included_patterns` instead of `parsed.patterns`
- Display warning if excluded patterns exist

```python
@project.command()
@click.argument("project_path")
def generate_code(project_path: str):
    """Generate extraction code from analyzed patterns."""

    # 1. Load analysis results (now includes filtering)
    filtered = load_analysis_results(project_path)

    # 2. Warn about excluded patterns
    if filtered.excluded_patterns:
        console.print(
            f"\n[yellow]⚠️  {len(filtered.excluded_patterns)} patterns excluded "
            f"(below threshold {filtered.threshold})[/yellow]"
        )
        console.print("[dim]Run analyze-project to adjust threshold[/dim]\n")

    # 3. Generate code (only included patterns)
    generator = CodeGeneratorService()
    code = generator.generate(filtered)

    # ... save code
```

---

## 5. UX Design Specifications

### 5.1 Screen 1: Confidence Threshold Selection

**Trigger**: After pattern detection completes in `analyze-project`

**Layout**:
```
┌──────────────────────────────────────────────────────────────────────┐
│                  Pattern Detection Complete                          │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│ Detected 5 transformation patterns from 3 examples:                 │
│                                                                      │
│   Pattern Distribution:                                             │
│   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━      │
│   ● 3 high confidence    (≥ 0.9)   ████████████░░░░░░░░░░ 60%      │
│   ● 1 medium confidence  (0.7-0.89) ████░░░░░░░░░░░░░░░░░ 20%      │
│   ● 1 low confidence     (< 0.7)   ████░░░░░░░░░░░░░░░░░ 20%      │
│                                                                      │
│ Select minimum confidence threshold:                                │
│                                                                      │
│   [1] 🛡️  Conservative (0.8)                                        │
│       Only include high confidence patterns                         │
│       Best for: Production systems, critical data extraction        │
│       Result: 3 patterns included, 2 patterns excluded              │
│                                                                      │
│   [2] ⚖️  Balanced (0.7) [RECOMMENDED]                              │
│       Include high + medium confidence patterns                     │
│       Best for: Most use cases, good accuracy/coverage balance      │
│       Result: 4 patterns included, 1 pattern excluded               │
│                                                                      │
│   [3] ⚡ Aggressive (0.6)                                           │
│       Include all patterns (even low confidence)                    │
│       Best for: Exploratory analysis, maximum coverage              │
│       Result: 5 patterns included, 0 patterns excluded              │
│                                                                      │
│   [4] 🎯 Custom                                                     │
│       Enter custom threshold (0.0-1.0)                              │
│                                                                      │
│ Your choice [1-4]: █                                                │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

**Colors**:
- Header: `[bold cyan]`
- High confidence stats: `[green]`
- Medium confidence stats: `[yellow]`
- Low confidence stats: `[red]`
- Options: `[white]`
- Recommended option: `[bold yellow]`

**Validation**:
- Choice must be 1-4
- If choice is 4 (Custom), prompt for float input
- Custom value must be 0.0-1.0

### 5.2 Screen 2: Custom Threshold Input

**Trigger**: User selects option 4 (Custom)

**Layout**:
```
Enter custom confidence threshold (0.0-1.0): █

Examples:
  • 0.9 = Very strict (only 90%+ confidence)
  • 0.75 = Moderate (75%+ confidence)
  • 0.5 = Lenient (50%+ confidence)
```

**Validation**:
- Must be valid float
- Must be 0.0 ≤ value ≤ 1.0
- Display error message if invalid: `[red]⚠️  Threshold must be between 0.0 and 1.0[/red]`

### 5.3 Screen 3: Pattern Review

**Trigger**: After threshold selection

**Layout**:
```
┌──────────────────────────────────────────────────────────────────────┐
│              Pattern Review (Threshold: 0.7)                         │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│ ✅ Patterns Included (4):                                            │
│                                                                      │
│ Pattern                        Type               Confidence  Level │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│ city                          field_mapping          1.00    ████  │
│ temperature_c                 field_extraction       0.95    ████  │
│ conditions                    array_first            0.90    ███░  │
│ humidity_percent              field_mapping          0.80    ███░  │
│                                                                      │
│ ❌ Patterns Excluded (1):                                            │
│                                                                      │
│ Pattern                        Type               Confidence  Level │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│ wind_direction                calculation            0.65    ██░░  │
│   ℹ️  This pattern had inconsistent results across examples         │
│                                                                      │
│ Actions:                                                             │
│   [Enter] Continue with 4 patterns                                  │
│   [R]     Adjust threshold and re-analyze                           │
│   [V]     View detailed pattern breakdown                           │
│                                                                      │
│ Choice: █                                                            │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

**Confidence Level Visualization**:
- `1.00`: `████` (4 blocks, green)
- `0.95-0.99`: `███░` (3.5 blocks, green)
- `0.90-0.94`: `███░` (3 blocks, green)
- `0.80-0.89`: `███░` (3 blocks, yellow)
- `0.70-0.79`: `██░░` (2 blocks, yellow)
- `0.60-0.69`: `██░░` (2 blocks, red)
- `<0.60`: `█░░░` (1 block, red)

**Colors**:
- Included section: `[green]` header, `[white]` patterns
- Excluded section: `[red]` header, `[dim]` patterns
- Info messages: `[cyan]`
- Warnings: `[yellow]`

### 5.4 Screen 4: Save Threshold Confirmation

**Trigger**: After user confirms pattern review

**Layout**:
```
┌──────────────────────────────────────────────────────────────────────┐
│              Save Configuration                                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│ Save confidence threshold (0.7) to project config?                  │
│                                                                      │
│ Benefits:                                                            │
│   ✓ Threshold used automatically in future runs                     │
│   ✓ Consistent results across team members                          │
│   ✓ Can be changed later by editing project.yaml                    │
│                                                                      │
│ If saved, this will be added to project.yaml:                       │
│   confidence_threshold: 0.7                                         │
│                                                                      │
│ Save? [Y/n]: █                                                       │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

**Default**: Yes (recommended for most users)

### 5.5 Success Message

**Layout**:
```
✅ Analysis Complete

   Threshold:     0.7 (Balanced)
   Patterns:      4 included, 1 excluded
   Config saved:  projects/my-api/project.yaml

Next steps:
   1. Review patterns:  cat projects/my-api/analysis_results.json
   2. Generate code:    edgar-analyzer generate-code projects/my-api/
   3. Run extraction:   edgar-analyzer run-extraction projects/my-api/
```

---

## 6. Implementation Plan

### 6.1 Phase 1: Core Functionality (MVP - Day 1)

**Goal**: Implement basic confidence threshold selection and filtering

**Tasks**:
| # | Task | Component | Est. Time | Priority |
|---|------|-----------|-----------|----------|
| 1.1 | Create `ConfidenceThresholdPrompt` component | CLI UI | 2 hours | P0 |
| 1.2 | Create `PatternFilterService` | Platform | 1.5 hours | P0 |
| 1.3 | Add `FilteredParsedExamples` model | Platform | 0.5 hours | P0 |
| 1.4 | Enhance `analyze-project` command | CLI | 2 hours | P0 |
| 1.5 | Update `generate-code` to use filtered patterns | CLI | 1 hour | P0 |
| 1.6 | Write unit tests for new components | Tests | 1 hour | P0 |

**Total MVP**: 8 hours (1 day)

**Deliverables**:
- ✅ Basic threshold selection (presets only)
- ✅ Pattern filtering
- ✅ Integration with analyze-project
- ✅ Code generation uses filtered patterns

### 6.2 Phase 2: Enhanced UX (Day 2)

**Goal**: Add pattern review, custom thresholds, and better visualization

**Tasks**:
| # | Task | Component | Est. Time | Priority |
|---|------|-----------|-----------|----------|
| 2.1 | Implement `PatternReviewScreen` | CLI UI | 2 hours | P1 |
| 2.2 | Add custom threshold input | CLI UI | 1 hour | P1 |
| 2.3 | Add confidence visualization (bars) | CLI UI | 1 hour | P1 |
| 2.4 | Add detailed pattern breakdown view | CLI UI | 1.5 hours | P2 |
| 2.5 | Improve error messages and help text | CLI UI | 0.5 hours | P2 |
| 2.6 | Integration tests for full workflow | Tests | 2 hours | P1 |

**Total Phase 2**: 8 hours (1 day)

**Deliverables**:
- ✅ Pattern review screen
- ✅ Custom threshold input
- ✅ Visual confidence bars
- ✅ Better error handling

### 6.3 Phase 3: Configuration Persistence (Day 3)

**Goal**: Save threshold to project config, support non-interactive mode

**Tasks**:
| # | Task | Component | Est. Time | Priority |
|---|------|-----------|-----------|----------|
| 3.1 | Add `confidence_threshold` field to `ProjectConfig` | Platform | 0.5 hours | P1 |
| 3.2 | Implement `save_confidence_threshold()` method | Platform | 1 hour | P1 |
| 3.3 | Add save threshold confirmation prompt | CLI UI | 0.5 hours | P1 |
| 3.4 | Load saved threshold in future runs | CLI | 1 hour | P1 |
| 3.5 | Add `--threshold` CLI flag for non-interactive | CLI | 0.5 hours | P2 |
| 3.6 | Add `--no-interactive` flag | CLI | 0.5 hours | P2 |
| 3.7 | Update project templates with threshold examples | Docs | 1 hour | P2 |

**Total Phase 3**: 5 hours (0.5 days)

**Deliverables**:
- ✅ Config persistence
- ✅ Non-interactive mode support
- ✅ CLI flags for automation

### 6.4 Phase 4: Documentation & Polish (Day 4)

**Goal**: Complete documentation and user guides

**Tasks**:
| # | Task | Component | Est. Time | Priority |
|---|------|-----------|-----------|----------|
| 4.1 | Write confidence threshold user guide | Docs | 2 hours | P0 |
| 4.2 | Update QUICK_START.md with threshold examples | Docs | 1 hour | P1 |
| 4.3 | Update CLI_USAGE.md with new flags | Docs | 0.5 hours | P1 |
| 4.4 | Add troubleshooting section | Docs | 1 hour | P2 |
| 4.5 | Record demo video/screenshots | Docs | 1.5 hours | P2 |
| 4.6 | Update CLAUDE.md with new workflow | Docs | 0.5 hours | P2 |

**Total Phase 4**: 6.5 hours (0.8 days)

**Deliverables**:
- ✅ Complete user documentation
- ✅ Updated guides
- ✅ Demo materials

### 6.5 Total Effort Estimate

| Phase | Hours | Days (8h) | Risk |
|-------|-------|-----------|------|
| Phase 1: Core MVP | 8 | 1.0 | Low |
| Phase 2: Enhanced UX | 8 | 1.0 | Medium |
| Phase 3: Config Persistence | 5 | 0.6 | Low |
| Phase 4: Documentation | 6.5 | 0.8 | Low |
| **Total** | **27.5** | **3.4** | **Low** |

**Ticket Estimate**: 1 day (accurate for MVP only, full implementation needs 3-4 days)

### 6.6 Recommended Phasing Strategy

**Option A**: Ship MVP only (1 day, matches ticket estimate)
- ✅ Meets core acceptance criteria
- ✅ Functional but basic UX
- ❌ Missing pattern review and config persistence

**Option B**: MVP + Phase 2 (2 days) ✅ **RECOMMENDED**
- ✅ Complete UX experience
- ✅ All acceptance criteria met
- ✅ Professional quality
- ❌ No config persistence yet

**Option C**: Full implementation (3.4 days)
- ✅ Production-ready
- ✅ All features
- ✅ Complete documentation
- ❌ Exceeds ticket estimate

**Recommendation**: Pursue Option B (2 days), ship Phase 3 as follow-up ticket

---

## 7. Risk Analysis

### 7.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **R1**: ExampleParser API changes required | Low | Medium | Current API supports filtering - no changes needed |
| **R2**: Rich UI compatibility issues | Low | Low | Rich is proven in setup.py, well-documented |
| **R3**: Project YAML schema breaking changes | Medium | High | Make confidence_threshold optional, maintain backward compatibility |
| **R4**: Integration with CodeGenerator fails | Low | High | Use existing filtered pattern APIs, add integration tests |
| **R5**: User confusion with threshold selection | Medium | Medium | Add clear descriptions, examples, and defaults |

### 7.2 Risk R3 Mitigation Strategy

**Problem**: Adding `confidence_threshold` field to project.yaml could break existing projects

**Solution**: Make field optional with graceful fallback
```python
class ProjectConfig(BaseModel):
    # ... existing fields
    confidence_threshold: Optional[float] = Field(
        default=None,
        description="Minimum confidence threshold (0.0-1.0)"
    )

    def get_confidence_threshold(self) -> float:
        """Get threshold with fallback to 0.7 default."""
        return self.confidence_threshold if self.confidence_threshold is not None else 0.7
```

**Backward Compatibility Test**:
1. Load existing project.yaml without confidence_threshold → should work
2. Load project.yaml with confidence_threshold → should use value
3. Upgrade old project → should not break, use default 0.7

### 7.3 UX Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **UX1**: Too many options overwhelm users | Low | Medium | Default to "Balanced", mark as recommended |
| **UX2**: Users don't understand confidence scores | Medium | Medium | Add clear explanations, visual feedback |
| **UX3**: Workflow too long/interruptive | Low | High | Allow `--no-interactive` and `--threshold` flags |
| **UX4**: Users accidentally exclude important patterns | Medium | High | Show excluded patterns in review screen, allow adjustment |

### 7.4 Risk UX4 Detailed Analysis

**Scenario**: User selects Conservative (0.8) and excludes important medium-confidence pattern

**Example**:
```
Pattern: wind_direction (calculation)
Confidence: 0.75 (medium)
Status: EXCLUDED (below 0.8 threshold)
```

**Mitigation**:
1. **Preview Impact**: Show exactly which patterns will be excluded
2. **Allow Adjustment**: User can go back and change threshold
3. **Warning Message**: If excluded patterns include field mappings (common patterns), show warning
4. **Documentation**: Explain when to use each preset

**Warning Example**:
```
⚠️  Warning: 1 field mapping pattern will be excluded (wind_direction)

Field mappings are typically reliable even at medium confidence.
Consider using "Balanced" (0.7) threshold instead.

Continue anyway? [y/N]:
```

---

## 8. Success Criteria

### 8.1 Acceptance Criteria Fulfillment

| # | Criterion | Implementation | Status |
|---|-----------|----------------|--------|
| 1 | CLI prompt for confidence threshold selection | `ConfidenceThresholdPrompt` component | ✅ Designed |
| 2 | Preset options: Conservative (0.8), Balanced (0.7), Aggressive (0.6), Custom | Preset menu with validation | ✅ Designed |
| 3 | Threshold applied to example parser pattern matching | `PatternFilterService.filter_patterns()` | ✅ Designed |
| 4 | Confidence scores displayed with color-coded feedback | Visual bars + color codes in review screen | ✅ Designed |
| 5 | User can review low-confidence patterns before applying | `PatternReviewScreen` with included/excluded sections | ✅ Designed |
| 6 | Setting persisted to project configuration (optional) | `save_confidence_threshold()` with confirmation prompt | ✅ Designed |
| 7 | Documentation updated with confidence threshold guide | Phase 4 deliverable | ✅ Planned |

**Overall**: 7/7 criteria addressed (100%)

### 8.2 Performance Criteria

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Prompt Display Time | < 500ms | Time from pattern detection to first prompt |
| Threshold Selection | < 30 seconds | User decision time (average) |
| Pattern Filtering | < 100ms | Filter 100 patterns by threshold |
| Config Save | < 200ms | Write threshold to YAML |
| Overall Workflow | < 2 minutes | Full analyze-project with interaction |

### 8.3 Usability Criteria

| Criterion | Target | Validation Method |
|-----------|--------|-------------------|
| Understandability | 90%+ users understand presets | User testing survey |
| Error Rate | < 5% invalid inputs | Track validation errors |
| Workflow Completion | 95%+ complete without help | User testing observation |
| Satisfaction | 4+/5 average rating | Post-implementation survey |

### 8.4 Quality Criteria

| Category | Target | Status |
|----------|--------|--------|
| **Test Coverage** | > 80% | Unit + integration tests |
| **Documentation** | All features documented | User guide + API docs |
| **Backward Compatibility** | 100% (no breaking changes) | Existing projects work |
| **Code Quality** | 0 linter errors | Black + mypy passing |
| **Error Handling** | All edge cases covered | Try/except + validation |

---

## 9. Appendices

### 9.1 Appendix A: Code Samples

#### A.1 ConfidenceThresholdPrompt Implementation

```python
"""Confidence threshold selection prompt for pattern analysis."""

from typing import Optional
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.table import Table

from extract_transform_platform.models.patterns import ParsedExamples

console = Console()

PRESETS = {
    "1": ("Conservative", 0.8, "Only high confidence patterns"),
    "2": ("Balanced", 0.7, "High + medium confidence (recommended)"),
    "3": ("Aggressive", 0.6, "All patterns including low confidence"),
    "4": ("Custom", None, "Enter custom threshold (0.0-1.0)"),
}

def prompt_confidence_threshold(
    parsed: ParsedExamples,
    default: str = "2"
) -> float:
    """Prompt user to select confidence threshold.

    Args:
        parsed: ParsedExamples with detected patterns
        default: Default choice (1-4)

    Returns:
        Selected threshold (0.0-1.0)
    """
    # Display pattern distribution
    _display_pattern_distribution(parsed)

    # Display preset options
    _display_preset_options(parsed)

    # Get user selection
    while True:
        choice = Prompt.ask(
            "\nYour choice",
            choices=["1", "2", "3", "4"],
            default=default
        )

        if choice == "4":
            # Custom threshold
            threshold = _prompt_custom_threshold()
            if threshold is not None:
                return threshold
            # Loop if invalid input
        else:
            # Preset threshold
            _, threshold, _ = PRESETS[choice]
            return threshold

def _display_pattern_distribution(parsed: ParsedExamples) -> None:
    """Display pattern distribution summary."""
    total = len(parsed.patterns)
    high = len(parsed.high_confidence_patterns)
    medium = len(parsed.medium_confidence_patterns)
    low = len(parsed.low_confidence_patterns)

    console.print("\n[bold cyan]Pattern Detection Complete[/bold cyan]\n")
    console.print(f"Detected [bold]{total}[/bold] transformation patterns:\n")

    # Create distribution table
    table = Table.grid(padding=(0, 2))
    table.add_column(style="bold")
    table.add_column(justify="left")
    table.add_column(justify="right")

    table.add_row(
        "[green]●[/green]",
        f"{high} high confidence",
        f"(≥ 0.9)   {_progress_bar(high, total, 'green')}"
    )
    table.add_row(
        "[yellow]●[/yellow]",
        f"{medium} medium confidence",
        f"(0.7-0.89) {_progress_bar(medium, total, 'yellow')}"
    )
    table.add_row(
        "[red]●[/red]",
        f"{low} low confidence",
        f"(< 0.7)   {_progress_bar(low, total, 'red')}"
    )

    console.print(table)

def _display_preset_options(parsed: ParsedExamples) -> None:
    """Display preset threshold options with predicted results."""
    console.print("\n[bold]Select minimum confidence threshold:[/bold]\n")

    for key, (name, threshold, desc) in PRESETS.items():
        if threshold is None:
            console.print(f"  [{key}] 🎯 [bold]{name}[/bold]")
            console.print(f"      {desc}")
        else:
            # Calculate impact
            included = sum(1 for p in parsed.patterns if p.confidence >= threshold)
            excluded = len(parsed.patterns) - included

            # Emoji based on preset
            emoji = {"1": "🛡️", "2": "⚖️", "3": "⚡"}[key]

            # Highlight recommended
            style = "[bold yellow]" if key == "2" else ""

            console.print(f"  [{key}] {emoji} {style}{name} ({threshold}){'' if key != '2' else ' [RECOMMENDED]'}[/]")
            console.print(f"      {desc}")
            console.print(f"      [dim]Result: {included} patterns included, {excluded} excluded[/dim]")

        console.print()

def _progress_bar(value: int, total: int, color: str) -> str:
    """Generate ASCII progress bar."""
    if total == 0:
        return ""

    pct = value / total
    filled = int(pct * 20)
    bar = "█" * filled + "░" * (20 - filled)

    return f"[{color}]{bar}[/] {int(pct * 100)}%"

def _prompt_custom_threshold() -> Optional[float]:
    """Prompt for custom threshold with validation."""
    console.print("\n[bold]Custom Threshold[/bold]")
    console.print("[dim]Examples:[/dim]")
    console.print("  [dim]• 0.9 = Very strict (90%+ confidence)[/dim]")
    console.print("  [dim]• 0.75 = Moderate (75%+ confidence)[/dim]")
    console.print("  [dim]• 0.5 = Lenient (50%+ confidence)[/dim]\n")

    threshold_str = Prompt.ask("Enter threshold (0.0-1.0)")

    try:
        threshold = float(threshold_str)
        if 0.0 <= threshold <= 1.0:
            return threshold
        else:
            console.print("[red]⚠️  Threshold must be between 0.0 and 1.0[/red]")
            return None
    except ValueError:
        console.print("[red]⚠️  Invalid number[/red]")
        return None
```

#### A.2 PatternFilterService Implementation

```python
"""Pattern filtering service for confidence threshold application."""

from dataclasses import dataclass
from typing import List

from extract_transform_platform.models.patterns import (
    ParsedExamples,
    Pattern,
    Schema,
)

@dataclass
class FilteredParsedExamples:
    """ParsedExamples with confidence threshold filtering applied."""

    # Original data (unchanged)
    input_schema: Schema
    output_schema: Schema
    num_examples: int
    warnings: List[str]

    # Filtering metadata
    threshold: float
    all_patterns: List[Pattern]
    included_patterns: List[Pattern]
    excluded_patterns: List[Pattern]

    @property
    def patterns(self) -> List[Pattern]:
        """Alias for included_patterns (backward compatibility)."""
        return self.included_patterns

class PatternFilterService:
    """Service for filtering patterns by confidence threshold."""

    def filter_patterns(
        self,
        parsed: ParsedExamples,
        threshold: float
    ) -> FilteredParsedExamples:
        """Filter patterns by confidence threshold.

        Args:
            parsed: ParsedExamples with all detected patterns
            threshold: Minimum confidence (0.0-1.0)

        Returns:
            FilteredParsedExamples with patterns split by threshold

        Example:
            >>> service = PatternFilterService()
            >>> filtered = service.filter_patterns(parsed, 0.7)
            >>> print(f"Included: {len(filtered.included_patterns)}")
            >>> print(f"Excluded: {len(filtered.excluded_patterns)}")
        """
        # Validate threshold
        if not 0.0 <= threshold <= 1.0:
            raise ValueError(f"Threshold must be 0.0-1.0, got {threshold}")

        # Split patterns
        included = [p for p in parsed.patterns if p.confidence >= threshold]
        excluded = [p for p in parsed.patterns if p.confidence < threshold]

        # Generate additional warnings if critical patterns excluded
        warnings = list(parsed.warnings)
        warnings.extend(self._check_excluded_patterns(excluded))

        return FilteredParsedExamples(
            input_schema=parsed.input_schema,
            output_schema=parsed.output_schema,
            num_examples=parsed.num_examples,
            warnings=warnings,
            threshold=threshold,
            all_patterns=parsed.patterns,
            included_patterns=included,
            excluded_patterns=excluded,
        )

    def _check_excluded_patterns(self, excluded: List[Pattern]) -> List[str]:
        """Generate warnings for excluded patterns."""
        warnings = []

        # Warn if many patterns excluded
        if len(excluded) > 3:
            warnings.append(
                f"{len(excluded)} patterns excluded. "
                "Consider lowering threshold for better coverage."
            )

        # Warn if field mappings excluded (usually reliable)
        from extract_transform_platform.models.patterns import PatternType
        field_mappings = [
            p for p in excluded
            if p.type == PatternType.FIELD_MAPPING
        ]
        if field_mappings:
            warnings.append(
                f"{len(field_mappings)} field mapping patterns excluded. "
                "These are typically reliable even at medium confidence."
            )

        return warnings
```

### 9.2 Appendix B: Configuration Schema

#### B.1 Enhanced ProjectConfig Model

```yaml
# project.yaml with confidence_threshold field

project:
  name: my_api_extractor
  version: 1.0.0

  # NEW: Confidence threshold configuration (optional)
  confidence_threshold: 0.7

  # Existing fields...
  description: Extract data from My API
  tags: [api, data-extraction]

data_sources:
  - type: api
    name: my_api
    endpoint: https://api.example.com/data

examples:
  - input: {...}
    output: {...}
```

#### B.2 Pydantic Model Enhancement

```python
class ProjectConfig(BaseModel):
    """Project configuration model."""

    # ... existing fields

    confidence_threshold: Optional[float] = Field(
        default=None,
        description="Minimum confidence threshold for pattern detection (0.0-1.0)",
        ge=0.0,
        le=1.0
    )

    def get_confidence_threshold(self) -> float:
        """Get threshold with default fallback."""
        return self.confidence_threshold if self.confidence_threshold is not None else 0.7

    @field_validator("confidence_threshold")
    @classmethod
    def validate_threshold(cls, v: Optional[float]) -> Optional[float]:
        """Validate threshold range."""
        if v is not None and not 0.0 <= v <= 1.0:
            raise ValueError("confidence_threshold must be between 0.0 and 1.0")
        return v
```

### 9.3 Appendix C: Test Plan

#### C.1 Unit Tests

**File**: `tests/unit/cli/test_confidence_threshold_prompt.py`

```python
"""Unit tests for confidence threshold prompt."""

import pytest
from unittest.mock import patch, MagicMock

from edgar_analyzer.cli.prompts.confidence_threshold import (
    prompt_confidence_threshold,
    _display_pattern_distribution,
    _prompt_custom_threshold,
)
from extract_transform_platform.models.patterns import (
    ParsedExamples,
    Pattern,
    PatternType,
    Schema,
)

@pytest.fixture
def sample_parsed():
    """Sample ParsedExamples for testing."""
    patterns = [
        Pattern(
            type=PatternType.FIELD_MAPPING,
            confidence=1.0,
            source_path="field1",
            target_path="field1",
            transformation="Direct copy"
        ),
        Pattern(
            type=PatternType.FIELD_EXTRACTION,
            confidence=0.85,
            source_path="main.temp",
            target_path="temperature",
            transformation="Extract nested"
        ),
        Pattern(
            type=PatternType.CALCULATION,
            confidence=0.6,
            source_path="value",
            target_path="result",
            transformation="Calculate"
        ),
    ]

    return ParsedExamples(
        input_schema=Schema(),
        output_schema=Schema(),
        patterns=patterns,
        schema_differences=[],
        num_examples=3,
        warnings=[]
    )

class TestConfidenceThresholdPrompt:
    """Test suite for confidence threshold prompt."""

    def test_preset_selection_conservative(self, sample_parsed):
        """Test selecting conservative preset."""
        with patch("edgar_analyzer.cli.prompts.confidence_threshold.Prompt.ask", return_value="1"):
            threshold = prompt_confidence_threshold(sample_parsed)
            assert threshold == 0.8

    def test_preset_selection_balanced(self, sample_parsed):
        """Test selecting balanced preset (default)."""
        with patch("edgar_analyzer.cli.prompts.confidence_threshold.Prompt.ask", return_value="2"):
            threshold = prompt_confidence_threshold(sample_parsed)
            assert threshold == 0.7

    def test_preset_selection_aggressive(self, sample_parsed):
        """Test selecting aggressive preset."""
        with patch("edgar_analyzer.cli.prompts.confidence_threshold.Prompt.ask", return_value="3"):
            threshold = prompt_confidence_threshold(sample_parsed)
            assert threshold == 0.6

    def test_custom_threshold_valid(self, sample_parsed):
        """Test custom threshold with valid input."""
        with patch("edgar_analyzer.cli.prompts.confidence_threshold.Prompt.ask") as mock_ask:
            # First call returns "4" (custom), second returns threshold
            mock_ask.side_effect = ["4", "0.75"]
            threshold = prompt_confidence_threshold(sample_parsed)
            assert threshold == 0.75

    def test_custom_threshold_invalid_then_valid(self, sample_parsed):
        """Test custom threshold with invalid then valid input."""
        with patch("edgar_analyzer.cli.prompts.confidence_threshold.Prompt.ask") as mock_ask:
            # Invalid input, then valid retry
            mock_ask.side_effect = ["4", "1.5", "0.8"]
            threshold = prompt_confidence_threshold(sample_parsed)
            assert threshold == 0.8

    def test_pattern_distribution_display(self, sample_parsed, capsys):
        """Test pattern distribution display."""
        _display_pattern_distribution(sample_parsed)
        captured = capsys.readouterr()

        assert "Pattern Detection Complete" in captured.out
        assert "1 high confidence" in captured.out
        assert "1 medium confidence" in captured.out
        assert "1 low confidence" in captured.out
```

**File**: `tests/unit/services/test_pattern_filter_service.py`

```python
"""Unit tests for pattern filter service."""

import pytest

from extract_transform_platform.services.analysis.pattern_filter import (
    PatternFilterService,
    FilteredParsedExamples,
)
from extract_transform_platform.models.patterns import (
    ParsedExamples,
    Pattern,
    PatternType,
    Schema,
)

class TestPatternFilterService:
    """Test suite for pattern filter service."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        return PatternFilterService()

    @pytest.fixture
    def sample_parsed(self):
        """Sample ParsedExamples with varying confidence."""
        patterns = [
            Pattern(
                type=PatternType.FIELD_MAPPING,
                confidence=0.95,
                source_path="field1",
                target_path="field1",
                transformation="High confidence"
            ),
            Pattern(
                type=PatternType.FIELD_EXTRACTION,
                confidence=0.75,
                source_path="field2",
                target_path="field2",
                transformation="Medium confidence"
            ),
            Pattern(
                type=PatternType.CALCULATION,
                confidence=0.55,
                source_path="field3",
                target_path="field3",
                transformation="Low confidence"
            ),
        ]

        return ParsedExamples(
            input_schema=Schema(),
            output_schema=Schema(),
            patterns=patterns,
            schema_differences=[],
            num_examples=3,
            warnings=[]
        )

    def test_filter_threshold_07(self, service, sample_parsed):
        """Test filtering with 0.7 threshold."""
        filtered = service.filter_patterns(sample_parsed, 0.7)

        assert filtered.threshold == 0.7
        assert len(filtered.included_patterns) == 2  # >= 0.7
        assert len(filtered.excluded_patterns) == 1  # < 0.7
        assert filtered.included_patterns[0].confidence >= 0.7
        assert filtered.excluded_patterns[0].confidence < 0.7

    def test_filter_threshold_09(self, service, sample_parsed):
        """Test filtering with 0.9 threshold (strict)."""
        filtered = service.filter_patterns(sample_parsed, 0.9)

        assert len(filtered.included_patterns) == 1  # Only 0.95
        assert len(filtered.excluded_patterns) == 2  # 0.75 and 0.55

    def test_filter_threshold_05(self, service, sample_parsed):
        """Test filtering with 0.5 threshold (lenient)."""
        filtered = service.filter_patterns(sample_parsed, 0.5)

        assert len(filtered.included_patterns) == 3  # All patterns
        assert len(filtered.excluded_patterns) == 0

    def test_filter_invalid_threshold(self, service, sample_parsed):
        """Test filtering with invalid threshold."""
        with pytest.raises(ValueError):
            service.filter_patterns(sample_parsed, 1.5)

        with pytest.raises(ValueError):
            service.filter_patterns(sample_parsed, -0.1)

    def test_warnings_generated(self, service, sample_parsed):
        """Test that warnings are generated for excluded patterns."""
        filtered = service.filter_patterns(sample_parsed, 0.9)

        # Should have warnings about excluded patterns
        assert len(filtered.warnings) > 0
        assert any("excluded" in w.lower() for w in filtered.warnings)
```

#### C.2 Integration Tests

**File**: `tests/integration/test_confidence_threshold_workflow.py`

```python
"""Integration tests for full confidence threshold workflow."""

import pytest
from pathlib import Path
import yaml

from edgar_analyzer.cli.commands.project import analyze_project
from extract_transform_platform.services.project_manager import ProjectManager

class TestConfidenceThresholdWorkflow:
    """Test end-to-end confidence threshold workflow."""

    @pytest.fixture
    def test_project_path(self, tmp_path):
        """Create test project with examples."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()

        # Create project.yaml
        config = {
            "project": {
                "name": "test_project",
                "version": "1.0.0"
            },
            "data_sources": [{
                "type": "api",
                "name": "test_api",
                "endpoint": "https://api.test.com"
            }],
            "examples": [
                {
                    "input": {"temp": 15.5, "city": "London"},
                    "output": {"temperature": 15.5, "location": "London"}
                },
                {
                    "input": {"temp": 22.0, "city": "Tokyo"},
                    "output": {"temperature": 22.0, "location": "Tokyo"}
                }
            ]
        }

        with open(project_dir / "project.yaml", "w") as f:
            yaml.dump(config, f)

        return project_dir

    def test_analyze_with_threshold_flag(self, test_project_path):
        """Test analyze-project with --threshold flag."""
        # Run analyze with threshold
        result = analyze_project(
            str(test_project_path),
            threshold=0.8,
            no_interactive=True
        )

        # Should have filtered patterns
        assert result["threshold"] == 0.8
        assert "included_patterns" in result
        assert "excluded_patterns" in result

    def test_threshold_persistence(self, test_project_path):
        """Test that threshold is saved to project config."""
        manager = ProjectManager()

        # Save threshold
        manager.save_confidence_threshold(str(test_project_path), 0.75)

        # Reload config
        config = manager.load_project_config(str(test_project_path))

        assert config.confidence_threshold == 0.75

    def test_threshold_used_in_next_run(self, test_project_path):
        """Test that saved threshold is used in subsequent runs."""
        manager = ProjectManager()

        # Save threshold
        manager.save_confidence_threshold(str(test_project_path), 0.8)

        # Run analyze without explicit threshold (should use saved)
        result = analyze_project(
            str(test_project_path),
            threshold=None,
            no_interactive=True
        )

        assert result["threshold"] == 0.8
```

### 9.4 Appendix D: Documentation Outline

#### D.1 User Guide: Confidence Thresholds

**Location**: `docs/guides/CONFIDENCE_THRESHOLDS.md`

**Outline**:
1. **Introduction**
   - What are confidence thresholds?
   - Why are they important?
   - When to adjust thresholds

2. **Understanding Confidence Scores**
   - How confidence is calculated
   - High (≥0.9), Medium (0.7-0.89), Low (<0.7)
   - Pattern consistency across examples

3. **Selecting the Right Threshold**
   - Conservative (0.8) - Production systems
   - Balanced (0.7) - Most use cases (recommended)
   - Aggressive (0.6) - Exploratory analysis
   - Custom - Advanced users

4. **Interactive Workflow**
   - Pattern detection summary
   - Threshold selection prompt
   - Pattern review screen
   - Configuration persistence

5. **Non-Interactive Mode**
   - `--threshold` flag
   - `--no-interactive` flag
   - Environment variables

6. **Best Practices**
   - Start with Balanced (0.7)
   - Review excluded patterns
   - Add more examples if many low-confidence patterns
   - Document threshold choices in project README

7. **Troubleshooting**
   - Too many patterns excluded
   - Low confidence on important patterns
   - Threshold not being saved
   - Conflicts between CLI flag and config

8. **Examples**
   - Weather API project
   - Employee roster project
   - Invoice transform project

#### D.2 CLI Usage Updates

**Location**: `docs/guides/CLI_USAGE.md`

**Additions**:
```markdown
### analyze-project

Analyze project examples and detect transformation patterns.

**Usage**:
```bash
edgar-analyzer analyze-project <project_path> [OPTIONS]
```

**Options**:
- `--threshold FLOAT`: Confidence threshold (0.0-1.0)
- `--no-interactive`: Skip interactive prompts
- `--save-threshold / --no-save-threshold`: Save threshold to config (default: prompt)

**Examples**:
```bash
# Interactive mode (default)
edgar-analyzer analyze-project projects/my-api/

# Non-interactive with explicit threshold
edgar-analyzer analyze-project projects/my-api/ --threshold 0.8 --no-interactive

# Use saved threshold from project config
edgar-analyzer analyze-project projects/my-api/ --no-interactive
```

**Workflow**:
1. Detects transformation patterns from examples
2. Prompts for confidence threshold selection
3. Displays pattern review (included/excluded)
4. Optionally saves threshold to project.yaml
5. Saves analysis results for code generation
```

---

## Conclusion

This research document provides comprehensive analysis for implementing ticket 1M-362: Interactive Confidence Threshold Selection UX. The feature is well-scoped, technically feasible, and aligns with user preferences for runtime configuration.

### Key Recommendations

1. **Implement in 3 phases**: MVP (1 day), Enhanced UX (1 day), Config Persistence (0.5 days)
2. **Use existing Rich UI patterns** from setup.py for consistency
3. **Maintain backward compatibility** with optional threshold field
4. **Provide clear visual feedback** with color-coded confidence levels
5. **Allow adjustment** via pattern review screen before proceeding

### Next Steps

1. Review this research document with stakeholders
2. Confirm phasing strategy (MVP only vs full implementation)
3. Begin Phase 1 implementation (core functionality)
4. Conduct user testing after Phase 2 (enhanced UX)
5. Ship Phase 3 as follow-up ticket if needed

---

**Research Complete**: All acceptance criteria analyzed, technical design documented, implementation plan created, and risks mitigated. Ready for development.

**Estimated Delivery**: 1 day (MVP) or 2 days (MVP + Enhanced UX)
