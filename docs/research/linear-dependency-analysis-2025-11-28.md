# Linear Project Dependency Analysis - EDGAR Platform Transformation

**Date**: 2025-11-28
**Epic**: EDGAR → General-Purpose Extract & Transform Platform
**Epic ID**: 4a248615-f1dd-4669-9f61-edec2d2355ac
**Research Agent**: Claude Code (Research)

---

## Executive Summary

**Critical Finding**: Phase 2 is BLOCKED by Phase 1 foundation work. Only 1/7 Phase 1 tickets completed (1M-329 GO decision). The critical path requires completing 5 Phase 1 foundation tickets before starting any Phase 2 work.

**User Preference Gaps Identified**:
- **Excel support**: NOT MAPPED to any ticket (HIGH PRIORITY GAP)
- **External directory**: NOT MAPPED to any ticket (HIGH PRIORITY GAP)
- **JS-heavy scraping**: Partially addressed by 1M-339 (Jina.ai), needs Playwright ticket
- **Confidence prompting**: NOT MAPPED to any ticket (MEDIUM PRIORITY GAP)

**Recommended Action**: Create 3-4 new tickets to address user preference gaps, then execute Phase 1 foundation work before attempting Phase 2.

---

## 1. Dependency Chain Analysis

### Project Status Overview

**Total Issues**: 20 (3 closed, 17 open)

**Completed (DONE)**:
- ✅ 1M-359: Auto-compaction at 75% context (chatbot improvement)
- ✅ 1M-358: One-shot query mode (chatbot improvement)
- ✅ 1M-329: GO Decision validation (Phase 1 critical)

**In Progress**:
- 🟡 1M-325: Sonnet 4.5 Integration (PM + Coder modes) - **CRITICAL**

**Open (17 tickets)**:
- Phase 1: 6 tickets (1 in-progress, 5 blocked)
- Phase 2: 10 tickets (all blocked by Phase 1)
- Phase 3: 1 ticket (blocked by Phase 2)
- Phase 4: 1 ticket (blocked by Phase 2)
- Phase 5: 1 ticket (blocked by all phases)

### Dependency Hierarchy

```
Epic: 4a248615-f1dd-4669-9f61-edec2d2355ac
├── 1M-359 (DONE - chatbot)
├── 1M-358 (DONE - chatbot)
├── Phase 1: 1M-318 (Weather API POC)
│   ├── 1M-329 (DONE - GO Decision) ✅
│   ├── 1M-325 (IN PROGRESS - Sonnet 4.5 Integration) 🟡
│   ├── 1M-328 (BLOCKED - Generate Weather Extractor) ❌ depends on 1M-323-327
│   ├── 1M-327 (OPEN - Constraint Enforcer) ⏸️ depends on 1M-323
│   ├── 1M-326 (OPEN - Weather API Template) ⏸️ depends on 1M-323
│   ├── 1M-324 (OPEN - Example Parser) ⏸️ depends on 1M-323
│   └── 1M-323 (OPEN - Project YAML Schema) 🔴 FOUNDATION
│
├── Phase 2: 1M-319 (Core Platform)
│   ├── 1M-330 (CRITICAL - Abstraction Layer) 🔴 FOUNDATION (blocks ALL Phase 2)
│   ├── 1M-333 (CRITICAL - Project Manager) 🔴 FOUNDATION (blocks ALL Phase 2)
│   ├── 1M-331 (HIGH - IDataSource) depends on 1M-330
│   ├── 1M-332 (HIGH - IDataExtractor) depends on 1M-330
│   ├── 1M-334 (HIGH - Isolation System) depends on 1M-330, 1M-333
│   ├── 1M-335 (HIGH - YAML Parser) depends on 1M-330, 1M-323
│   ├── 1M-336 (HIGH - DI Container) depends on 1M-330, 1M-333
│   ├── 1M-337 (MEDIUM - Template Engine) depends on 1M-330
│   ├── 1M-338 (MEDIUM - Validation Framework) depends on 1M-330, 1M-335
│   └── 1M-339 (MEDIUM - Jina.ai Support) depends on 1M-331
│
├── Phase 3: 1M-320 (Polish & Testing) - depends on Phase 2
├── Phase 4: 1M-321 (EDGAR Migration) - depends on Phase 2
└── Phase 5: 1M-322 (Community Launch) - depends on Phases 2-4
```

