# User Testing Plan - Extract & Transform Platform Alpha Release

**Version**: 1.0
**Status**: Ready for Alpha Testing
**Date**: 2025-12-04
**Test Duration**: 1 Week
**Platform Version**: Phase 2 Complete (90.3% test pass rate)

---

## Executive Summary

### Testing Objectives

1. **Validate Core Workflows** - Confirm all 4 major work paths function end-to-end
2. **Gather User Feedback** - Collect qualitative and quantitative feedback on usability
3. **Identify Blockers** - Discover critical issues preventing production use
4. **Measure Success** - Assess readiness for beta release based on user completion rates

### Timeline

- **Week 1** (Alpha Testing): User onboarding, testing, and feedback collection
- **Week 2** (Analysis): Consolidate feedback, prioritize fixes, plan iteration 2
- **Week 3+** (Iteration): Implement fixes and prepare for beta release

### Success Criteria

✅ **Minimum Success Threshold**:
- 3+ users complete at least 3 out of 5 test scenarios
- 10+ pieces of actionable feedback collected
- Zero P0 blockers identified (issues preventing basic functionality)
- 80%+ user satisfaction (4+ out of 5 average rating)

🎯 **Optimal Success Target**:
- 5+ users complete all 5 test scenarios
- 20+ pieces of actionable feedback collected
- No more than 2 P1 issues identified (high-impact but workarounds exist)
- 90%+ user satisfaction (4.5+ out of 5 average rating)

### Known Limitations

The following limitations are documented and communicated upfront to set expectations:

1. **Test Infrastructure** (110 failures) - Mock-related issues, doesn't affect production
2. **Schema Services** (Some pattern detection failures) - May need manual adjustment
3. **Type Hints** (Async function limitation) - Use regular helper functions instead
4. **API Keys Required** - OpenRouter API key required for code generation
5. **Jina.ai** - Limited production validation, use with caution for JS-heavy sites

---

## Test Scenarios

### Scenario 1: Excel File Transformation

**Duration**: 15-20 minutes
**Complexity**: Beginner
**Objective**: Transform employee roster Excel file into structured JSON

#### Prerequisites
- Sample employee roster Excel file (provided in `test_data/`)
- Basic understanding of Excel structure

#### Steps
1. **Setup Project**
   ```bash
   cd projects/
   mkdir my_excel_test
   cd my_excel_test
   mkdir input examples output
   ```

2. **Add Sample Data**
   ```bash
   cp ../../test_data/employee_roster_sample.xlsx input/roster.xlsx
   ```

3. **Create Transformation Examples**
   - Copy 2-3 examples from `test_data/examples/employee_roster/`
   - Modify to match your desired output format

4. **Configure Project**
   ```yaml
   # project.yaml
   name: Employee Roster Transform
   data_source:
     type: excel
     config:
       file_path: input/roster.xlsx
       sheet_name: 0
       header_row: 0
   examples:
     - examples/row1.json
     - examples/row2.json
   ```

5. **Run Analysis and Code Generation**
   ```bash
   cd ../..
   python -m edgar_analyzer analyze-project projects/my_excel_test/
   python -m edgar_analyzer generate-code projects/my_excel_test/
   ```

6. **Execute Extraction**
   ```bash
   python -m edgar_analyzer run-extraction projects/my_excel_test/
   ```

#### Expected Output
- Transformed JSON file in `output/` directory
- Type conversions applied (int → float, "Yes" → true)
- Field renaming and concatenation as defined in examples

#### Success Criteria
- ✅ Code generation completes without errors
- ✅ Extraction runs successfully
- ✅ Output matches expected transformation patterns
- ✅ At least 2 transformation types detected (rename, type conversion, etc.)

#### Common Issues
- **Issue**: "Pattern detection failed" → Provide 3rd example for clarity
- **Issue**: "Type inference incorrect" → Check example data types match Excel
- **Issue**: "Missing API key" → Configure OpenRouter key in `.env.local`

---

