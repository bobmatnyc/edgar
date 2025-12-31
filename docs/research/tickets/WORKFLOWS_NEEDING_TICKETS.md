# Workflows Needing Linear Tickets

**Generated**: 2025-12-05
**Epic**: edgar-e4cb3518b13e (EDGAR → General-Purpose Platform)
**Total Workflows Missing Tickets**: 6

---

## 🔴 High Priority (P0-P1)

### 1. PPTX File Transformation (P1)

**Status**: Implementation unclear
**Evidence**:
- Listed in user preferences: "Excel → PDF → DOCX → PPTX priority"
- Reference: `docs/decisions/USER_PREFERENCES_WORK_PATHS_2025-11-28.md`
- Office formats research: `docs/research/office-format-implementation-comparison-2025-11-29.md`
- No dedicated ticket found in Linear search

**Recommended Ticket**:
```
Title: Implement PPTX File Transformation (PowerPoint Extract & Transform)
Priority: Medium (P1)
Epic: edgar-e4cb3518b13e
Tags: pptx, file-transform, work-path-4, office-formats

Description:
Implement PowerPoint file transformation capability to complete office format support.

User Story:
As a market researcher, I want to extract data tables from PowerPoint presentations so that I can analyze competitor information without manual transcription.

Acceptance Criteria:
- [ ] PPTXDataSource reads .pptx files
- [ ] Table extraction from slides
- [ ] Text box content extraction
- [ ] Chart data extraction (if supported)
- [ ] Slide metadata (title, number, notes)
- [ ] User guide: docs/guides/PPTX_FILE_TRANSFORM.md
- [ ] Example project in projects/pptx_transform/
- [ ] Test coverage: 70%+ (minimum)

Files to Create:
- src/extract_transform_platform/data_sources/file/pptx_source.py
- docs/guides/PPTX_FILE_TRANSFORM.md
- docs/architecture/PPTX_DATA_SOURCE.md
- tests/unit/data_sources/test_pptx_source.py
- projects/pptx_transform/ (example)

References:
- DOCX implementation: [1M-385]
- PDF implementation: [1M-384]
- Excel implementation: [1M-383]
```

---

### 2. Conversational CLI Interface (P1)

**Status**: Working, not tracked
**Evidence**:
- Extensively documented in `docs/guides/CLI_USAGE.md`
- Quick Start: `docs/guides/QUICK_START.md`
- Working feature, used daily
- No dedicated implementation ticket

**Recommended Ticket**:
```
Title: [Retrospective] Conversational CLI Interface Implementation
Priority: Low (P2 - retrospective documentation)
Epic: edgar-e4cb3518b13e
Tags: conversational-cli, chatbot, terminal-ui, retrospective

Description:
Document the implementation of the conversational CLI interface for future reference and knowledge sharing.

This is a RETROSPECTIVE ticket - the feature is complete and working. This ticket exists to:
1. Formally track the feature in Linear
2. Link related documentation
3. Record implementation decisions
4. Provide reference for similar features

User Story:
As a business user, I want to ask questions in plain English about data extraction so that I can use the platform without learning complex commands.

Features Implemented:
- ✅ Natural language query understanding
- ✅ Context-aware responses
- ✅ Built-in commands: help, quit, info, status, clear
- ✅ Web search integration
- ✅ Fallback to traditional CLI

Documentation:
- Guide: docs/guides/CLI_USAGE.md
- Quick Start: docs/guides/QUICK_START.md
- Related: [1M-358] One-shot query mode
- Related: [1M-359] Session compaction

Acceptance Criteria:
- [x] Feature is working (DONE)
- [ ] Documentation complete and linked
- [ ] Implementation decisions recorded
- [ ] Future improvements noted
```

---

### 3. Web Search Integration (OpenRouter) (P1)

**Status**: Working, enabled by default
**Evidence**:
- Guide: `docs/guides/WEB_SEARCH_CAPABILITIES.md`
- API: `docs/api/OPENROUTER_SERVICE.md`
- Architecture: `docs/architecture/OPENROUTER_ARCHITECTURE.md`
- Enabled by default in CLI
- No tracking ticket

