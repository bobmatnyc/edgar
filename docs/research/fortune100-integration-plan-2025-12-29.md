# Fortune 100 Pipeline Integration Plan

**Date:** 2025-12-29
**Context:** Integrate Fortune 100 pipeline (`src/edgar/`) into Meta-Extractor architecture (`src/edgar_analyzer/`)
**Goal:** Unified architecture leveraging Meta-Extractor's extractor pattern with Fortune 100's production pipeline

---

## Executive Summary

The Fortune 100 pipeline provides battle-tested production code for extracting executive compensation (DEF 14A) and tax data (10-K) from SEC filings. The Meta-Extractor architecture provides a sophisticated extractor registry, dynamic loading, and CLI infrastructure. Integration will combine the best of both: production-ready extractors with scalable architecture.

**Key Decision:** Migrate Fortune 100 extractors into `edgar_analyzer` structure while preserving their robust implementation.

**Estimated Effort:** 3-4 days

---

## Part 1: Architecture Analysis

### 1.1 Meta-Extractor Architecture (`src/edgar_analyzer/`)

**Core Design Pattern:** Extractor Registry + Dynamic Loading

```
src/edgar_analyzer/
├── extractors/
│   ├── meta_extractor.py         # Orchestrator for extractor generation
│   ├── registry.py                # Dynamic extractor loading + metadata
│   ├── sct/                       # Existing SCT extractor (legacy)
│   │   ├── extractor.py
│   │   └── models.py
│   └── patent/                    # Example domain extractor
│       ├── extractor.py
│       └── models.py
├── cli/
│   ├── main.py                    # Main CLI with fortune500/analyze commands
│   └── commands/
│       ├── extractors.py          # Extractor management (create/list/info)
│       └── project.py             # Project commands
├── services/
│   ├── llm_service.py             # OpenRouter LLM integration
│   ├── data_extraction_service.py # High-level data extraction
│   ├── historical_analysis_service.py
│   └── edgar_api_service.py       # SEC EDGAR API client
├── config/
│   ├── container.py               # Dependency injection
│   └── settings.py                # Configuration management
└── models/
    ├── company.py                 # Company/analysis models
    └── sct_models.py              # Domain-specific models
```

**Key Features:**
- **ExtractorRegistry:** JSON-based registry with dynamic class loading
- **MetaExtractor:** Generates extractors from examples (pattern synthesis)
- **CLI Commands:** Rich CLI with fortune500, analyze, extractors commands
- **Dependency Injection:** Container-based DI with service providers
- **LLM Integration:** OpenRouter service with model fallbacks

**Interface Standard:**
```python
from extract_transform_platform.core.base import IDataExtractor

class MyExtractor(IDataExtractor):
    async def extract(self, raw_data: dict) -> BaseModel:
        # Extract structured data
        pass
```

### 1.2 Fortune 100 Pipeline (`src/edgar/`)

**Core Design Pattern:** Pipeline Orchestration + Batch Processing

```
src/edgar/
├── pipelines/
│   └── fortune100.py              # Main pipeline orchestrator
├── extractors/
│   ├── sct/                       # Summary Compensation Table
│   │   ├── extractor.py           # Production SCT extractor
│   │   └── models.py              # SCTData, ExecutiveCompensation
│   └── tax/                       # Corporate Tax
│       ├── extractor.py           # Production Tax extractor
│       └── models.py              # TaxData, TaxYear
├── services/
│   ├── batch_processor.py         # Rate-limited batch processing
│   ├── sec_edgar_client.py        # SEC API client
│   └── context_manager.py         # LLM context management
├── data/
│   └── fortune100.py              # Fortune 100 registry
└── exporters/
    └── csv_exporter.py            # CSV export
```

**Key Features:**
- **Production Extractors:** Battle-tested SCT + Tax extractors with robust HTML parsing
- **BatchProcessor:** Rate-limited (8 req/sec), concurrent processing with retry logic
- **Fortune100Pipeline:** End-to-end orchestrator (fetch → extract → export)
- **Rate Limiting:** Token bucket algorithm (SEC compliant)
- **Error Handling:** Individual failure isolation, exponential backoff

