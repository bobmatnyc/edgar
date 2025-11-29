# Batch 1 Execution Plan: Data Source Migrations

**Status**: Ready to Execute
**Estimated Time**: 2 days (parallel execution)
**Expected Completion**: End of Week 1, Day 2
**Parallelization**: 4 simultaneous tasks

---

## Quick Reference

| Task | Component | LOC | Priority | Est. Hours | Branch Name |
|------|-----------|-----|----------|------------|-------------|
| **T2-A** | FileDataSource | 286 | 🔴 High | 12h | `feat/batch1-file-datasource` |
| **T2-B** | APIDataSource | 232 | 🟡 Medium | 10h | `feat/batch1-api-datasource` |
| **T2-C** | URLDataSource | 190 | 🟢 Low | 8h | `feat/batch1-url-datasource` |
| **T2-D** | JinaDataSource | 239 | 🟡 Medium | 10h | `feat/batch1-jina-datasource` |

**Total**: 947 LOC, 40 hours (10h per person with 4 parallel workers)

---

## Pre-Execution Checklist

### Setup
- [ ] Verify BaseDataSource is migrated (`src/extract_transform_platform/core/base.py`)
- [ ] Verify OpenRouter AI integration is complete (1M-380)
- [ ] Check platform package structure exists
- [ ] Review EDGAR data source implementations
- [ ] Set up 4 feature branches

### Environment
- [ ] Git status clean on main branch
- [ ] All tests passing on main
- [ ] Python environment active (3.11+)
- [ ] Dependencies installed: `pip install -e ".[dev]"`

### Coordination
- [ ] Review parallelization strategy with team
- [ ] Assign tasks to workers/threads
- [ ] Set up Slack/Linear notifications
- [ ] Schedule daily sync meetings

---

## Task Breakdown

### **T2-A: FileDataSource (CSV/JSON/YAML)** 🔴
**Priority**: Highest (most complex, blocking other work)
**Source**: `src/edgar_analyzer/data_sources/file_source.py` (286 LOC)
**Target**: `src/extract_transform_platform/data_sources/file/`

#### Subtasks
1. **Split FileDataSource into 3 classes** (4h):
   - `csv_source.py` (CSVDataSource) - pandas CSV reader
   - `json_source.py` (JSONDataSource) - JSON parsing
   - `yaml_source.py` (YAMLDataSource) - YAML parsing

2. **Update imports and exports** (1h):
   - Update `__init__.py` in `file/` directory
   - Update platform root `__init__.py`
   - Add factory method for file type detection

3. **Migrate tests** (4h):
   - Split `test_file_source.py` into 3 files
   - Update test fixtures
   - Ensure 80%+ coverage per source

4. **Documentation** (2h):
   - Update `docs/architecture/FILE_DATA_SOURCE.md`
   - Add code examples for each format
   - Update platform QUICK_REFERENCE.md

5. **Integration test** (1h):
   - Test file type auto-detection
   - Test all 3 formats in sequence
   - Verify error handling

#### Files to Create/Update
```
src/extract_transform_platform/data_sources/file/
├── csv_source.py           (new, ~100 LOC)
├── json_source.py          (new, ~90 LOC)
└── yaml_source.py          (new, ~90 LOC)

tests/unit/data_sources/file/
├── test_csv_source.py      (new)
├── test_json_source.py     (new)
└── test_yaml_source.py     (new)
```

#### Success Criteria
- ✅ 3 separate data source classes
- ✅ All unit tests passing (80%+ coverage)
- ✅ Documentation complete
- ✅ Clean PR ready for review

---

### **T2-B: APIDataSource** 🟡
**Priority**: Medium (generic REST API, commonly used)
**Source**: `src/edgar_analyzer/data_sources/api_source.py` (232 LOC)
**Target**: `src/extract_transform_platform/data_sources/web/api_source.py`

#### Subtasks
1. **Remove EDGAR-specific logic** (2h):
   - Remove SEC rate limiting assumptions
   - Generalize error messages
   - Make headers fully configurable

2. **Migrate to platform** (3h):
   - Copy to `web/api_source.py`
   - Update imports (httpx, base classes)
   - Update class docstrings