**Recommended Ticket**:
```
Title: [Retrospective] Web Search Integration via OpenRouter
Priority: Low (P2 - retrospective documentation)
Epic: edgar-e4cb3518b13e
Tags: web-search, openrouter, ai-features, retrospective

Description:
Document the web search integration implementation for formal tracking and reference.

This is a RETROSPECTIVE ticket - the feature is complete and working.

User Story:
As a compliance analyst, I want the platform to access current SEC filing requirements so that I can ensure my data extraction follows the latest regulations.

Features Implemented:
- ✅ OpenRouter API integration
- ✅ Web search enabled by default
- ✅ Current market data access
- ✅ Latest SEC requirements retrieval
- ✅ Real-time validation capability
- ✅ API key configuration via .env.local

Documentation:
- Guide: docs/guides/WEB_SEARCH_CAPABILITIES.md
- API Reference: docs/api/OPENROUTER_SERVICE.md
- Architecture: docs/architecture/OPENROUTER_ARCHITECTURE.md

Configuration:
- Requires: OPENROUTER_API_KEY in .env.local
- Enabled by default in conversational mode
- Can disable with: --disable-web-search flag

Acceptance Criteria:
- [x] Feature working (DONE)
- [ ] Documentation complete
- [ ] API key security documented
- [ ] Usage limits and costs documented
```

---

## 🟡 Medium Priority (P2)

### 4. Alpha User Testing (5 Scenarios) (P2)

**Status**: Documented, not executed
**Evidence**:
- Plan: `docs/USER_TESTING_PLAN.md` (815 lines)
- Guide: `docs/guides/USER_TESTING_GUIDE.md` (975 lines)
- Template: `docs/USER_FEEDBACK_TEMPLATE.md`
- Checklist: `ALPHA_RELEASE_CHECKLIST.md` (119 tasks)
- Not tracked in Linear

**Recommended Epic + Subtasks**:
```
Epic:
Title: Alpha User Testing (Extract & Transform Platform)
Priority: High (P0 - critical for release)
Tags: user-testing, alpha-release, quality-assurance

Description:
Execute comprehensive alpha user testing for Extract & Transform Platform with 5 core scenarios.

Success Criteria:
- Minimum: 3+ users complete 3+ scenarios, 80%+ satisfaction
- Optimal: 5+ users complete all 5 scenarios, 90%+ satisfaction
- Zero P0 blockers identified

Timeline: 3 weeks
- Week -1: Preparation (sample data, tester recruitment)
- Week 0: Testing (5 days active testing)
- Week +1: Analysis and planning

Documentation:
- Test Plan: docs/USER_TESTING_PLAN.md
- Testing Guide: docs/guides/USER_TESTING_GUIDE.md
- Feedback Template: docs/USER_FEEDBACK_TEMPLATE.md
- Checklist: ALPHA_RELEASE_CHECKLIST.md

Subtasks:
- [ ] Prepare sample data files
- [ ] Recruit 5-7 alpha testers
- [ ] Set up support channels
- [ ] Execute Scenario 1: Excel Transformation
- [ ] Execute Scenario 2: PDF Extraction
- [ ] Execute Scenario 3: Weather API
- [ ] Execute Scenario 4: Report Generation
- [ ] Execute Scenario 5: Custom Workflow
- [ ] Collect and analyze feedback
- [ ] Create alpha testing summary report
```

**5 Scenario Subtasks**:

```
Subtask 1:
Title: User Testing Scenario 1 - Excel File Transformation
Parent: Alpha User Testing Epic
Priority: High
Tags: excel, user-testing, scenario-1, beginner

Description:
Test Excel transformation workflow with employee roster example.

Duration: 15-20 minutes
Complexity: Beginner
Sample Data: test_data/employee_roster_sample.xlsx

Success Criteria:
- ✅ Code generation completes without errors
- ✅ Extraction runs successfully
- ✅ Output matches expected transformation patterns
- ✅ At least 2 transformation types detected

Metrics:
- Completion rate
- Time to complete
- Errors encountered
- User satisfaction (1-5)

Documentation: docs/USER_TESTING_PLAN.md#scenario-1
```

