# 🎯 Confidence Threshold Selection Guide

**Feature**: Interactive confidence threshold selection for example-driven workflows
**Status**: Production Ready (Phase 1 MVP Complete)
**Ticket**: [1M-362](https://linear.app/1m-hyperdev/issue/1M-362)

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Understanding Confidence Scores](#understanding-confidence-scores)
4. [Threshold Presets](#threshold-presets)
5. [Pattern Confidence Levels](#pattern-confidence-levels)
6. [Interactive Mode](#interactive-mode)
7. [Non-Interactive Mode](#non-interactive-mode)
8. [Examples](#examples)
9. [Troubleshooting](#troubleshooting)
10. [Best Practices](#best-practices)
11. [API Reference](#api-reference)

---

## Overview

### What is Confidence Threshold Selection?

Confidence threshold selection allows you to control which **transformation patterns** are included in your generated extraction code based on their **confidence scores**. This gives you control over the quality-vs-coverage trade-off:

- **Higher thresholds** (0.8+): Only include patterns that appear very consistently across your examples → **higher quality**, fewer patterns
- **Lower thresholds** (0.6-0.7): Include patterns that have some inconsistencies → **more coverage**, lower quality

### Why It Matters

When you provide 2-3 transformation examples, the platform automatically detects patterns and assigns confidence scores (0.0-1.0) based on how consistently each pattern appears across all examples.

**Example**:
```
Pattern: city → location (field rename)
- Appears in 3/3 examples → Confidence: 1.0 (100%)

Pattern: wind_direction → cardinal_direction (calculation)
- Appears in 2/3 examples → Confidence: 0.67 (67%)
```

You can then **filter** which patterns to include based on a minimum confidence threshold.

### When to Use Each Preset

| Preset | Threshold | Use Case |
|--------|-----------|----------|
| **Conservative** | 0.8 | Production systems, critical data extraction |
| **Balanced** | 0.7 | Most use cases (recommended default) |
| **Aggressive** | 0.6 | Exploratory analysis, maximum coverage |
| **Custom** | 0.0-1.0 | Advanced users with specific requirements |

### Visual Example

```
Pattern Distribution:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
● 3 high confidence    (≥ 0.9)   ████████████░░░░░░░░ 60%
● 1 medium confidence  (0.7-0.89) ████░░░░░░░░░░░░░░░░ 20%
● 1 low confidence     (< 0.7)   ████░░░░░░░░░░░░░░░░ 20%

Threshold 0.8 → Includes: 3 patterns (60%)
Threshold 0.7 → Includes: 4 patterns (80%)
Threshold 0.6 → Includes: 5 patterns (100%)
```

---

## Quick Start

### 5-Minute Guide to Your First Threshold Selection

**Step 1**: Create a project with examples
```bash
cd projects/
mkdir my_project
cd my_project

# Create project.yaml with 2-3 examples
# See PLATFORM_USAGE.md for project structure
```

**Step 2**: Run analysis (interactive mode)
```bash
edgar-analyzer project generate my_project
```

**Step 3**: Review pattern summary
```
┌─────────────────────────────────────────────┐
│      Pattern Detection Complete            │
├─────────────────────────────────────────────┤
│ Detected 5 patterns from 3 examples:       │
│   • 3 high confidence (≥ 0.9)              │
│   • 1 medium confidence (0.7-0.89)         │
│   • 1 low confidence (< 0.7)               │
└─────────────────────────────────────────────┘
```

**Step 4**: Select threshold
```
Select minimum confidence threshold:
  [1] 🛡️  Conservative (0.8)
  [2] ⚖️  Balanced (0.7) [RECOMMENDED]
  [3] ⚡ Aggressive (0.6)
  [4] 🎯 Custom

Your choice [1-4]: 2
```

**Step 5**: Review filtered patterns
```
✅ Patterns Included (4):
  city             field_mapping     1.00  ████
  temperature_c    field_extraction  0.95  ████
  conditions       array_first       0.90  ███░
  humidity_percent field_mapping     0.80  ███░

❌ Patterns Excluded (1):
  wind_direction   calculation       0.65  ██░░
```

**Step 6**: Proceed with code generation
- Press Enter to continue with 4 patterns
- Or press 'R' to adjust threshold

**Expected Output**:
```
✅ Analysis Complete
   Threshold:     0.7 (Balanced)
   Patterns:      4 included, 1 excluded
   Config saved:  projects/my_project/project.yaml

Next steps:
   1. Review patterns:  cat projects/my_project/analysis_results.json
   2. Generate code:    edgar-analyzer project generate my_project
   3. Run extraction:   edgar-analyzer project run my_project
```

---

## Understanding Confidence Scores

### How Confidence is Calculated

Confidence scores are **data-driven** and automatically calculated based on **pattern consistency** across your examples:

```python
# Pattern applies to ALL examples
confidence = 1.0  # 100%

# Pattern applies to SOME examples
confidence = matches / total_examples

# Example: Pattern in 2 out of 3 examples
confidence = 2 / 3 = 0.67  # 67%
```

### Confidence Level Categories

The platform categorizes patterns into three confidence levels:

#### 🟢 High Confidence (≥ 0.9)

**Meaning**: Pattern appears in 90%+ of examples with consistent behavior

**Characteristics**:
- Very consistent transformation
- Minimal variation across examples
- High reliability for code generation

**Example**:
```json
{
  "type": "field_mapping",
  "source_path": "city",
  "target_path": "location",
  "confidence": 1.0,
  "transformation": "Direct field rename"
}
```

**Risk**: Very low - Safe to include

---

#### 🟡 Medium Confidence (0.7-0.89)

**Meaning**: Pattern appears in 70-89% of examples with mostly consistent behavior

**Characteristics**:
- Mostly consistent transformation
- Some variation or edge cases
- Generally reliable but may need validation

**Example**:
```json
{
  "type": "type_conversion",
  "source_path": "temperature",
  "target_path": "temp_c",
  "confidence": 0.75,
  "transformation": "String to float conversion"
}
```

**Risk**: Low to Medium - Usually safe to include

---

#### 🔴 Low Confidence (< 0.7)

**Meaning**: Pattern appears in <70% of examples with inconsistent behavior

**Characteristics**:
- Inconsistent transformation
- Significant variation across examples
- May indicate complex logic or edge cases

**Example**:
```json
{
  "type": "calculation",
  "source_path": "wind.deg",
  "target_path": "wind_direction",
  "confidence": 0.65,
  "transformation": "Degrees to cardinal direction"
}
```

**Risk**: Medium to High - Review carefully before including

**Common Causes**:
- Complex business logic
- Conditional transformations
- Insufficient examples
- Data quality issues

---

### Pattern Consistency Across Examples

**Example 1**: High Confidence Pattern (1.0)
```
Example 1: { "temp": 15.5 } → { "temperature": 15.5 }
Example 2: { "temp": 22.0 } → { "temperature": 22.0 }
Example 3: { "temp": 18.3 } → { "temperature": 18.3 }

Pattern: temp → temperature (field rename)
Confidence: 3/3 = 1.0 (appears in ALL examples)
```

**Example 2**: Medium Confidence Pattern (0.67)
```
Example 1: { "status": "A" } → { "active": true }
Example 2: { "status": "I" } → { "active": false }
Example 3: { "status": "P" } → { "active": null }  # Inconsistent

Pattern: status → active (boolean conversion)
Confidence: 2/3 = 0.67 (partially consistent)
```

---

## Threshold Presets

### Conservative (0.8) 🛡️

**When to Use**:
- Production systems handling critical data
- Financial or healthcare applications
- Compliance-sensitive environments
- When accuracy is more important than coverage

**Characteristics**:
- Only includes high confidence patterns (≥ 0.8)
- Prioritizes quality over quantity
- Safer for automated workflows
- May exclude useful medium-confidence patterns

**Pros**:
- ✅ Highest reliability
- ✅ Minimal false positives
- ✅ Production-ready code
- ✅ Lower maintenance burden

**Cons**:
- ❌ May exclude valid patterns
- ❌ Lower coverage
- ❌ More manual work for edge cases

**Example Use Case**:
```bash
# Medical records transformation (high accuracy required)
edgar-analyzer project generate medical_records --confidence-threshold 0.8
```

**Expected Results**:
```
Detected 10 patterns:
  • 6 high confidence (≥ 0.9)   → ✅ Included
  • 3 medium confidence (0.7-0.89) → ❌ Excluded
  • 1 low confidence (< 0.7)   → ❌ Excluded

Result: 6/10 patterns included (60%)
```

---

### Balanced (0.7) ⚖️ [RECOMMENDED]

**When to Use**:
- Most use cases (default recommendation)
- General data transformation projects
- Internal tools and dashboards
- When you want good accuracy with reasonable coverage

**Characteristics**:
- Includes high + medium confidence patterns (≥ 0.7)
- Good balance between quality and coverage
- Recommended for 80% of projects
- Excludes only low-confidence patterns

**Pros**:
- ✅ Good quality/coverage balance
- ✅ Works well for most projects
- ✅ Includes reliable medium-confidence patterns
- ✅ Still filters out unreliable patterns

**Cons**:
- ⚠️ May include some patterns needing validation
- ⚠️ Not as strict as conservative

**Example Use Case**:
```bash
# Internal analytics dashboard (balanced approach)
edgar-analyzer project generate analytics_dashboard --confidence-threshold 0.7
```

**Expected Results**:
```
Detected 10 patterns:
  • 6 high confidence (≥ 0.9)   → ✅ Included
  • 3 medium confidence (0.7-0.89) → ✅ Included
  • 1 low confidence (< 0.7)   → ❌ Excluded

Result: 9/10 patterns included (90%)
```

**Why Recommended**:
- Filters out only truly unreliable patterns (<70% consistency)
- Includes patterns that work in 70%+ of cases
- Best trade-off for most projects
- Used successfully in employee roster and weather API POCs

---

### Aggressive (0.6) ⚡

**When to Use**:
- Exploratory data analysis
- Proof-of-concept projects
- Research and development
- When coverage is more important than accuracy
- When you'll manually review generated code

**Characteristics**:
- Includes all patterns including low confidence (≥ 0.6)
- Maximizes coverage
- Higher risk of including unreliable patterns
- Good for discovering edge cases

**Pros**:
- ✅ Maximum coverage
- ✅ Discovers all potential patterns
- ✅ Good for exploration
- ✅ Useful for understanding data structure

**Cons**:
- ❌ May include unreliable patterns
- ❌ More manual validation needed
- ❌ Higher maintenance burden
- ❌ Not recommended for production

**Example Use Case**:
```bash
# Research project exploring data patterns
edgar-analyzer project generate research_exploration --confidence-threshold 0.6
```

**Expected Results**:
```
Detected 10 patterns:
  • 6 high confidence (≥ 0.9)   → ✅ Included
  • 3 medium confidence (0.7-0.89) → ✅ Included
  • 1 low confidence (< 0.7)   → ✅ Included

Result: 10/10 patterns included (100%)
```

**Warning**: Review all low-confidence patterns before using in production

---

### Custom (0.0-1.0) 🎯

**When to Use**:
- Advanced users with specific requirements
- Domain-specific accuracy needs
- When you need fine-grained control
- After testing with presets

**How to Select**:
```bash
# In interactive mode, choose option 4 (Custom)
edgar-analyzer project generate my_project

# Or use CLI flag with exact threshold
edgar-analyzer project generate my_project --confidence-threshold 0.75
```

**Custom Threshold Guide**:

| Threshold | Strictness | Use Case |
|-----------|-----------|----------|
| 0.9-1.0 | Very Strict | Only perfect patterns |
| 0.85 | Strict | Between conservative and balanced |
| 0.75 | Moderate | Between balanced and aggressive |
| 0.65 | Lenient | Slightly more strict than aggressive |
| 0.5-0.59 | Very Lenient | Experimental only |
| 0.0-0.49 | No Filter | Include everything (not recommended) |

**Examples**:
```bash
# 85% threshold (stricter than balanced)
edgar-analyzer project generate critical_data --confidence-threshold 0.85

# 75% threshold (between balanced and aggressive)
edgar-analyzer project generate internal_tool --confidence-threshold 0.75

# 90% threshold (only near-perfect patterns)
edgar-analyzer project generate financial_data --confidence-threshold 0.9
```

---

## Pattern Confidence Levels

### Confidence Distribution Visualization

The platform shows you pattern distribution before you select a threshold:

```
┌──────────────────────────────────────────────────────────┐
│          Pattern Detection Complete                      │
├──────────────────────────────────────────────────────────┤
│ Detected 8 transformation patterns from 3 examples:     │
│                                                          │
│   Pattern Distribution:                                 │
│   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━     │
│   ● 5 high confidence    (≥ 0.9)   ████████████░░ 62%  │
│   ● 2 medium confidence  (0.7-0.89) ████░░░░░░░░ 25%   │
│   ● 1 low confidence     (< 0.7)   ██░░░░░░░░░░ 13%   │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### Understanding the Visual Bars

**Confidence Level Visualization**:
- `████` (4 blocks) = 1.00 (100% confidence)
- `███░` (3.5 blocks) = 0.95-0.99 (95-99% confidence)
- `███░` (3 blocks) = 0.90-0.94 (90-94% confidence)
- `███░` (3 blocks) = 0.80-0.89 (80-89% confidence)
- `██░░` (2 blocks) = 0.70-0.79 (70-79% confidence)
- `██░░` (2 blocks) = 0.60-0.69 (60-69% confidence)
- `█░░░` (1 block) = <0.60 (<60% confidence)

**Colors**:
- 🟢 Green bars = High confidence (≥ 0.9)
- 🟡 Yellow bars = Medium confidence (0.7-0.89)
- 🔴 Red bars = Low confidence (< 0.7)

### Example Pattern Breakdown

#### High Confidence Pattern Example (0.95)

```
Pattern: city (field_mapping)
  Source:        main.name
  Target:        location
  Confidence:    0.95  ████
  Transformation: Extract nested field and rename
  Status:        ✅ Included (all thresholds)
```

**Why High Confidence**:
- Appears in 19/20 examples
- Consistent transformation logic
- No edge cases or exceptions

---

#### Medium Confidence Pattern Example (0.80)

```
Pattern: temperature_c (field_extraction)
  Source:        main.temp
  Target:        temperature_celsius
  Confidence:    0.80  ███░
  Transformation: Extract and convert units
  Status:        ✅ Included (balanced, aggressive)
                ❌ Excluded (conservative if <0.8)
```

**Why Medium Confidence**:
- Appears in 16/20 examples
- Mostly consistent with minor variations
- Unit conversion sometimes missing

---

#### Low Confidence Pattern Example (0.65)

```
Pattern: wind_direction (calculation)
  Source:        wind.deg
  Target:        wind_cardinal
  Confidence:    0.65  ██░░
  Transformation: Convert degrees to N/S/E/W
  Status:        ❌ Excluded (conservative, balanced)
                ✅ Included (aggressive only)
```

**Why Low Confidence**:
- Appears in 13/20 examples
- Complex calculation logic
- Edge cases not handled consistently

**Recommendation**: Add more examples or use custom extractor

---

## Interactive Mode

### Complete Walkthrough

Interactive mode provides a guided experience with visual feedback at each step.

#### Step 1: Pattern Detection

After running `edgar-analyzer project generate my_project`, the platform analyzes your examples and detects transformation patterns:

```
🔍 Analyzing examples...
   Loading: projects/my_project/examples/*.json
   Parsing: 3 input/output pairs
   Detecting: Transformation patterns

✅ Pattern detection complete!
```

---

#### Step 2: Pattern Summary Display

The platform shows you what it found:

```
┌──────────────────────────────────────────────────────────────────────┐
│                  Pattern Detection Complete                          │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│ Detected 5 transformation patterns from 3 examples:                 │
│                                                                      │
│   Pattern Distribution:                                             │
│   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    │
│   ● 3 high confidence    (≥ 0.9)   ████████████░░░░░░░░░░ 60%      │
│   ● 1 medium confidence  (0.7-0.89) ████░░░░░░░░░░░░░░░░░ 20%      │
│   ● 1 low confidence     (< 0.7)   ████░░░░░░░░░░░░░░░░░ 20%      │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

**Understanding the Summary**:
- **Total patterns**: 5 detected
- **High confidence**: 3 patterns (60%) - very reliable
- **Medium confidence**: 1 pattern (20%) - mostly reliable
- **Low confidence**: 1 pattern (20%) - needs review

---

#### Step 3: Preset Selection Workflow

The platform presents threshold options with impact preview:

```
┌──────────────────────────────────────────────────────────────────────┐
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

**What to Look For**:
- **Result preview**: Shows how many patterns will be included/excluded
- **Use case descriptions**: Helps you decide which preset fits your needs
- **Recommended option**: Balanced (0.7) works for most projects

**Making Your Selection**:
- Type `1`, `2`, `3`, or `4` and press Enter
- For balanced (recommended), just press Enter (default is 2)

---

#### Step 4: Custom Threshold Workflow

If you selected option 4 (Custom), you'll see:

```
┌──────────────────────────────────────────────────────────────┐
│              Custom Threshold Selection                      │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ Enter custom confidence threshold (0.0-1.0): █              │
│                                                              │
│ Examples:                                                    │
│   • 0.9  = Very strict (only 90%+ confidence)               │
│   • 0.75 = Moderate (75%+ confidence)                       │
│   • 0.5  = Lenient (50%+ confidence)                        │
│                                                              │
│ Tips:                                                        │
│   • Start with presets before using custom                  │
│   • Round to 2 decimal places (e.g., 0.85)                  │
│   • Review excluded patterns after selection                │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Valid Inputs**:
- Any decimal number between 0.0 and 1.0
- Examples: `0.75`, `0.85`, `0.65`

**Invalid Inputs** (will re-prompt):
- Negative numbers: `-0.5`
- Numbers > 1.0: `1.5`
- Non-numeric text: `high`
- Empty input: uses default (0.7)

**Example Interaction**:
```
Enter custom confidence threshold (0.0-1.0): 0.85
✅ Custom threshold set: 0.85

Calculating impact...
   Result: 3 patterns included, 2 patterns excluded
```

---

#### Step 5: Pattern Review Screen

After threshold selection, you see exactly which patterns are included/excluded:

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
│   "city" field renamed to "location"                               │
│                                                                      │
│ temperature_c                 field_extraction       0.95    ████  │
│   Extract "main.temp", convert to Celsius                          │
│                                                                      │
│ conditions                    array_first            0.90    ███░  │
│   Get first element from "weather" array                           │
│                                                                      │
│ humidity_percent              field_mapping          0.80    ███░  │
│   "humidity" field renamed to "humidity_pct"                       │
│                                                                      │
│ ❌ Patterns Excluded (1):                                            │
│                                                                      │
│ Pattern                        Type               Confidence  Level │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│ wind_direction                calculation            0.65    ██░░  │
│   Convert wind degrees to cardinal direction (N/S/E/W)             │
│   ℹ️  This pattern had inconsistent results across examples         │
│   💡 Consider adding more examples or using custom extractor        │
│                                                                      │
│ Actions:                                                             │
│   [Enter] Continue with 4 patterns                                  │
│   [R]     Adjust threshold and re-analyze                           │
│   [V]     View detailed pattern breakdown                           │
│   [Q]     Quit without saving                                       │
│                                                                      │
│ Choice: █                                                            │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

**Understanding the Review Screen**:

**Included Patterns** (Green section):
- Shows pattern name, type, confidence score, and visual bar
- Provides brief description of transformation
- All patterns here will be in generated code

**Excluded Patterns** (Red/dimmed section):
- Shows patterns below threshold
- Explains why they were inconsistent
- Provides recommendations (add examples, custom extractor)

**Available Actions**:
- **Enter**: Proceed with current selection
- **R**: Go back and select different threshold
- **V**: See detailed pattern breakdown (all fields, transformations)
- **Q**: Quit without saving

**Example Decision Flow**:
```
# Scenario 1: Excluded pattern is important
Choice: R  (go back and lower threshold to 0.6)

# Scenario 2: Excluded pattern is acceptable
Choice: [Enter]  (continue with 4 patterns)

# Scenario 3: Want to see more details
Choice: V  (view detailed breakdown)
```

---

#### Step 6: Detailed Pattern Breakdown (Optional)

If you press 'V' for detailed view:

```
┌──────────────────────────────────────────────────────────────────────┐
│              Detailed Pattern Breakdown                              │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│ Pattern 1/5: city → location                                        │
│   Type:           field_mapping                                     │
│   Confidence:     1.00 (100%)                                       │
│   Source Path:    city                                              │
│   Target Path:    location                                          │
│   Transformation: Direct field rename                               │
│   Examples:                                                          │
│     Example 1: "London" → "London"                                  │
│     Example 2: "Tokyo" → "Tokyo"                                    │
│     Example 3: "Paris" → "Paris"                                    │
│   Consistency:    3/3 examples (100%)                               │
│   Risk:          Very Low                                            │
│   Status:        ✅ Included                                         │
│                                                                      │
│ [Next] [Previous] [Back to Summary] [Continue]                     │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

**Navigation**:
- **Next**: View next pattern
- **Previous**: View previous pattern
- **Back to Summary**: Return to pattern review
- **Continue**: Proceed with code generation

---

#### Step 7: Success Message

After confirming your selection:

```
✅ Analysis Complete

   Threshold:     0.7 (Balanced)
   Patterns:      4 included, 1 excluded
   Config saved:  projects/my_project/project.yaml

📋 Pattern Summary:
   ✅ city              (field_mapping, 1.00)
   ✅ temperature_c     (field_extraction, 0.95)
   ✅ conditions        (array_first, 0.90)
   ✅ humidity_percent  (field_mapping, 0.80)
   ❌ wind_direction    (calculation, 0.65)

💾 Threshold saved to project configuration
   Future runs will use this threshold automatically

📝 Next steps:
   1. Review patterns:  cat projects/my_project/analysis_results.json
   2. Generate code:    edgar-analyzer project generate my_project
   3. Run extraction:   edgar-analyzer project run my_project
```

---

## Non-Interactive Mode

### Using CLI Flags

For automation, CI/CD, or scripting, you can bypass interactive prompts:

#### Basic Non-Interactive Usage

```bash
# Use specific threshold (no prompts)
edgar-analyzer project generate my_project --confidence-threshold 0.8

# Short form
edgar-analyzer project generate my_project -t 0.8
```

#### Common Scenarios

**Conservative Production Deployment**:
```bash
# Production: Conservative threshold, no interaction
edgar-analyzer project generate my_project \
  --confidence-threshold 0.8 \
  --no-interactive
```

**CI/CD Pipeline**:
```bash
# Automated testing: Balanced threshold
edgar-analyzer project generate my_project \
  --confidence-threshold 0.7 \
  --no-interactive \
  --output-dir /tmp/test_output
```

**Development/Exploration**:
```bash
# Development: Aggressive threshold to see all patterns
edgar-analyzer project generate my_project \
  --confidence-threshold 0.6 \
  --no-interactive
```

**Custom Threshold**:
```bash
# Custom threshold for specific use case
edgar-analyzer project generate my_project \
  --confidence-threshold 0.75
```

---

### Automation and Scripting

#### Shell Script Example

```bash
#!/bin/bash
# generate_all_projects.sh - Batch process multiple projects

THRESHOLD=0.7  # Balanced threshold for all projects
PROJECTS_DIR="projects"

for project in $(ls -d $PROJECTS_DIR/*/); do
    project_name=$(basename $project)
    echo "Processing: $project_name"

    edgar-analyzer project generate $project_name \
        --confidence-threshold $THRESHOLD \
        --no-interactive

    if [ $? -eq 0 ]; then
        echo "✅ $project_name completed"
    else
        echo "❌ $project_name failed"
    fi
done
```

#### Python Script Example

```python
#!/usr/bin/env python3
"""Batch project generation with custom thresholds."""

import subprocess
import sys
from pathlib import Path

PROJECTS = {
    "weather_api": 0.7,      # Balanced
    "financial_data": 0.8,   # Conservative
    "research_project": 0.6  # Aggressive
}

def generate_project(name: str, threshold: float) -> bool:
    """Generate project with specified threshold."""
    cmd = [
        "edgar-analyzer", "project", "generate", name,
        "--confidence-threshold", str(threshold),
        "--no-interactive"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"✅ {name} (threshold: {threshold})")
        return True
    else:
        print(f"❌ {name} failed: {result.stderr}")
        return False

if __name__ == "__main__":
    successes = 0
    for name, threshold in PROJECTS.items():
        if generate_project(name, threshold):
            successes += 1

    print(f"\nCompleted: {successes}/{len(PROJECTS)} projects")
    sys.exit(0 if successes == len(PROJECTS) else 1)
```

---

### CI/CD Integration

#### GitHub Actions Example

```yaml
# .github/workflows/generate-extractors.yml
name: Generate Extractors

on:
  push:
    paths:
      - 'projects/*/examples/*.json'
      - 'projects/*/project.yaml'

jobs:
  generate:
    runs-on: ubuntu-latest

    strategy:
      matrix:
        project:
          - name: weather_api
            threshold: 0.7
          - name: financial_data
            threshold: 0.8

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e .

      - name: Generate extractor
        run: |
          edgar-analyzer project generate ${{ matrix.project.name }} \
            --confidence-threshold ${{ matrix.project.threshold }} \
            --no-interactive

      - name: Run tests
        run: |
          pytest projects/${{ matrix.project.name }}/tests/

      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: ${{ matrix.project.name }}-extractor
          path: projects/${{ matrix.project.name }}/output/
```

#### GitLab CI Example

```yaml
# .gitlab-ci.yml
stages:
  - generate
  - test

variables:
  BALANCED_THRESHOLD: "0.7"
  CONSERVATIVE_THRESHOLD: "0.8"

generate_weather_api:
  stage: generate
  script:
    - edgar-analyzer project generate weather_api
        --confidence-threshold $BALANCED_THRESHOLD
        --no-interactive
  artifacts:
    paths:
      - projects/weather_api/output/
    expire_in: 1 week

generate_financial_data:
  stage: generate
  script:
    - edgar-analyzer project generate financial_data
        --confidence-threshold $CONSERVATIVE_THRESHOLD
        --no-interactive
  artifacts:
    paths:
      - projects/financial_data/output/
    expire_in: 1 week
```

---

### Error Handling in Non-Interactive Mode

#### Exit Codes

```bash
# Check exit code after generation
edgar-analyzer project generate my_project --confidence-threshold 0.7

if [ $? -eq 0 ]; then
    echo "Success"
else
    echo "Failed with exit code: $?"
fi
```

**Exit Codes**:
- `0`: Success
- `1`: General error
- `2`: Invalid threshold (not in 0.0-1.0 range)
- `3`: Project not found
- `4`: No patterns detected
- `5`: All patterns excluded (threshold too high)

#### Capturing Output

```bash
# Capture output for logging
output=$(edgar-analyzer project generate my_project \
    --confidence-threshold 0.7 \
    --no-interactive 2>&1)

if [ $? -eq 0 ]; then
    echo "$output" >> success.log
else
    echo "$output" >> error.log
    # Send alert
    send_alert "Project generation failed"
fi
```

---

## Examples

### Example 1: Employee Roster (High-Quality Data)

**Scenario**: Transforming clean, well-structured employee data from Excel

**Data Source**: Excel spreadsheet with consistent columns
**Quality**: High (all fields present, consistent format)
**Recommendation**: Use **Balanced (0.7)** threshold

#### Project Setup

```bash
cd projects/
mkdir employee_roster
cd employee_roster

# Create project.yaml
cat > project.yaml <<EOF
project:
  name: employee_roster
  description: Extract employee data from Excel
  version: 1.0.0

data_sources:
  - type: excel
    name: roster
    config:
      file_path: input/employees.xlsx
      sheet_name: 0
      header_row: 0

examples:
  - input:
      employee_id: "E1001"
      first_name: "Alice"
      last_name: "Johnson"
      department: "Engineering"
      hire_date: "2020-03-15"
      salary: 95000
      is_manager: "Yes"
    output:
      id: "E1001"
      full_name: "Alice Johnson"
      dept: "Engineering"
      hired: "2020-03-15"
      annual_salary_usd: 95000.0
      manager: true

  - input:
      employee_id: "E1002"
      first_name: "Bob"
      last_name: "Smith"
      department: "Sales"
      hire_date: "2021-06-01"
      salary: 85000
      is_manager: "No"
    output:
      id: "E1002"
      full_name: "Bob Smith"
      dept: "Sales"
      hired: "2021-06-01"
      annual_salary_usd: 85000.0
      manager: false
EOF
```

#### Pattern Detection Results

```bash
edgar-analyzer project generate employee_roster

# Output:
┌─────────────────────────────────────────────┐
│      Pattern Detection Complete            │
├─────────────────────────────────────────────┤
│ Detected 7 patterns from 2 examples:       │
│   • 5 high confidence (≥ 0.9)              │
│   • 2 medium confidence (0.7-0.89)         │
│   • 0 low confidence (< 0.7)               │
└─────────────────────────────────────────────┘
```

#### Pattern Breakdown

```
✅ High Confidence Patterns (5):
1. employee_id → id (1.0) - Direct field rename
2. department → dept (1.0) - Direct field rename
3. hire_date → hired (1.0) - Direct field rename
4. salary → annual_salary_usd (1.0) - Int to float conversion
5. first_name + last_name → full_name (0.95) - String concatenation

✅ Medium Confidence Patterns (2):
6. is_manager → manager (0.85) - Boolean conversion ("Yes"/"No" → true/false)
7. salary format (0.80) - Currency formatting
```

#### Threshold Selection

```
Select threshold:
  [1] Conservative (0.8) → 6/7 patterns
  [2] Balanced (0.7) → 7/7 patterns ✅ RECOMMENDED
  [3] Aggressive (0.6) → 7/7 patterns

Your choice: 2  (Balanced)
```

**Why Balanced**:
- All patterns have confidence ≥ 0.8
- High-quality, consistent data
- Boolean conversion is reliable ("Yes"/"No" pattern)
- No low-confidence patterns to exclude

#### Generated Code Preview

```python
# output/employee_extractor.py
from extract_transform_platform.core import IDataExtractor
from typing import Dict, Optional, Any

class EmployeeExtractor(IDataExtractor):
    """Extract employee data from Excel roster."""

    async def extract(self, row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Transform employee row to output format.

        Patterns detected (confidence threshold: 0.7):
        - 5 high confidence patterns (100%)
        - 2 medium confidence patterns (100%)
        - 0 patterns excluded
        """
        try:
            return {
                "id": row["employee_id"],  # Confidence: 1.0
                "full_name": f"{row['first_name']} {row['last_name']}",  # 0.95
                "dept": row["department"],  # Confidence: 1.0
                "hired": row["hire_date"],  # Confidence: 1.0
                "annual_salary_usd": float(row["salary"]),  # 1.0
                "manager": row["is_manager"].lower() == "yes"  # 0.85
            }
        except (KeyError, ValueError) as e:
            self.logger.error(f"Extraction failed: {e}")
            return None
```

**Result**: Clean, production-ready code with all patterns included

---

### Example 2: Web Scraping (Noisy Data)

**Scenario**: Extracting article data from web pages with inconsistent structure

**Data Source**: Web scraping via Jina.ai (JS-heavy sites)
**Quality**: Medium (some fields missing, format variations)
**Recommendation**: Use **Conservative (0.8)** threshold

#### Project Setup

```bash
cd projects/
mkdir news_scraper
cd news_scraper

# Create project.yaml
cat > project.yaml <<EOF
project:
  name: news_scraper
  description: Extract article metadata from news sites
  version: 1.0.0

data_sources:
  - type: url
    name: jina_reader
    config:
      api_url: https://r.jina.ai/
      auth:
        type: bearer
        token_env: JINA_API_KEY

examples:
  - input:
      # Example from TechCrunch
      url: "https://techcrunch.com/article"
      markdown: "# AI Startup Raises $50M\n\nBy Jane Doe\n\nPublished: 2025-01-15..."
    output:
      title: "AI Startup Raises $50M"
      author: "Jane Doe"
      published_date: "2025-01-15"
      category: "Technology"

  - input:
      # Example from The Verge (different format)
      url: "https://theverge.com/article"
      markdown: "# New iPhone Released\n\nWritten by John Smith\n\n01/20/2025..."
    output:
      title: "New iPhone Released"
      author: "John Smith"
      published_date: "2025-01-20"
      category: "Technology"

  - input:
      # Example from blog (missing author)
      url: "https://blog.example.com/post"
      markdown: "# Product Launch\n\nPosted on Jan 25, 2025..."
    output:
      title: "Product Launch"
      author: null
      published_date: "2025-01-25"
      category: "Business"
EOF
```

#### Pattern Detection Results

```bash
edgar-analyzer project generate news_scraper

# Output:
┌─────────────────────────────────────────────┐
│      Pattern Detection Complete            │
├─────────────────────────────────────────────┤
│ Detected 6 patterns from 3 examples:       │
│   • 2 high confidence (≥ 0.9)              │
│   • 2 medium confidence (0.7-0.89)         │
│   • 2 low confidence (< 0.7)               │
└─────────────────────────────────────────────┘
```

#### Pattern Breakdown

```
✅ High Confidence Patterns (2):
1. title extraction (1.0) - Extract from markdown H1
2. category classification (0.95) - URL-based category detection

⚠️ Medium Confidence Patterns (2):
3. published_date parsing (0.85) - Multiple date formats
4. url → source mapping (0.75) - Domain extraction

❌ Low Confidence Patterns (2):
5. author extraction (0.65) - Inconsistent format ("By", "Written by", missing)
6. reading_time calculation (0.60) - Not present in all examples
```

#### Threshold Selection

```
Select threshold:
  [1] Conservative (0.8) → 4/6 patterns ✅ RECOMMENDED
  [2] Balanced (0.7) → 5/6 patterns
  [3] Aggressive (0.6) → 6/6 patterns

Your choice: 1  (Conservative)
```

**Why Conservative**:
- Web data quality is inconsistent
- Author extraction is unreliable (0.65 confidence)
- Reading time calculation is speculative (0.60 confidence)
- Better to exclude unreliable patterns for production
- Can add custom extractor logic for edge cases

#### Pattern Review

```
┌──────────────────────────────────────────────────────────┐
│        Pattern Review (Threshold: 0.8)                   │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ ✅ Patterns Included (4):                                │
│   title extraction       (extraction, 1.0)              │
│   category classification (classification, 0.95)        │
│   published_date parsing (parsing, 0.85)                │
│   url → source mapping   (extraction, 0.75) ⚠️          │
│                                                          │
│ ❌ Patterns Excluded (2):                                │
│   author extraction      (extraction, 0.65)             │
│     ℹ️  Inconsistent format across sources               │
│     💡 Recommendation: Add custom fallback logic         │
│                                                          │
│   reading_time calculation (calculation, 0.60)          │
│     ℹ️  Not present in all examples                      │
│     💡 Recommendation: Make optional field               │
│                                                          │
└──────────────────────────────────────────────────────────┘

⚠️  Warning: 1 pattern near threshold (0.75)
    Consider reviewing: url → source mapping
```

#### Generated Code with Exclusions

```python
# output/news_extractor.py
from extract_transform_platform.core import IDataExtractor
from typing import Dict, Optional, Any
import re
from datetime import datetime

class NewsExtractor(IDataExtractor):
    """Extract article metadata from web scraping.

    Patterns detected (confidence threshold: 0.8):
    - 2 high confidence patterns (included)
    - 2 medium confidence patterns (included)
    - 2 low confidence patterns (excluded)
    """

    async def extract(self, markdown: str, url: str) -> Optional[Dict[str, Any]]:
        """Extract article metadata from markdown content."""
        try:
            # High confidence pattern (1.0)
            title = self._extract_title(markdown)

            # High confidence pattern (0.95)
            category = self._classify_category(url)

            # Medium confidence pattern (0.85)
            published_date = self._parse_date(markdown)

            # Medium confidence pattern (0.75) - near threshold
            source = self._extract_source(url)

            # EXCLUDED: author extraction (0.65)
            # Reason: Inconsistent format across sources
            # TODO: Add custom fallback logic if needed

            # EXCLUDED: reading_time calculation (0.60)
            # Reason: Not present in all examples
            # TODO: Make optional field or calculate from word count

            return {
                "title": title,
                "category": category,
                "published_date": published_date,
                "source": source,
                # Author and reading_time excluded due to low confidence
            }
        except Exception as e:
            self.logger.error(f"Extraction failed: {e}")
            return None

    def _extract_title(self, markdown: str) -> str:
        """Extract title from markdown H1 (confidence: 1.0)."""
        match = re.search(r'^# (.+)$', markdown, re.MULTILINE)
        return match.group(1) if match else ""

    # ... other methods
```

**Result**: Production-ready code with only reliable patterns, clear TODOs for excluded patterns

---

### Example 3: Legacy Data (Mixed Quality)

**Scenario**: Migrating data from legacy system with inconsistent format

**Data Source**: CSV export from legacy database
**Quality**: Mixed (some fields standardized, others not)
**Recommendation**: Use **Custom (0.75)** threshold

#### Context

```
Legacy system data characteristics:
- Core fields: Consistent (customer_id, name, email)
- Address fields: Partially consistent
- Phone numbers: Multiple formats
- Status codes: Inconsistent mapping
- Notes: Free text (unreliable)
```

#### Pattern Detection Results

```
Detected 12 patterns from 5 examples:
  • 4 high confidence (≥ 0.9)    - Core fields
  • 4 medium confidence (0.7-0.89) - Address, phone
  • 4 low confidence (< 0.7)     - Status, notes
```

#### Threshold Analysis

```
Threshold Options:
  0.8 (Conservative) → 6/12 patterns (50%) - Too restrictive
  0.7 (Balanced) → 8/12 patterns (67%) - May include unreliable patterns
  0.75 (Custom) → 7/12 patterns (58%) - Good balance ✅
```

**Why Custom 0.75**:
- Conservative (0.8) excludes useful address patterns (0.75-0.79)
- Balanced (0.7) includes questionable status mapping (0.70)
- Custom 0.75 includes address patterns, excludes status mapping
- Fine-tuned control for mixed-quality data

#### Command

```bash
# Use custom threshold between presets
edgar-analyzer project generate legacy_migration --confidence-threshold 0.75
```

#### Result

```
✅ Analysis Complete
   Threshold:     0.75 (Custom)
   Patterns:      7 included, 5 excluded

Included:
  ✅ customer_id        (1.0) - Core field
  ✅ name               (1.0) - Core field
  ✅ email              (0.95) - Core field
  ✅ created_date       (0.90) - Core field
  ✅ street_address     (0.78) - Address component
  ✅ city               (0.77) - Address component
  ✅ phone_normalized   (0.76) - Phone formatting

Excluded:
  ❌ status_mapping     (0.70) - Inconsistent codes
  ❌ notes_extraction   (0.65) - Free text
  ❌ zip_code          (0.62) - Multiple formats
  ❌ state_abbr        (0.58) - Inconsistent
  ❌ alt_phone         (0.55) - Optional field
```

**Benefits of Custom 0.75**:
- Includes essential address fields (just below 0.8)
- Excludes unreliable status mapping (just above 0.7)
- Provides granular control for edge cases
- Optimal for legacy data migration

---

### Example 4: Trusted Source (All Patterns)

**Scenario**: Extracting data from well-documented API with consistent schema

**Data Source**: REST API with OpenAPI spec
**Quality**: Excellent (validated schema, consistent responses)
**Recommendation**: Use **Aggressive (0.6)** or even **Custom (0.5)**

#### Why Aggressive/Lower Threshold

```
Trusted source characteristics:
- API schema validated
- Responses consistent
- Documentation comprehensive
- Edge cases documented
- Optional fields clearly marked
```

Even "low confidence" patterns (0.6-0.7) are reliable because:
- Lower confidence often due to **optional fields** (not present in all examples)
- Not because of inconsistent transformation logic
- All patterns follow documented schema

#### Example

```bash
# OpenWeatherMap API - all patterns reliable
edgar-analyzer project generate weather_api --confidence-threshold 0.6

# Result:
Detected 10 patterns:
  • 6 high confidence (≥ 0.9) - Required fields
  • 3 medium confidence (0.7-0.89) - Common optional fields
  • 1 low confidence (< 0.7) - Rare optional field

All 10 patterns included ✅

Pattern with 0.65 confidence:
  "visibility" field (optional in API response)
  Low confidence: Only 2/3 examples had this field
  BUT: When present, transformation is consistent
  Safe to include with null handling
```

#### Generated Code

```python
async def extract(self, response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract weather data (all patterns included)."""
    return {
        # High confidence required fields
        "city": response["name"],  # 1.0
        "temperature": response["main"]["temp"],  # 1.0

        # Medium confidence optional fields
        "humidity": response.get("main", {}).get("humidity"),  # 0.75

        # Low confidence optional field (still included)
        "visibility": response.get("visibility"),  # 0.65
        # Safe because: null handling, documented as optional
    }
```

**When to Use Aggressive for Trusted Sources**:
- OpenAPI/GraphQL schema available
- Comprehensive API documentation
- Consistent response format
- Optional fields clearly marked
- Production API with SLA

---

### Example 5: CI/CD Pipeline (Automated)

**Scenario**: Automated code generation in CI/CD pipeline

**Context**: GitHub Actions workflow generating extractors on commit

**Requirement**: Non-interactive, consistent, production-safe

#### GitHub Actions Workflow

```yaml
# .github/workflows/generate-extractors.yml
name: Generate Extractors

on:
  push:
    branches: [main]
    paths:
      - 'projects/*/examples/*.json'
      - 'projects/*/project.yaml'

jobs:
  generate:
    runs-on: ubuntu-latest

    strategy:
      matrix:
        project:
          # Production projects: Conservative threshold
          - name: customer_data
            threshold: 0.8
            environment: production

          # Internal tools: Balanced threshold
          - name: analytics_dashboard
            threshold: 0.7
            environment: staging

          # Research projects: Aggressive threshold
          - name: data_exploration
            threshold: 0.6
            environment: development

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e .

      - name: Generate extractor
        run: |
          edgar-analyzer project generate ${{ matrix.project.name }} \
            --confidence-threshold ${{ matrix.project.threshold }} \
            --no-interactive

      - name: Run unit tests
        run: |
          pytest projects/${{ matrix.project.name }}/tests/unit/ -v

      - name: Run integration tests (staging/prod only)
        if: matrix.project.environment != 'development'
        run: |
          pytest projects/${{ matrix.project.name }}/tests/integration/ -v

      - name: Deploy to environment
        if: success()
        run: |
          ./scripts/deploy.sh \
            ${{ matrix.project.name }} \
            ${{ matrix.project.environment }}

      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: ${{ matrix.project.name }}-extractor
          path: projects/${{ matrix.project.name }}/output/

      - name: Notify on failure
        if: failure()
        run: |
          curl -X POST ${{ secrets.SLACK_WEBHOOK }} \
            -d "{\"text\":\"Extractor generation failed: ${{ matrix.project.name }}\"}"
```

#### Benefits of Automated Threshold Selection

**Consistency**:
- Same threshold every time
- No human decision required
- Reproducible builds

**Environment-Specific**:
- Production: Conservative (0.8)
- Staging: Balanced (0.7)
- Development: Aggressive (0.6)

**Fast Feedback**:
- No interactive prompts
- Immediate failure on errors
- Automated testing

**Audit Trail**:
- Threshold in version control (workflow file)
- Documented in commit history
- Compliance-friendly

---

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: All Patterns Excluded

**Symptom**:
```
❌ Error: All patterns excluded by threshold 0.9
   No patterns meet minimum confidence requirement
```

**Cause**: Threshold too high for your data quality

**Solutions**:

1. **Lower the threshold**:
```bash
# Try balanced instead of conservative
edgar-analyzer project generate my_project --confidence-threshold 0.7
```

2. **Review pattern confidence**:
```bash
# Check what confidence your patterns have
cat projects/my_project/analysis_results.json | jq '.patterns[].confidence'
```

3. **Add more examples**:
```bash
# More examples → better confidence scores
# Add 1-2 more input/output pairs to examples/
```

4. **Review data quality**:
```
Check if your examples are consistent:
- Same fields in all examples?
- Same data types?
- Same transformation logic?
```

**Example Fix**:
```bash
# Before: 3 examples, highest confidence 0.75
edgar-analyzer project generate my_project --confidence-threshold 0.8
# Error: All patterns excluded

# Add 2 more examples with consistent transformations
# Now: 5 examples, highest confidence 0.90
edgar-analyzer project generate my_project --confidence-threshold 0.8
# Success: 3 patterns included
```

---

#### Issue 2: No Patterns Detected

**Symptom**:
```
⚠️  Warning: No transformation patterns detected
   Ensure examples have input/output fields
```

**Cause**: Not a threshold issue - pattern detection failed

**Root Causes**:

1. **Examples missing required fields**:
```yaml
# ❌ Invalid - missing 'output'
examples:
  - input:
      city: "London"

# ✅ Valid - has both input and output
examples:
  - input:
      city: "London"
    output:
      location: "London"
```

2. **Identical input and output**:
```yaml
# ❌ No transformation detected
examples:
  - input:
      city: "London"
    output:
      city: "London"  # Same field name and value

# ✅ Transformation detected
examples:
  - input:
      city: "London"
    output:
      location: "London"  # Different field name
```

3. **Too few examples**:
```bash
# Minimum: 2 examples recommended
# Optimal: 3-5 examples
```

**Solutions**:

1. **Validate example structure**:
```bash
# Check examples are valid JSON/YAML
python -m json.tool projects/my_project/examples/example1.json
```

2. **Add more examples**:
```bash
# Create at least 2 examples
ls projects/my_project/examples/
# Should show: example1.json, example2.json
```

3. **Ensure transformations exist**:
```
Review examples and ensure:
- Field names change (city → location)
- Data types change (string → int)
- Values transform (degrees → cardinal direction)
```

---

#### Issue 3: Custom Threshold Not Accepted

**Symptom**:
```
❌ Invalid threshold: 1.5
   Threshold must be between 0.0 and 1.0
```

**Cause**: Invalid threshold value

**Valid Range**: 0.0 to 1.0 (inclusive)

**Common Mistakes**:

```bash
# ❌ Invalid - percentage instead of decimal
--confidence-threshold 80  # Should be 0.8

# ❌ Invalid - greater than 1.0
--confidence-threshold 1.5

# ❌ Invalid - negative
--confidence-threshold -0.5

# ❌ Invalid - non-numeric
--confidence-threshold high

# ✅ Valid - decimal between 0.0 and 1.0
--confidence-threshold 0.75
--confidence-threshold 0.8
--confidence-threshold 0.65
--confidence-threshold 1.0
--confidence-threshold 0.0
```

**Solution**:
```bash
# Convert percentage to decimal
80% → 0.8
75% → 0.75
90% → 0.9

# Use decimal format
edgar-analyzer project generate my_project --confidence-threshold 0.8
```

---

#### Issue 4: Interactive Prompt Not Working

**Symptom**:
```
# No prompt appears, uses default threshold
edgar-analyzer project generate my_project
# Expected: Interactive prompt
# Actual: Uses default 0.7 without asking
```

**Causes**:

1. **Non-interactive mode enabled**:
```bash
# Check environment variables
echo $EDGAR_NO_INTERACTIVE  # If "true", prompts disabled

# Unset to enable prompts
unset EDGAR_NO_INTERACTIVE
```

2. **Threshold already set in project config**:
```yaml
# projects/my_project/project.yaml
project:
  confidence_threshold: 0.8  # Pre-set threshold
```

**Solutions**:

1. **Force interactive mode**:
```bash
edgar-analyzer project generate my_project --interactive
```

2. **Remove saved threshold**:
```bash
# Edit project.yaml and remove confidence_threshold field
vim projects/my_project/project.yaml
```

3. **Use fresh project**:
```bash
# Start new project without saved config
edgar-analyzer project create new_project --template minimal
```

---

#### Issue 5: Integration Tests Failing

**Symptom**:
```bash
pytest tests/integration/test_analyze_project_threshold.py
# ModuleNotFoundError: No module named 'aiohttp'
```

**Cause**: Missing dependencies

**Solution**:
```bash
# Install missing dependencies
uv add aiohttp structlog
uv sync --all-extras

# Rerun tests
pytest tests/integration/test_analyze_project_threshold.py -v
```

**Expected Output After Fix**:
```
test_analyze_project_with_interactive_threshold_prompt PASSED [12%]
test_analyze_project_with_cli_threshold_flag PASSED [25%]
test_threshold_filters_patterns_correctly PASSED [37%]
...
===== 8 passed in 2.34s =====
```

---

#### Issue 6: Excluded Pattern Is Important

**Symptom**:
```
Pattern Review:
  ❌ address_parser (0.68) - Excluded

# But address is critical for your use case
```

**Solutions**:

1. **Lower threshold**:
```bash
# Press 'R' in interactive mode to adjust
# Or use CLI flag
edgar-analyzer project generate my_project --confidence-threshold 0.65
```

2. **Add more examples**:
```bash
# Add 2-3 more examples showing address transformation
# Improves confidence score for address_parser pattern
```

3. **Custom extractor**:
```python
# Add manual logic for low-confidence critical patterns
# output/custom_extractor.py

async def extract(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    result = await super().extract(data)

    # Manual address parsing (excluded pattern)
    if "address" in data:
        result["parsed_address"] = self._parse_address(data["address"])

    return result

def _parse_address(self, address: str) -> Dict[str, str]:
    """Custom address parser for low-confidence pattern."""
    # Implement reliable address parsing logic
    ...
```

---

#### Issue 7: Warning About Field Mapping Exclusion

**Symptom**:
```
⚠️  Warning: 2 field mapping patterns excluded
    Field mappings are typically reliable even at medium confidence.
    Consider using "Balanced" (0.7) threshold instead.
```

**Cause**: Conservative threshold (0.8) excluding reliable medium-confidence patterns

**Why This Matters**:
- Field mapping patterns (field renames) are usually reliable
- Medium confidence (0.7-0.79) often due to optional fields, not inconsistency
- Excluding them may reduce coverage unnecessarily

**Solutions**:

1. **Review excluded patterns**:
```
Check pattern review screen:
- Are excluded field mappings for optional fields?
- Are they for core fields?
```

2. **Lower threshold if appropriate**:
```bash
# If excluded patterns are valuable
edgar-analyzer project generate my_project --confidence-threshold 0.7
```

3. **Keep conservative if needed**:
```
If production-critical and you prefer strictness:
- Document excluded patterns
- Add manual field mapping in code
- Accept lower coverage for higher reliability
```

---

### Debugging Tips

#### Enable Debug Logging

```bash
# Set log level to see detailed threshold filtering
export LOG_LEVEL=DEBUG
edgar-analyzer project generate my_project --confidence-threshold 0.7

# Check logs
tail -f logs/edgar_analyzer.log | grep "confidence"
```

#### Inspect Analysis Results

```bash
# View full pattern analysis with confidence scores
cat projects/my_project/analysis_results.json | jq '.patterns[] | {
  type,
  source_path,
  target_path,
  confidence,
  transformation
}'
```

#### Test Different Thresholds

```bash
# Quickly test impact of different thresholds
for threshold in 0.6 0.7 0.8 0.9; do
    echo "Testing threshold: $threshold"
    edgar-analyzer project generate my_project \
        --confidence-threshold $threshold \
        --no-interactive \
        --output-dir /tmp/test_$threshold
    echo "Patterns included: $(cat /tmp/test_$threshold/analysis_results.json | jq '.included_patterns | length')"
done
```

---

## Best Practices

### 1. Start with Balanced (0.7)

**Why**: Works for 80% of projects

```bash
# Default recommendation
edgar-analyzer project generate my_project --confidence-threshold 0.7
```

**Rationale**:
- Filters out only truly unreliable patterns (<70%)
- Includes patterns that work in 70%+ of cases
- Good quality/coverage trade-off
- Validated in employee roster and weather API POCs

**When to Deviate**:
- Production-critical data → Use Conservative (0.8)
- Exploratory research → Use Aggressive (0.6)
- Trusted API → Use Custom (lower)

---

### 2. Review Excluded Patterns Before Proceeding

**Why**: Understand what you're losing

```
Pattern Review Screen:
  ❌ Patterns Excluded (2):
     wind_direction (0.65) - Convert degrees to cardinal
     visibility_km (0.60) - Miles to kilometers
```

**Questions to Ask**:
1. Are excluded patterns important for my use case?
2. Are they optional fields or core fields?
3. Can I add more examples to improve confidence?
4. Should I implement custom logic for these patterns?

**Action Items**:
- **Critical excluded pattern** → Lower threshold or add examples
- **Optional excluded pattern** → Proceed, implement if needed later
- **Unreliable excluded pattern** → Proceed, good decision to exclude

---

### 3. Use Conservative for Production Systems

**Why**: Prioritize reliability over coverage

```bash
# Production deployment
edgar-analyzer project generate customer_data --confidence-threshold 0.8
```

**Production Criteria**:
- Financial data
- Healthcare records
- Compliance-sensitive
- Customer-facing systems
- High SLA requirements

**Benefits**:
- Fewer bugs in generated code
- Lower maintenance burden
- Predictable behavior
- Audit-friendly

**Trade-off**: May need manual implementation for excluded medium-confidence patterns

---

### 4. Use Aggressive for Development/Testing

**Why**: Discover all patterns early

```bash
# Development exploration
edgar-analyzer project generate prototype --confidence-threshold 0.6
```

**Development Use Cases**:
- Proof-of-concept
- Research projects
- Understanding data structure
- Discovering edge cases
- Initial exploration

**Workflow**:
1. Start with aggressive (0.6) to see all patterns
2. Review low-confidence patterns
3. Add more examples or custom logic
4. Increase threshold for production (0.7 or 0.8)

---

### 5. Save Threshold in Project Config

**Why**: Consistency across team and CI/CD

```bash
# Interactive mode will prompt:
Save confidence threshold (0.7) to project config? [Y/n]: Y
```

**Benefits**:
- Team members use same threshold
- CI/CD pipelines consistent
- Documented decision
- Version controlled

**project.yaml**:
```yaml
project:
  name: my_project
  confidence_threshold: 0.7  # Saved threshold
```

**Override When Needed**:
```bash
# CLI flag overrides saved config
edgar-analyzer project generate my_project --confidence-threshold 0.8
```

---

### 6. Add More Examples for Low Confidence

**Problem**: Important pattern has low confidence (0.65)

**Solution**: Add 1-2 more examples showing consistent transformation

**Example**:

**Before** (2 examples, confidence 0.65):
```yaml
examples:
  - input: { "wind": { "deg": 90 } }
    output: { "wind_direction": "E" }

  - input: { "wind": { "deg": 180 } }
    output: { "wind_direction": "S" }

  - input: { "wind": { "deg": 270 } }
    output: { "wind_direction": null }  # Inconsistent!
```

**After** (4 examples, confidence 0.90):
```yaml
examples:
  # Previous examples...

  # Add 2 more consistent examples
  - input: { "wind": { "deg": 270 } }
    output: { "wind_direction": "W" }  # Consistent now

  - input: { "wind": { "deg": 0 } }
    output: { "wind_direction": "N" }
```

**Result**: Confidence increases from 0.65 to 0.90 (3/3 → 4/4 consistency)

---

### 7. Document Threshold Choices

**Why**: Help future maintainers understand decisions

**In project README**:
```markdown
# Project Configuration

## Confidence Threshold: 0.8 (Conservative)

**Rationale**: Production-critical customer data requires high reliability.

**Patterns Excluded**:
- `discount_percentage` (0.72) - Inconsistent calculation, implemented manually
- `loyalty_tier` (0.68) - Complex rules, custom extractor added

**Last Reviewed**: 2025-12-03
**Next Review**: After 100 production runs
```

**In Commit Messages**:
```bash
git commit -m "Set confidence threshold to 0.8 for production data

Conservative threshold chosen for customer_data project due to:
- Production-critical data (customer records)
- Regulatory compliance requirements
- 2 medium-confidence patterns excluded (discount, loyalty)
- Manual implementations added for excluded patterns

Ticket: PROJ-123"
```

---

### 8. Monitor Production Patterns

**Why**: Validate threshold choice with real data

**Monitoring Strategy**:

```python
# Add metrics to generated extractor
class CustomerExtractor(IDataExtractor):
    def __init__(self):
        super().__init__()
        self.pattern_success_count = {}
        self.pattern_failure_count = {}

    async def extract(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        result = {}

        # Track success rate for each pattern
        try:
            result["customer_id"] = data["id"]
            self.pattern_success_count["customer_id"] = \
                self.pattern_success_count.get("customer_id", 0) + 1
        except KeyError:
            self.pattern_failure_count["customer_id"] = \
                self.pattern_failure_count.get("customer_id", 0) + 1

        # ... other patterns

        return result

    def get_metrics(self) -> Dict[str, Any]:
        """Get pattern success/failure metrics."""
        return {
            "success": self.pattern_success_count,
            "failure": self.pattern_failure_count
        }
```

**Analyze Metrics**:
```bash
# After 1000 production extractions
edgar-analyzer analyze-metrics customer_data

# Output:
Pattern Success Rates:
  customer_id:       1000/1000 (100%) ✅
  email:              998/1000 (99.8%) ✅
  phone_normalized:   950/1000 (95.0%) ⚠️
  address_parsed:     920/1000 (92.0%) ⚠️

# Action: Review phone_normalized and address_parsed patterns
```

**Adjust Threshold**:
```bash
# If patterns consistently fail in production
# Consider raising threshold or adding more examples
edgar-analyzer project generate customer_data --confidence-threshold 0.85
```

---

### 9. Use Different Thresholds Per Environment

**Why**: Match risk tolerance to environment

**Example**:

```bash
# Development: Aggressive (see all patterns)
export EDGAR_ENV=development
export CONFIDENCE_THRESHOLD=0.6

# Staging: Balanced (realistic testing)
export EDGAR_ENV=staging
export CONFIDENCE_THRESHOLD=0.7

# Production: Conservative (prioritize reliability)
export EDGAR_ENV=production
export CONFIDENCE_THRESHOLD=0.8
```

**Deployment Script**:
```bash
#!/bin/bash
# deploy.sh - Environment-specific threshold

ENV=$1  # development, staging, production
PROJECT=$2

case $ENV in
    development)
        THRESHOLD=0.6
        ;;
    staging)
        THRESHOLD=0.7
        ;;
    production)
        THRESHOLD=0.8
        ;;
    *)
        echo "Unknown environment: $ENV"
        exit 1
        ;;
esac

edgar-analyzer project generate $PROJECT \
    --confidence-threshold $THRESHOLD \
    --no-interactive

echo "Deployed $PROJECT to $ENV with threshold $THRESHOLD"
```

---

### 10. Review Threshold Periodically

**Why**: Data quality and patterns evolve

**Review Triggers**:
- After adding new examples
- After 6 months in production
- After significant data source changes
- When success rate drops below 95%

**Review Process**:
```bash
# 1. Check current threshold
cat projects/my_project/project.yaml | grep confidence_threshold

# 2. Analyze current pattern performance
edgar-analyzer analyze-metrics my_project

# 3. Re-run pattern detection with current examples
edgar-analyzer project generate my_project --interactive

# 4. Compare old vs new pattern confidence
diff <(cat old_analysis.json | jq '.patterns[].confidence') \
     <(cat new_analysis.json | jq '.patterns[].confidence')

# 5. Adjust threshold if needed
# Update project.yaml with new threshold
```

**Document Review**:
```markdown
# Threshold Review Log

## 2025-12-03 - Initial Configuration
- Threshold: 0.7 (Balanced)
- Patterns: 8 detected, 7 included
- Rationale: Standard web API extraction

## 2026-06-01 - 6-Month Review
- Current threshold: 0.7
- Production success rate: 97.5%
- Recommendation: No change needed
- Next review: 2026-12-01
```

---

## API Reference

### Command-Line Interface

```bash
edgar-analyzer project generate PROJECT_NAME [OPTIONS]
```

#### Options

**`--confidence-threshold FLOAT` / `-t FLOAT`**
- **Description**: Set minimum confidence threshold for pattern filtering
- **Range**: 0.0 to 1.0 (inclusive)
- **Default**: Interactive prompt (if not provided)
- **Presets**:
  - `0.8` - Conservative (high confidence only)
  - `0.7` - Balanced (high + medium confidence) [RECOMMENDED]
  - `0.6` - Aggressive (all patterns including low confidence)

**`--interactive` / `--no-interactive`**
- **Description**: Enable/disable interactive prompts
- **Default**: Interactive mode enabled
- **Use Case**: Set `--no-interactive` for automation and CI/CD

**`--save-threshold` / `--no-save-threshold`**
- **Description**: Save threshold to project configuration
- **Default**: Prompt user (interactive mode only)
- **Use Case**: Set `--no-save-threshold` to prevent config updates

**`--output-dir PATH`**
- **Description**: Custom output directory for generated code
- **Default**: `projects/PROJECT_NAME/output/`
- **Use Case**: Testing or CI/CD artifacts

**`--verbose` / `-v`**
- **Description**: Enable verbose output
- **Default**: Standard output
- **Use Case**: Debugging and detailed logging

---

### Python API

```python
from extract_transform_platform.services.analysis import (
    PatternFilterService,
    FilteredParsedExamples
)
```

#### PatternFilterService

**Class**: `PatternFilterService`

**Purpose**: Filter patterns by confidence threshold

**Methods**:

##### `filter_patterns()`

```python
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

    Raises:
        ValueError: If threshold not in valid range (0.0-1.0)

    Example:
        >>> service = PatternFilterService()
        >>> filtered = service.filter_patterns(parsed, 0.7)
        >>> print(f"Included: {len(filtered.included_patterns)}")
        >>> print(f"Excluded: {len(filtered.excluded_patterns)}")
    """
```

##### `get_threshold_presets()`

```python
@staticmethod
def get_threshold_presets() -> Dict[str, Dict[str, Any]]:
    """Get available threshold presets.

    Returns:
        Dict mapping preset names to threshold info

    Example:
        >>> presets = PatternFilterService.get_threshold_presets()
        >>> print(presets["balanced"]["threshold"])  # 0.7
        >>> print(presets["balanced"]["description"])
        # "Include high + medium confidence patterns"
    """
```

##### `format_confidence_summary()`

```python
@staticmethod
def format_confidence_summary(parsed: ParsedExamples) -> str:
    """Format confidence distribution summary for display.

    Args:
        parsed: ParsedExamples with patterns

    Returns:
        Formatted string with confidence breakdown

    Example:
        >>> summary = PatternFilterService.format_confidence_summary(parsed)
        >>> print(summary)
        # Detected 5 patterns:
        #   • 3 high confidence (≥ 0.9)   60%
        #   • 1 medium confidence (0.7-0.89) 20%
        #   • 1 low confidence (< 0.7)   20%
    """
```

---

#### FilteredParsedExamples

**Class**: `FilteredParsedExamples`

**Purpose**: Represents parsed examples with confidence filtering applied

**Attributes**:

```python
@dataclass
class FilteredParsedExamples:
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
```

**Properties**:

##### `patterns`

```python
@property
def patterns(self) -> List[Pattern]:
    """Alias for included_patterns (backward compatibility)."""
```

##### `high_confidence_patterns`

```python
@property
def high_confidence_patterns(self) -> List[Pattern]:
    """Get high confidence patterns (≥ 0.9) from included patterns."""
```

##### `medium_confidence_patterns`

```python
@property
def medium_confidence_patterns(self) -> List[Pattern]:
    """Get medium confidence patterns (0.7-0.89) from included patterns."""
```

##### `low_confidence_patterns`

```python
@property
def low_confidence_patterns(self) -> List[Pattern]:
    """Get low confidence patterns (< 0.7) from included patterns."""
```

---

### Configuration Schema

#### project.yaml

```yaml
project:
  name: my_project
  description: Project description
  version: 1.0.0

  # Confidence threshold (optional)
  confidence_threshold: 0.7
```

**Field**: `confidence_threshold`
- **Type**: `float` (optional)
- **Range**: 0.0 to 1.0
- **Default**: `null` (prompts user in interactive mode)
- **Description**: Minimum confidence threshold for pattern filtering
- **Usage**: Automatically used in future `project generate` runs

---

## Related Documentation

- **[Platform Usage Guide](PLATFORM_USAGE.md)** - Complete platform usage examples
- **[Pattern Detection Guide](PATTERN_DETECTION.md)** - Detailed pattern types and detection
- **[CLI Usage Guide](CLI_USAGE.md)** - Complete CLI reference
- **[Quick Start Guide](QUICK_START.md)** - 5-minute setup guide
- **[Troubleshooting Guide](TROUBLESHOOTING.md)** - Common issues and solutions

---

## Support

### Get Help

- **Documentation**: [docs/](../../)
- **Issues**: [GitHub Issues](https://github.com/bobmatnyc/zach-edgar/issues)
- **Discussions**: [GitHub Discussions](https://github.com/bobmatnyc/zach-edgar/discussions)

### Report Bugs

Found a bug with confidence threshold selection? Please report it:

1. Check [existing issues](https://github.com/bobmatnyc/zach-edgar/issues)
2. Create new issue with:
   - Project configuration
   - Threshold used
   - Expected behavior
   - Actual behavior
   - Pattern detection results (if relevant)

---

**Last Updated**: 2025-12-03
**Feature Version**: Phase 1 MVP (Ticket 1M-362)
**Next Update**: Phase 2 (Pattern config persistence, additional UX enhancements)
