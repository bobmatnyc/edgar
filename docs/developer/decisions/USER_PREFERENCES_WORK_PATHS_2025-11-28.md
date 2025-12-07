# User Preferences: Platform Work Paths Configuration

**Date**: 2025-11-28
**Context**: Confirmed 4 major work paths with user-specific preferences and implementation requirements
**Status**: Decision Record - Implementation Planning

---

## Preferences Summary

| Preference | User Choice | Implementation Status | Priority |
|------------|-------------|----------------------|----------|
| **Office Format Priority** | Excel → PDF → DOCX → PPTX | Partial (Excel ready) | HIGH |
| **Artifact Storage** | External directory (outside repo) | Needs config | HIGH |
| **Web Scraping** | JS-heavy sites (Jina.ai key provided) | Needs auth setup | MEDIUM |
| **Example Collection** | Exemplar-based with data types | Ready | LOW |
| **Confidence Threshold** | User-prompted choice | Needs UI update | MEDIUM |
| **Project Workflow** | Sequential (one at a time) | Ready | LOW |

---

## Detailed Preferences

### 1. Office Format Priority

**User Preference**: Excel (XLS/XLSX) → PDF → DOCX → PPTX

**Rationale**:
- Excel is primary business data format (80% use case)
- PDF for document processing (reports, statements)
- DOCX for text-heavy documents
- PPTX lowest priority (can defer)

**Current Status**:
- ✅ Excel: `openpyxl` and `pandas` installed and tested
- 🔨 PDF: Need parser selection (PyPDF2 vs pdfplumber vs pymupdf)
- 🔨 DOCX: Need `python-docx` library
- 🔨 PPTX: Need `python-pptx` library

**Implementation Timeline**:
1. **Week 1**: PDF support (3-4 days)
   - Evaluate parsers for table extraction
   - Implement PDF → structured data pipeline
   - Test with financial reports
2. **Week 2**: DOCX support (2-3 days)
   - Install python-docx
   - Implement text + table extraction
   - Test with corporate filings
3. **Week 3**: PPTX support (2-3 days, deferred)
   - Install python-pptx
   - Implement slide content extraction
   - Test with investor presentations

**Dependencies**:
```bash
# PDF parsing
pip install pdfplumber  # Recommended for tables
pip install PyPDF2      # Fallback for text

# DOCX parsing
pip install python-docx

# PPTX parsing (deferred)
pip install python-pptx
```

---

### 2. Artifact Storage Strategy

**User Preference**: External directory outside repository

**Rationale**:
- Keep repository clean (no large binary files)
- Easier backup and archival
- Better .gitignore management
- Supports multiple projects without repo bloat

**Proposed Structure**:
```
~/edgar-platform-artifacts/
├── projects/
│   ├── project-001-apple-compensation/
│   │   ├── source/           # Original files
│   │   ├── extracted/        # Extracted data (CSV, JSON)
│   │   ├── examples/         # Training examples
│   │   └── results/          # Generated code
│   └── project-002-meta-10k/
│       └── ...
├── examples/                  # Shared examples library
│   ├── excel-tables/
│   ├── pdf-reports/
│   └── web-scraping/
└── cache/                     # Shared cache
    └── web-content/
```

**Configuration Required**:
```yaml
# config/artifact_storage.yaml
artifact_storage:
  base_path: "~/edgar-platform-artifacts"
  auto_create: true
  max_size_gb: 50
  cleanup_policy: "archive_after_30_days"

  paths:
    projects: "${base_path}/projects"
    examples: "${base_path}/examples"
    cache: "${base_path}/cache"
```

**Implementation Tasks**:
1. Add `artifact_storage.yaml` to config
2. Create `ArtifactStorageService` class
3. Update project creation to use external paths
4. Add cleanup/archival scripts
5. Update documentation (user needs to set base path)

**Estimated Effort**: 1-2 days

---

### 3. Web Scraping Capabilities

**User Preference**: JS-heavy site support using Jina.ai

**Status**:
- Jina.ai API key provided
- Authentication NOT yet configured
- Need to implement Jina Reader integration

