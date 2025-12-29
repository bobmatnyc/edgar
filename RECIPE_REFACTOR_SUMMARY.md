# Recipe Refactor Summary: Directory-Based Recipes

## Overview
Successfully refactored the recipe system from single YAML files to directory-based structure with input/output subdirectories.

## Changes Made

### 1. Updated Schema (`src/edgar_analyzer/recipes/schema.py`)

**Added:**
- `recipe_dir: Optional[Path]` field to track recipe directory location
- `@computed_field` properties:
  - `input_dir` → `{recipe_dir}/input/`
  - `output_dir` → `{recipe_dir}/output/`
  - `config_path` → `{recipe_dir}/config.yaml`

**Benefits:**
- Recipes know their location on disk
- Easy access to input/output directories
- Self-contained recipe packages

### 2. Updated Loader (`src/edgar_analyzer/recipes/loader.py`)

**Modified Functions:**
- `load_recipe(recipe_dir)` - Now takes directory path instead of file path
  - Loads `config.yaml` from directory
  - Sets `recipe_dir` on Recipe object
  - Validates directory structure

- `discover_recipes(directory)` - Now discovers recipe directories
  - Searches for directories containing `config.yaml`
  - Only processes direct children (avoids nested config files)

**Added Function:**
- `ensure_recipe_dirs(recipe)` - Creates input/output directories if missing

### 3. Migrated Existing Recipes

**New Directory Structure:**
```
recipes/
├── fortune100/
│   ├── config.yaml      # Moved from fortune100.yaml
│   ├── input/           # New - for input files
│   └── output/          # New - for generated files
├── sct_extraction/
│   ├── config.yaml      # Moved from sct_extraction.yaml
│   ├── input/
│   └── output/
└── tax_extraction/
    ├── config.yaml      # Moved from tax_extraction.yaml
    ├── input/
    └── output/
```

**Updated Sub-Recipe References in fortune100/config.yaml:**
- Changed `recipe: sct_extraction.yaml` → `recipe: sct_extraction`
- Changed `recipe: tax_extraction.yaml` → `recipe: tax_extraction`

### 4. Updated CLI Commands (`src/edgar_analyzer/cli/commands/recipes.py`)

**Modified Commands:**

#### `recipes list`
- Now discovers recipe directories (not YAML files)
- Added `--verbose` flag shows directory location
- Displays helpful tip when no recipes found

#### `recipes validate <recipe_dir>`
- Takes directory path instead of file path
- Validates `config.yaml` within directory
- Example: `edgar recipes validate recipes/fortune100`

#### `recipes info <recipe_dir>`
- Takes directory path instead of file path
- Shows recipe metadata from directory
- Example: `edgar recipes info recipes/fortune100`

#### **NEW** `recipes init <name>`
- Creates new recipe directory structure
- Generates `config.yaml` template with examples
- Creates `input/` and `output/` directories
- Generates `README.md` with usage instructions
- Options:
  - `--directory` - Parent directory (default: recipes/)
  - `--title` - Recipe title
  - `--description` - Recipe description

**Example:**
```bash
edgar recipes init my_recipe
edgar recipes init fraud_detection --title "Fraud Detection Pipeline"
```

## Files Modified

1. **`src/edgar_analyzer/recipes/schema.py`**
   - Added `recipe_dir` field
   - Added computed properties for paths
   - Updated docstrings

2. **`src/edgar_analyzer/recipes/loader.py`**
   - Refactored `load_recipe()` for directory loading
   - Refactored `discover_recipes()` for directory discovery
   - Added `ensure_recipe_dirs()` helper

3. **`src/edgar_analyzer/cli/commands/recipes.py`**
   - Updated all commands to use directory paths
   - Added `recipes init` command
   - Improved error messages and help text

4. **Recipe Files (migrated):**
   - `recipes/fortune100.yaml` → `recipes/fortune100/config.yaml`
   - `recipes/sct_extraction.yaml` → `recipes/sct_extraction/config.yaml`
   - `recipes/tax_extraction.yaml` → `recipes/tax_extraction/config.yaml`

## Breaking Changes

### For Users
- **Before:** `edgar recipes validate recipes/fortune100.yaml`
- **After:** `edgar recipes validate recipes/fortune100`

- **Before:** `edgar recipes info recipes/fortune100.yaml`
- **After:** `edgar recipes info recipes/fortune100`

### For Sub-Recipe References (in config.yaml)
- **Before:** `recipe: sct_extraction.yaml`
- **After:** `recipe: sct_extraction`

## Benefits of New Structure

