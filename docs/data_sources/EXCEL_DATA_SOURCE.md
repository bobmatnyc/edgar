# ExcelDataSource Documentation

## Overview

`ExcelDataSource` is a data source class for reading Excel files (.xlsx, .xls) with schema-aware parsing capabilities. It extends `BaseDataSource` and provides seamless integration with the EDGAR platform's data extraction pipeline.

## Installation

Required dependencies (already included in project):
```bash
pip install pandas>=2.0.0 openpyxl>=3.1.0
```

## Basic Usage

```python
from pathlib import Path
from edgar_analyzer.data_sources import ExcelDataSource

# Create data source
source = ExcelDataSource(
    file_path=Path("employees.xlsx"),
    sheet_name="Roster",  # or 0 for first sheet
    header_row=0
)

# Validate configuration
is_valid = await source.validate_config()

# Fetch data
result = await source.fetch()

# Access rows
for row in result['rows']:
    print(row['Employee Name'], row['Department'])
```

## Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `file_path` | `Path` or `str` | Required | Path to Excel file (.xlsx or .xls) |
| `sheet_name` | `str` or `int` | `0` | Sheet name (string) or index (0-based int) |
| `header_row` | `int` | `0` | Row number to use as column headers (0-indexed) |
| `skip_rows` | `int` or `None` | `None` | Number of rows to skip after header |
| `max_rows` | `int` or `None` | `None` | Maximum rows to read (for large files) |
| `encoding` | `str` | `"utf-8"` | File encoding |

## Return Format

The `fetch()` method returns a dictionary with:

```python
{
    'rows': List[Dict],        # Each row as dictionary
    'columns': List[str],      # Column names
    'sheet_name': str,         # Active sheet name
    'row_count': int,          # Number of data rows
    'source_file': str,        # Original file path
    'file_name': str           # File name only
}
```

## Features

### ✅ Supported
- Single sheet reading
- Sheet selection by name or index
- Automatic type detection (int, float, str, bool)
- NaN handling (converts to None for JSON compatibility)
- Header row specification
- Row limiting (for large files)
- Configuration validation
- Error handling with specific exceptions

### 🔜 Future (Phase 2)
- Multi-sheet batch reading
- Merged cell handling
- Formula extraction
- Large file streaming (chunked reading)

## Examples

### Example 1: Read First Sheet
```python
source = ExcelDataSource(Path("data.xlsx"))
result = await source.fetch()
print(f"Found {result['row_count']} rows")
```

### Example 2: Read Specific Sheet by Name
```python
source = ExcelDataSource(
    Path("report.xlsx"),
    sheet_name="Q1 Results"
)
result = await source.fetch()
```

### Example 3: Read with Custom Header Row
```python
source = ExcelDataSource(
    Path("report.xlsx"),
    sheet_name="Summary",
    header_row=2  # Skip 2 title rows
)
result = await source.fetch()
```

### Example 4: Limit Rows for Large Files
```python
source = ExcelDataSource(
    Path("large_dataset.xlsx"),
    max_rows=1000  # Only read first 1000 rows
)
result = await source.fetch()
```

### Example 5: Validate Before Reading
```python
source = ExcelDataSource(Path("data.xlsx"), sheet_name="Sheet1")

if await source.validate_config():
    result = await source.fetch()
    # Process data
else:
    print("Invalid configuration")
```

## Data Type Handling

### Automatic Type Conversion
| Excel Type | Python Type | Example |
|-----------|-------------|---------|
| Text | `str` | "John Doe" |
| Number (integer) | `int` | 12345 |
| Number (decimal) | `float` | 123.45 |
| Boolean | `bool` | True, False |
| Date | `str` | "2023-01-15" |
| Empty cell | `None` | None |

### NaN Handling
Excel's empty cells are represented as NaN in pandas. `ExcelDataSource` automatically converts NaN to None for:
- JSON serialization compatibility
- Pythonic null checking (`if value is None`)
- Database insertion compatibility

```python
# NaN is automatically converted to None
result = await source.fetch()
for row in result['rows']:
    if row['bonus'] is None:  # Works correctly
        print("No bonus")
```

## Error Handling

| Error | When Raised | How to Handle |
|-------|-------------|---------------|
| `FileNotFoundError` | Excel file doesn't exist | Check file path |
| `ValueError` | Invalid file extension or sheet not found | Verify extension is .xlsx or .xls |
| `RuntimeError` | Excel parsing fails | Check file corruption |
| `ImportError` | pandas/openpyxl not installed | Install dependencies |