3. **Enhance generalization** (2h):
   - Add support for custom auth strategies
   - Add support for query parameter encoding
   - Add support for response transformations

4. **Migrate tests** (2h):
   - Update `test_api_source.py`
   - Add mock API server tests
   - Test rate limiting behavior

5. **Documentation** (1h):
   - Update `docs/architecture/API_DATA_SOURCE.md`
   - Add REST API examples
   - Document auth strategies

#### Files to Create/Update
```
src/extract_transform_platform/data_sources/web/
└── api_source.py           (232 LOC → ~210 LOC)

tests/unit/data_sources/web/
└── test_api_source.py      (migrated)
```

#### Success Criteria
- ✅ APIDataSource supports generic REST APIs
- ✅ No EDGAR-specific logic remaining
- ✅ Tests pass with mock servers
- ✅ Documentation updated

---

### **T2-C: URLDataSource** 🟢
**Priority**: Low (simplest, good starter task)
**Source**: `src/edgar_analyzer/data_sources/url_source.py` (190 LOC)
**Target**: `src/extract_transform_platform/data_sources/web/url_source.py`

#### Subtasks
1. **Migrate to platform** (2h):
   - Copy to `web/url_source.py`
   - Update imports
   - Update docstrings

2. **Verify generalization** (1h):
   - Check for hardcoded URLs
   - Verify error handling is generic
   - Test with various URL types

3. **Migrate tests** (2h):
   - Update `test_url_source.py`
   - Add mock HTTP server tests
   - Test JSON and text responses

4. **Documentation** (1h):
   - Update `docs/architecture/URL_DATA_SOURCE.md`
   - Add simple URL examples
   - Document response types

5. **Integration test** (2h):
   - Test with real public APIs (GitHub, JSONPlaceholder)
   - Verify caching behavior
   - Test error scenarios (404, timeout)

#### Files to Create/Update
```
src/extract_transform_platform/data_sources/web/
└── url_source.py           (190 LOC → ~180 LOC)

tests/unit/data_sources/web/
└── test_url_source.py      (migrated)
```

#### Success Criteria
- ✅ URLDataSource fully generic
- ✅ Tests pass with mock and real URLs
- ✅ Documentation complete
- ✅ Clean PR ready

---

### **T2-D: JinaDataSource** 🟡
**Priority**: Medium (web scraping critical for Phase 2)
**Source**: `src/edgar_analyzer/data_sources/jina_source.py` (239 LOC)
**Target**: `src/extract_transform_platform/data_sources/web/jina_source.py`

#### Subtasks
1. **Migrate to platform** (2h):
   - Copy to `web/jina_source.py`
   - Update imports
   - Verify API key handling

2. **Enhance features** (3h):
   - Add support for Jina.ai options (no images, cache, etc.)
   - Add markdown-to-JSON transformation
   - Add rate limiting based on tier (free vs paid)

3. **Migrate tests** (2h):
   - Update `test_jina_source.py`
   - Add mock Jina.ai responses
   - Test rate limiting

4. **Documentation** (2h):
   - Update `docs/architecture/JINA_DATA_SOURCE.md`
   - Add web scraping examples
   - Document Jina.ai API options

5. **Integration test** (1h):
   - Test with real URLs (if API key available)
   - Verify markdown extraction
   - Test error handling (404, rate limit)

#### Files to Create/Update
```
src/extract_transform_platform/data_sources/web/
└── jina_source.py          (239 LOC → ~230 LOC)

tests/unit/data_sources/web/
└── test_jina_source.py     (migrated)
```

#### Success Criteria
- ✅ JinaDataSource supports all Jina.ai options
- ✅ Rate limiting works for free and paid tiers
- ✅ Tests pass (mock and optional real API)
- ✅ Documentation complete

---

## Git Workflow

### Branch Creation
```bash
# Start from clean main
git checkout main
git pull origin main

# Create 4 feature branches
git checkout -b feat/batch1-file-datasource
git checkout main
git checkout -b feat/batch1-api-datasource
git checkout main
git checkout -b feat/batch1-url-datasource
git checkout main
git checkout -b feat/batch1-jina-datasource
```