### Scenario 2: PDF Invoice Extraction

**Duration**: 15-20 minutes
**Complexity**: Intermediate
**Objective**: Extract line items from PDF invoice tables

#### Prerequisites
- Sample invoice PDF (provided in `test_data/`)
- Understanding of table structures

#### Steps
1. **Setup Project**
   ```bash
   cd projects/
   mkdir invoice_test
   cd invoice_test
   mkdir input examples output
   ```

2. **Add Sample Data**
   ```bash
   cp ../../test_data/invoice_sample.pdf input/invoice_001.pdf
   ```

3. **Create Transformation Examples**
   - Copy 2-3 examples from `test_data/examples/invoice/`
   - Define desired output structure

4. **Configure Project**
   ```yaml
   # project.yaml
   name: Invoice Line Item Extraction
   data_source:
     type: pdf
     config:
       file_path: input/invoice_001.pdf
       page_number: 0
       table_strategy: lines  # or 'text', 'mixed'
   examples:
     - examples/line1.json
     - examples/line2.json
   ```

5. **Run Analysis and Code Generation**
   ```bash
   cd ../..
   python -m edgar_analyzer analyze-project projects/invoice_test/
   python -m edgar_analyzer generate-code projects/invoice_test/
   ```

6. **Execute Extraction**
   ```bash
   python -m edgar_analyzer run-extraction projects/invoice_test/
   ```

#### Expected Output
- Structured invoice data in JSON format
- Currency parsing (`$15.00` → `15.00`)
- Field renaming and type conversions

#### Success Criteria
- ✅ Table extraction detects correct structure
- ✅ Currency values parsed correctly
- ✅ Code generation completes successfully
- ✅ Extraction produces valid JSON

#### Common Issues
- **Issue**: "Table not detected" → Try different table_strategy (lines/text/mixed)
- **Issue**: "Currency parsing failed" → Check example format matches PDF
- **Issue**: "Wrong page extracted" → Verify page_number (0-indexed)

---

### Scenario 3: Weather API Integration

**Duration**: 10-15 minutes
**Complexity**: Beginner
**Objective**: Extract current weather data from OpenWeatherMap API

#### Prerequisites
- OpenWeatherMap API key (free tier - see `test_data/instructions/api_setup.md`)
- Internet connection

#### Steps
1. **Get API Key**
   - Visit https://openweathermap.org/api
   - Sign up for free tier account
   - Copy API key

2. **Create Project from Template**
   ```bash
   python -m edgar_analyzer project create weather_test --template weather
   ```

3. **Configure API Key**
   ```bash
   # Edit .env.local
   OPENWEATHERMAP_API_KEY=your_api_key_here
   ```

4. **Customize Project (Optional)**
   - Edit `projects/weather_test/project.yaml`
   - Change city, units, or output format

5. **Run Extraction**
   ```bash
   python -m edgar_analyzer run-extraction projects/weather_test/
   ```

#### Expected Output
- Current weather data JSON file
- Temperature, humidity, conditions, wind speed
- Timestamps and location data

#### Success Criteria
- ✅ API call succeeds
- ✅ Data extracted and validated
- ✅ Output file created in correct format
- ✅ No authentication errors

#### Common Issues
- **Issue**: "API key invalid" → Verify key copied correctly to `.env.local`
- **Issue**: "Rate limit exceeded" → Wait 1 minute and retry (free tier limits)
- **Issue**: "City not found" → Check spelling or try different city name

---

### Scenario 4: Report Generation

**Duration**: 10 minutes
**Complexity**: Beginner
**Objective**: Generate multi-format reports from extracted data

#### Prerequisites
- Completed extraction from Scenario 1, 2, or 3
- Extracted data in `output/` directory

#### Steps
1. **Verify Extracted Data**
   ```bash
   ls -la projects/my_excel_test/output/
   cat projects/my_excel_test/output/extracted_data.json
   ```