**Extractor Implementation:**
```python
@dataclass(frozen=True)
class SCTExtractor:
    company: str
    cik: str

    def extract(self, raw_data: dict[str, Any]) -> SCTData:
        # BeautifulSoup-based HTML parsing
        # Pattern: Find table → Parse executives → Extract compensation
        pass
```

### 1.3 Key Architectural Differences

| Aspect | Meta-Extractor | Fortune 100 |
|--------|----------------|-------------|
| **Extractor Pattern** | Interface-based (`IDataExtractor`) | Protocol-based (duck typing) |
| **Registration** | Dynamic via registry.json | Hardcoded factory functions |
| **CLI Structure** | Click groups + commands | Single pipeline runner |
| **Services** | DI container (providers.Singleton) | Direct instantiation |
| **Batch Processing** | Historical service (5-year data) | BatchProcessor (rate-limited) |
| **Models** | Mixed (Pydantic + dataclass) | Pure Pydantic models |
| **API Client** | edgar_api_service.py | sec_edgar_client.py |

### 1.4 Compatibility Assessment

**Compatible Elements:**
- ✅ Both use BeautifulSoup for HTML parsing
- ✅ Both target SEC EDGAR filings (DEF 14A, 10-K)
- ✅ Both use Pydantic models for data validation
- ✅ Both have rate limiting (Meta-Extractor: implicit, Fortune 100: explicit)

**Incompatible Elements:**
- ❌ Extractor interface: `IDataExtractor` vs. protocol
- ❌ Model types: `company.py` vs. `fortune100.py`
- ❌ API client: Different implementation
- ❌ Batch processing: Different orchestration

---

## Part 2: Integration Strategy

### 2.1 Core Integration Approach

**Decision:** Adapt Fortune 100 extractors to Meta-Extractor interface while preserving implementation.

**Rationale:**
- Meta-Extractor has superior architecture (registry, DI, CLI)
- Fortune 100 has superior extractors (production-tested, robust)
- Keep Fortune 100 extraction logic, wrap in Meta-Extractor interface

### 2.2 Migration Phases

#### Phase 1: Adapter Layer (Day 1)
**Goal:** Make Fortune 100 extractors compatible with `IDataExtractor` interface

**Tasks:**
1. Create adapter wrapper for `SCTExtractor`
2. Create adapter wrapper for `TaxExtractor`
3. Implement `IDataExtractor.extract()` interface
4. Map Fortune 100 models to Meta-Extractor models

**Output:**
```python
# src/edgar_analyzer/extractors/fortune100/sct_adapter.py
from extract_transform_platform.core.base import IDataExtractor
from edgar.extractors.sct import SCTExtractor as Fortune100SCTExtractor

class SCTExtractor(IDataExtractor):
    """Adapter for Fortune 100 SCT extractor."""

    def __init__(self, company: str, cik: str):
        self.fortune100_extractor = Fortune100SCTExtractor(
            company=company,
            cik=cik
        )

    async def extract(self, raw_data: dict) -> SCTData:
        # Delegate to Fortune 100 implementation
        return self.fortune100_extractor.extract(raw_data)
```

#### Phase 2: Service Integration (Day 2)
**Goal:** Integrate BatchProcessor into edgar_analyzer services layer

**Tasks:**
1. Create `Fortune100Service` wrapper around `BatchProcessor`
2. Integrate rate limiting into existing services
3. Add Fortune 100 company registry to `company_service.py`
4. Consolidate API clients (merge `sec_edgar_client.py` functionality)

**Output:**
```python
# src/edgar_analyzer/services/fortune100_service.py
class Fortune100Service:
    def __init__(
        self,
        edgar_api_service: EdgarApiService,
        company_service: CompanyService,
        cache_service: CacheService
    ):
        self.batch_processor = BatchProcessor(...)
        self.registry = Fortune100Registry.load_default()

    async def process_companies(
        self,
        rank_range: tuple[int, int],
        extractors: list[str]  # ["sct", "tax"]
    ) -> PipelineResult:
        pass
```