---

## 2. Most Dependent Issues (Work These FIRST)

### 🔴 CRITICAL FOUNDATIONS (Phase 1)

#### 1. **1M-323: Design Project Configuration Schema (project.yaml)**
- **Status**: OPEN
- **Priority**: HIGH → Should be CRITICAL
- **Effort**: 1-2 days
- **Why Critical**: Blocks 4 Phase 1 tickets (1M-324, 1M-326, 1M-327, 1M-328)
- **Dependencies**: NONE (can start immediately)
- **Unblocks**:
  - 1M-324 (Example Parser) - needs schema to parse examples
  - 1M-326 (Weather Template) - needs schema to create project.yaml
  - 1M-327 (Constraint Enforcer) - needs schema to validate constraints
  - 1M-335 (YAML Parser) - needs schema to implement validation

**Recommendation**: START HERE. This is the FIRST foundation ticket.

---

#### 2. **1M-325: Implement Sonnet 4.5 Integration (PM + Coder Modes)**
- **Status**: IN PROGRESS
- **Priority**: CRITICAL
- **Effort**: 3 days
- **Why Critical**: Core AI engine for code generation
- **Dependencies**: 1M-323 (needs schema to understand project structure)
- **Unblocks**: 1M-328 (Weather Extractor generation)

**Current Status**: Already in progress. Should complete after 1M-323.

---

### 🔴 CRITICAL FOUNDATIONS (Phase 2)

#### 3. **1M-330: Design Generic Abstraction Layer Interfaces**
- **Status**: OPEN
- **Priority**: CRITICAL
- **Effort**: 2 days
- **Why Critical**: **BLOCKS ALL 7 Phase 2 implementation tickets**
- **Dependencies**: 1M-323 (needs schema to align interface design)
- **Unblocks**:
  - 1M-331 (IDataSource) - implements interfaces defined here
  - 1M-332 (IDataExtractor) - implements interfaces defined here
  - 1M-334 (Isolation) - depends on interface architecture
  - 1M-335 (YAML Parser) - needs interfaces for validation
  - 1M-336 (DI Container) - needs interfaces for registration
  - 1M-337 (Template Engine) - generates code using these interfaces
  - 1M-338 (Validation) - validates code against interfaces

**Recommendation**: This is the MOST DEPENDENT ticket in Phase 2. Complete immediately after Phase 1 foundation.

---

#### 4. **1M-333: Build Project Manager Service**
- **Status**: OPEN
- **Priority**: CRITICAL
- **Effort**: 2 days
- **Why Critical**: Blocks 3 Phase 2 tickets (project lifecycle management)
- **Dependencies**: 1M-330 (needs interfaces), 1M-323 (needs schema)
- **Unblocks**:
  - 1M-334 (Isolation) - needs project lifecycle hooks
  - 1M-336 (DI Container) - needs per-project container management
  - All other Phase 2 tickets indirectly (project creation prerequisite)

**Recommendation**: Work in parallel with 1M-330 after schema is done.

---

### 🟡 HIGH PRIORITY DEPENDENCIES

#### 5. **1M-324: Build Example Parser**
- **Status**: OPEN
- **Priority**: HIGH
- **Effort**: 2 days
- **Why Important**: Prerequisite for end-to-end Weather API test
- **Dependencies**: 1M-323 (needs schema)
- **Unblocks**: 1M-328 (Weather Extractor generation)

---

#### 6. **1M-327: Build Constraint Enforcer (AST Validation)**
- **Status**: OPEN
- **Priority**: HIGH
- **Effort**: 2 days
- **Why Important**: Validates generated code quality
- **Dependencies**: 1M-323 (needs constraint definitions from schema)
- **Unblocks**: 1M-328 (Weather Extractor validation)

---

## 3. User Preference → Linear Ticket Mapping

### 👤 User Preferences (Confirmed)