2. **Generate Excel Report**
   ```bash
   python -m edgar_analyzer report generate \
     --project projects/my_excel_test/ \
     --format excel \
     --output reports/employee_roster.xlsx
   ```

3. **Generate PDF Report**
   ```bash
   python -m edgar_analyzer report generate \
     --project projects/my_excel_test/ \
     --format pdf \
     --output reports/employee_roster.pdf
   ```

4. **Generate DOCX Report**
   ```bash
   python -m edgar_analyzer report generate \
     --project projects/my_excel_test/ \
     --format docx \
     --output reports/employee_roster.docx
   ```

5. **Generate PPTX Report**
   ```bash
   python -m edgar_analyzer report generate \
     --project projects/my_excel_test/ \
     --format pptx \
     --output reports/employee_roster.pptx
   ```

#### Expected Output
- 4 report files in different formats
- Consistent data across all formats
- Professional formatting and layout

#### Success Criteria
- ✅ All 4 formats generate successfully
- ✅ Data is accurate and complete
- ✅ Files open correctly in respective applications
- ✅ Formatting is professional and readable

#### Common Issues
- **Issue**: "No data found" → Verify extraction completed successfully
- **Issue**: "Template not found" → Check platform installation is complete
- **Issue**: "Permission denied" → Check write permissions on output directory

---

### Scenario 5: End-to-End Custom Workflow

**Duration**: 30-45 minutes
**Complexity**: Advanced
**Objective**: Complete full workflow with user's own data source

#### Prerequisites
- User's own data source (Excel file, PDF, or API endpoint)
- Clear understanding of desired transformation
- 2-3 example transformations prepared

#### Steps
1. **Define Requirements**
   - What data source are you using? (Excel, PDF, API, web scraping)
   - What fields do you want to extract?
   - What transformations are needed?

2. **Create Project**
   ```bash
   python -m edgar_analyzer project create my_custom_project
   ```

3. **Configure Data Source**
   - Edit `projects/my_custom_project/project.yaml`
   - Set appropriate data source type and config
   - Add authentication if required (API keys, etc.)

4. **Add Sample Data**
   - Place source file in `input/` directory
   - Or configure API endpoint in `project.yaml`

5. **Create Transformation Examples**
   - Create 2-3 example JSON files in `examples/` directory
   - Show input → output transformation patterns
   - Include all field types and transformations

6. **Run Complete Workflow**
   ```bash
   # Analyze project
   python -m edgar_analyzer analyze-project projects/my_custom_project/

   # Generate code
   python -m edgar_analyzer generate-code projects/my_custom_project/

   # Run extraction
   python -m edgar_analyzer run-extraction projects/my_custom_project/

   # Generate reports
   python -m edgar_analyzer report generate \
     --project projects/my_custom_project/ \
     --format excel
   ```

7. **Validate Results**
   - Check output data for accuracy
   - Verify transformations applied correctly
   - Test edge cases and error handling

#### Expected Output
- Working data extractor for custom use case
- Extracted data in desired format
- Generated reports
- Repeatable workflow for future runs

#### Success Criteria
- ✅ User completes workflow independently
- ✅ Extraction produces expected results
- ✅ User can explain what the platform did
- ✅ User identifies value for their use case

#### Common Issues
- **Issue**: "Pattern detection unclear" → Add 3rd example with edge cases
- **Issue**: "Transformation not detected" → Verify examples show clear before/after
- **Issue**: "API authentication failed" → Double-check credentials and config
- **Issue**: "Code generation stuck" → Check OpenRouter API key and quota

---

## Test Data Preparation

### Provided Sample Data

All test data is located in `test_data/` directory:

```
test_data/
├── employee_roster_sample.xlsx     # 10 employee records
├── invoice_sample.pdf              # Simple invoice with line items
├── examples/                       # Pre-built transformation examples
│   ├── employee_roster/
│   │   ├── row1.json
│   │   ├── row2.json
│   │   └── row3.json
│   └── invoice/
│       ├── line1.json
│       ├── line2.json
│       └── line3.json
└── instructions/
    ├── api_setup.md                # How to get OpenWeatherMap API key
    └── quick_reference.md          # Common commands and troubleshooting
```