### 1. Self-Contained Recipes
- Each recipe is a standalone directory package
- Input data can be versioned with recipe
- Output data is organized per recipe

### 2. Better Organization
```
fortune100/
├── config.yaml           # Recipe definition
├── input/
│   ├── companies.csv     # Input data (e.g., company lists)
│   └── filters.json      # Configuration files
├── output/
│   ├── results.json      # Generated results
│   ├── reports.xlsx      # Generated reports
│   └── logs/             # Execution logs
└── README.md             # Recipe documentation
```

### 3. Portability
- Copy entire recipe directory to share
- All inputs/outputs stay together
- Easy to version control

### 4. Extensibility
- Can add README.md per recipe
- Can add tests/ directory
- Can add templates/ directory
- Can add docs/ directory

## Usage Examples

### List Recipes
```bash
# Basic list
edgar recipes list

# Verbose (shows directories)
edgar recipes list --verbose
```

### Validate Recipe
```bash
edgar recipes validate recipes/fortune100
edgar recipes validate recipes/sct_extraction --verbose
```

### Show Recipe Info
```bash
edgar recipes info recipes/fortune100
edgar recipes info recipes/tax_extraction --show-steps
```

### Create New Recipe
```bash
# Basic scaffold
edgar recipes init my_recipe

# With metadata
edgar recipes init fraud_detection \
  --title "Fraud Detection Pipeline" \
  --description "Detect fraudulent transactions using ML"

# In custom directory
edgar recipes init custom --directory my_recipes/
```

### Recipe Structure After Init
```
recipes/my_recipe/
├── config.yaml     # Template with examples
├── input/          # Empty directory
├── output/         # Empty directory
└── README.md       # Auto-generated documentation
```

## Migration Guide

### For Existing Recipe Files

1. **Create directory:**
   ```bash
   mkdir -p recipes/my_recipe/{input,output}
   ```

2. **Move YAML file:**
   ```bash
   mv recipes/my_recipe.yaml recipes/my_recipe/config.yaml
   ```

3. **Update sub-recipe references:**
   ```yaml
   # In config.yaml
   # Before:
   recipe: other_recipe.yaml
   
   # After:
   recipe: other_recipe
   ```

### For Custom Recipe Loaders

If you have custom code loading recipes:

**Before:**
```python
from edgar_analyzer.recipes import load_recipe

recipe = load_recipe("recipes/fortune100.yaml")
```

**After:**
```python
from edgar_analyzer.recipes import load_recipe, ensure_recipe_dirs

recipe = load_recipe("recipes/fortune100")

# Ensure input/output directories exist
ensure_recipe_dirs(recipe)

# Access directories
print(f"Input: {recipe.input_dir}")
print(f"Output: {recipe.output_dir}")
```

## Testing

### Verify Migration
```bash
# List all recipes (should show 3)
edgar recipes list

# Validate each recipe
edgar recipes validate recipes/fortune100
edgar recipes validate recipes/sct_extraction
edgar recipes validate recipes/tax_extraction

# Check info
edgar recipes info recipes/fortune100 --show-steps
```

### Test New Command
```bash
# Create test recipe
edgar recipes init test_recipe

# Verify structure
ls -la recipes/test_recipe/

# Validate it
edgar recipes validate recipes/test_recipe
```

## LOC Delta

**Lines Added:** ~250 lines
- `recipes.py`: +175 lines (init command + updated commands)
- `schema.py`: +40 lines (computed fields + docstrings)
- `loader.py`: +35 lines (refactored functions + ensure_recipe_dirs)

**Lines Removed:** ~30 lines
- Old YAML file paths in documentation
- Simplified discovery logic (no rglob for .yaml/.yml)

**Net Change:** +220 lines

**Files Deleted:** 0 (moved to new locations)

## Next Steps

1. **Add README.md to existing recipes:**
   - Document fortune100 pipeline
   - Document sct_extraction process
   - Document tax_extraction process

2. **Update documentation:**
   - Update main README with new recipe structure
   - Add recipe development guide
   - Add recipe best practices

3. **Add tests:**
   - Test directory-based loading
   - Test ensure_recipe_dirs()
   - Test recipes init command
   - Test sub-recipe resolution

4. **Future Enhancements:**
   - Recipe templates system
   - Recipe validation schemas
   - Recipe dependency management
   - Recipe versioning

## Compatibility Notes

- **Backward Compatible:** No (breaking change)
- **Migration Path:** Automated script could be created
- **Rollback:** Old YAML files were moved, not deleted (in git history)

## Phase

**Phase:** MVP Enhancement (Phase 1.5)
- Core functionality refactored
- Better organization for future features
- Foundation for advanced recipe features