### Example Error Handling
```python
try:
    source = ExcelDataSource(Path("data.xlsx"), sheet_name="Results")
    result = await source.fetch()
except FileNotFoundError:
    print("Excel file not found")
except ValueError as e:
    print(f"Invalid configuration: {e}")
except RuntimeError as e:
    print(f"Excel parsing failed: {e}")
```

## SchemaAnalyzer Integration

`ExcelDataSource` is designed to work seamlessly with `SchemaAnalyzer`:

```python
from edgar_analyzer.data_sources import ExcelDataSource
from edgar_analyzer.analyzers import SchemaAnalyzer

# Read Excel file
source = ExcelDataSource(Path("employees.xlsx"))
result = await source.fetch()

# Analyze schema
analyzer = SchemaAnalyzer()
schema = await analyzer.analyze(result['rows'])

print(f"Detected fields: {list(schema.fields.keys())}")
```

## Performance Considerations

### Time Complexity
- **Read operation**: O(r × c) where r = rows, c = columns
- **NaN cleaning**: O(r × c) for full data scan
- **Type detection**: Handled by pandas (optimized C code)

### Space Complexity
- **Memory usage**: O(r × c) - full sheet loaded into memory
- **For large files**: Use `max_rows` parameter to limit memory

### Optimization Tips
1. **Large files**: Use `max_rows` to read in chunks
2. **Multiple sheets**: Read only required sheets by name
3. **Skip irrelevant rows**: Use `header_row` to skip title rows
4. **Type hints**: Pandas auto-detects types efficiently

## Design Decisions

### Why No Caching?
- Files are already local (caching adds overhead)
- File changes should be reflected immediately
- Avoids memory duplication

### Why No Rate Limiting?
- Local I/O doesn't need throttling
- No API rate limits to worry about

### Why No Retries?
- Local file operations fail fast
- Retrying won't fix missing/corrupted files
- Better to fail explicitly and let user fix issue

### Why NaN → None Conversion?
- JSON doesn't support NaN (serialization fails)
- None is more Pythonic than NaN
- Easier null checking: `if value is None`

## Comparison with FileDataSource

| Feature | FileDataSource | ExcelDataSource |
|---------|---------------|-----------------|
| CSV support | ✅ | ❌ |
| Excel support | ❌ | ✅ |
| JSON support | ✅ | ❌ |
| YAML support | ✅ | ❌ |
| Multi-sheet | ❌ | ✅ (planned) |
| Type detection | Via pandas | Via pandas |
| Return format | List[Dict] | List[Dict] |

## Troubleshooting

### Problem: "Excel file not found"
**Solution**: Check file path exists and is absolute
```python
file_path = Path("data.xlsx").absolute()
print(f"Checking: {file_path}")
```

### Problem: "Sheet 'X' not found"
**Solution**: List available sheets first
```python
import pandas as pd
with pd.ExcelFile("data.xlsx") as xls:
    print(f"Available sheets: {xls.sheet_names}")
```

### Problem: "Unsupported file type"
**Solution**: Verify file has .xlsx or .xls extension
```python
file_path = Path("data.xlsx")
print(f"Extension: {file_path.suffix}")
```

### Problem: NaN values in output
**Solution**: This shouldn't happen (bug if it does)
```python
# NaN should be converted to None automatically
# If you see NaN, please report as bug
```

## Best Practices

1. **Always validate configuration first**
   ```python
   if await source.validate_config():
       result = await source.fetch()
   ```

2. **Use absolute paths**
   ```python
   file_path = Path("data.xlsx").absolute()
   ```

3. **Specify sheet by name (more readable)**
   ```python
   source = ExcelDataSource(path, sheet_name="Results")
   ```

4. **Limit rows for large files**
   ```python
   source = ExcelDataSource(path, max_rows=1000)
   ```

5. **Handle errors explicitly**
   ```python
   try:
       result = await source.fetch()
   except (FileNotFoundError, ValueError) as e:
       logger.error(f"Failed to read Excel: {e}")
   ```

## See Also

- [BaseDataSource](./BASE_DATA_SOURCE.md) - Base class documentation
- [FileDataSource](./FILE_DATA_SOURCE.md) - CSV/JSON/YAML files
- [SchemaAnalyzer](../analyzers/SCHEMA_ANALYZER.md) - Schema detection

## Changelog

### Version 1.0.0 (2024-11-29)
- Initial implementation
- Single sheet reading support
- NaN handling
- SchemaAnalyzer integration
- Comprehensive error handling