| Preference | Status | Related Ticket | Priority | Gap Analysis |
|------------|--------|----------------|----------|--------------|
| **1. Excel support** | ❌ NOT MAPPED | MISSING | 🔴 HIGH | Need new ticket: "Add Excel Report Generation" |
| **2. PDF support** | ❌ NOT MAPPED | MISSING | 🔴 HIGH | Need new ticket: "Add PDF Report Generation" |
| **3. DOCX support** | ❌ NOT MAPPED | MISSING | 🟡 MEDIUM | Need new ticket: "Add DOCX Report Generation" |
| **4. PPTX support** | ❌ NOT MAPPED | MISSING | 🟡 MEDIUM | Need new ticket: "Add PPTX Report Generation" |
| **5. External directory** | ❌ NOT MAPPED | MISSING | 🔴 HIGH | Need new ticket: "Configure External Artifacts Directory" |
| **6. Jina.ai (JS-heavy)** | ✅ MAPPED | 1M-339 | 🟡 MEDIUM | Partial: Jina.ai exists, but may need Playwright for full JS support |
| **7. Exemplar-based** | ✅ MAPPED | 1M-324, 1M-326 | ✅ COVERED | Example parser + template system |
| **8. Confidence threshold** | ❌ NOT MAPPED | MISSING | 🟡 MEDIUM | Need UX enhancement in code generation flow |
| **9. Sequential workflow** | ✅ MAPPED | 1M-333 | ✅ COVERED | Project Manager handles one-at-a-time |

### 🚨 CRITICAL GAPS

#### Gap 1: Office Format Support (Excel → PDF → DOCX → PPTX)
**User Priority**: Excel FIRST, then PDF, then DOCX, then PPTX

**Current State**:
- ❌ No Excel report generation ticket
- ❌ No PDF report generation ticket
- ❌ No DOCX report generation ticket
- ❌ No PPTX report generation ticket

**EDGAR Analyzer Current Capability**:
- ✅ CSV reports: `create_csv_reports.py`
- ✅ Excel spreadsheet: `create_report_spreadsheet.py` (EDGAR-specific)
- ❌ PDF: None
- ❌ DOCX: None
- ❌ PPTX: None