```
Subtask 2:
Title: User Testing Scenario 2 - PDF Invoice Extraction
Parent: Alpha User Testing Epic
Priority: High
Tags: pdf, user-testing, scenario-2, intermediate

Description:
Test PDF table extraction with invoice line items example.

Duration: 15-20 minutes
Complexity: Intermediate
Sample Data: test_data/invoice_sample.pdf

Success Criteria:
- ✅ Table extraction detects correct structure
- ✅ Currency values parsed correctly
- ✅ Code generation completes successfully
- ✅ Extraction produces valid JSON

Common Issues to Track:
- Table strategy selection
- Currency parsing
- Page number confusion

Documentation: docs/USER_TESTING_PLAN.md#scenario-2
```

```
Subtask 3:
Title: User Testing Scenario 3 - Weather API Integration
Parent: Alpha User Testing Epic
Priority: High
Tags: weather-api, user-testing, scenario-3, beginner, template

Description:
Test project template workflow with Weather API.

Duration: 10-15 minutes
Complexity: Beginner
Template: weather

Success Criteria:
- ✅ API call succeeds
- ✅ Data extracted and validated
- ✅ Output file created in correct format
- ✅ No authentication errors

Prerequisites:
- OpenWeatherMap API key (free tier)

Documentation: docs/USER_TESTING_PLAN.md#scenario-3
```

```
Subtask 4:
Title: User Testing Scenario 4 - Multi-Format Report Generation
Parent: Alpha User Testing Epic
Priority: High
Tags: reports, user-testing, scenario-4, beginner

Description:
Test report generation in Excel, PDF, DOCX, PPTX formats.

Duration: 10 minutes
Complexity: Beginner
Prerequisites: Completed Scenario 1, 2, or 3

Success Criteria:
- ✅ All 4 formats generate successfully
- ✅ Data is accurate and complete
- ✅ Files open correctly in respective applications
- ✅ Formatting is professional and readable

Formats to Test:
- Excel (.xlsx)
- PDF (.pdf)
- DOCX (.docx)
- PPTX (.pptx)

Documentation: docs/USER_TESTING_PLAN.md#scenario-4
```

```
Subtask 5:
Title: User Testing Scenario 5 - End-to-End Custom Workflow
Parent: Alpha User Testing Epic
Priority: High
Tags: custom-workflow, user-testing, scenario-5, advanced

Description:
Test complete workflow with user's own data source.

Duration: 30-45 minutes
Complexity: Advanced
Data Source: User provided

Success Criteria:
- ✅ User completes workflow independently
- ✅ Extraction produces expected results
- ✅ User can explain what the platform did
- ✅ User identifies value for their use case

This scenario validates:
- Real-world applicability
- Documentation clarity
- Error handling
- Overall user experience

Documentation: docs/USER_TESTING_PLAN.md#scenario-5
```

---

### 5. DOCX User Guide (P1 - Documentation)

**Status**: Implementation complete, guide missing
**Evidence**:
- Ticket: [1M-385] DOCX File Transform Implementation (CLOSED)
- Research: `docs/research/docx-parsing-requirements-phase2-2025-11-29.md`
- No guide: `docs/guides/DOCX_FILE_TRANSFORM.md` not found

**Recommended Ticket**:
```
Title: Create DOCX File Transform User Guide
Priority: Medium (P1 - documentation)
Epic: edgar-e4cb3518b13e
Tags: documentation, docx, user-guide

Description:
Create comprehensive user guide for DOCX file transformation workflow.

Implementation Complete: [1M-385] ✅
Missing: User-facing documentation

User Story:
As a legal administrator, I want clear instructions for extracting data from Word documents so that I can set up extraction projects without trial and error.

Deliverables:
- [ ] docs/guides/DOCX_FILE_TRANSFORM.md (900+ lines, follow Excel/PDF structure)
- [ ] Example project: projects/docx_transform/
- [ ] Section in CLAUDE.md
- [ ] Troubleshooting section
- [ ] Tutorial with screenshots/examples

Structure (follow Excel/PDF guides):
1. Overview
2. How It Works
3. Quick Start (5 minutes)
4. Step-by-Step Tutorial
5. Configuration Reference
6. Supported Transformations
7. Best Practices
8. Troubleshooting
9. Examples

Reference Guides:
- Excel: docs/guides/EXCEL_FILE_TRANSFORM.md (900 lines)
- PDF: docs/guides/PDF_FILE_TRANSFORM.md (1,866 lines)

Acceptance Criteria:
- [ ] Guide matches quality of Excel/PDF guides
- [ ] At least 2-3 complete examples
- [ ] Troubleshooting covers common issues
- [ ] Linked from main documentation index
```

