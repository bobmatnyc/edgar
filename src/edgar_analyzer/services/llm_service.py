"""LLM service for financial data analysis using OpenRouter."""

import json
import os
from typing import Dict, List, Optional, Any
import structlog
from dotenv import load_dotenv

from edgar_analyzer.models.company import ExecutiveCompensation
from .openrouter_service import OpenRouterService

# Load environment variables
load_dotenv('.env.local')

logger = structlog.get_logger(__name__)


class LLMService:
    """Service for LLM-powered financial data analysis."""
    
    def __init__(self):
        """Initialize LLM service with centralized OpenRouter service."""
        # Initialize centralized OpenRouter service
        self.openrouter = OpenRouterService()

        # Model configuration from environment
        self.primary_model = os.getenv("PRIMARY_MODEL", "x-ai/grok-4.1-fast:free")
        self.fallback_model = os.getenv("FALLBACK_MODEL", "anthropic/claude-3.5-sonnet")
        self.tertiary_model = os.getenv("TERTIARY_MODEL", "anthropic/claude-3-sonnet")
        self.model = self.primary_model

        logger.info("LLM service initialized",
                   primary_model=self.primary_model,
                   fallback_model=self.fallback_model,
                   tertiary_model=self.tertiary_model)

    async def _make_llm_request(
        self,
        messages: list,
        temperature: float = 0.1,
        max_tokens: int = 4000,
        enable_web_search: bool = False,
        web_search_params: Optional[Dict[str, Any]] = None
    ):
        """
        Make LLM request using centralized OpenRouter service with fallback support.

        WHY: Centralized API handling with model-independent interface
        HOW: Uses OpenRouterService for all API interactions
        WHEN: Refactored 2025-11-21 for centralized service architecture

        Args:
            messages: Chat messages for the LLM
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum response tokens
            enable_web_search: Whether to enable web search capabilities
            web_search_params: Additional parameters for web search (deprecated)

        Returns:
            LLM response content as string
        """
        # Use centralized OpenRouter service with fallback
        try:
            return await self.openrouter.chat_completion_with_fallback(
                messages=messages,
                primary_model=self.primary_model,
                fallback_models=[self.fallback_model, self.tertiary_model],
                temperature=temperature,
                max_tokens=max_tokens,
                enable_web_search=enable_web_search
            )
        except Exception as e:
            logger.error("All models failed in centralized service", error=str(e))
            raise



    async def web_search_request(
        self,
        query: str,
        context: Optional[str] = None,
        max_results: int = 5,
        temperature: float = 0.3
    ) -> str:
        """
        Perform web search using LLM with OpenRouter web search capabilities.

        WHY: Enables real-time information access for analysis and validation
        HOW: Uses OpenRouter's web search tools with structured queries
        WHEN: Created 2025-11-21 for enhanced information gathering

        Args:
            query: Search query string
            context: Optional context to guide the search
            max_results: Maximum number of search results to consider
            temperature: Sampling temperature for response generation

        Returns:
            Formatted search results and analysis
        """
        messages = [
            {
                "role": "system",
                "content": f"""You are an intelligent web search assistant with access to real-time information.

Your task is to search for information and provide a comprehensive, accurate response.

Search Guidelines:
- Use web search to find current, factual information
- Prioritize authoritative sources (SEC filings, company websites, financial news)
- Cross-reference multiple sources when possible
- Clearly indicate when information is from web search vs. your training data
- Focus on factual, verifiable information

Context: {context if context else 'General information search'}
Maximum results to consider: {max_results}

Please search for the requested information and provide a well-structured response."""
            },
            {
                "role": "user",
                "content": f"Search for: {query}"
            }
        ]

        try:
            response = await self._make_llm_request(
                messages=messages,
                temperature=temperature,
                max_tokens=2000,
                enable_web_search=True
            )

            logger.info("Web search completed",
                       query=query,
                       response_length=len(response))

            return response

        except Exception as e:
            logger.error("Web search failed", query=query, error=str(e))
            return f"Web search failed for query '{query}': {str(e)}"

    async def enhanced_analysis_with_search(
        self,
        primary_content: str,
        search_queries: List[str],
        analysis_prompt: str,
        context: Optional[str] = None
    ) -> str:
        """
        Perform enhanced analysis combining primary content with web search results.

        WHY: Combines static content analysis with real-time information
        HOW: Executes multiple searches and synthesizes with primary analysis
        WHEN: Created 2025-11-21 for comprehensive analysis capabilities

        Args:
            primary_content: Main content to analyze
            search_queries: List of search queries for additional information
            analysis_prompt: Analysis instructions for the LLM
            context: Optional context for the analysis

        Returns:
            Comprehensive analysis combining all sources
        """
        # Perform web searches
        search_results = []
        for query in search_queries:
            try:
                result = await self.web_search_request(
                    query=query,
                    context=context,
                    max_results=3
                )
                search_results.append(f"Search: {query}\nResults: {result}\n")
            except Exception as e:
                logger.warning("Search query failed", query=query, error=str(e))
                search_results.append(f"Search: {query}\nError: {str(e)}\n")

        # Combine all information for analysis
        combined_content = f"""
PRIMARY CONTENT:
{primary_content}

WEB SEARCH RESULTS:
{''.join(search_results)}

ANALYSIS CONTEXT:
{context if context else 'Comprehensive analysis requested'}
"""

        messages = [
            {
                "role": "system",
                "content": f"""You are an expert analyst with access to both provided content and real-time web search results.

Your task is to provide comprehensive analysis by combining:
1. The primary content provided
2. Real-time information from web searches
3. Your analytical expertise

Analysis Guidelines:
- Clearly distinguish between sources (primary content vs. web search)
- Cross-reference information for accuracy
- Highlight any discrepancies or contradictions
- Provide evidence-based conclusions
- Note limitations or areas needing further investigation

{analysis_prompt}"""
            },
            {
                "role": "user",
                "content": combined_content
            }
        ]

        try:
            response = await self._make_llm_request(
                messages=messages,
                temperature=0.2,
                max_tokens=3000
            )

            logger.info("Enhanced analysis completed",
                       search_queries=len(search_queries),
                       response_length=len(response))

            return response

        except Exception as e:
            logger.error("Enhanced analysis failed", error=str(e))
            return f"Enhanced analysis failed: {str(e)}"

    async def parse_proxy_compensation_table(
        self, 
        html_content: str, 
        company_name: str,
        year: int
    ) -> List[Dict[str, Any]]:
        """Use LLM to parse executive compensation from proxy statement HTML."""
        
        # Grok 4.1 Fast has 2M context window - can handle much larger content
        # Truncate only if extremely large (keep first 500k chars to stay well within limits)
        if len(html_content) > 500000:
            html_content = html_content[:500000] + "... [truncated due to size]"
        
        prompt = f"""You are an advanced agentic AI financial analyst with deep expertise in SEC filing analysis and executive compensation research. Use your agentic reasoning capabilities to systematically analyze this complex financial document.

AGENTIC TASK: Systematically extract executive compensation data from this {company_name} proxy statement for fiscal year {year}.

AGENTIC APPROACH:
1. SCAN: First scan the entire document for "Summary Compensation Table" - the primary SEC-required table
2. IDENTIFY: Locate Named Executive Officers (NEOs) - typically CEO, CFO, COO, and other highest-paid executives
3. EXTRACT: Pull EXACT figures from compensation tables, not estimates or calculations
4. CROSS-REFERENCE: Check footnotes and supplementary tables that might affect compensation amounts
5. VALIDATE: Ensure component amounts align with total compensation figures
6. REASON: Apply financial expertise to distinguish between different compensation components

REQUIRED DATA POINTS:
- Executive full name (as listed in filing)
- Official title/position
- Total compensation (rightmost column in Summary Compensation Table)
- Salary (base salary column)
- Bonus (non-equity incentive plan compensation)
- Stock awards (stock awards column value)
- Option awards (option awards column value)
- All other compensation (if significant)

QUALITY STANDARDS:
- Only extract data you can clearly identify in compensation tables
- Set confidence based on clarity of source data (0.9+ for clear table data, 0.7+ for reasonably clear, <0.7 for uncertain)
- Verify that component amounts roughly align with total compensation
- Flag any unusual patterns or potential data quality issues

HTML Content:
{html_content}

OUTPUT FORMAT (JSON only, no explanatory text):
[
  {{
    "name": "Timothy D. Cook",
    "title": "Chief Executive Officer",
    "total_compensation": 63209845,
    "salary": 3000000,
    "bonus": 0,
    "stock_awards": 46000000,
    "option_awards": 0,
    "other_compensation": 209845,
    "confidence": 0.95,
    "source_note": "Summary Compensation Table, page X"
  }}
]

Return empty array [] if no clear compensation data is found."""

        try:
            content = await self._make_llm_request([
                {"role": "system", "content": "You are Grok 4.1 Fast, an advanced agentic AI model specialized in real-world analysis tasks. You are functioning as a senior financial analyst and SEC filing expert with deep expertise in executive compensation analysis. Use your 2M context window and agentic reasoning capabilities to provide precise, institutional-grade analysis of complex financial documents."},
                {"role": "user", "content": prompt}
            ], temperature=0.05, max_tokens=4000)  # Very low temperature for precise extraction
            
            # Try to parse JSON response
            try:
                # Remove any markdown formatting
                if content.startswith('```json'):
                    content = content[7:]
                if content.endswith('```'):
                    content = content[:-3]

                # Try to extract JSON from the response (handle cases where LLM adds explanation)
                json_start = content.find('[')
                json_end = content.rfind(']') + 1

                if json_start >= 0 and json_end > json_start:
                    json_content = content[json_start:json_end]
                    executives = json.loads(json_content)
                else:
                    # Fallback to parsing the entire content
                    executives = json.loads(content)
                
                logger.info(
                    "LLM parsed executive compensation",
                    company=company_name,
                    year=year,
                    executives_found=len(executives)
                )
                
                return executives
                
            except json.JSONDecodeError as e:
                logger.warning(
                    "Failed to parse LLM JSON response",
                    company=company_name,
                    year=year,
                    error=str(e),
                    content=content[:500]
                )
                return []

        except Exception as e:
            logger.error(
                "LLM proxy parsing failed",
                company=company_name,
                year=year,
                error=str(e)
            )
            return []

    async def validate_compensation_data(
        self,
        executives: List[ExecutiveCompensation],
        company_name: str,
        year: int
    ) -> Dict[str, Any]:
        """Use LLM to validate and quality-check extracted compensation data."""

        # Convert executives to dict format for LLM analysis
        exec_data = []
        for exec in executives:
            exec_data.append({
                "name": exec.executive_name,
                "title": exec.title,
                "total_compensation": float(exec.total_compensation),
                "salary": float(exec.salary) if exec.salary else None,
                "bonus": float(exec.bonus) if exec.bonus else None,
                "stock_awards": float(exec.stock_awards) if exec.stock_awards else None,
                "option_awards": float(exec.option_awards) if exec.option_awards else None
            })

        prompt = f"""You are a senior financial analyst and executive compensation expert with deep knowledge of Fortune 500 companies, SEC regulations, and market compensation benchmarks.

TASK: Conduct a comprehensive quality assessment of this executive compensation data for {company_name} (fiscal year {year}).

EXECUTIVE COMPENSATION DATA:
{json.dumps(exec_data, indent=2)}

ANALYSIS FRAMEWORK:

1. **AUTHENTICITY VERIFICATION:**
   - Are these real executives of {company_name}? (Cross-reference with known leadership)
   - Do the names match actual people vs. generated/placeholder names?
   - Are the titles consistent with {company_name}'s organizational structure?

2. **COMPENSATION REASONABLENESS:**
   - Compare to {company_name}'s historical compensation levels
   - Benchmark against industry peers and market data
   - Assess CEO pay ratio to other executives (typical ratios: CEO 2-4x other NEOs)
   - Evaluate total compensation relative to company size/performance

3. **DATA INTEGRITY:**
   - Do component amounts sum to total compensation?
   - Are compensation structures realistic (salary/bonus/equity mix)?
   - Check for artificial patterns or overly uniform distributions
   - Validate against typical Fortune 500 compensation structures

4. **COMPLETENESS ASSESSMENT:**
   - Are key executives present (CEO, CFO, COO, General Counsel, etc.)?
   - Missing critical compensation components?
   - Sufficient detail for analysis?

5. **RED FLAGS:**
   - Generated/fake names (common patterns: generic first/last name combinations)
   - Unrealistic compensation amounts (too high/low for company size)
   - Artificial mathematical relationships between components
   - Missing key executives that should be present

MARKET CONTEXT FOR {company_name}:
- Consider company size, industry, and typical compensation levels
- Factor in recent market conditions and regulatory changes
- Account for company-specific factors affecting compensation

OUTPUT (JSON only):
{{
  "overall_quality_score": 0.85,
  "data_appears_authentic": true,
  "authenticity_confidence": 0.90,
  "market_reasonableness_score": 0.80,
  "data_completeness_score": 0.75,
  "issues_found": [
    "Specific issue description with reasoning"
  ],
  "recommendations": [
    "Actionable recommendation for data improvement"
  ],
  "executive_authenticity": {{
    "likely_real_executives": ["Name 1", "Name 2"],
    "questionable_entries": ["Name 3"],
    "missing_expected_roles": ["CFO", "General Counsel"]
  }},
  "compensation_analysis": {{
    "ceo_pay_ratio": 2.3,
    "total_comp_vs_market": "within_range",
    "component_mix_realistic": true
  }},
  "confidence_in_data": 0.88,
  "summary": "Detailed assessment with specific findings and confidence level"
}}"""

        try:
            content = await self._make_llm_request([
                {"role": "system", "content": "You are Grok 4.1 Fast, an advanced agentic AI model excelling at real-world analysis tasks. You are functioning as a senior financial analyst and executive compensation expert with comprehensive knowledge of Fortune 500 companies, SEC regulations, and market benchmarks. Use your agentic reasoning capabilities and 2M context window to provide institutional-grade assessment."},
                {"role": "user", "content": prompt}
            ], temperature=0.1, max_tokens=3000)

            # Parse JSON response
            try:
                if content.startswith('```json'):
                    content = content[7:]
                if content.endswith('```'):
                    content = content[:-3]

                # Try to extract JSON from the response
                json_start = content.find('{')
                json_end = content.rfind('}') + 1

                if json_start >= 0 and json_end > json_start:
                    json_content = content[json_start:json_end]
                    validation_result = json.loads(json_content)
                else:
                    validation_result = json.loads(content)

                logger.info(
                    "LLM validated compensation data",
                    company=company_name,
                    year=year,
                    quality_score=validation_result.get('overall_quality_score', 0),
                    authentic=validation_result.get('data_appears_authentic', False)
                )

                return validation_result

            except json.JSONDecodeError as e:
                logger.warning(
                    "Failed to parse LLM validation response",
                    company=company_name,
                    year=year,
                    error=str(e)
                )
                return {
                    "overall_quality_score": 0.5,
                    "data_appears_authentic": False,
                    "issues_found": ["Failed to parse LLM response"],
                    "recommendations": ["Manual review required"],
                    "confidence_in_data": 0.0,
                    "summary": "LLM validation failed"
                }

        except Exception as e:
            logger.error(
                "LLM validation failed",
                company=company_name,
                year=year,
                error=str(e)
            )
            return {
                "overall_quality_score": 0.0,
                "data_appears_authentic": False,
                "issues_found": [f"LLM validation error: {str(e)}"],
                "recommendations": ["Manual review required"],
                "confidence_in_data": 0.0,
                "summary": "LLM validation failed due to error"
            }