**Rationale**:
- Many corporate sites use React/Vue/Angular
- Traditional scrapers fail on JS-rendered content
- Jina.ai handles JS execution + returns clean markdown
- Reduces complexity vs Selenium/Playwright

**Implementation Plan**:

**Phase 1: Jina.ai Integration (Day 1-2)**
```python
# src/edgar_analyzer/services/jina_reader_service.py
import httpx
from typing import Optional

class JinaReaderService:
    """
    Service for scraping JS-heavy websites using Jina.ai Reader API.

    Jina.ai handles:
    - JavaScript execution
    - Dynamic content loading
    - Clean markdown conversion
    - Screenshot capture (optional)
    """

    BASE_URL = "https://r.jina.ai"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.Client(
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0
        )

    async def scrape_url(
        self,
        url: str,
        wait_for_selector: Optional[str] = None
    ) -> dict:
        """
        Scrape URL and return markdown content.

        Args:
            url: Target URL
            wait_for_selector: CSS selector to wait for (optional)

        Returns:
            {
                "content": "markdown text",
                "title": "page title",
                "url": "final url after redirects"
            }
        """
        endpoint = f"{self.BASE_URL}/{url}"
        params = {}
        if wait_for_selector:
            params["wait_for"] = wait_for_selector

        response = self.client.get(endpoint, params=params)
        response.raise_for_status()

        return {
            "content": response.text,
            "title": response.headers.get("X-Title", ""),
            "url": response.headers.get("X-Final-URL", url)
        }
```

**Phase 2: Configuration Setup (Day 2)**
```yaml
# config/web_scraping.yaml
web_scraping:
  jina:
    api_key: "${JINA_API_KEY}"  # From environment
    timeout: 30
    max_retries: 3

  fallback_scrapers:
    - beautifulsoup  # For simple HTML
    - requests       # For static content
```

**Phase 3: Testing (Day 3)**
- Test with JS-heavy corporate sites
- Compare results vs BeautifulSoup
- Document limitations and edge cases

**Estimated Effort**: 3-5 days

**Dependencies**:
```bash
pip install httpx  # Async HTTP client
```

---

### 4. Example Collection Method

**User Preference**: Exemplar-based with explicit data types

**Rationale**:
- Start with representative example file
- User annotates with data types (string, number, date, etc.)
- System learns extraction patterns from annotations
- More reliable than unsupervised learning

**Current Status**: ✅ Architecture already supports this

**Example Workflow**:
```python
# User provides exemplar Excel file
exemplar = "~/artifacts/examples/apple-exec-comp-2023.xlsx"

# User annotates data types
annotations = {
    "Name": {"type": "string", "role": "executive_name"},
    "Total Compensation": {"type": "currency", "role": "total_comp"},
    "Salary": {"type": "currency", "role": "base_salary"},
    "Bonus": {"type": "currency", "role": "bonus"},
    "Stock Awards": {"type": "currency", "role": "equity"}
}

# System generates extraction code
project = platform.create_project(
    exemplar=exemplar,
    annotations=annotations,
    project_type="executive_compensation"
)
```

**Implementation Status**:
- Pattern matching: ✅ Ready (in LLM-based extraction)
- Data type validation: ✅ Ready (Pydantic models)
- Example storage: 🔨 Needs external directory config
- Annotation UI: ⏳ Future enhancement (optional)

**No additional development needed** - this is already supported.

---

### 5. Confidence Threshold

**User Preference**: Prompt user to choose threshold at runtime

**Rationale**:
- Different projects have different accuracy requirements
- User knows their risk tolerance
- Flexibility > hardcoded values

**Proposed UI Flow**:
```
🎯 Confidence Threshold Selection

How certain should the extraction be before accepting results?

1. HIGH (95%+)     - Use when: Financial data, regulatory filings
2. MEDIUM (85%+)   - Use when: General business data, reports
3. LOW (70%+)      - Use when: Exploratory analysis, rough estimates
4. CUSTOM          - Enter specific threshold (0-100%)

Your choice [1-4]: _
```