#### Phase 3: CLI Integration (Day 2-3)
**Goal:** Add Fortune 100 commands to existing CLI structure

**Tasks:**
1. Create `fortune100.py` command group
2. Add `edgar fortune100 run` command
3. Add `edgar fortune100 list` command (show Fortune 100 companies)
4. Integrate with existing progress tracking

**Output:**
```python
# src/edgar_analyzer/cli/commands/fortune100.py
@click.group(name="fortune100")
def fortune100_cli():
    """Fortune 100 analysis commands."""
    pass

@fortune100_cli.command(name="run")
@click.option("--start-rank", type=int, default=1)
@click.option("--end-rank", type=int, default=100)
@click.option("--extractors", multiple=True, default=["sct", "tax"])
def run_analysis(...):
    """Run Fortune 100 extraction pipeline."""
    pass
```

#### Phase 4: Extractor Registration (Day 3)
**Goal:** Register Fortune 100 extractors in ExtractorRegistry

**Tasks:**
1. Register SCT adapter in registry.json
2. Register Tax adapter in registry.json
3. Add metadata (confidence, examples_count)
4. Verify dynamic loading works

**Output:**
```json
// src/edgar_analyzer/extractors/registry.json
{
  "version": "1.0.0",
  "extractors": {
    "fortune100_sct": {
      "name": "fortune100_sct",
      "class_path": "edgar_analyzer.extractors.fortune100.sct_adapter.SCTExtractor",
      "version": "1.0.0",
      "description": "Extract Summary Compensation Table from DEF 14A filings",
      "domain": "fortune100",
      "confidence": 0.95,
      "examples_count": 100,
      "tags": ["fortune100", "sct", "executive-compensation"]
    },
    "fortune100_tax": {
      "name": "fortune100_tax",
      "class_path": "edgar_analyzer.extractors.fortune100.tax_adapter.TaxExtractor",
      "version": "1.0.0",
      "description": "Extract corporate tax data from 10-K filings",
      "domain": "fortune100",
      "confidence": 0.90,
      "examples_count": 100,
      "tags": ["fortune100", "tax", "10k"]
    }
  }
}
```

#### Phase 5: Testing & Validation (Day 3-4)
**Goal:** Ensure integration works end-to-end

**Tasks:**
1. Test extractor adapters with sample filings
2. Test batch processing with 5 companies
3. Test CLI commands
4. Test registry dynamic loading
5. Compare output with original Fortune 100 pipeline

---

## Part 3: File Organization

### 3.1 New Directory Structure

```
src/edgar_analyzer/
├── extractors/
│   ├── fortune100/                     # NEW: Fortune 100 extractors
│   │   ├── __init__.py
│   │   ├── sct_adapter.py              # Adapter for SCT extractor
│   │   ├── tax_adapter.py              # Adapter for Tax extractor
│   │   └── models.py                   # Re-export Fortune 100 models
│   ├── meta_extractor.py
│   ├── registry.py
│   └── registry.json                   # Updated with fortune100 extractors
├── services/
│   ├── fortune100_service.py           # NEW: Fortune 100 pipeline service
│   ├── batch_processor.py              # NEW: Migrated from src/edgar/
│   └── ...
├── cli/
│   ├── commands/
│   │   ├── fortune100.py               # NEW: Fortune 100 CLI commands
│   │   └── ...
│   └── main.py                         # Updated with fortune100 group
└── data/
    └── fortune100_registry.json        # NEW: Migrated from src/edgar/
```

### 3.2 Code Reuse Strategy

**Keep in `src/edgar/` (reference library):**
- Original extractors (for reference/comparison)
- Original pipeline (for testing/validation)
- CSV exporters (may adapt for edgar_analyzer)

