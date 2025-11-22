# 📚 Executive Compensation Data Dictionary

## **Overview**

This data dictionary provides detailed definitions for all fields in our executive compensation dataset. Understanding these fields is crucial for accurate analysis and interpretation of executive compensation data.

---

## **🏢 Company-Level Fields**

### **company_name**
- **Type**: String
- **Description**: Official company name as registered with SEC
- **Example**: "Apple Inc.", "Microsoft Corporation"
- **Source**: SEC company filings
- **Notes**: May differ from common trading name

### **symbol**
- **Type**: String
- **Description**: Stock ticker symbol
- **Example**: "AAPL", "MSFT", "GOOGL"
- **Source**: SEC ticker mapping
- **Notes**: Primary exchange symbol used

### **filing_date**
- **Type**: Date (ISO format)
- **Description**: Date when proxy statement was filed with SEC
- **Example**: "2025-01-10"
- **Source**: SEC EDGAR filing metadata
- **Notes**: Compensation data typically covers prior fiscal year

### **accession_number**
- **Type**: String
- **Description**: Unique SEC filing identifier
- **Example**: "0001308179-25-000008"
- **Source**: SEC EDGAR system
- **Notes**: Can be used to retrieve original filing

---

## **👤 Executive-Level Fields**

### **name**
- **Type**: String
- **Description**: Executive's full name as disclosed in proxy
- **Example**: "Timothy D. Cook", "Luca Maestri"
- **Source**: Proxy statement executive tables
- **Notes**: May include middle initial or suffix

### **title**
- **Type**: String
- **Description**: Executive's official title/position
- **Example**: "Chief Executive Officer", "Chief Financial Officer"
- **Source**: Proxy statement disclosures
- **Notes**: May be abbreviated (CEO, CFO, etc.)

---

## **💰 Compensation Fields**

### **total_compensation**
- **Type**: Integer (USD)
- **Description**: Total compensation for the fiscal year per SEC Summary Compensation Table
- **Calculation**: Salary + Bonus + Stock Awards + Option Awards + Other Compensation
- **Example**: 99420097 (represents $99,420,097)
- **Source**: SEC proxy statement Summary Compensation Table
- **SEC Definition**: Column (j) of Summary Compensation Table
- **Notes**: 
  - Represents compensation **granted** during fiscal year
  - Stock/option awards valued at grant date fair value
  - May differ significantly from cash actually received

### **actually_paid_compensation**
- **Type**: Integer (USD)
- **Description**: Compensation actually paid/received (Pay vs Performance table)
- **Calculation**: Adjusts total compensation for actual stock performance
- **Example**: 106643588 (represents $106,643,588)
- **Source**: SEC Pay vs Performance disclosure table
- **SEC Definition**: Required since 2022 for large accelerated filers
- **Notes**:
  - Reflects actual value received vs. grant date value
  - Accounts for stock price changes since grant
  - More representative of actual economic benefit

### **salary**
- **Type**: Integer (USD)
- **Description**: Base annual salary earned during fiscal year
- **Example**: 3000000 (represents $3,000,000)
- **Source**: Summary Compensation Table, Column (c)
- **SEC Definition**: Cash compensation for services during fiscal year
- **Notes**:
  - Generally stable year-over-year
  - Paid in cash during the fiscal year
  - Does not include deferred compensation

### **bonus**
- **Type**: Integer (USD)
- **Description**: Annual cash incentive awards
- **Example**: 12000000 (represents $12,000,000)
- **Source**: Summary Compensation Table, Column (d)
- **SEC Definition**: Discretionary cash awards not based on performance metrics
- **Notes**:
  - Excludes performance-based incentives (reported separately)
  - May be paid in year following performance
  - Highly variable based on company/individual performance

### **stock_awards**
- **Type**: Integer (USD)
- **Description**: Grant date fair value of stock-based compensation
- **Example**: 75000000 (represents $75,000,000)
- **Source**: Summary Compensation Table, Column (e)
- **SEC Definition**: ASC 718 grant date fair value of stock awards
- **Types Include**:
  - Restricted Stock Units (RSUs)
  - Performance Share Units (PSUs)
  - Restricted Stock Awards
- **Notes**:
  - Valued at grant date stock price
  - Actual value depends on future stock performance
  - Usually vests over 3-4 years

### **option_awards**
- **Type**: Integer (USD)
- **Description**: Grant date fair value of stock option grants
- **Example**: 25000000 (represents $25,000,000)
- **Source**: Summary Compensation Table, Column (f)
- **SEC Definition**: ASC 718 grant date fair value of option awards
- **Valuation**: Black-Scholes or similar option pricing model
- **Notes**:
  - Theoretical value at grant date
  - Actual value depends on stock price appreciation
  - May expire worthless if stock doesn't appreciate