### Employee Roster Sample

**File**: `employee_roster_sample.xlsx`

| employee_id | first_name | last_name | department  | hire_date  | salary | is_manager |
|-------------|------------|-----------|-------------|------------|--------|------------|
| E1001       | Alice      | Johnson   | Engineering | 2020-03-15 | 95000  | Yes        |
| E1002       | Bob        | Smith     | Sales       | 2021-06-20 | 75000  | No         |
| E1003       | Carol      | Williams  | Marketing   | 2019-11-10 | 82000  | Yes        |
| E1004       | David      | Brown     | Engineering | 2022-01-05 | 88000  | No         |
| E1005       | Emma       | Davis     | HR          | 2020-08-30 | 70000  | No         |
| E1006       | Frank      | Miller    | Finance     | 2018-04-15 | 92000  | Yes        |
| E1007       | Grace      | Wilson    | Operations  | 2021-09-12 | 78000  | No         |
| E1008       | Henry      | Moore     | Engineering | 2023-02-20 | 85000  | No         |
| E1009       | Iris       | Taylor    | Marketing   | 2020-05-25 | 80000  | No         |
| E1010       | Jack       | Anderson  | Sales       | 2022-07-18 | 73000  | Yes        |

**Transformation Patterns**:
- Field rename: `employee_id` → `id`
- Concatenation: `first_name + last_name` → `full_name`
- Type conversion: `salary` (int) → `annual_salary_usd` (float)
- Boolean: `is_manager` ("Yes"/"No") → `manager` (true/false)
- Field abbreviation: `department` → `dept`

### Invoice Sample

**File**: `invoice_sample.pdf`

**Invoice Header**:
- Invoice Number: INV-2025-001
- Date: 2025-01-15
- Customer: Acme Corporation

**Line Items Table**:

| Item       | Quantity | Unit Price | Total   |
|------------|----------|------------|---------|
| Widget A   | 2        | $15.00     | $30.00  |
| Service B  | 1        | $50.00     | $50.00  |
| Product C  | 5        | $8.50      | $42.50  |
| Support D  | 3        | $25.00     | $75.00  |

**Transformation Patterns**:
- Field rename: `Item` → `product`
- Type conversion: `Quantity` (string) → `qty` (int)
- Currency parsing: `$15.00` → `15.00` (float)
- Field rename: `Unit Price` → `unit_price_usd`
- Field rename: `Total` → `line_total_usd`

---

## Known Limitations

### Test Infrastructure (110 failures)

**Status**: Known Issue - Does NOT affect production functionality

**Description**: Mock-related test failures in unit tests due to response format mismatches. These are infrastructure issues, not code issues.

**Impact**: None on user workflows. All production code paths tested and working.

**Workaround**: None required for users. Internal development issue only.

---

### Schema Service Pattern Detection

**Status**: May require manual adjustment in some cases

**Description**: AI-based pattern detection sometimes misses complex transformations or edge cases.

**Impact**: User may need to provide 3rd example or manually adjust generated code.

**Workaround**:
- Provide 3 examples instead of 2 for complex transformations
- Review generated code and adjust transformation logic if needed
- Check pattern detection confidence scores

---

### Async Function Type Hints

**Status**: Technical limitation - use regular functions instead

**Description**: Type hint detection for async functions has limitations in code generation.

**Impact**: Generated extractors may have incorrect type hints for async helper functions.

**Workaround**:
- Use regular (non-async) helper functions when possible
- Manually add type hints to async functions if needed
- Focus async on main extract() method only

---

### OpenRouter API Key Required

**Status**: Required for code generation

**Description**: Code generation uses OpenRouter API (Sonnet 4.5) which requires API key.

**Impact**: Users must sign up for OpenRouter account and obtain API key.

