# P1 Bug Fix: Session Save - datetime JSON Serialization

**Bug ID**: P1-001
**Severity**: P1 (High)
**Discovered**: 2025-12-06 (Smoke Test #9)
**Impact**: Session save/resume functionality broken
**Frequency**: 100% (all session saves fail)
**Blocking**: No (core workflow unaffected)

---

## Error

```
TypeError: Object of type datetime is not JSON serializable
```

**Location**: `src/edgar_analyzer/interactive/session.py:991`

**Stack Trace**:
```python
File "session.py", line 1001, in cmd_save_session
    json.dump(session_data, f, indent=2)
TypeError: Object of type datetime is not JSON serializable
```

---

## Root Cause

`ProjectConfig.model_dump()` returns Pydantic datetime objects which are not JSON serializable by default.

**Current Code (session.py:991)**:
```python
session_data = {
    "project_path": str(self.project_path) if self.project_path else None,
    "project_config": self.project_config.model_dump() if self.project_config else None,  # ❌ PROBLEM
    "analysis_results": self.analysis_results,
    "generated_code_path": str(self.generated_code_path) if self.generated_code_path else None,
    "extraction_count": len(self.extraction_results) if self.extraction_results else 0,
    "timestamp": datetime.now().isoformat(),
}
```

**Problem**:
```python
self.project_config.model_dump()
# Returns:
{
    'project': {
        'created': datetime.datetime(2025, 12, 6, 12, 7, 15, 3865),  # ❌ NOT JSON SERIALIZABLE
        'updated': datetime.datetime(2025, 12, 6, 12, 7, 15, 3869),  # ❌ NOT JSON SERIALIZABLE
    }
}
```

---

## Fix

Use `model_dump(mode='json')` to automatically convert datetime objects to ISO strings.

**Fixed Code**:
```python
session_data = {
    "project_path": str(self.project_path) if self.project_path else None,
    "project_config": self.project_config.model_dump(mode='json') if self.project_config else None,  # ✅ FIXED
    "analysis_results": self.analysis_results,
    "generated_code_path": str(self.generated_code_path) if self.generated_code_path else None,
    "extraction_count": len(self.extraction_results) if self.extraction_results else 0,
    "timestamp": datetime.now().isoformat(),
}
```

**Result**:
```python
self.project_config.model_dump(mode='json')
# Returns:
{
    'project': {
        'created': '2025-12-06T12:07:15.003865',  # ✅ JSON SERIALIZABLE
        'updated': '2025-12-06T12:07:15.003869',  # ✅ JSON SERIALIZABLE
    }
}
```

---

## Test Coverage

**Failing Test**: Test 9 - Session Save/Resume

**Reproduction**:
```bash
echo -e "analyze\nsave test\nexit" | edgar-analyzer chat --project projects/weather_test/
# Error: TypeError: Object of type datetime is not JSON serializable
```

**Expected After Fix**:
```bash
echo -e "analyze\nsave test\nexit" | edgar-analyzer chat --project projects/weather_test/
# ✅ Session saved: test
# File: /Users/user/.edgar/sessions/test_session.json
```

---

## Implementation Steps

1. **Edit file**: `src/edgar_analyzer/interactive/session.py`
2. **Line 991**: Change `model_dump()` to `model_dump(mode='json')`
3. **Run test**:
   ```bash
   source .venv/bin/activate
   echo -e "analyze\nsave smoke_test\nexit" | edgar-analyzer chat --project projects/weather_test/
   ```
4. **Verify**:
   ```bash
   cat ~/.edgar/sessions/smoke_test_session.json | python -m json.tool
   # Should print valid JSON without errors
   ```
5. **Regression test**: Re-run smoke Test 9

---

## Estimated Fix Time

- **Code Change**: 2 minutes
- **Testing**: 10 minutes
- **Regression**: 15 minutes
- **Total**: ~30 minutes

---

## Related Issues

- **P0 Bug #4**: ExampleConfig attribute changes (introduced datetime fields)
- **Session.py**: Lines 991-1001 (save logic)
- **Pydantic Docs**: https://docs.pydantic.dev/latest/concepts/serialization/#modelmodel_dump

---

## Alternative Fixes

### Option 1: Custom JSON Encoder (More Complex)
```python
import json
from datetime import datetime

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Usage
json.dump(session_data, f, indent=2, cls=DateTimeEncoder)
```

### Option 2: Manual Conversion (More Work)
```python
def convert_datetimes(obj):
    if isinstance(obj, dict):
        return {k: convert_datetimes(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_datetimes(item) for item in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    return obj

session_data_serializable = convert_datetimes(session_data)
json.dump(session_data_serializable, f, indent=2)
```

**Recommended**: Option in main fix (Pydantic built-in)

---

## Priority Justification

**Why P1, not P0?**
- Session save/resume is a convenience feature
- Core extraction workflow unaffected (show, examples, analyze, patterns all work)
- Users can complete workflows without session persistence
- Workaround: Exit without saving, re-run analysis (cached results)
- 9/10 smoke tests pass
- No data loss risk (projects saved independently)

**Why fix before alpha release?**
- User experience: Session save appears in help text
- Expected feature: `save` and `resume` commands visible
- Polish: Prevents confusion during user testing
- Low risk: Trivial fix, clear solution

---

**Created**: 2025-12-06
**QA Agent**: Claude Code
**Review**: Recommended for immediate fix (30 min)