**Implementation**:
```python
# src/edgar_analyzer/services/confidence_prompt_service.py

class ConfidencePromptService:
    PRESETS = {
        "HIGH": 0.95,
        "MEDIUM": 0.85,
        "LOW": 0.70
    }

    def prompt_threshold(self) -> float:
        """Interactive confidence threshold selection."""
        print("\n🎯 Confidence Threshold Selection\n")
        print("1. HIGH (95%+)   - Financial data, regulatory filings")
        print("2. MEDIUM (85%+) - General business data, reports")
        print("3. LOW (70%+)    - Exploratory analysis, estimates")
        print("4. CUSTOM        - Enter specific threshold\n")

        choice = input("Your choice [1-4]: ").strip()

        if choice == "1":
            return self.PRESETS["HIGH"]
        elif choice == "2":
            return self.PRESETS["MEDIUM"]
        elif choice == "3":
            return self.PRESETS["LOW"]
        elif choice == "4":
            custom = float(input("Enter threshold (0-100): ")) / 100
            return max(0.0, min(1.0, custom))
        else:
            print("Invalid choice, using MEDIUM (85%)")
            return self.PRESETS["MEDIUM"]
```

**Integration Point**:
```python
# In project creation workflow
confidence_service = ConfidencePromptService()
threshold = confidence_service.prompt_threshold()

project = platform.create_project(
    ...,
    confidence_threshold=threshold
)
```

**Estimated Effort**: 1 day (add service + integrate into CLI)

---

### 6. Project Workflow

**User Preference**: Sequential (one project at a time)

**Rationale**:
- Simpler state management
- Easier debugging and iteration
- User focuses on one problem at a time
- Can still create multiple projects, just not parallel execution

**Current Status**: ✅ Already implemented this way

**Architecture**:
```
User creates Project A
  → Generate extraction code
  → Test and iterate
  → Save results

User creates Project B
  → Reuse patterns from Project A
  → Generate extraction code
  → Test and iterate
  → Save results
```

**Parallelization** (future enhancement):
- Backend: Run multiple extractions in parallel
- Frontend: User still configures one at a time
- No UI complexity for managing parallel projects

**No development needed** - current architecture already sequential.

---

## Implementation Roadmap

### Phase 1: Foundation (Ready Now) ✅
**Duration**: 0 days (already complete)
**Work Paths Ready**:
- ✅ Work Path A (Project-based): Core architecture ready
- ✅ Work Path D (Interactive chat): CLI chatbot ready

**What User Can Do Now**:
- Create projects for Excel file extraction
- Use interactive chat for queries
- Sequential workflow (one project at a time)

**Limitations**:
- Artifacts stored in repo (need external dir)
- No PDF/DOCX support yet
- No JS-heavy web scraping yet
- Hardcoded confidence threshold

---

### Phase 2: Configuration & Storage (Week 1) 🔨
**Duration**: 2-3 days
**Priority**: HIGH (enables clean artifact management)

**Tasks**:
1. Create `artifact_storage.yaml` config
2. Implement `ArtifactStorageService`
3. Update project creation to use external paths
4. Add cleanup/archival scripts
5. Update user documentation

**Deliverables**:
- External artifact directory structure
- Configuration guide for users
- Migration script for existing projects

**Blockers Removed**:
- Repository bloat from binary files
- Easier project management
- Better backup strategies

---

### Phase 3: PDF Support (Week 1-2) 🔨
**Duration**: 3-4 days
**Priority**: HIGH (80% of document processing needs)

**Tasks**:
1. Evaluate PDF parsers (pdfplumber, PyPDF2, pymupdf)
2. Implement PDF extraction service
3. Add table detection and extraction
4. Test with financial reports (10-K, proxy statements)
5. Document PDF extraction capabilities

**Deliverables**:
- PDF → structured data pipeline
- Table extraction from PDFs
- Text extraction with layout preservation

**Work Path Enabled**:
- ✅ Work Path B (File transformation): Excel + PDF support

---

### Phase 4: Web Scraping (Week 2-3) 🔨
**Duration**: 3-5 days
**Priority**: MEDIUM (enables JS-heavy sites)