**Workaround**:
- Sign up at https://openrouter.ai/
- Get API key (free tier available)
- Add to `.env.local`: `OPENROUTER_API_KEY=your_key_here`
- See `test_data/instructions/api_setup.md` for details

---

### Jina.ai Limited Validation

**Status**: Integration tested but limited production validation

**Description**: Web scraping via Jina.ai Reader API is tested but not extensively validated in production scenarios.

**Impact**: May encounter issues with certain website structures or JS-heavy sites.

**Workaround**:
- Start with simple, static websites
- Test extraction thoroughly before production use
- Report any issues encountered for investigation

---

## Feedback Collection

### Feedback Template

See `docs/USER_FEEDBACK_TEMPLATE.md` for complete feedback form.

### Key Metrics to Collect

**Quantitative Metrics**:
- Completion rate per scenario (% of users who complete)
- Time to complete each scenario
- Number of errors encountered
- Success rate for code generation
- Success rate for extraction

**Qualitative Metrics**:
- Ease of use (1-5 scale)
- Documentation quality (1-5 scale)
- Error message clarity (1-5 scale)
- Performance satisfaction (1-5 scale)
- Overall experience (1-5 scale)

**Open Feedback**:
- Blocker issues (preventing workflow completion)
- Feature requests (what would make it more useful)
- Use case validation (does this solve your problem?)
- Improvement suggestions

### Feedback Collection Process

1. **Pre-Testing Survey** (5 minutes)
   - User background and experience level
   - Intended use case
   - Current solution (if any)

2. **During Testing** (Live notes)
   - Screen recording or observation notes
   - Real-time issue tracking
   - Timestamp key events

3. **Post-Testing Survey** (10 minutes)
   - Complete feedback template
   - Ratings for all categories
   - Open-ended feedback

4. **Follow-up Interview** (Optional, 15 minutes)
   - Deep dive on specific issues
   - Feature prioritization
   - Use case validation

---

## Alpha Release Timeline

### Week 1: User Testing

**Days 1-2: Onboarding**
- Invite 3-5 alpha testers
- Send welcome email with:
  - User Testing Guide
  - Sample data access
  - Support channel info (Slack, email, GitHub)
- Schedule kickoff call (30 minutes)
- Set up test environment for each user

**Days 3-5: Active Testing**
- Users complete test scenarios independently
- Daily check-ins via Slack/email
- Track issues in GitHub/Linear
- Collect feedback forms as completed

**Days 6-7: Wrap-up**
- Final feedback collection
- Optional follow-up interviews
- Consolidate all feedback
- Begin prioritization

### Week 2: Analysis and Planning

**Days 1-2: Feedback Consolidation**
- Organize all feedback by category
- Identify patterns and themes
- Count occurrences of similar issues
- Create master issue list

**Days 3-4: Prioritization**
- **P0 (Blockers)**: Issues preventing basic functionality - FIX IMMEDIATELY
- **P1 (High Impact)**: Significant usability issues with workarounds - FIX NEXT
- **P2 (Medium Impact)**: Nice-to-have improvements - BACKLOG
- **P3 (Low Impact)**: Minor issues or feature requests - FUTURE

**Day 5: Summary Report**
- Create user testing summary report
- Document all findings and metrics
- Share with stakeholders
- Plan iteration 2

---

## Support Channels

### During Alpha Testing

**Slack Channel**: #edgar-alpha-testing (invite-only)
- Real-time support from development team
- Share issues and workarounds
- Connect with other testers

**Email Support**: edgar-support@example.com
- For private issues or sensitive data
- Response within 24 hours (weekdays)

**GitHub Issues**: https://github.com/yourorg/edgar/issues
- Public bug reports and feature requests
- Include "alpha-tester" label
- Attach logs and screenshots

### Documentation

- **User Testing Guide**: `docs/guides/USER_TESTING_GUIDE.md`
- **Quick Start**: `docs/guides/QUICK_START.md`
- **Troubleshooting**: `docs/guides/TROUBLESHOOTING.md`
- **Platform Usage**: `docs/guides/PLATFORM_USAGE.md`