**Migrate to `src/edgar_analyzer/`:**
- `batch_processor.py` → `services/batch_processor.py`
- `fortune100.py` (data) → `data/fortune100_registry.json`
- Extractor logic (wrapped in adapters)

**Consolidate/Merge:**
- `sec_edgar_client.py` + `edgar_api_service.py` → Enhanced `edgar_api_service.py`
- Fortune 100 models → Import from `edgar.extractors.*.models`

---

## Part 4: Critical Decisions

### Decision 1: Extractor Interface Compliance

**Question:** Should we modify Fortune 100 extractors or create adapter wrappers?

**Decision:** Create adapter wrappers (Phase 1 approach)

**Rationale:**
- Preserves original Fortune 100 implementation (battle-tested)
- Minimal changes to production code
- Easier to revert if issues arise
- Clean separation of concerns

**Trade-off:**
- Extra layer of indirection
- Slightly more code
- But: Safer and more maintainable

### Decision 2: Model Consolidation

**Question:** Should we merge `edgar.extractors.*.models` with `edgar_analyzer.models`?

**Decision:** Import Fortune 100 models, don't duplicate

**Rationale:**
- Fortune 100 models are well-designed Pydantic models
- Avoid model version drift
- Single source of truth for data structures

**Implementation:**
```python
# src/edgar_analyzer/extractors/fortune100/models.py
from edgar.extractors.sct.models import SCTData, ExecutiveCompensation
from edgar.extractors.tax.models import TaxData, TaxYear

__all__ = ["SCTData", "ExecutiveCompensation", "TaxData", "TaxYear"]
```

### Decision 3: CLI Command Structure

**Question:** Should Fortune 100 be a top-level command or subcommand?

**Decision:** Subcommand under `edgar fortune100`

**Rationale:**
- Consistent with existing `edgar extractors`, `edgar project` pattern
- Future-proof (can add `edgar russell2000`, etc.)
- Cleaner namespace

**Implementation:**
```bash
# Existing
edgar analyze --cik 0000320193 --year 2023
edgar fortune500 --year 2023 --limit 50

# New (coexist)
edgar fortune100 run --start-rank 1 --end-rank 10
edgar fortune100 list --filter tech
edgar extractors info fortune100_sct
```

### Decision 4: Batch Processing Integration

**Question:** Should we use `BatchProcessor` or `historical_analysis_service`?

**Decision:** Use both, with `Fortune100Service` as orchestrator

**Rationale:**
- `BatchProcessor`: Better for single-filing extraction (DEF 14A, 10-K)
- `historical_analysis_service`: Better for multi-year analysis
- Fortune 100 pipeline needs both capabilities

**Implementation:**
```python
class Fortune100Service:
    def __init__(self, ...):
        self.batch_processor = BatchProcessor(...)
        self.historical_service = HistoricalAnalysisService(...)

    async def run_pipeline(self, mode: str):
        if mode == "latest":
            # Use BatchProcessor for latest filings
            return await self.batch_processor.process_companies(...)
        elif mode == "historical":
            # Use historical_service for 5-year data
            return await self.historical_service.extract_multi_year(...)
```

### Decision 5: Existing `src/edgar/` Fate

**Question:** Should we delete, archive, or keep `src/edgar/`?

**Decision:** Keep as reference library, mark as legacy

**Rationale:**
- May need to compare implementations
- Useful for validation/testing
- Can deprecate in future release

**Action:**
- Add `# LEGACY: See src/edgar_analyzer/extractors/fortune100/` comment
- Update README to point to new location
- Add deprecation warning if imported

---

## Part 5: Implementation Checklist

### Day 1: Adapter Layer
- [ ] Create `src/edgar_analyzer/extractors/fortune100/` directory
- [ ] Implement `sct_adapter.py` (SCTExtractor → IDataExtractor)
- [ ] Implement `tax_adapter.py` (TaxExtractor → IDataExtractor)
- [ ] Create `models.py` (re-export Fortune 100 models)
- [ ] Write unit tests for adapters
- [ ] Test with 3 sample companies (Apple, Walmart, ExxonMobil)