**Tasks**:
1. Implement Jina.ai Reader service
2. Add authentication configuration
3. Create fallback to BeautifulSoup
4. Test with corporate websites
5. Document scraping capabilities and limitations

**Deliverables**:
- JS-heavy website scraping
- Clean markdown conversion
- Scraping service documentation

**Work Path Enabled**:
- ✅ Work Path C (Web scraping): Full capability

---

### Phase 5: DOCX Support (Week 3-4) 🔨
**Duration**: 2-3 days
**Priority**: MEDIUM (completes office format trio)

**Tasks**:
1. Install python-docx
2. Implement DOCX extraction service
3. Add table and text extraction
4. Test with corporate filings
5. Document DOCX capabilities

**Deliverables**:
- DOCX → structured data pipeline
- Table and text extraction
- DOCX service documentation

**Work Path Enhancement**:
- ✅ Work Path B: Excel + PDF + DOCX support

---

### Phase 6: Confidence UI (Week 4) 🔨
**Duration**: 1 day
**Priority**: LOW (nice-to-have, can use defaults)

**Tasks**:
1. Create `ConfidencePromptService`
2. Integrate into project creation workflow
3. Add presets (HIGH/MEDIUM/LOW)
4. Test user experience

**Deliverables**:
- Interactive confidence threshold selection
- Preset options for common use cases
- Custom threshold input

**Enhancement**:
- Better user control over extraction accuracy

---

### Phase 7: PPTX Support (Future) ⏳
**Duration**: 2-3 days
**Priority**: DEFERRED (lowest priority)

**Tasks**:
1. Install python-pptx
2. Implement PPTX extraction service
3. Test with investor presentations
4. Document capabilities

**Deliverables**:
- PPTX → structured data pipeline
- Slide content extraction

**Deferral Rationale**:
- Lowest user priority
- Can launch without this
- Add based on demand

---

## Gap Analysis: What Exists vs What Needs Development

### Work Path A: Project-Based Development ✅
**Status**: 90% Ready

| Component | Status | Effort |
|-----------|--------|--------|
| Project creation | ✅ Ready | 0 days |
| Example collection | ✅ Ready | 0 days |
| Code generation | ✅ Ready | 0 days |
| External artifact storage | 🔨 Config needed | 2 days |
| Excel extraction | ✅ Ready | 0 days |
| PDF extraction | 🔨 Needs development | 4 days |
| DOCX extraction | 🔨 Needs development | 3 days |

**Blocker**: External directory configuration (2 days)
**Timeline to Full Ready**: 2 days (storage) + 4 days (PDF) = 6 days

---

### Work Path B: Office File Transformation 🔨
**Status**: 30% Ready

| Component | Status | Effort |
|-----------|--------|--------|
| Excel → structured data | ✅ Ready | 0 days |
| PDF → structured data | 🔨 Needs development | 4 days |
| DOCX → structured data | 🔨 Needs development | 3 days |
| PPTX → structured data | ⏳ Deferred | 3 days |
| Data validation | ✅ Ready | 0 days |
| Output generation | ✅ Ready | 0 days |

**Blocker**: PDF and DOCX parsers (7 days total)
**Timeline to 80% Ready**: 7 days (Excel + PDF + DOCX)
**Timeline to 100% Ready**: 10 days (add PPTX)

---

### Work Path C: Web Content Extraction 🔨
**Status**: 40% Ready

| Component | Status | Effort |
|-----------|--------|--------|
| Basic HTML scraping | ✅ Ready | 0 days |
| JS-heavy scraping | 🔨 Needs Jina.ai integration | 4 days |
| Table extraction | ✅ Ready | 0 days |
| Content caching | ✅ Ready | 0 days |
| External storage | 🔨 Config needed | 2 days |

**Blocker**: Jina.ai integration (4 days)
**Timeline to Full Ready**: 4 days (Jina.ai) + 2 days (storage) = 6 days

---

### Work Path D: Interactive Chat Interface ✅
**Status**: 95% Ready

