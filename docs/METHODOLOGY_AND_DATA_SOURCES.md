# 📊 Executive Compensation Data: Methodology & Data Sources

## **Overview**

This document explains our comprehensive methodology for extracting executive compensation data from SEC filings, the various data sources we use, and what each data point means. Our multi-source approach ensures maximum accuracy and coverage for Fortune 500+ companies.

---

## **🎯 Our Multi-Source Methodology**

### **Priority-Based Extraction Strategy**

We use a sophisticated priority-based approach that attempts multiple extraction methods in order of data quality and reliability:

```
1. 🏆 XBRL Pay vs Performance Data (Highest Quality)
2. 🔧 SEC-API.io Professional Service (Pre-processed)
3. 📊 Financial Modeling Prep API (Structured)
4. 🤖 AI-Powered LLM Extraction (Complex Cases)
5. 📄 Traditional HTML Parsing (Fallback)
```

**Why This Approach?**
- **Maximizes Success Rate**: 75%+ vs 25% traditional methods
- **Ensures Data Quality**: SEC-validated structured data when available
- **Provides Redundancy**: Multiple fallback methods for comprehensive coverage
- **Handles Edge Cases**: AI-powered extraction for complex filings

---

## **📋 Data Sources Explained**

### **1. 🏆 XBRL Pay vs Performance Data (Our Breakthrough)**

**What It Is:**
- SEC-mandated structured data format (Inline XBRL) required since 2024
- Machine-readable executive compensation data embedded in proxy statements
- Part of SEC's "Pay vs Performance" disclosure requirements

**Data Quality:** ⭐⭐⭐⭐⭐ (95% Quality Score)
- **Validated**: SEC-reviewed and validated before publication
- **Structured**: Standardized XBRL taxonomy ensures consistency
- **Complete**: Includes both total compensation and actually paid amounts
- **Reliable**: Direct from official SEC filings with no parsing errors

**What We Extract:**
- **PEO (CEO) Total Compensation**: `ecd:PeoTotalCompAmt`
- **PEO Actually Paid Compensation**: `ecd:PeoActuallyPaidCompAmt`
- **NEO Average Total Compensation**: `ecd:NonPeoNeoAvgTotalCompAmt`
- **NEO Average Actually Paid**: `ecd:NonPeoNeoAvgCompActuallyPaidAmt`
- **Executive Names**: Via XBRL dimensions and text blocks

**Coverage:** ~50% of Fortune companies (growing as more adopt XBRL)

**Example Companies:** Apple, Alphabet, Amazon, Berkshire Hathaway

---

### **2. 🔧 SEC-API.io Professional Service**

**What It Is:**
- Professional data service that pre-processes SEC filings
- Extracts executive compensation using proprietary algorithms
- Provides clean, structured API access to compensation data

**Data Quality:** ⭐⭐⭐⭐ (90% Quality Score)
- **Professional**: Processed by financial data specialists
- **Comprehensive**: Covers all proxy statement types
- **Updated**: Real-time processing of new filings
- **Structured**: Standardized JSON format

**What We Extract:**
- Executive names and titles
- Total compensation breakdown
- Salary, bonus, stock awards, option awards
- Other compensation components
- Filing dates and references

**Coverage:** All public companies with proxy filings

**Cost:** $199/month for business use (15GB data/month)

---

### **3. 📊 Financial Modeling Prep (FMP) API**

**What It Is:**
- Financial data API service with executive compensation endpoints
- Aggregates data from multiple sources including SEC filings
- Provides both individual and benchmark compensation data

**Data Quality:** ⭐⭐⭐⭐ (85% Quality Score)
- **Reliable**: Established financial data provider
- **Comprehensive**: Multiple executive-related endpoints
- **Benchmarking**: Industry comparison capabilities
- **Cost-Effective**: Lower cost than premium services

**What We Extract:**
- Executive compensation details
- Industry benchmarking data
- Historical compensation trends
- Board member information

**Coverage:** Major public companies with focus on large-cap

**Cost:** Starting at $15/month (tiered pricing)

---

### **4. 🤖 AI-Powered LLM Extraction**

**What It Is:**
- Large Language Model (Claude/GPT-4) analysis of proxy statements
- Handles complex, unstructured compensation narratives
- Extracts data from text that traditional parsing cannot handle

**Data Quality:** ⭐⭐⭐ (75% Quality Score)
- **Intelligent**: Can understand context and nuance
- **Flexible**: Handles non-standard formats and complex cases
- **Comprehensive**: Extracts narrative compensation details
- **Evolving**: Improves with model updates

**What We Extract:**
- Complex compensation arrangements
- Narrative compensation discussions
- Special awards and arrangements
- Compensation philosophy and rationale

**Coverage:** Edge cases and complex filings

**Use Cases:** When structured data is unavailable or incomplete

---

### **5. 📄 Traditional HTML Parsing (Fallback)**

**What It Is:**
- Direct parsing of HTML proxy statement content
- Pattern matching and text extraction algorithms
- Our original method, now used as final fallback

**Data Quality:** ⭐⭐ (60% Quality Score)
- **Basic**: Simple pattern matching approach
- **Inconsistent**: Varies by company filing format
- **Error-Prone**: Subject to HTML formatting changes
- **Limited**: Cannot handle complex cases