### Day 2: Service Integration
- [ ] Migrate `batch_processor.py` to `services/`
- [ ] Create `Fortune100Service` in `services/fortune100_service.py`
- [ ] Integrate rate limiting with existing services
- [ ] Migrate Fortune 100 registry data
- [ ] Add Fortune 100 service to DI container
- [ ] Update `edgar_api_service.py` with missing features from `sec_edgar_client.py`

### Day 3: CLI & Registry
- [ ] Create `cli/commands/fortune100.py`
- [ ] Implement `edgar fortune100 run` command
- [ ] Implement `edgar fortune100 list` command
- [ ] Register extractors in `registry.json`
- [ ] Add commands to `cli/main.py`
- [ ] Test CLI end-to-end with 5 companies

### Day 4: Testing & Documentation
- [ ] Integration tests (10 companies)
- [ ] Compare output with original pipeline
- [ ] Performance benchmarking
- [ ] Update README with Fortune 100 commands
- [ ] Create migration guide
- [ ] Add deprecation notice to `src/edgar/`

---

## Part 6: Risks & Mitigation

### Risk 1: Performance Degradation
**Risk:** Adapter layer + DI overhead slows extraction
**Likelihood:** Low
**Impact:** Medium
**Mitigation:**
- Benchmark before/after (Day 4)
- Profile hot paths
- Optimize if >10% slowdown

### Risk 2: Model Incompatibility
**Risk:** Fortune 100 models don't map cleanly to Meta-Extractor models
**Likelihood:** Medium
**Impact:** High
**Mitigation:**
- Use Fortune 100 models directly (Decision 2)
- Avoid forced mapping
- Accept model diversity

### Risk 3: Rate Limiting Conflicts
**Risk:** Multiple services hit SEC API, exceed limits
**Likelihood:** Low
**Impact:** High
**Mitigation:**
- Centralize rate limiter in `edgar_api_service.py`
- Share single RateLimiter instance across services
- Add global request counter

### Risk 4: Extractor Registration Fails
**Risk:** Dynamic loading doesn't work for adapters
**Likelihood:** Low
**Impact:** Medium
**Mitigation:**
- Test dynamic import early (Day 1)
- Add clear error messages
- Fallback to direct import if needed

---

## Part 7: Success Criteria

### Functional Requirements
1. ✅ Fortune 100 extractors work via ExtractorRegistry
2. ✅ CLI commands execute Fortune 100 pipeline
3. ✅ Batch processing handles rate limiting correctly
4. ✅ Output matches original pipeline (within 5% variation)

### Non-Functional Requirements
1. ✅ Performance: <15% overhead vs. original pipeline
2. ✅ Maintainability: Clear separation between original and adapted code
3. ✅ Extensibility: Easy to add Russell 2000, S&P 500 extractors
4. ✅ Documentation: Migration guide + usage examples

### Testing Requirements
1. ✅ Unit tests for all adapters (>90% coverage)
2. ✅ Integration test with 10 companies
3. ✅ End-to-end CLI test
4. ✅ Registry dynamic loading test

---

## Part 8: Future Enhancements

### Post-Integration Improvements
1. **Unified API Client:** Merge `edgar_api_service.py` + `sec_edgar_client.py` completely
2. **Enhanced Registry:** Add extractor versioning, deprecation support
3. **Parallel Extraction:** Multi-year + multi-form extraction in parallel
4. **CSV Export Integration:** Add CSV exporters to Meta-Extractor services
5. **Progress Tracking:** Rich progress bars for batch processing

### Potential Extensions
1. **Russell 2000 Pipeline:** Adapt Fortune 100 approach for Russell 2000
2. **S&P 500 Pipeline:** Mid-cap company analysis
3. **Multi-Domain Extractors:** Combine SCT + Tax in single run
4. **Incremental Updates:** Only fetch new filings since last run
5. **Historical Backfill:** Automatically backfill missing years

