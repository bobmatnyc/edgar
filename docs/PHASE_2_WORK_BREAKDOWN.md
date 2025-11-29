# Phase 2 Work Breakdown
# General-Purpose Extract & Transform Platform

**Date**: 2025-11-29
**Phase**: Phase 2 - Core Platform Architecture
**Timeline**: 2 weeks (10 working days)
**Epic ID**: 4a248615-f1dd-4669-9f61-edec2d2355ac
**Linear Project**: [EDGAR → General-Purpose Platform](https://linear.app/1m-hyperdev/project/edgar-%E2%86%92-general-purpose-extract-and-transform-platform-e4cb3518b13e/issues)

---

## Table of Contents

- [Executive Summary](#executive-summary)
- [Ticket Prioritization Matrix](#ticket-prioritization-matrix)
- [Week 1: Platform Extraction](#week-1-platform-extraction)
- [Week 2: Work Paths & Integration](#week-2-work-paths--integration)
- [Dependency Graph](#dependency-graph)
- [Resource Allocation](#resource-allocation)
- [Milestone Schedule](#milestone-schedule)

---

## Executive Summary

### Phase 2 Overview

**Objective**: Transform EDGAR MVP into general-purpose extract & transform platform

**Total Effort**: 10 days (2 weeks)
**Total Tickets**: 18 tickets
**Priority Breakdown**:
- P0 (Critical): 6 tickets (33%)
- P1 (High): 8 tickets (45%)
- P2 (Medium): 3 tickets (16%)
- P3 (Low): 1 ticket (6%)

**Key Deliverables**:
1. ✅ Generic platform package (`extract_transform_platform/`)
2. ✅ Project isolation system (per-project DI containers)
3. ✅ 4 work paths functional (project-based, file transform, web scraping, interactive)
4. ✅ Performance optimization (<4:00 generation time)
5. ✅ Migration from EDGAR completed (70% code reuse)

### Success Criteria

**Must-Have (Phase 2 Complete)**:
- [ ] Generic platform package created
- [ ] Weather API project works with new platform
- [ ] 70% code reusability validated
- [ ] All P0 + P1 tickets completed (14/18 tickets)

**Should-Have (Production-Ready)**:
- [ ] PDF extraction working
- [ ] External artifacts directory functional
- [ ] Interactive mode implemented
- [ ] All P2 tickets completed (17/18 tickets)

**Nice-to-Have (Phase 3+)**:
- [ ] DOCX extraction working
- [ ] PPTX extraction working (deferred)
- [ ] All P3 tickets completed

---

## Ticket Prioritization Matrix

### Priority Definitions

| Priority | Definition | Timeline | Blocking |
|----------|-----------|----------|----------|
| **P0** | Critical - Blocks Phase 2 completion | Week 1 | Blocks everything |
| **P1** | High - Core functionality | Week 1-2 | Blocks some features |
| **P2** | Medium - Enhanced features | Week 2 | Blocks nice-to-have |
| **P3** | Low - Polish/optimization | Phase 3+ | Non-blocking |

### All Tickets (18 Total)

| ID | Title | Priority | Effort | Week | Dependencies |
|----|-------|----------|--------|------|--------------|
| **Phase 2A: Platform Extraction** | | | | | |
| T1 | Create generic platform package structure | P0 | 0.5d | 1 | - |
| T2 | Extract data source abstractions | P0 | 1.0d | 1 | T1 |
| T3 | Extract configuration models | P0 | 0.5d | 1 | T1 |
| T4 | Extract code generation services | P0 | 1.5d | 1 | T1, T3 |
| T5 | Extract AI integration (agents, clients) | P0 | 1.0d | 1 | T1 |
| T6 | Create protocol interfaces (IDataSource, IDataExtractor) | P0 | 0.5d | 1 | T2 |
| **Phase 2B: Project Isolation** | | | | | |
| T7 | Implement per-project DI container | P1 | 1.0d | 2 | T1, T3 |
| T8 | Create project registry system | P1 | 1.0d | 2 | T7 |
| T9 | Refactor CLI for multi-project support | P1 | 1.5d | 2 | T7, T8 |
| T10 | Add project CRUD commands | P1 | 0.5d | 2 | T8, T9 |
| **Phase 2C: Work Paths** | | | | | |
| T11 | Work Path A: External artifacts directory | P1 | 1.0d | 2 | T3, T8 |
| T12 | Work Path B: PDF extraction (pdfplumber) | P1 | 2.0d | 2 | T2, T6 |
| T13 | Work Path B: Excel extraction (pandas) | P2 | 0.5d | 2 | T2, T6 |
| T14 | Work Path D: Interactive mode (confidence threshold) | P1 | 1.0d | 2 | T4, T9 |
| T15 | Work Path C: Jina.ai configuration guide | P2 | 0.5d | 2 | - |
| **Phase 2D: Performance & Migration** | | | | | |
| T16 | Performance optimization (parallel AI, caching) | P1 | 1.5d | 2 | T4 |
| T17 | Migrate EDGAR code to legacy/ | P2 | 1.0d | 2 | T1-T6 |
| T18 | DOCX extraction (python-docx) | P3 | 1.5d | 3+ | T2, T6 |

**Total Effort**: 17.0 days (scoped to 10 days for Phase 2)
**Phase 2 Scope**: T1-T17 (15.5 days → 10 days with parallelization)
**Deferred to Phase 3**: T18 (DOCX extraction)

---

## Week 1: Platform Extraction

### Objective

Extract generic platform from EDGAR codebase, achieving 70% code reusability.

**Duration**: 5 days
**Tickets**: T1-T6 (6 tickets, all P0)
**Effort**: 5.0 days

### Day 1: Package Structure & Data Sources

#### T1: Create Generic Platform Package Structure

**Priority**: P0 (Critical - Blocks everything)
**Effort**: 0.5 days (4 hours)
**Assignee**: Engineer

**Objective**: Create `extract_transform_platform/` package with proper structure

**Tasks**:
1. Create directory structure:
   ```bash
   mkdir -p extract_transform_platform/{interfaces,sources,models,services,agents,clients,container,cli,utils}
   ```

2. Create `__init__.py` files for all packages

3. Set up `pyproject.toml` entries:
   ```toml
   [tool.poetry.packages]
   packages = [
       { include = "extract_transform_platform", from = "src" },
       { include = "edgar_analyzer", from = "src" },
   ]
   ```

4. Create package metadata:
   ```python
   # extract_transform_platform/__init__.py
   __version__ = "0.1.0"
   __author__ = "Platform Team"
   __description__ = "General-purpose data extraction and transformation platform"
   ```

**Deliverables**:
- [ ] Directory structure created
- [ ] All `__init__.py` files present
- [ ] `pyproject.toml` updated
- [ ] Package importable: `import extract_transform_platform`

**Acceptance Criteria**:
- Package structure matches architecture diagram
- All subdirectories have `__init__.py`
- Package can be imported without errors

**Dependencies**: None (blocking ticket)

---

#### T2: Extract Data Source Abstractions

**Priority**: P0 (Critical - Blocks work paths)
**Effort**: 1.0 days (8 hours)
**Assignee**: Engineer

**Objective**: Move data source classes from `edgar_analyzer` to generic platform

**Tasks**:
1. Copy base abstraction:
   ```bash
   cp src/edgar_analyzer/data_sources/base.py \
      extract_transform_platform/sources/base.py
   ```

2. Copy source implementations:
   - `api_source.py` (180 LOC)
   - `file_source.py` (195 LOC)
   - `url_source.py` (150 LOC)
   - `jina_source.py` (185 LOC)

3. Refactor imports:
   ```python
   # Before
   from edgar_analyzer.utils.rate_limiter import RateLimiter

   # After
   from extract_transform_platform.utils.rate_limiter import RateLimiter
   ```

4. Remove EDGAR-specific code:
   - Remove `EDGARDataSource` (keep in `edgar_analyzer/legacy/`)
   - Remove EDGAR API dependencies

5. Update tests:
   ```bash
   cp tests/unit/test_data_sources.py \
      tests/unit/test_platform_sources.py
   ```

**Deliverables**:
- [ ] `base.py` copied and refactored
- [ ] 4 source implementations copied (api, file, url, jina)
- [ ] All imports updated
- [ ] Tests passing
- [ ] No EDGAR dependencies in generic sources

**Acceptance Criteria**:
- All data sources importable from `extract_transform_platform.sources`
- Tests pass: `pytest tests/unit/test_platform_sources.py`
- No circular dependencies
- `mypy --strict` passes

**Dependencies**: T1 (package structure)

---

### Day 2: Models & Configuration

#### T3: Extract Configuration Models

**Priority**: P0 (Critical - Blocks code generation)
**Effort**: 0.5 days (4 hours)
**Assignee**: Engineer

**Objective**: Move Pydantic models from EDGAR to generic platform

**Tasks**:
1. Copy models:
   - `project_config.py` (800 LOC) ✅ Already generic
   - `patterns.py` (450 LOC) ✅ Already generic
   - `plan.py` (380 LOC) ✅ Already generic
   - `validation.py` (280 LOC) ✅ Already generic

2. Move to platform:
   ```bash
   cp src/edgar_analyzer/models/project_config.py \
      extract_transform_platform/models/
   ```

3. Update imports (minimal changes needed)

4. Validate YAML schema still works:
   ```bash
   python -c "from extract_transform_platform.models import ProjectConfig; \
              config = ProjectConfig.from_yaml('projects/weather_api/project.yaml'); \
              print(f'Loaded project: {config.project.name}')"
   ```

**Deliverables**:
- [ ] 4 model files copied to platform
- [ ] Imports updated
- [ ] YAML parsing works
- [ ] Tests passing

**Acceptance Criteria**:
- Weather API `project.yaml` loads successfully
- Pydantic validation works
- No EDGAR-specific code in models
- Type hints complete

**Dependencies**: T1 (package structure)

---

### Day 3: Code Generation Services (Part 1)

#### T4: Extract Code Generation Services

**Priority**: P0 (Critical - Core platform functionality)
**Effort**: 1.5 days (12 hours)
**Assignee**: Engineer

**Objective**: Move code generation pipeline from EDGAR to platform

**Tasks**:
1. **Day 3 Morning**: Copy services (4 hours)
   - `example_parser.py` (650 LOC)
   - `schema_analyzer.py` (420 LOC)
   - `prompt_generator.py` (380 LOC)
   - `code_generator.py` (580 LOC)
   - `constraint_enforcer.py` (220 LOC)

2. **Day 3 Afternoon**: Refactor imports (4 hours)
   - Update all cross-references
   - Remove EDGAR-specific references
   - Fix circular dependencies

3. **Day 4 Morning**: Update templates (4 hours)
   - Generalize code generation templates
   - Remove EDGAR branding
   - Update import statements in templates

**Deliverables**:
- [ ] 5 service files copied
- [ ] All imports refactored
- [ ] Templates updated
- [ ] Weather API code generation works
- [ ] Constraint enforcement passes (0.88ms target)

**Acceptance Criteria**:
- Code generation produces valid Python
- Generated code passes AST validation
- Type hints enforced
- Interface compliance checked
- Tests pass: `pytest tests/integration/test_code_generation.py`

**Dependencies**: T1, T3 (package structure, models)

---

### Day 4: AI Integration & Interfaces

#### T5: Extract AI Integration (Agents, Clients)

**Priority**: P0 (Critical - Enables code generation)
**Effort**: 1.0 days (8 hours)
**Assignee**: Engineer

**Objective**: Move Sonnet 4.5 agent and OpenRouter client to platform

**Tasks**:
1. Copy AI components:
   - `agents/sonnet45_agent.py` (450 LOC)
   - `clients/openrouter_client.py` (300 LOC)

2. Refactor imports:
   ```python
   # Update agent imports
   from extract_transform_platform.models.plan import PlanSpec
   from extract_transform_platform.clients.openrouter_client import OpenRouterClient
   ```

3. Generalize prompts:
   - Remove EDGAR-specific examples
   - Add generic transformation examples
   - Update system prompts

4. Test integration:
   ```python
   # Test PM mode
   agent = Sonnet45Agent(mode="pm")
   plan = await agent.generate_plan(examples)

   # Test Coder mode
   agent = Sonnet45Agent(mode="coder")
   code = await agent.generate_code(plan)
   ```

**Deliverables**:
- [ ] Agent copied and refactored
- [ ] Client copied and refactored
- [ ] Prompts generalized
- [ ] PM + Coder modes working
- [ ] OpenRouter API integration functional

**Acceptance Criteria**:
- Sonnet 4.5 agent generates plans
- Code generation produces valid code
- OpenRouter API calls succeed
- Retry logic works
- Error handling robust

**Dependencies**: T1, T3, T4 (package structure, models, services)

---

#### T6: Create Protocol Interfaces

**Priority**: P0 (Critical - Defines contracts)
**Effort**: 0.5 days (4 hours)
**Assignee**: Engineer

**Objective**: Define formal interfaces for data sources and extractors

**Tasks**:
1. Create `IDataSource` protocol:
   ```python
   # extract_transform_platform/interfaces/data_source.py
   from typing import Protocol, runtime_checkable

   @runtime_checkable
   class IDataSource(Protocol):
       async def fetch(self, **kwargs) -> Dict[str, Any]: ...
       async def validate_config(self) -> bool: ...
       def get_cache_key(self, **kwargs) -> str: ...
   ```

2. Create `IDataExtractor` protocol:
   ```python
   # extract_transform_platform/interfaces/data_extractor.py
   @runtime_checkable
   class IDataExtractor(Protocol):
       async def extract(
           self, source_data: Dict[str, Any], **kwargs
       ) -> List[Dict[str, Any]]: ...
   ```

3. Update `BaseDataSource` to implement `IDataSource`

4. Update code generator to enforce `IDataExtractor`

5. Add runtime checks:
   ```python
   assert isinstance(source, IDataSource), "Source must implement IDataSource"
   ```

**Deliverables**:
- [ ] `IDataSource` protocol defined
- [ ] `IDataExtractor` protocol defined
- [ ] Base classes updated
- [ ] Runtime checks added
- [ ] Type checking passes (`mypy --strict`)

**Acceptance Criteria**:
- Protocols define clear contracts
- `mypy` validates compliance
- Runtime `isinstance()` checks work
- Generated code implements `IDataExtractor`

**Dependencies**: T2 (data sources)

---

### Week 1 Summary

**Completed Tickets**: T1-T6 (6 tickets)
**Effort**: 5.0 days
**Deliverables**:
- ✅ Generic platform package created
- ✅ Data sources extracted and refactored
- ✅ Configuration models migrated
- ✅ Code generation services working
- ✅ AI integration functional
- ✅ Protocol interfaces defined

**Validation**:
- [ ] Run full test suite: `pytest tests/`
- [ ] Type check: `mypy --strict extract_transform_platform/`
- [ ] Generate weather API code: `platform generate weather_api`
- [ ] Verify 70% code reuse: Count LOC in generic vs. legacy

---

## Week 2: Work Paths & Integration

### Objective

Implement project isolation, 4 work paths, and performance optimizations.

**Duration**: 5 days
**Tickets**: T7-T17 (11 tickets)
**Effort**: 10.5 days (parallelized to 5 days)

### Day 6: Project Isolation System

#### T7: Implement Per-Project DI Container

**Priority**: P1 (High - Enables multi-project)
**Effort**: 1.0 days (8 hours)
**Assignee**: Engineer

**Objective**: Create DI container that isolates project dependencies

**Tasks**:
1. Create `ProjectContainer` class:
   ```python
   # extract_transform_platform/container/project_container.py
   from dependency_injector import containers, providers

   class ProjectContainer(containers.DeclarativeContainer):
       config = providers.Configuration()
       cache_service = providers.Singleton(CacheService, ...)
       llm_service = providers.Singleton(LLMService, ...)
       # ... other services
   ```

2. Add dynamic wiring:
   ```python
   def wire_project(self, project_name: str):
       generated_module = f"projects.{project_name}.generated"
       self.wire(modules=[generated_module])
   ```

3. Test isolation:
   ```python
   # Create two project containers
   weather_container = ProjectContainer()
   invoice_container = ProjectContainer()

   # Verify no shared state
   assert weather_container.cache_service() != invoice_container.cache_service()
   ```

**Deliverables**:
- [ ] `ProjectContainer` class implemented
- [ ] Dynamic wiring works
- [ ] Service isolation validated
- [ ] Tests pass

**Acceptance Criteria**:
- Each project gets isolated DI container
- Services don't share state between projects
- Container lifecycle managed properly
- Memory leaks prevented

**Dependencies**: T1, T3 (package structure, models)

---

#### T8: Create Project Registry System

**Priority**: P1 (High - Enables project management)
**Effort**: 1.0 days (8 hours)
**Assignee**: Engineer

**Objective**: Build system to discover, load, and manage projects

**Tasks**:
1. Create `ProjectRegistry`:
   ```python
   class ProjectRegistry:
       def discover_projects(self) -> List[str]: ...
       def load_project(self, name: str) -> ProjectContainer: ...
       def unload_project(self, name: str) -> None: ...
       def list_projects(self) -> List[Dict]: ...
   ```

2. Implement project discovery:
   - Scan `projects/` directory
   - Validate `project.yaml` exists
   - Load and cache configurations

3. Add lifecycle management:
   - Load on demand
   - Cache loaded projects
   - Unload to free memory

4. Create singleton registry:
   ```python
   def get_registry() -> ProjectRegistry:
       global _registry
       if _registry is None:
           _registry = ProjectRegistry()
       return _registry
   ```

**Deliverables**:
- [ ] `ProjectRegistry` implemented
- [ ] Project discovery works
- [ ] Load/unload lifecycle correct
- [ ] Singleton pattern implemented
- [ ] Tests pass

**Acceptance Criteria**:
- Registry discovers all projects in `projects/`
- Projects load without errors
- Memory freed on unload
- Thread-safe singleton

**Dependencies**: T7 (project container)

---

### Day 7: CLI Refactoring & Work Path A

#### T9: Refactor CLI for Multi-Project Support

**Priority**: P1 (High - User-facing)
**Effort**: 1.5 days (12 hours)
**Assignee**: Engineer

**Tasks**:
1. **Day 7 Morning**: Refactor main CLI (4 hours)
   ```python
   # extract_transform_platform/cli/main.py
   import click

   @click.group()
   def platform():
       """Generic extract & transform platform"""
       pass

   @platform.command()
   @click.argument("project_name")
   def generate(project_name):
       """Generate code for project"""
       registry = get_registry()
       container = registry.load_project(project_name)
       # ... generation logic
   ```

2. **Day 7 Afternoon**: Add project commands (4 hours)
   - `create-project`
   - `list-projects`
   - `validate-project`
   - `delete-project`

3. **Day 8 Morning**: Update help text (4 hours)
   - Remove EDGAR branding
   - Add generic examples
   - Update documentation

**Deliverables**:
- [ ] CLI refactored for multi-project
- [ ] EDGAR branding removed
- [ ] Help text updated
- [ ] Backward compatibility maintained (for EDGAR legacy)

**Acceptance Criteria**:
- `platform --help` shows generic help
- All commands work with project names
- Error messages clear and helpful
- Tests pass

**Dependencies**: T7, T8 (containers, registry)

---

#### T10: Add Project CRUD Commands

**Priority**: P1 (High - Core functionality)
**Effort**: 0.5 days (4 hours)
**Assignee**: Engineer

**Objective**: Implement create, list, validate, delete commands

**Tasks**:
1. `create-project` command:
   ```bash
   platform create-project weather_api --template api
   ```

2. `list-projects` command:
   ```bash
   platform list-projects
   # Output:
   # weather_api (v1.0.0) - Extract weather data [loaded]
   # pdf_invoices (v1.0.0) - Parse invoices [available]
   ```

3. `validate-project` command:
   ```bash
   platform validate-project weather_api
   # Validates: YAML schema, examples, config
   ```

4. `delete-project` command:
   ```bash
   platform delete-project old_project --confirm
   ```

**Deliverables**:
- [ ] 4 CRUD commands implemented
- [ ] Templates for project creation (api, file, url)
- [ ] Validation runs comprehensive checks
- [ ] Delete requires confirmation

**Acceptance Criteria**:
- Projects can be created, listed, validated, deleted
- Templates generate valid `project.yaml`
- Validation catches errors early
- Delete prevents accidental data loss

**Dependencies**: T8, T9 (registry, CLI)

---

#### T11: Work Path A - External Artifacts Directory

**Priority**: P1 (High - User preference #2)
**Effort**: 1.0 days (8 hours)
**Assignee**: Engineer

**Objective**: Support external artifact storage (prevent repo bloat)

**Tasks**:
1. Add `artifacts` section to `ProjectConfig`:
   ```python
   class ArtifactsConfig(BaseModel):
       enabled: bool = False
       base_path: str  # ${ARTIFACT_BASE_PATH} from env
       subdirectory: str
       cleanup_policy: Literal["keep_all", "keep_last_N", "keep_days"]
   ```

2. Implement artifact manager:
   ```python
   class ArtifactManager:
       def initialize_dirs(self, config: ArtifactsConfig): ...
       def get_artifact_path(self, filename: str) -> Path: ...
       def cleanup(self, policy: str): ...
   ```

3. Update CLI:
   ```bash
   platform create-project pdf_invoices \
       --artifact-path ~/extract-artifacts/invoices
   ```

4. Environment variable resolution:
   ```python
   # Resolve ${ARTIFACT_BASE_PATH} from .env
   base_path = os.path.expanduser(os.getenv("ARTIFACT_BASE_PATH"))
   ```

**Deliverables**:
- [ ] `artifacts` config section added
- [ ] Artifact manager implemented
- [ ] Directory auto-initialization
- [ ] Cleanup policies working
- [ ] Environment variables resolved

**Acceptance Criteria**:
- External artifacts stored outside repo
- Directories created automatically
- Cleanup policies prevent disk bloat
- Paths resolve correctly

**Dependencies**: T3, T8 (models, registry)

---

### Day 8: Work Path B - File Transformation

#### T12: Work Path B - PDF Extraction (pdfplumber)

**Priority**: P1 (High - User preference #1, Office format #2)
**Effort**: 2.0 days (16 hours)
**Assignee**: Engineer

**Tasks**:
1. **Day 8**: Implement PDFDataSource (8 hours)
   ```python
   # extract_transform_platform/sources/pdf_source.py
   import pdfplumber

   class PDFDataSource(BaseDataSource):
       async def fetch(self, **kwargs) -> Dict[str, Any]:
           with pdfplumber.open(self.file_path) as pdf:
               tables = []
               for page in pdf.pages:
                   tables.extend(page.extract_tables())
               return {"tables": tables, "metadata": {...}}
   ```

2. **Day 9 Morning**: Add table parsing logic (4 hours)
   - Convert tables to list of dicts (first row = headers)
   - Handle multi-page tables
   - Extract text alongside tables

3. **Day 9 Afternoon**: Test with invoice example (4 hours)
   - Create `projects/pdf_invoices/` test project
   - Add example PDF invoices
   - Validate extraction accuracy

**Deliverables**:
- [ ] `PDFDataSource` implemented
- [ ] Table extraction working
- [ ] Text extraction working
- [ ] Invoice test project created
- [ ] Tests pass

**Acceptance Criteria**:
- PDF tables extracted accurately (>90% accuracy)
- Multi-page PDFs handled
- Performance acceptable (<1s per page)
- Example project demonstrates usage

**Dependencies**: T2, T6 (data sources, interfaces)

---

#### T13: Work Path B - Excel Extraction (pandas)

**Priority**: P2 (Medium - User preference #1, Office format #1)
**Effort**: 0.5 days (4 hours)
**Assignee**: Engineer

**Objective**: Extend `FileDataSource` to support Excel files

**Tasks**:
1. Add Excel support to `FileDataSource`:
   ```python
   # In file_source.py
   async def fetch(self, **kwargs) -> Dict[str, Any]:
       if self.file_path.suffix in [".xlsx", ".xls"]:
           import pandas as pd
           df = pd.read_excel(self.file_path, **kwargs)
           return {"data": df.to_dict(orient="records")}
   ```

2. Add Excel-specific options:
   - `sheet_name`: Which sheet to read
   - `header_row`: Row number for headers
   - `skip_rows`: Rows to skip

3. Test with expense report example:
   ```yaml
   data_sources:
     - type: file
       file_path: data/expenses.xlsx
       options:
         sheet_name: "Expenses"
         header_row: 0
   ```

**Deliverables**:
- [ ] Excel support added to `FileDataSource`
- [ ] Sheet selection works
- [ ] Header row configuration works
- [ ] Test project created

**Acceptance Criteria**:
- Excel files load correctly
- Complex formulas ignored (values only)
- Multiple sheets supported
- pandas integration stable

**Dependencies**: T2, T6 (data sources, interfaces)

---

### Day 9-10: Performance, Interactive Mode, Migration

#### T14: Work Path D - Interactive Mode (Confidence Threshold)

**Priority**: P1 (High - User preference #5)
**Effort**: 1.0 days (8 hours)
**Assignee**: Engineer

**Objective**: Add interactive confidence threshold prompting

**Tasks**:
1. **Day 9**: Add confidence display (4 hours)
   ```python
   # After pattern detection
   print_pattern_confidence_table(patterns)
   # Shows: Pattern | Frequency | Confidence
   ```

2. **Day 9**: Implement threshold prompts (4 hours)
   ```python
   def prompt_confidence_threshold() -> float:
       print("Confidence Threshold Options:")
       print("1. Strict (90%+)")
       print("2. Moderate (70%+)")
       print("3. Lenient (50%+)")
       print("4. Custom")
       choice = input("Select (1-4): ")
       # ... handle selection
       return threshold
   ```

3. Add `--interactive` flag to `generate` command:
   ```bash
   platform generate weather_api --interactive
   ```

4. Filter patterns based on threshold:
   ```python
   filtered_patterns = [
       p for p in patterns if p.confidence >= threshold
   ]
   ```

**Deliverables**:
- [ ] Confidence table display
- [ ] Interactive threshold prompting
- [ ] `--interactive` flag works
- [ ] Pattern filtering implemented
- [ ] Recommendations shown

**Acceptance Criteria**:
- User can see pattern confidence
- User can select threshold
- Low-confidence patterns filtered
- Recommendations helpful

**Dependencies**: T4, T9 (code generation, CLI)

---

#### T15: Work Path C - Jina.ai Configuration Guide

**Priority**: P2 (Medium - Documentation)
**Effort**: 0.5 days (4 hours)
**Assignee**: Tech Writer / Engineer

**Objective**: Document Jina.ai setup for JS-heavy web scraping

**Tasks**:
1. Create guide: `docs/guides/WEB_SCRAPING_JINA.md`

2. Document API key setup:
   ```bash
   # .env.local
   JINA_API_KEY=your_jina_api_key_here
   ```

3. Provide example project:
   ```yaml
   # projects/linkedin_jobs/project.yaml
   data_sources:
     - type: jina
       url: https://www.linkedin.com/jobs/search/?keywords=python
       auth:
         type: api_key
         key: ${JINA_API_KEY}
   ```

4. Document limitations and best practices

**Deliverables**:
- [ ] Jina.ai guide written
- [ ] Example project created
- [ ] API key setup documented
- [ ] Best practices included

**Acceptance Criteria**:
- Guide is clear and actionable
- Example project works
- User can set up Jina.ai in <10 minutes

**Dependencies**: None (documentation only)

---

#### T16: Performance Optimization (Parallel AI, Caching)

**Priority**: P1 (High - Performance target <4:00)
**Effort**: 1.5 days (12 hours)
**Assignee**: Engineer

**Objective**: Reduce generation time from 5:11 to <4:00

**Tasks**:
1. **Day 10 Morning**: Implement parallel AI calls (4 hours)
   ```python
   async def generate_code_optimized(examples, config):
       # Start PM mode + boilerplate in parallel
       pm_task = asyncio.create_task(pm_mode_generate_plan(examples))
       imports_task = asyncio.create_task(generate_imports(config))

       plan = await pm_task
       imports = await imports_task

       # Coder mode (now faster)
       code = await coder_mode_generate(plan, imports)
       return code
   ```

2. **Day 10 Midday**: Add component caching (2 hours)
   - Cache imports (rarely change)
   - Cache interface templates
   - Cache common patterns

3. **Day 10 Afternoon**: Optimize prompts (4 hours)
   - Reduce prompt size (3,500 → 2,500 tokens)
   - Remove redundancy
   - Compress examples

4. **Day 10 Late**: Benchmark and validate (2 hours)
   - Test with weather_api project
   - Measure generation time
   - Validate quality unchanged

**Deliverables**:
- [ ] Parallel AI calls implemented
- [ ] Component caching added
- [ ] Prompts optimized
- [ ] Generation time <4:00
- [ ] Quality maintained

**Acceptance Criteria**:
- Weather API generates in <4:00 (down from 5:11)
- Code quality unchanged (same tests pass)
- No regression in accuracy

**Dependencies**: T4 (code generation)

---

#### T17: Migrate EDGAR Code to legacy/

**Priority**: P2 (Medium - Cleanup)
**Effort**: 1.0 days (8 hours)
**Assignee**: Engineer

**Objective**: Move EDGAR-specific code to `legacy/` subdirectory

**Tasks**:
1. Create `edgar_analyzer/legacy/` directory

2. Move EDGAR-specific services:
   - `edgar_api_service.py`
   - `breakthrough_xbrl_service.py`
   - `company_service.py`
   - `fortune500_builder.py`
   - `historical_analysis_service.py`
   - `multi_source_enhanced_service.py`
   - `qa_controller.py`

3. Update `edgar_analyzer/__init__.py` for backward compatibility:
   ```python
   from edgar_analyzer.legacy.edgar_api_service import EdgarApiService
   # ... re-export for compatibility
   ```

4. Add deprecation warnings

5. Update tests to import from `legacy/`

**Deliverables**:
- [ ] EDGAR code moved to `legacy/`
- [ ] Backward compatibility maintained
- [ ] Deprecation warnings added
- [ ] Tests updated and passing

**Acceptance Criteria**:
- Existing EDGAR code still works
- Clear separation: generic vs. legacy
- Deprecation warnings visible but non-blocking

**Dependencies**: T1-T6 (generic platform complete)

---

### Week 2 Summary

**Completed Tickets**: T7-T17 (11 tickets)
**Effort**: 10.5 days (parallelized to 5 days)
**Deliverables**:
- ✅ Project isolation system (containers, registry)
- ✅ Multi-project CLI
- ✅ External artifacts directory
- ✅ PDF + Excel extraction
- ✅ Interactive mode
- ✅ Performance optimization (<4:00)
- ✅ EDGAR migration to legacy/

**Validation**:
- [ ] Create 3 test projects (api, pdf, excel)
- [ ] Run end-to-end tests
- [ ] Benchmark generation time
- [ ] Validate 70% code reuse metric

---

## Dependency Graph

### Critical Path (P0 Tickets)

```
T1 (Package Structure)
 ├─> T2 (Data Sources)
 │    └─> T6 (Interfaces)
 ├─> T3 (Models)
 │    └─> T4 (Code Generation)
 │         └─> T5 (AI Integration)
 └─> [Week 1 Complete]
```

### Week 2 Dependencies

```
Week 1 Complete
 ├─> T7 (Project Container)
 │    └─> T8 (Registry)
 │         └─> T9 (CLI Refactor)
 │              └─> T10 (CRUD Commands)
 │              └─> T14 (Interactive Mode)
 ├─> T11 (External Artifacts)
 ├─> T12 (PDF Extraction)
 ├─> T13 (Excel Extraction)
 ├─> T16 (Performance)
 └─> T17 (EDGAR Migration)
```

### Parallelization Opportunities

**Week 1**:
- T2 + T3 can run in parallel (Day 1-2)
- T5 + T6 can run in parallel (Day 4)

**Week 2**:
- T11 + T12 + T13 can run in parallel (Day 7-8)
- T14 + T15 can run in parallel (Day 9)
- T16 + T17 can run in parallel (Day 10)

**Effect**: 17.0 days of effort → 10 days calendar time

---

## Resource Allocation

### Engineer Time Breakdown

| Week | Focus Area | Tickets | Effort |
|------|-----------|---------|--------|
| Week 1 | Platform extraction | T1-T6 | 5.0 days |
| Week 2 | Work paths & integration | T7-T17 | 5.0 days |
| **Total** | | **18 tickets** | **10 days** |

### Skill Requirements

**Required Skills**:
- Python 3.11+ (advanced)
- Async/await patterns
- Dependency injection (dependency-injector)
- Pydantic models
- Click CLI framework
- pytest testing
- mypy type checking

**Nice-to-Have Skills**:
- AI/LLM integration
- PDF parsing (pdfplumber)
- pandas data manipulation
- Web scraping (Jina.ai)

### External Dependencies

**Third-Party Libraries**:
- `pdfplumber` (PDF extraction) - install Week 2, Day 8
- `pandas` (Excel extraction) - already installed
- `python-docx` (DOCX extraction) - Phase 3
- `python-pptx` (PPTX extraction) - Phase 3

**API Keys Required**:
- ✅ OpenRouter API key (already configured)
- ⏳ Jina.ai API key (user provided, needs configuration)

---

## Milestone Schedule

### Week 1 Milestones

| Day | Milestone | Tickets | Validation |
|-----|-----------|---------|------------|
| Day 1-2 | Package structure + data sources | T1, T2, T3 | Package imports, tests pass |
| Day 3-4 | Code generation services | T4, T5 | Weather API generates |
| Day 5 | Interfaces + Week 1 complete | T6 | All tests pass, 70% reuse validated |

### Week 2 Milestones

| Day | Milestone | Tickets | Validation |
|-----|-----------|---------|------------|
| Day 6-7 | Project isolation + CLI | T7, T8, T9, T10 | Multi-project CLI works |
| Day 8 | File transformation | T11, T12, T13 | PDF + Excel extraction works |
| Day 9 | Interactive mode | T14, T15 | Confidence prompting works |
| Day 10 | Performance + migration | T16, T17 | <4:00 generation, legacy separated |

### Phase 2 Completion Criteria

**Must Complete (P0 + P1)**:
- [ ] T1-T6: Generic platform package (P0)
- [ ] T7-T10: Project isolation (P1)
- [ ] T11-T12, T14, T16: Core work paths (P1)

**Should Complete (P2)**:
- [ ] T13: Excel extraction
- [ ] T15: Jina.ai guide
- [ ] T17: EDGAR migration

**Can Defer (P3)**:
- [ ] T18: DOCX extraction (Phase 3)

### Phase 2 Success Metrics

| Metric | Target | Validation Method |
|--------|--------|-------------------|
| Code reusability | ≥70% | Count LOC: generic / total |
| Generation time | <4:00 | Benchmark weather_api project |
| Test coverage | ≥80% | `pytest --cov` report |
| Type safety | 100% | `mypy --strict` passes |
| Work paths functional | 4/4 | Manual testing + integration tests |

---

## Deferred to Phase 3

### T18: DOCX Extraction (python-docx)

**Priority**: P3 (Low - Office format #3)
**Effort**: 1.5 days
**Reason for Deferral**: Lower user priority, PDF + Excel cover 80% use cases

**Implementation Plan (Phase 3)**:
1. Install `python-docx` library
2. Implement `DOCXDataSource`
3. Extract text, tables, images
4. Test with contract documents

**User Impact**: Minimal - most users need Excel and PDF first

---

## Document Metadata

**Version**: 1.0
**Status**: Phase 2 Work Breakdown
**Author**: Research Agent (Claude Sonnet 4.5)
**Date**: 2025-11-29
**Related Documents**:
- [PHASE_2_ARCHITECTURE.md](PHASE_2_ARCHITECTURE.md)
- [PHASE_2_RISKS_AND_MITIGATION.md](PHASE_2_RISKS_AND_MITIGATION.md)
- [GO_DECISION_PHASE_2_2025-11-28.md](decisions/GO_DECISION_PHASE_2_2025-11-28.md)

**Epic**: [4a248615-f1dd-4669-9f61-edec2d2355ac](https://linear.app/1m-hyperdev/project/edgar-%E2%86%92-general-purpose-extract-and-transform-platform-e4cb3518b13e/issues)