### **other_compensation**
- **Type**: Integer (USD)
- **Description**: All other compensation not in above categories
- **Example**: 1500000 (represents $1,500,000)
- **Source**: Summary Compensation Table, Column (i)
- **Includes**:
  - Perquisites and personal benefits
  - Life insurance premiums
  - Company contributions to retirement plans
  - Tax gross-ups
  - Severance payments
- **SEC Requirement**: Must detail if total >$10,000
- **Notes**: Often includes non-cash benefits valued at cost to company

---

## **📊 Metadata Fields**

### **data_source**
- **Type**: String (Enumerated)
- **Description**: Primary source of the compensation data
- **Values**:
  - `xbrl_pay_vs_performance`: XBRL Pay vs Performance table
  - `xbrl_peo_compensation`: XBRL PEO-specific data
  - `xbrl_neo_average`: XBRL NEO average compensation
  - `sec_api_professional`: SEC-API.io professional service
  - `fmp_api`: Financial Modeling Prep API
  - `ai_llm_extraction`: AI-powered text extraction
  - `html_parsing`: Traditional HTML parsing
- **Quality Ranking**: Listed in order of data quality (highest to lowest)

### **extraction_method**
- **Type**: String
- **Description**: Specific method used to extract the data
- **Examples**:
  - `breakthrough_xbrl_pvp`: Our XBRL breakthrough method
  - `multi_source_xbrl_priority`: Multi-source with XBRL priority
  - `sec_api_professional`: Professional API service
  - `fmp_api`: Financial Modeling Prep API
- **Notes**: Indicates the technical approach used

### **quality_score**
- **Type**: Float (0.0 to 1.0)
- **Description**: Data quality confidence score
- **Scale**:
  - 0.95: XBRL structured data (highest quality)
  - 0.90: Professional API services
  - 0.85: Established financial APIs
  - 0.75: AI-powered extraction
  - 0.60: Traditional HTML parsing
- **Usage**: Higher scores indicate more reliable data

---

## **🎯 Executive Categories**

### **PEO (Principal Executive Officer)**
- **Definition**: Chief Executive Officer or equivalent
- **SEC Requirement**: Must be separately identified
- **Data Quality**: Highest - always disclosed in detail
- **Typical Titles**: "Chief Executive Officer", "President and CEO"

### **NEO (Named Executive Officers)**
- **Definition**: 5 highest-paid executives including CEO
- **SEC Requirement**: Must disclose compensation for top 5
- **Data Quality**: High - detailed disclosure required
- **Selection**: Based on total compensation ranking

---

## **📈 Data Quality Indicators**

### **Success Indicators**
- **success**: Boolean indicating if extraction was successful
- **executives**: Array of executive compensation records
- **total_executives**: Count of executives extracted

### **Error Indicators**
- **reason**: Reason for extraction failure
- **error**: Detailed error message
- **attempts**: Array of attempted extraction methods

---

## **💡 Usage Guidelines**

### **Comparing Compensation**
- **Use Total Compensation** for year-over-year comparisons
- **Use Actually Paid** for economic reality analysis
- **Consider Fiscal Year Differences** when comparing companies
- **Account for Company Size** when benchmarking

### **Data Freshness**
- **Filing Date**: Check filing date for data recency
- **Fiscal Year**: Compensation typically covers prior fiscal year
- **Update Frequency**: Proxy statements filed annually

### **Quality Assessment**
- **Quality Score**: Higher scores indicate more reliable data
- **Data Source**: XBRL sources are most reliable
- **Cross-Validation**: Compare with other sources when available

---

## **⚠️ Important Notes**

### **Compensation Timing**
- **Grant Date vs. Payment**: Stock awards valued at grant, not payment
- **Vesting Schedules**: Awards may vest over multiple years
- **Performance Conditions**: Some awards subject to performance metrics

### **Valuation Methods**
- **Stock Awards**: Market price at grant date
- **Option Awards**: Black-Scholes or binomial model
- **Actual Value**: May differ significantly from reported value

### **Disclosure Variations**
- **Company Differences**: Disclosure formats may vary
- **Regulatory Changes**: SEC requirements evolve over time
- **International Companies**: May have different disclosure standards

---

## **🔍 Data Validation**

### **Reasonableness Checks**
- **Total = Sum of Components**: Validate calculation accuracy
- **Year-over-Year Changes**: Flag unusual variations
- **Peer Comparisons**: Compare to industry benchmarks
- **Outlier Detection**: Identify potential data errors

### **Completeness Validation**
- **Required Fields**: Ensure core compensation data present
- **Executive Count**: Validate expected number of NEOs
- **Filing References**: Verify source document availability

---

**📋 This data dictionary ensures accurate interpretation and analysis of our executive compensation dataset for business intelligence, research, and compliance purposes.**