| Component | Status | Effort |
|-----------|--------|--------|
| CLI chatbot | ✅ Ready | 0 days |
| Query processing | ✅ Ready | 0 days |
| Context management | ✅ Ready | 0 days |
| Confidence prompting | 🔨 UI enhancement | 1 day |
| Response formatting | ✅ Ready | 0 days |

**Blocker**: None (confidence prompting is optional)
**Timeline to Full Ready**: 1 day (add confidence UI)

---

## Development Priority by User Need

### Immediate Needs (Week 1) 🔴
**Can't launch without these**:
1. **External artifact storage** (2 days)
   - Prevents repo bloat
   - Required for clean project management
2. **PDF extraction** (4 days)
   - 80% of user's document processing
   - Critical for financial reports

**Total**: 6 days to minimum viable platform

---

### High-Value Enhancements (Week 2-3) 🟡
**Significantly improves user experience**:
1. **DOCX extraction** (3 days)
   - Completes office format trio (Excel + PDF + DOCX)
   - Handles text-heavy corporate filings
2. **Jina.ai web scraping** (4 days)
   - Enables JS-heavy corporate sites
   - Competitive differentiator

**Total**: 7 days for enhanced capabilities

---

### Nice-to-Have (Week 4+) 🟢
**Can defer or add based on demand**:
1. **Confidence threshold UI** (1 day)
   - Better UX, but defaults work fine
2. **PPTX extraction** (3 days)
   - Lowest priority per user
   - Add if requested

**Total**: 4 days for polish and completeness

---

## Ready-to-Use vs Needs-Development Breakdown

### ✅ Ready to Use NOW (0 days)
**User can start using immediately**:
- Create projects for Excel file extraction
- Interactive chat for data queries
- Example-based learning (exemplar approach)
- Sequential project workflow
- Basic HTML web scraping
- Data validation and quality checks
- CSV/Excel report generation

**Use Cases Supported**:
- Excel-based executive compensation extraction
- Simple web scraping (static HTML)
- Interactive data exploration
- One project at a time workflow

**Limitations**:
- No PDF or DOCX support
- No JS-heavy website scraping
- Artifacts stored in repo
- Hardcoded confidence threshold

---

### 🔨 Needs Development (6-13 days)

#### Critical Path (6 days minimum)
**Must-have for launch**:
1. External artifact storage (2 days)
2. PDF extraction (4 days)

**After these 6 days**:
- User can process Excel + PDF files
- Clean artifact management outside repo
- 80% of document processing needs met

#### Enhanced Capabilities (7 more days)
**High value but not blocking**:
1. DOCX extraction (3 days)
2. Jina.ai web scraping (4 days)

**After these 7 days**:
- Full office format support (Excel + PDF + DOCX)
- JS-heavy website scraping
- 95% of user needs met

#### Polish (4 more days)
**Nice-to-have enhancements**:
1. Confidence threshold UI (1 day)
2. PPTX extraction (3 days)

**After these 4 days**:
- Complete office format support
- Better UX for confidence selection
- 100% of identified needs met

---

## Configuration Requirements

### 1. Environment Variables
```bash
# .env.local (gitignored)
OPENROUTER_API_KEY=your_key_here
JINA_API_KEY=jina_provided_key_here
SEC_EDGAR_USER_AGENT=YourName/YourEmail
LOG_LEVEL=INFO

# Artifact storage path (user-specific)
ARTIFACT_BASE_PATH=~/edgar-platform-artifacts
```

### 2. Configuration Files

**artifact_storage.yaml**:
```yaml
artifact_storage:
  base_path: "${ARTIFACT_BASE_PATH}"
  auto_create: true
  max_size_gb: 50
  cleanup_policy: "archive_after_30_days"

  paths:
    projects: "${base_path}/projects"
    examples: "${base_path}/examples"
    cache: "${base_path}/cache"
```

**web_scraping.yaml**:
```yaml
web_scraping:
  jina:
    api_key: "${JINA_API_KEY}"
    timeout: 30
    max_retries: 3

  fallback_scrapers:
    - beautifulsoup
    - requests
```

**file_parsers.yaml**:
```yaml
file_parsers:
  excel:
    engine: openpyxl
    read_only: true

  pdf:
    engine: pdfplumber  # Best for tables
    fallback: PyPDF2    # For text

  docx:
    engine: python-docx
```