### Development Workflow (Per Task)
```bash
# 1. Switch to task branch
git checkout feat/batch1-{component}-datasource

# 2. Make changes
# ... edit files ...

# 3. Run tests frequently
pytest tests/unit/data_sources/{web|file}/ -v

# 4. Commit atomic changes
git add src/extract_transform_platform/data_sources/{web|file}/
git commit -m "feat(data-sources): migrate {Component}DataSource to platform"

# 5. Push to remote
git push origin feat/batch1-{component}-datasource

# 6. Create PR (when complete)
gh pr create --title "Migrate {Component}DataSource to platform" \
  --body "Part of Batch 1 (1M-377): Data source migrations"
```

### Merge Strategy
```bash
# After all 4 PRs are approved:

# 1. Merge in dependency order (least → most complex)
# URLDataSource (simplest)
gh pr merge feat/batch1-url-datasource --squash

# JinaDataSource
gh pr merge feat/batch1-jina-datasource --squash

# APIDataSource
gh pr merge feat/batch1-api-datasource --squash

# FileDataSource (most complex, merge last)
gh pr merge feat/batch1-file-datasource --squash

# 2. Run integration tests on main
git checkout main
git pull origin main
pytest tests/integration/test_data_source_factory.py -v

# 3. Tag release
git tag v0.2.0-batch1-complete
git push origin v0.2.0-batch1-complete
```

---

## Testing Strategy

### Unit Tests (Per Data Source)

**Coverage Target**: 80%+

**Test Cases**:
1. **Happy path**: Valid data fetch
2. **Error handling**: Network errors, timeouts, 404s
3. **Validation**: Schema validation, type checking
4. **Caching**: Cache hit/miss behavior
5. **Rate limiting**: Respect rate limits
6. **Edge cases**: Empty responses, malformed data

**Example Test Structure**:
```python
# tests/unit/data_sources/web/test_api_source.py

import pytest
from extract_transform_platform.data_sources.web import APIDataSource

class TestAPIDataSource:
    def test_fetch_json_success(self, mock_api_server):
        """Test successful JSON fetch from API."""
        source = APIDataSource(base_url=mock_api_server.url)
        result = await source.fetch(endpoint="users/1")
        assert result["id"] == 1
        assert "name" in result

    def test_fetch_with_auth(self, mock_api_server):
        """Test API with bearer token authentication."""
        source = APIDataSource(
            base_url=mock_api_server.url,
            auth_token="test-token-123"
        )
        result = await source.fetch(endpoint="protected")
        assert result["authenticated"] is True

    def test_rate_limiting(self, mock_api_server):
        """Test rate limiting behavior."""
        source = APIDataSource(
            base_url=mock_api_server.url,
            rate_limit_per_minute=10
        )
        # Make 11 requests rapidly
        for i in range(11):
            if i < 10:
                await source.fetch(endpoint=f"item/{i}")
            else:
                with pytest.raises(RateLimitError):
                    await source.fetch(endpoint="item/10")
```

### Integration Tests (After All Migrations)

**Coverage Target**: 65%+

**Test Cases**:
1. **Data source factory**: Auto-detect source type from config
2. **Multi-source pipeline**: Fetch from API → transform → save to file
3. **Error propagation**: Ensure errors bubble up correctly
4. **Performance**: Benchmark read times for each source type

---

## Quality Gates

### Pre-Merge Checklist (Per PR)

- [ ] All unit tests passing (80%+ coverage)
- [ ] No linting errors (`flake8`, `mypy`)
- [ ] Code formatted (`black`, `isort`)
- [ ] Docstrings complete (Google style)
- [ ] Type hints on all public methods
- [ ] No hardcoded EDGAR-specific logic
- [ ] Documentation updated
- [ ] Integration tests passing (if applicable)
- [ ] PR approved by 1+ reviewer

### Post-Merge Checklist (After All 4 PRs)

- [ ] All 4 data sources merged to main
- [ ] Integration tests passing
- [ ] Platform package imports work:
  ```python
  from extract_transform_platform.data_sources.file import CSVDataSource, JSONDataSource
  from extract_transform_platform.data_sources.web import APIDataSource, URLDataSource, JinaDataSource
  ```
- [ ] Documentation site updated
- [ ] Git tag created: `v0.2.0-batch1-complete`
- [ ] Linear issue 1M-377 marked as complete
- [ ] Batch 2 planning initiated