---

## Part 9: Estimated Effort

### Breakdown by Phase

| Phase | Tasks | Estimated Hours |
|-------|-------|-----------------|
| **Day 1: Adapter Layer** | Adapter wrappers, model mapping, unit tests | 6-8 hours |
| **Day 2: Service Integration** | Service migration, DI setup, API consolidation | 6-8 hours |
| **Day 3: CLI & Registry** | CLI commands, registry updates, testing | 5-6 hours |
| **Day 4: Testing & Docs** | Integration tests, benchmarking, documentation | 4-5 hours |

**Total:** 21-27 hours (3-4 days)

### Assumptions
- Adapters are straightforward (Fortune 100 extractors are well-structured)
- Registry integration is simple (proven pattern)
- No major API incompatibilities
- Testing data available (sample filings)

### Contingency
- +1 day for unexpected model mapping issues
- +0.5 day for performance optimization if needed
- +0.5 day for comprehensive testing

**Conservative Estimate:** 4-5 days with contingency

---

## Part 10: Next Steps

### Immediate Actions (Today)
1. Review this integration plan with stakeholders
2. Confirm architectural decisions (Section 4)
3. Set up development branch: `feature/fortune100-integration`
4. Create Day 1 tasks in project tracker

### Pre-Implementation
1. Backup `src/edgar/` directory (reference copy)
2. Create test dataset (5-10 sample companies)
3. Set up performance benchmarking infrastructure
4. Review Fortune 100 extractor code for edge cases

### Post-Implementation
1. Deprecate `src/edgar/` with migration guide
2. Update main README with Fortune 100 features
3. Create example notebooks for Fortune 100 analysis
4. Schedule stakeholder demo

---

## Appendix A: Key Code Patterns

### Pattern 1: Extractor Adapter

```python
# src/edgar_analyzer/extractors/fortune100/sct_adapter.py
from typing import Any, Dict
from extract_transform_platform.core.base import IDataExtractor
from edgar.extractors.sct import SCTExtractor as Fortune100SCTExtractor
from edgar.extractors.sct.models import SCTData

class SCTExtractor(IDataExtractor):
    """Adapter for Fortune 100 SCT extractor.

    Maps Fortune 100 extractor to IDataExtractor interface.
    Preserves original implementation while conforming to registry pattern.
    """

    def __init__(self, company: str, cik: str):
        self.company = company
        self.cik = cik
        self._fortune100_extractor = Fortune100SCTExtractor(
            company=company,
            cik=cik
        )

    async def extract(self, raw_data: Dict[str, Any]) -> SCTData:
        """Extract using Fortune 100 implementation."""
        # Fortune 100 extractor is sync, wrap in async
        return self._fortune100_extractor.extract(raw_data)
```

### Pattern 2: Service Integration

```python
# src/edgar_analyzer/services/fortune100_service.py
from typing import Tuple, List
from edgar_analyzer.services.interfaces import ICompanyService
from edgar.services.batch_processor import BatchProcessor, RateLimiter
from edgar.pipelines.fortune100 import PipelineConfig, PipelineResult
from edgar.data.fortune100 import Fortune100Registry

class Fortune100Service:
    """Fortune 100 analysis service integrated into edgar_analyzer."""

    def __init__(
        self,
        edgar_api_service,
        company_service: ICompanyService,
        cache_service,
    ):
        self.edgar_api = edgar_api_service
        self.company_service = company_service
        self.cache = cache_service

        # Initialize Fortune 100 components
        self.registry = Fortune100Registry.load_default()
        self.rate_limiter = RateLimiter(requests_per_second=8.0)
        self.batch_processor = BatchProcessor(
            sec_client=edgar_api_service,
            rate_limiter=self.rate_limiter,
            max_concurrent=5
        )

    async def run_pipeline(
        self,
        rank_range: Tuple[int, int],
        extractors: List[str],
        output_dir: str
    ) -> PipelineResult:
        """Run Fortune 100 extraction pipeline."""
        config = PipelineConfig(
            companies_range=rank_range,
            output_dir=Path(output_dir),
            skip_def14a="sct" not in extractors,
            skip_10k="tax" not in extractors,
        )

        # Use Fortune 100 pipeline with edgar_analyzer infrastructure
        pipeline = Fortune100Pipeline(config)
        return await pipeline.run()
```