### 3. Dependency Updates

**pyproject.toml additions**:
```toml
[project.dependencies]
# Existing...
# Web scraping
httpx = "^0.27.0"  # For Jina.ai

# PDF parsing
pdfplumber = "^0.11.0"
PyPDF2 = "^3.0.0"

# DOCX parsing
python-docx = "^1.1.0"

# PPTX parsing (deferred)
# python-pptx = "^0.6.23"
```

---

## Next Actions (Prioritized)

### Week 1: Foundation 🔴
**Goal**: Minimum viable platform

1. **Day 1-2: External Artifact Storage**
   - Create `artifact_storage.yaml`
   - Implement `ArtifactStorageService`
   - Update project creation workflow
   - Test with existing projects
   - Document configuration for users

2. **Day 3-6: PDF Extraction**
   - Install pdfplumber and PyPDF2
   - Implement `PDFExtractionService`
   - Add table detection
   - Test with 10-K filings and proxy statements
   - Document PDF capabilities

**Deliverable**: User can process Excel + PDF with clean artifact management

---

### Week 2: Enhanced Capabilities 🟡
**Goal**: Full office format + web scraping

1. **Day 7-9: DOCX Extraction**
   - Install python-docx
   - Implement `DOCXExtractionService`
   - Test with corporate filings
   - Document DOCX capabilities

2. **Day 10-13: Jina.ai Web Scraping**
   - Implement `JinaReaderService`
   - Add authentication configuration
   - Test with JS-heavy sites
   - Document scraping capabilities

**Deliverable**: User can process Excel + PDF + DOCX + JS-heavy websites

---

### Week 3-4: Polish & Completeness 🟢
**Goal**: 100% user preferences supported

1. **Day 14: Confidence Threshold UI**
   - Create `ConfidencePromptService`
   - Integrate into CLI workflow
   - Test user experience

2. **Day 15-17: PPTX Extraction (optional)**
   - Install python-pptx
   - Implement `PPTXExtractionService`
   - Test with investor presentations

**Deliverable**: Complete platform with all 6 user preferences supported

---

## Success Metrics

### Platform Readiness
- ✅ **Minimum Viable** (6 days): Excel + PDF + external storage
- ✅ **Full Featured** (13 days): Excel + PDF + DOCX + web scraping
- ✅ **Complete** (17 days): All office formats + web scraping + polish

### User Capability
- ✅ **Week 1**: Process 80% of document types
- ✅ **Week 2**: Process 95% of document types + websites
- ✅ **Week 3**: Process 100% of identified needs

### Quality Metrics
- All new services have ≥80% test coverage
- Documentation complete for each capability
- User configuration guide updated
- Example projects for each format type

---

## Risk Assessment

### Low Risk ✅
- External artifact storage (straightforward implementation)
- Confidence threshold UI (small enhancement)
- DOCX extraction (mature library)

### Medium Risk ⚠️
- PDF extraction (table detection can be tricky)
  - Mitigation: Test with diverse PDF formats
  - Fallback: Multiple parser options
- Jina.ai integration (external API dependency)
  - Mitigation: Fallback to BeautifulSoup
  - Fallback: Document limitations

### High Risk 🔴
- None identified for Phase 1-2 implementation

---

## Conclusion

**Current State**:
- 2 out of 4 work paths fully ready
- 2 out of 4 work paths need 6-13 days development

**Recommended Approach**:
1. **Week 1**: External storage + PDF (enables 80% use cases)
2. **Week 2**: DOCX + Jina.ai (enables 95% use cases)
3. **Week 3**: Confidence UI + PPTX (enables 100% use cases)

**User Can Start Now With**:
- Excel-based projects
- Interactive chat
- Basic web scraping
- Sequential workflow

**Timeline to Full Capability**: 13 working days (2.5 weeks)

---

**Document Maintenance**:
- Update this document as implementation progresses
- Mark completed phases with ✅
- Add learnings and adjustments to roadmap
- Track actual vs estimated timelines