---

## Success Metrics

### Quantitative
- ✅ 4/4 data sources migrated
- ✅ 947 LOC migrated (~870 LOC after cleanup = 92% reuse)
- ✅ 80%+ test coverage per source
- ✅ 0 critical bugs in code review
- ✅ Completion within 2 days (40 hours total, 10h per worker)

### Qualitative
- ✅ Code is generic (no EDGAR assumptions)
- ✅ Clean separation of concerns (file vs web sources)
- ✅ Documentation is clear and comprehensive
- ✅ Team understands parallelization workflow

---

## Risk Mitigation

### Merge Conflicts
**Risk**: 4 parallel branches touching `__init__.py` files
**Mitigation**:
- Coordinate `__init__.py` updates in Slack
- Use separate directories (`file/` vs `web/`)
- Merge URLDataSource first (establishes pattern)

### Test Failures
**Risk**: Tests fail after migration due to import changes
**Mitigation**:
- Run tests before pushing each commit
- Use absolute imports consistently
- Keep test fixtures in shared location

### Documentation Drift
**Risk**: Documentation lags behind code changes
**Mitigation**:
- Update docs in same commit as code
- Require docs in PR checklist
- Review docs in code review

---

## Next Steps After Batch 1

### Immediate (Same Day)
1. Run full integration test suite
2. Update platform QUICK_REFERENCE.md
3. Create release notes for v0.2.0-batch1
4. Notify team of Batch 1 completion

### Short-Term (Next Day)
1. Start Batch 2 planning (Pattern Models + Schema Services)
2. Review Batch 1 retrospective:
   - What went well?
   - What could be improved?
   - Adjust estimates for Batch 2
3. Update project timeline based on actual Batch 1 completion time

### Medium-Term (Week 1 End)
1. Execute Batch 2 (Schema Services)
2. Monitor for integration issues with Batch 1
3. Update architecture diagrams with new structure

---

## Communication Plan

### Daily Standup (10 minutes)
- **Time**: 9:00 AM daily
- **Attendees**: All Batch 1 workers
- **Format**:
  1. Yesterday: What did you complete?
  2. Today: What will you work on?
  3. Blockers: Any impediments?
  4. Coordination: Merge window planning

### Progress Updates (Linear/Slack)
- **Frequency**: End of each work session
- **Format**: "{Component}DataSource: {status} ({hours_spent}h / {hours_estimated}h)"
- **Examples**:
  - "FileDataSource: CSV split complete (4h / 12h)"
  - "APIDataSource: Tests passing, ready for review (9h / 10h)"

### PR Reviews (As Needed)
- **SLA**: Review within 4 hours of PR creation
- **Focus**: Code quality, test coverage, documentation
- **Format**: GitHub PR review with inline comments

---

## Appendix: File Reference

### Source Files (EDGAR)
```
src/edgar_analyzer/data_sources/
├── file_source.py      (286 LOC) → Split into 3 files
├── api_source.py       (232 LOC) → Migrate to web/
├── url_source.py       (190 LOC) → Migrate to web/
└── jina_source.py      (239 LOC) → Migrate to web/
```

### Target Files (Platform)
```
src/extract_transform_platform/data_sources/
├── file/
│   ├── __init__.py
│   ├── csv_source.py      (~100 LOC, new)
│   ├── json_source.py     (~90 LOC, new)
│   └── yaml_source.py     (~90 LOC, new)
└── web/
    ├── __init__.py
    ├── api_source.py      (232 → ~210 LOC)
    ├── url_source.py      (190 → ~180 LOC)
    └── jina_source.py     (239 → ~230 LOC)
```

### Test Files
```
tests/unit/data_sources/
├── file/
│   ├── test_csv_source.py
│   ├── test_json_source.py
│   └── test_yaml_source.py
└── web/
    ├── test_api_source.py
    ├── test_url_source.py
    └── test_jina_source.py
```

---

**Ready to Execute**: This plan is ready for immediate execution. Start by creating the 4 feature branches and assigning tasks to workers.

**Questions?**: Contact research agent or PM for clarification.

**Good luck with Batch 1!** 🚀