**Recommendation**: Create new ticket under Phase 2 (1M-319):
- **Ticket**: "Implement IReportGenerator with Multi-Format Support (Excel/PDF/DOCX/PPTX)"
- **Parent**: 1M-319 (Phase 2)
- **Depends On**: 1M-330 (interfaces), 1M-332 (data extraction)
- **Priority**: HIGH (user preference #1-4)
- **Effort**: 3-4 days
- **Scope**:
  - Implement IReportGenerator interface (defined in 1M-330)
  - ExcelReportGenerator (openpyxl or xlsxwriter)
  - PDFReportGenerator (reportlab or weasyprint)
  - DOCXReportGenerator (python-docx)
  - PPTXReportGenerator (python-pptx)
  - Template-based report generation
  - EDGAR report migration (use new interface)

---

#### Gap 2: External Artifacts Directory
**User Preference**: Store generated artifacts OUTSIDE repository

**Current State**:
- ❌ No configuration for external directory
- ❌ Project structure uses `output/` in repo

**Current EDGAR Structure**:
```
edgar/
├── output/               # In-repo (current)
├── data/
│   ├── cache/
│   └── checkpoints/
```

**Recommendation**: Create new ticket under Phase 2 (1M-319):
- **Ticket**: "Configure External Artifacts Directory with Environment Variables"
- **Parent**: 1M-319 (Phase 2)
- **Depends On**: 1M-333 (Project Manager - needs path management)
- **Priority**: HIGH (user preference #2)
- **Effort**: 1 day
- **Scope**:
  - Add ARTIFACTS_DIR environment variable
  - Update Project Manager to use external directory
  - Default: `~/.edgar_platform/artifacts/` or configurable
  - Symlink support for easy access
  - Documentation for setup

---

#### Gap 3: Advanced Web Scraping (JS-Heavy Sites)
**User Preference**: Jina.ai provided (with API key), needs JS-heavy support

**Current State**:
- ✅ 1M-339: Jina.ai Support (OPEN, MEDIUM priority)
- ❌ No Playwright/Puppeteer for full JavaScript rendering

**Recommendation**: Enhance 1M-339 or create companion ticket:
- **Option A**: Enhance 1M-339 scope
  - Add Playwright integration for JS-heavy sites
  - Fallback chain: Jina.ai → Playwright → BeautifulSoup
  - Priority: HIGH (user preference #6)

- **Option B**: Create separate ticket
  - **Ticket**: "Add Playwright Support for JS-Heavy Web Scraping"
  - **Parent**: 1M-319 (Phase 2)
  - **Depends On**: 1M-331 (IDataSource)
  - **Priority**: MEDIUM
  - **Effort**: 2 days

**Recommendation**: Enhance 1M-339 scope (cleaner architecture).

---

#### Gap 4: Confidence Threshold Prompting
**User Preference**: Prompt user for confidence threshold during workflow

**Current State**:
- ❌ No UX for confidence threshold selection
- ❌ No prompting in code generation flow

**Recommendation**: Create new ticket under Phase 3 (1M-320):
- **Ticket**: "Add Interactive Confidence Threshold Prompting"
- **Parent**: 1M-320 (Phase 3 - Polish & Testing)
- **Depends On**: 1M-338 (Validation Framework - provides quality scoring)
- **Priority**: MEDIUM (user preference #8)
- **Effort**: 1 day
- **Scope**:
  - CLI prompt for confidence threshold (0.0-1.0)
  - Quality scoring integration
  - Validation report filtering by confidence
  - Documentation for threshold selection

---

## 4. Phase 2 Critical Path (Sequence)

### Foundation Layer (Week 1)
```
PARALLEL START (after Phase 1 complete):
┌─────────────────────────────────────┐
│ 1M-330 (Abstraction Layer)          │ 2 days  🔴 FOUNDATION
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│ 1M-333 (Project Manager)             │ 2 days  🔴 FOUNDATION
└─────────────────────────────────────┘
```

### Implementation Layer (Week 2)
```
PARALLEL (after foundation):
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│ 1M-331 (IDataSource)│  │ 1M-332 (IExtractor) │  │ 1M-335 (YAML Parser)│
│ 2 days              │  │ 2 days              │  │ 1-2 days            │
└─────────────────────┘  └─────────────────────┘  └─────────────────────┘
         ↓                        ↓                        ↓
┌───────────────────────────────────────────────────────────────────────┐
│ 1M-334 (Isolation System) - 2 days                                    │
└───────────────────────────────────────────────────────────────────────┘
         ↓
┌───────────────────────────────────────────────────────────────────────┐
│ 1M-336 (DI Container) - 2 days                                        │
└───────────────────────────────────────────────────────────────────────┘
```

### Enhancement Layer (Week 2-3)
```
PARALLEL (after implementation):
┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
│ 1M-337 (Templates)   │  │ 1M-338 (Validation)  │  │ 1M-339 (Jina.ai)     │
│ 2 days               │  │ 2 days               │  │ 2 days               │
└──────────────────────┘  └──────────────────────┘  └──────────────────────┘
```

### NEW: User Preference Layer (Week 3)
```
PARALLEL (after enhancement):
┌─────────────────────────────────────┐  ┌─────────────────────────────────┐
│ NEW: Multi-Format Reports           │  │ NEW: External Artifacts Dir     │
│ 3-4 days (Excel/PDF/DOCX/PPTX)      │  │ 1 day                          │
└─────────────────────────────────────┘  └─────────────────────────────────┘
```

**Total Phase 2 Timeline**: 3 weeks (15 developer-days)

---

## 5. Recommended Work Order

### 🔴 IMMEDIATE (This Week)

#### Phase 1 Foundation (5 tickets, 8-9 days)
1. **1M-323**: Project YAML Schema (1-2 days) - **START HERE**
2. **1M-324**: Example Parser (2 days) - parallel with #3
3. **1M-327**: Constraint Enforcer (2 days) - parallel with #2
4. **1M-325**: Sonnet 4.5 Integration (3 days) - **IN PROGRESS**, complete after #1
5. **1M-326**: Weather API Template (1 day) - after #1-3
6. **1M-328**: Generate Weather Extractor (1 day) - after #2-5 (END-TO-END TEST)

**Success Criteria**: Weather API extractor generated and validated end-to-end.

---

### 🟡 NEXT WEEK (Week 2)

#### Phase 2 Foundation (2 tickets, 4 days)
7. **1M-330**: Abstraction Layer Interfaces (2 days) - **CRITICAL**
8. **1M-333**: Project Manager Service (2 days) - **CRITICAL**

#### Phase 2 Implementation (3 tickets, 5-6 days)
9. **1M-331**: IDataSource (2 days) - parallel with #10-11
10. **1M-332**: IDataExtractor (2 days) - parallel with #9, #11
11. **1M-335**: YAML Parser (1-2 days) - parallel with #9-10

---

### 🟢 WEEK 3-4 (Phase 2 Completion)

#### Phase 2 Core Services (2 tickets, 4 days)
12. **1M-334**: Isolation System (2 days)
13. **1M-336**: DI Container (2 days)

#### Phase 2 Enhancement (3 tickets, 6 days)
14. **1M-337**: Template Engine (2 days) - parallel with #15-16
15. **1M-338**: Validation Framework (2 days) - parallel with #14, #16
16. **1M-339**: Jina.ai Support (2 days) - parallel with #14-15

---

### 🆕 NEW TICKETS (Week 3-4)

#### User Preference Gaps (4 tickets, 5-6 days)
17. **NEW**: Multi-Format Report Generation (Excel/PDF/DOCX/PPTX) - 3-4 days - **HIGH PRIORITY**
18. **NEW**: External Artifacts Directory - 1 day - **HIGH PRIORITY**
19. **NEW**: Enhanced Jina.ai with Playwright (if separate ticket) - 2 days - **MEDIUM**
20. **NEW**: Confidence Threshold Prompting - 1 day - **MEDIUM** (Phase 3)

---

## 6. Gap Analysis vs User Preferences

### ✅ Well-Covered Preferences

| Preference | Coverage | Tickets | Status |
|------------|----------|---------|--------|
| Exemplar-based approach | ✅ EXCELLENT | 1M-324, 1M-326, 1M-323 | Phase 1 foundation |
| Sequential workflow | ✅ EXCELLENT | 1M-333 | Phase 2 critical |
| Project isolation | ✅ EXCELLENT | 1M-334 | Phase 2 implementation |

### 🚨 Critical Gaps

| Preference | Gap | Recommended Ticket | Priority | Effort |
|------------|-----|-------------------|----------|--------|
| Excel support | ❌ MISSING | "Multi-Format Reports" | 🔴 HIGH | 3-4 days |
| PDF support | ❌ MISSING | (same as above) | 🔴 HIGH | (included) |
| DOCX support | ❌ MISSING | (same as above) | 🟡 MEDIUM | (included) |
| PPTX support | ❌ MISSING | (same as above) | 🟡 MEDIUM | (included) |
| External directory | ❌ MISSING | "External Artifacts Dir" | 🔴 HIGH | 1 day |
| Confidence UX | ❌ MISSING | "Confidence Prompting" | 🟡 MEDIUM | 1 day |
| JS-heavy scraping | 🟡 PARTIAL | Enhance 1M-339 | 🟡 MEDIUM | +2 days |

### Priority Matrix

```
                HIGH IMPACT
                    ↑
    Quadrant 2      │      Quadrant 1
    (Do Second)     │      (DO FIRST)
                    │
    - Confidence    │      - Excel/PDF Reports
    - DOCX/PPTX     │      - External Directory
                    │      - Phase 1 Foundation
                    │      - Phase 2 Foundation
    ────────────────┼────────────────────────→
                    │              HIGH PRIORITY
    Quadrant 3      │      Quadrant 4
    (Do Later)      │      (Quick Wins)
                    │
    - Phase 4-5     │      - Jina.ai enhancement
    - Community     │      - JS-heavy scraping
                    ↓
                LOW IMPACT
```

---

## 7. Dependency Graph Visualization

### Legend
- 🔴 CRITICAL (blocks multiple tickets)
- 🟡 HIGH (blocks some tickets)
- 🟢 MEDIUM (enhancement)
- ✅ DONE
- 🚧 IN PROGRESS
- ⏸️ BLOCKED
- ❌ NOT STARTED

### Full Dependency Tree

```
PHASE 1: Weather API POC
=======================
1M-323 (YAML Schema) 🔴 FOUNDATION [NOT STARTED]
  ├── 1M-324 (Example Parser) 🟡 [BLOCKED by 1M-323]
  ├── 1M-326 (Weather Template) 🟡 [BLOCKED by 1M-323]
  ├── 1M-327 (Constraint Enforcer) 🟡 [BLOCKED by 1M-323]
  └── 1M-325 (Sonnet 4.5) 🔴 CRITICAL [IN PROGRESS, depends on 1M-323]
        └── 1M-328 (Weather Extractor) 🟡 [BLOCKED by 1M-323-327]
              └── 1M-329 (GO Decision) ✅ DONE

PHASE 2: Core Platform Architecture
====================================
1M-330 (Abstraction Layer) 🔴 FOUNDATION [BLOCKED by Phase 1]
  ├── 1M-331 (IDataSource) 🟡 [BLOCKED by 1M-330]
  ├── 1M-332 (IDataExtractor) 🟡 [BLOCKED by 1M-330]
  ├── 1M-334 (Isolation) 🟡 [BLOCKED by 1M-330, 1M-333]
  ├── 1M-335 (YAML Parser) 🟡 [BLOCKED by 1M-330, 1M-323]
  ├── 1M-336 (DI Container) 🟡 [BLOCKED by 1M-330, 1M-333]
  ├── 1M-337 (Templates) 🟢 [BLOCKED by 1M-330]
  ├── 1M-338 (Validation) 🟢 [BLOCKED by 1M-330, 1M-335]
  └── 1M-339 (Jina.ai) 🟢 [BLOCKED by 1M-331]

1M-333 (Project Manager) 🔴 FOUNDATION [BLOCKED by Phase 1, 1M-330]
  ├── 1M-334 (Isolation) 🟡 [BLOCKED by 1M-333, 1M-330]
  └── 1M-336 (DI Container) 🟡 [BLOCKED by 1M-333, 1M-330]

NEW TICKETS (User Preferences)
===============================
NEW-1 (Multi-Format Reports) 🔴 HIGH PRIORITY [depends on 1M-330, 1M-332]
NEW-2 (External Artifacts) 🔴 HIGH PRIORITY [depends on 1M-333]
NEW-3 (Confidence UX) 🟡 MEDIUM [depends on 1M-338]

PHASE 3-5 (Blocked by Phase 2)
===============================
1M-320 (Polish & Testing) [BLOCKED by Phase 2]
1M-321 (EDGAR Migration) [BLOCKED by Phase 2]
1M-322 (Community Launch) [BLOCKED by Phases 2-4]
```

---

## 8. Timeline Estimates

### Phase 1: Weather API POC (2 weeks)
- ✅ 1M-329: DONE (GO Decision)
- 🚧 1M-325: IN PROGRESS (Sonnet 4.5) - 3 days remaining
- ❌ 1M-323: NOT STARTED (YAML Schema) - 1-2 days
- ❌ 1M-324: NOT STARTED (Example Parser) - 2 days
- ❌ 1M-327: NOT STARTED (Constraint Enforcer) - 2 days
- ❌ 1M-326: NOT STARTED (Weather Template) - 1 day
- ❌ 1M-328: NOT STARTED (Weather Extractor) - 1 day

**Total Remaining**: 9-10 developer-days

---

### Phase 2: Core Platform (3 weeks)
- **Week 1 (Foundation)**: 1M-330, 1M-333 (4 days)
- **Week 2 (Implementation)**: 1M-331, 1M-332, 1M-335, 1M-334, 1M-336 (9-10 days)
- **Week 3 (Enhancement)**: 1M-337, 1M-338, 1M-339 (6 days)

**Total**: 19-20 developer-days

---

### NEW Tickets: User Preferences (1 week)
- NEW-1: Multi-Format Reports (3-4 days)
- NEW-2: External Artifacts (1 day)
- NEW-3: Confidence UX (1 day)

**Total**: 5-6 developer-days

---

### **GRAND TOTAL (Phases 1-2 + User Prefs)**: 33-36 developer-days (~7 weeks)

---

## 9. Recommendations for PM

### Immediate Actions (Today)

1. **Create 3 new tickets** to address user preference gaps:
   - "Implement IReportGenerator with Multi-Format Support (Excel/PDF/DOCX/PPTX)"
   - "Configure External Artifacts Directory with Environment Variables"
   - "Add Interactive Confidence Threshold Prompting"

2. **Reprioritize 1M-323** from HIGH → CRITICAL (it's the Phase 1 foundation blocker)

3. **Start work on 1M-323** immediately (can work parallel with 1M-325 completion)

---

### Phase 1 Execution Plan (This Week)

**Sequence**:
1. Complete 1M-325 (Sonnet 4.5) - already in progress
2. Start 1M-323 (YAML Schema) - parallel with #1 if possible
3. Parallel: 1M-324 + 1M-327 (Example Parser + Constraint Enforcer)
4. Create 1M-326 (Weather Template)
5. Execute 1M-328 (Weather Extractor end-to-end test)

**Success Metric**: Weather API extractor generated, validated, and working end-to-end.

---

### Phase 2 Execution Plan (Weeks 2-4)

**Week 1 Foundation**:
- 1M-330 (Abstraction Layer) - 2 days
- 1M-333 (Project Manager) - 2 days

**Week 2 Implementation**:
- Parallel: 1M-331, 1M-332, 1M-335
- Sequential: 1M-334 → 1M-336

**Week 3 Enhancement**:
- Parallel: 1M-337, 1M-338, 1M-339
- NEW-1, NEW-2, NEW-3 (user preference tickets)

**Success Metric**: Full platform functional with all user preferences addressed.

---

### Risk Mitigation

**Risk 1**: Phase 1 takes longer than expected
- **Mitigation**: Focus on MVP scope only, defer advanced features to Phase 2
- **Indicator**: If 1M-323 takes >2 days, reassess scope

**Risk 2**: User preference gaps delay Phase 2 completion
- **Mitigation**: Prioritize Excel + External Directory (highest user priority)
- **Defer**: DOCX/PPTX to Phase 3 if needed

**Risk 3**: 1M-330 (Abstraction Layer) becomes bottleneck
- **Mitigation**: Break into smaller incremental tickets if scope creeps
- **Indicator**: If effort estimate exceeds 3 days, split into multiple tickets

---

## 10. Memory Updates

**Project Architecture Learnings**:
- Phase 1 has 1 critical foundation blocker (1M-323 YAML Schema)
- Phase 2 has 2 critical foundation blockers (1M-330 Abstraction Layer, 1M-333 Project Manager)
- 7 out of 10 Phase 2 tickets depend on 1M-330 (highest dependency count)
- User preferences reveal 4 critical gaps (Excel/PDF/DOCX/PPTX, External Dir, Confidence UX)

**Implementation Guidelines**:
- Always complete foundation tickets before dependent implementation tickets
- Parallel execution possible for 1M-331, 1M-332, 1M-335 after foundation complete
- User preference tickets should be created immediately and added to Phase 2 scope

**Current Technical Context**:
- EDGAR already has CSV + Excel report generation (`create_report_spreadsheet.py`)
- Project structure uses in-repo `output/` directory (needs external directory support)
- Jina.ai API key provided, but JS-heavy support may need Playwright enhancement
- 16/18 project command tests passing (project isolation nearly ready)

---

## Appendix A: Ticket Details Reference

### Phase 1 Tickets (1M-318)
- 1M-323: YAML Schema (1-2 days, HIGH)
- 1M-324: Example Parser (2 days, HIGH)
- 1M-325: Sonnet 4.5 Integration (3 days, CRITICAL) 🚧 IN PROGRESS
- 1M-326: Weather Template (1 day, MEDIUM)
- 1M-327: Constraint Enforcer (2 days, HIGH)
- 1M-328: Weather Extractor End-to-End (1 day, CRITICAL)
- 1M-329: GO Decision ✅ DONE

### Phase 2 Tickets (1M-319)
- 1M-330: Abstraction Layer Interfaces (2 days, CRITICAL)
- 1M-331: IDataSource Implementation (2 days, HIGH)
- 1M-332: IDataExtractor Implementation (2 days, HIGH)
- 1M-333: Project Manager Service (2 days, CRITICAL)
- 1M-334: Project Isolation System (2 days, HIGH)
- 1M-335: YAML Configuration Parser (1-2 days, HIGH)
- 1M-336: Per-Project DI Container (2 days, HIGH)
- 1M-337: Template Engine (2 days, MEDIUM)
- 1M-338: Validation Framework (2 days, MEDIUM)
- 1M-339: Jina.ai Support (2 days, MEDIUM)

### Recommended New Tickets
- NEW-1: Multi-Format Report Generation (3-4 days, HIGH)
- NEW-2: External Artifacts Directory (1 day, HIGH)
- NEW-3: Confidence Threshold Prompting (1 day, MEDIUM)

---

**End of Research Document**