### Pattern 3: CLI Command

```python
# src/edgar_analyzer/cli/commands/fortune100.py
import click
from edgar_analyzer.services.fortune100_service import Fortune100Service

@click.group(name="fortune100")
def fortune100_cli():
    """Fortune 100 company analysis."""
    pass

@fortune100_cli.command(name="run")
@click.option("--start-rank", type=int, default=1, help="Starting rank")
@click.option("--end-rank", type=int, default=100, help="Ending rank")
@click.option("--extractors", multiple=True, default=["sct", "tax"])
@click.option("--output", type=click.Path(), default="output/fortune100")
@inject
async def run_pipeline(
    start_rank: int,
    end_rank: int,
    extractors: tuple[str],
    output: str,
    fortune100_service: Fortune100Service = Provide[Container.fortune100_service],
):
    """Run Fortune 100 extraction pipeline."""
    result = await fortune100_service.run_pipeline(
        rank_range=(start_rank, end_rank),
        extractors=list(extractors),
        output_dir=output,
    )

    click.echo(f"Success rate: {result.def14a_success_rate:.1%}")
    click.echo(f"Output: {result.output_files}")
```

---

## Appendix B: Testing Strategy

### Unit Tests
```python
# tests/extractors/fortune100/test_sct_adapter.py
import pytest
from edgar_analyzer.extractors.fortune100.sct_adapter import SCTExtractor

def test_sct_adapter_conforms_to_interface():
    """Verify adapter implements IDataExtractor."""
    from extract_transform_platform.core.base import IDataExtractor
    extractor = SCTExtractor(company="Apple Inc.", cik="0000320193")
    assert isinstance(extractor, IDataExtractor)

@pytest.mark.asyncio
async def test_sct_extraction_from_sample():
    """Test extraction from sample Apple DEF 14A filing."""
    extractor = SCTExtractor(company="Apple Inc.", cik="0000320193")

    with open("tests/fixtures/apple_def14a.html") as f:
        raw_data = {"html": f.read()}

    result = await extractor.extract(raw_data)

    assert result.company == "Apple Inc."
    assert len(result.executives) > 0
    assert result.executives[0].name == "Timothy D. Cook"
```

### Integration Tests
```python
# tests/integration/test_fortune100_pipeline.py
import pytest
from edgar_analyzer.services.fortune100_service import Fortune100Service

@pytest.mark.asyncio
async def test_fortune100_pipeline_e2e(fortune100_service):
    """Test complete pipeline with 3 companies."""
    result = await fortune100_service.run_pipeline(
        rank_range=(1, 3),
        extractors=["sct", "tax"],
        output_dir="tests/output"
    )

    assert result.success
    assert result.companies_processed == 3
    assert result.def14a_success_rate >= 0.66  # At least 2/3 success
    assert len(result.output_files) > 0
```

---

## Summary

This integration plan provides a clear, phased approach to combining Fortune 100's production-ready extractors with Meta-Extractor's scalable architecture. The adapter pattern ensures we preserve battle-tested extraction logic while gaining registry, DI, and CLI benefits.

**Key Success Factors:**
1. Minimal changes to Fortune 100 extraction code
2. Leverages Meta-Extractor infrastructure
3. Clear separation of concerns
4. Comprehensive testing strategy
5. Realistic timeline (3-4 days)

**Critical Path:**
Day 1 (Adapters) → Day 2 (Services) → Day 3 (CLI/Registry) → Day 4 (Testing)

**Next Action:** Review with stakeholders and proceed with Day 1 implementation.