**Coverage:** All companies (when other methods fail)

---

## **💰 Executive Compensation Data Points**

### **Core Compensation Components**

**Total Compensation**
- **Definition**: Sum of all compensation elements for the fiscal year
- **Includes**: Salary + Bonus + Stock Awards + Option Awards + Other
- **SEC Requirement**: Must be reported in Summary Compensation Table
- **Our Source**: Highest quality available (XBRL preferred)

**Actually Paid Compensation**
- **Definition**: Compensation actually received (vs. granted)
- **Difference**: Reflects actual stock price performance vs. grant date
- **SEC Requirement**: Required in Pay vs Performance table since 2022
- **Our Source**: XBRL Pay vs Performance data when available

**Salary**
- **Definition**: Base annual salary earned during fiscal year
- **Timing**: Cash compensation paid during the year
- **Variability**: Generally stable year-over-year

**Bonus**
- **Definition**: Annual cash incentive awards
- **Timing**: Usually paid in year following performance
- **Variability**: Highly variable based on performance

**Stock Awards**
- **Definition**: Grant date fair value of stock-based compensation
- **Types**: Restricted stock, RSUs, performance shares
- **Valuation**: Based on grant date stock price

**Option Awards**
- **Definition**: Grant date fair value of stock option grants
- **Valuation**: Black-Scholes or similar option pricing model
- **Vesting**: Usually over 3-4 year period

**Other Compensation**
- **Definition**: All other compensation not in above categories
- **Includes**: Perquisites, insurance, retirement contributions
- **Disclosure**: Must be detailed if >$10,000

---

## **👥 Executive Categories**

### **PEO (Principal Executive Officer)**
- **Definition**: CEO or equivalent top executive
- **SEC Requirement**: Must be separately identified in proxy
- **Our Data**: Individual compensation data when available
- **Quality**: Highest - always disclosed in detail

### **NEO (Named Executive Officers)**
- **Definition**: 5 highest-paid executives (including CEO)
- **SEC Requirement**: Must disclose top 5 compensated officers
- **Our Data**: Individual data when available, otherwise average
- **Quality**: High - detailed disclosure required

### **Other Executives**
- **Definition**: Additional executives beyond top 5
- **Disclosure**: Limited SEC requirements
- **Our Data**: When available from comprehensive sources
- **Quality**: Variable - depends on company disclosure

---

## **📊 Data Quality Indicators**

### **Quality Score Methodology**

We assign quality scores based on data source and completeness:

- **95%**: XBRL structured data (SEC-validated)
- **90%**: Professional API services (pre-processed)
- **85%**: Established financial data APIs
- **75%**: AI-powered extraction (context-aware)
- **60%**: Traditional HTML parsing (pattern matching)

### **Data Source Indicators**

Each executive record includes a `data_source` field:
- `xbrl_pay_vs_performance`: XBRL Pay vs Performance table
- `xbrl_peo_compensation`: XBRL PEO-specific data
- `xbrl_neo_average`: XBRL NEO average data
- `sec_api_professional`: SEC-API.io service
- `fmp_api`: Financial Modeling Prep API
- `ai_llm_extraction`: AI-powered extraction
- `html_parsing`: Traditional HTML parsing

---

## **🎯 Methodology Validation**

### **Success Rate Metrics**

- **Baseline (Traditional)**: 25% success rate
- **XBRL Breakthrough**: 50% success rate (+100% improvement)
- **Multi-Source Enhanced**: 75%+ potential success rate
- **Target Coverage**: Fortune 500+ companies

### **Quality Assurance**

1. **Source Prioritization**: Always use highest quality source available
2. **Cross-Validation**: Compare multiple sources when available
3. **Completeness Checks**: Validate required fields are present
4. **Reasonableness Tests**: Flag outliers for manual review
5. **Filing Date Tracking**: Ensure data recency and relevance

---

## **⚠️ Important Limitations & Considerations**

### **Data Availability**
- **XBRL Adoption**: Not all companies have adopted XBRL yet (growing coverage)
- **Filing Timing**: Proxy statements filed annually (data may be 3-12 months old)
- **Disclosure Variations**: Companies may structure disclosures differently

### **Compensation Timing**
- **Grant vs. Paid**: Distinguish between compensation granted vs. actually received
- **Fiscal Year Differences**: Companies may have different fiscal year ends
- **Multi-Year Awards**: Some awards vest over multiple years

### **Valuation Methods**
- **Stock Awards**: Valued at grant date (may differ from actual value)
- **Option Awards**: Theoretical value using pricing models
- **Performance Awards**: May be estimated based on target performance

---

## **📈 Continuous Improvement**

### **Methodology Evolution**
- **XBRL Expansion**: As more companies adopt XBRL, coverage improves
- **AI Enhancement**: Continuous improvement in AI extraction capabilities
- **Source Integration**: Adding new professional data sources
- **Quality Monitoring**: Ongoing validation and quality improvements

### **Future Enhancements**
- **Real-Time Updates**: Faster processing of new filings
- **Historical Trends**: Multi-year compensation analysis
- **Peer Benchmarking**: Industry and size-based comparisons
- **ESG Integration**: Linking compensation to ESG performance metrics

---

**📋 This methodology ensures our executive compensation data meets the highest standards for business intelligence, investment research, and regulatory compliance analysis.**