---

### 6. CI/CD Automation & Scripting Guide (P2)

**Status**: Feature works (one-shot mode), guide missing
**Evidence**:
- Ticket: [1M-358] One-shot query mode (CLOSED)
- Feature: `--query` flag works
- No guide for automation use cases

**Recommended Ticket**:
```
Title: Create CI/CD Automation & Scripting Guide
Priority: Low (P2 - documentation)
Epic: edgar-e4cb3518b13e
Tags: documentation, automation, ci-cd, scripting

Description:
Create guide for using platform in automated workflows, CI/CD pipelines, and batch processing.

Features to Document:
- One-shot query mode ([1M-358])
- External artifacts directory ([1M-361])
- Exit codes and error handling
- Batch processing patterns
- Pipeline integration examples

User Story:
As a CI/CD engineer, I want to integrate the platform into automated pipelines so that I can run data extraction as part of our build process.

Deliverables:
- [ ] docs/guides/AUTOMATION_SCRIPTING.md
- [ ] CI/CD integration examples (GitHub Actions, GitLab CI)
- [ ] Batch processing patterns
- [ ] Error handling best practices
- [ ] Exit code reference

Content Sections:
1. One-Shot Query Mode
2. Batch Processing Multiple Files
3. CI/CD Pipeline Integration
4. Exit Codes and Error Handling
5. Performance Optimization
6. Monitoring and Logging
7. Examples (GitHub Actions, GitLab CI, Jenkins)

Reference Implementation:
- [1M-358] One-shot query mode
- CLI Usage: docs/guides/CLI_USAGE.md

Acceptance Criteria:
- [ ] One-shot mode fully documented
- [ ] At least 2 CI/CD platform examples
- [ ] Batch processing patterns explained
- [ ] Exit codes documented
- [ ] Error handling strategies provided
```

---

## Summary

**Total Tickets to Create**: 6 main + 1 epic + 5 subtasks = **12 total**

### Breakdown by Priority

| Priority | Tickets | Type |
|----------|---------|------|
| **P0 (Critical)** | 1 | Epic (Alpha Testing) |
| **P1 (High)** | 3 | Implementation (PPTX) + Documentation (DOCX) + Retrospective (CLI) |
| **P2 (Medium)** | 8 | Documentation (2) + Retrospective (1) + User Testing Scenarios (5) |

### Breakdown by Type

| Type | Count | Examples |
|------|-------|----------|
| **Implementation** | 1 | PPTX File Transform |
| **Documentation** | 2 | DOCX Guide, CI/CD Guide |
| **Retrospective** | 2 | Conversational CLI, Web Search |
| **User Testing** | 6 | Epic + 5 scenarios |
| **Process** | 1 | Alpha Testing preparation |

---

## Recommended Creation Order

### Week 1: Critical for Alpha Testing
1. **Alpha User Testing Epic** (+ 5 subtask scenarios)
2. **PPTX File Transformation** (if implemented) or defer to Phase 3
3. **DOCX User Guide** (implementation complete, guide missing)

### Week 2: Retrospective Documentation
4. **Conversational CLI Retrospective** (low priority)
5. **Web Search Retrospective** (low priority)

### Week 3: Nice-to-Have Documentation
6. **CI/CD Automation & Scripting Guide** (low priority)

---

## Template for Creating Tickets in Linear

```markdown
Project: edgar-e4cb3518b13e
Assignee: bob@matsuoka.com (or appropriate team member)

Title: [From above]
Priority: [P0/P1/P2]
Tags: [Copy from recommendations]

Description:
[Copy Description section from above]

User Story:
[Copy User Story section]

Acceptance Criteria:
[Copy checkboxes]

Related Tickets:
[List related Linear tickets]

Documentation:
[List relevant docs]
```

---

**Report Generated**: 2025-12-05
**Next Action**: Review with PM and create tickets in Linear
**Contact**: See PROJECT_OVERVIEW.md for stakeholder information