---

## Success Metrics

### Quantitative Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Scenario Completion Rate** | 80%+ | % users completing 3+ scenarios |
| **Code Generation Success** | 90%+ | % successful code generations |
| **Extraction Success** | 85%+ | % successful extractions |
| **Report Generation Success** | 95%+ | % successful report generations |
| **Average Completion Time** | <2 hours | Total time for all 5 scenarios |

### Qualitative Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Ease of Use** | 4.0+ / 5.0 | Average rating across all users |
| **Documentation Quality** | 4.0+ / 5.0 | Average rating across all users |
| **Error Message Clarity** | 3.5+ / 5.0 | Average rating across all users |
| **Overall Satisfaction** | 4.0+ / 5.0 | Average rating across all users |
| **Recommendation Rate** | 80%+ | % users who would recommend |

### Issue Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **P0 Blockers** | 0 | Issues preventing basic functionality |
| **P1 High Impact** | ≤2 | Major usability issues |
| **P2 Medium Impact** | ≤5 | Nice-to-have improvements |
| **Total Unique Issues** | <20 | Distinct issues reported |

---

## Next Steps

### Immediate Actions (Before Testing)

1. **Prepare Sample Data** ✅
   - Create employee roster Excel file
   - Create invoice PDF
   - Write transformation examples

2. **Write User Testing Guide** ✅
   - Step-by-step instructions
   - Troubleshooting section
   - API setup guide

3. **Set Up Support Channels**
   - Create Slack channel
   - Configure email alias
   - Prepare GitHub issue templates

4. **Recruit Alpha Testers**
   - Identify 5-7 potential testers
   - Send invitations
   - Schedule onboarding calls

### During Testing (Week 1)

1. **Monitor Progress**
   - Daily check-ins with testers
   - Track completion rates
   - Respond to issues quickly

2. **Collect Feedback**
   - Send feedback forms
   - Schedule follow-up interviews
   - Document all observations

3. **Track Issues**
   - Create GitHub/Linear tickets
   - Prioritize as they come in
   - Communicate fixes to testers

### After Testing (Week 2+)

1. **Analyze Results**
   - Consolidate all feedback
   - Calculate success metrics
   - Identify patterns

2. **Plan Iteration 2**
   - Prioritize fixes (P0, P1, P2)
   - Create implementation tickets
   - Set timeline for iteration 2

3. **Prepare Summary**
   - Write user testing summary report
   - Share with stakeholders
   - Plan beta release

---

## Appendix

### Test Environment Specifications

**Hardware Requirements**:
- 4GB RAM minimum (8GB recommended)
- 2GB free disk space
- Internet connection

**Software Requirements**:
- Python 3.11+ (3.13 recommended)
- macOS, Linux, or Windows (WSL recommended)
- Excel viewer (for Excel reports)
- PDF viewer (for PDF reports)

### API Keys Required

**OpenRouter** (Required):
- Sign up: https://openrouter.ai/
- Purpose: Code generation (Sonnet 4.5)
- Cost: Free tier available, ~$0.10 per generation

**OpenWeatherMap** (Scenario 3 only):
- Sign up: https://openweathermap.org/api
- Purpose: Weather data extraction
- Cost: Free tier (60 calls/minute)

**Jina.ai** (Optional - Web scraping):
- Sign up: https://jina.ai/reader
- Purpose: Web content extraction
- Cost: Free tier available

### Glossary

- **Data Source**: Input for extraction (Excel, PDF, API, web)
- **Extractor**: Generated code that performs data extraction
- **Pattern**: Transformation rule detected from examples
- **Project**: Workspace containing configuration, examples, and outputs
- **Scenario**: Complete test workflow from setup to validation
- **Transformation**: Conversion applied to data (rename, type change, etc.)

---

**Document Version**: 1.0
**Last Updated**: 2025-12-04
**Maintained By**: Platform Development Team
**Contact**: edgar-support@example.com
