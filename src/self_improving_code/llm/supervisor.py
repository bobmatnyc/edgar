"""
LLM Supervisor + QA Implementation

This implements the Supervisor + QA role using any LLM that supports
the OpenAI-compatible chat completions API.
"""

import json
from typing import Dict, Any, Callable, List
import structlog

from ..core.interfaces import SupervisorLLM

logger = structlog.get_logger(__name__)


class LLMSupervisor(SupervisorLLM):
    """
    LLM-based Supervisor + QA implementation.
    
    This class can work with any LLM that supports chat completions
    (OpenAI, Anthropic via OpenRouter, local models, etc.)
    """
    
    def __init__(
        self,
        llm_client: Callable,
        model_name: str = "grok-4.1-fast",
        domain_expertise: str = "general software quality",
        quality_standards: Dict[str, Any] = None,
        enable_web_search: bool = False,
        web_search_client: Callable = None
    ):
        """
        Initialize LLM Supervisor.

        WHY: Provides intelligent quality assurance with optional web search
        HOW: Uses LLM for analysis with real-time information when needed
        WHEN: Enhanced 2025-11-21 to add web search capabilities

        Args:
            llm_client: Function that takes messages and returns LLM response
            model_name: Name of the model for logging
            domain_expertise: Domain expertise description for prompts
            quality_standards: Custom quality standards dict
            enable_web_search: Whether to enable web search for validation
            web_search_client: Function for web search requests
        """
        self.llm_client = llm_client
        self.model_name = model_name
        self.domain_expertise = domain_expertise
        self.quality_standards = quality_standards or {
            "pass_threshold": 0.8,
            "conditional_threshold": 0.5,
            "fail_threshold": 0.0
        }
        self.enable_web_search = enable_web_search
        self.web_search_client = web_search_client
        
        logger.info("LLM Supervisor initialized", 
                   model=model_name, 
                   domain=domain_expertise)
    
    async def evaluate_results(
        self,
        test_results: Dict[str, Any],
        iteration: int,
        context: Dict[str, Any],
        enable_search_for_validation: bool = False
    ) -> Dict[str, Any]:
        """
        Evaluate test results using LLM as Supervisor + QA with optional web search.

        WHY: Provides comprehensive quality analysis with real-time validation
        HOW: Uses LLM analysis enhanced with web search when needed
        WHEN: Enhanced 2025-11-21 to add web search validation

        Args:
            test_results: Results to evaluate
            iteration: Current iteration number
            context: Analysis context
            enable_search_for_validation: Whether to use web search for validation

        Returns:
            Evaluation results with quality assessment
        """
        
        # Build context-aware prompt
        domain_context = context.get('domain', 'software development')
        requirements = context.get('requirements', 'general quality standards')

        # Perform web search validation if enabled and needed
        web_search_context = ""
        if (enable_search_for_validation and
            self.enable_web_search and
            self.web_search_client):

            try:
                # Generate search queries based on domain and results
                search_queries = self._generate_validation_queries(test_results, domain_context)

                if search_queries:
                    logger.info("Performing web search validation",
                               queries=search_queries)

                    search_results = []
                    for query in search_queries[:3]:  # Limit to 3 searches
                        try:
                            result = await self.web_search_client(
                                query=query,
                                context=f"Validating {domain_context} results"
                            )
                            search_results.append(f"Query: {query}\nResults: {result}\n")
                        except Exception as e:
                            logger.warning("Search validation failed",
                                         query=query, error=str(e))

                    if search_results:
                        web_search_context = f"""
WEB SEARCH VALIDATION:
{''.join(search_results)}

Use this real-time information to validate the test results against current standards and practices.
"""
            except Exception as e:
                logger.warning("Web search validation failed", error=str(e))
        
        prompt = f"""You are the SUPERVISOR + QA ANALYST in a self-improving code system with access to real-time information.

DOMAIN EXPERTISE: {self.domain_expertise}
ITERATION: {iteration + 1}
CONTEXT: {domain_context}
REQUIREMENTS: {requirements}

{web_search_context}

DUAL ROLE:
1. SUPERVISOR: Orchestrate improvement process and make go/no-go decisions
2. QA ANALYST: Perform rigorous quality assurance on results

TEST RESULTS:
{json.dumps(test_results, indent=2)}

QA ANALYSIS FRAMEWORK:
1. **Result Validity**: Are the results technically correct and complete?
2. **Quality Standards**: Do results meet professional/industry standards?
3. **Data Integrity**: Are there signs of errors, corruption, or artificial patterns?
4. **Business Requirements**: Do results satisfy the stated requirements?
5. **Edge Cases**: Are there obvious failure modes or missing scenarios?

QUALITY THRESHOLDS:
- Score >= {self.quality_standards['pass_threshold']}: PASS - No improvement needed
- Score >= {self.quality_standards['conditional_threshold']}: CONDITIONAL - Minor improvements
- Score < {self.quality_standards['conditional_threshold']}: FAIL - Major improvements required

SUPERVISOR DECISION: Based on QA analysis, determine if code improvements are needed.

OUTPUT (JSON only):
{{
  "needs_improvement": true,
  "quality_score": 0.6,
  "qa_status": "FAIL",
  "data_authenticity": "questionable",
  "issues_found": [
    "QA: Specific quality issue with evidence",
    "TECHNICAL: Specific technical problem",
    "BUSINESS: Business requirement not met"
  ],
  "improvement_directions": [
    "Specific actionable improvement 1",
    "Specific actionable improvement 2"
  ],
  "priority": "high",
  "confidence": 0.9,
  "qa_recommendations": [
    "Professional QA recommendation 1",
    "Professional QA recommendation 2"
  ]
}}"""

        try:
            messages = [
                {
                    "role": "system", 
                    "content": f"You are an expert {self.domain_expertise} Supervisor + QA Analyst using {self.model_name}. Provide rigorous, professional-grade quality assessment."
                },
                {"role": "user", "content": prompt}
            ]
            
            response = await self.llm_client(messages)
            evaluation = self._parse_json_response(response)
            
            logger.info("Supervisor evaluation complete",
                       quality_score=evaluation.get('quality_score', 0),
                       qa_status=evaluation.get('qa_status', 'UNKNOWN'),
                       needs_improvement=evaluation.get('needs_improvement', True))
            
            return evaluation
            
        except Exception as e:
            logger.error("Supervisor evaluation failed", error=str(e))
            return {
                "needs_improvement": True,
                "quality_score": 0.0,
                "qa_status": "ERROR",
                "issues_found": [f"Evaluation error: {str(e)}"],
                "improvement_directions": ["Manual review required"],
                "priority": "high",
                "confidence": 0.0
            }
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from LLM response, handling various formats."""
        try:
            # Remove markdown formatting
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            
            # Try to extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_content = response[json_start:json_end]
                return json.loads(json_content)
            else:
                return json.loads(response)
                
        except json.JSONDecodeError as e:
            logger.warning("Failed to parse JSON response", error=str(e), response=response[:200])
            raise

    def _generate_validation_queries(
        self,
        test_results: Dict[str, Any],
        domain_context: str
    ) -> List[str]:
        """
        Generate web search queries for validation based on test results.

        WHY: Creates targeted searches to validate results against current standards
        HOW: Analyzes test results and domain to generate relevant queries
        WHEN: Created 2025-11-21 for web search validation

        Args:
            test_results: Test results to validate
            domain_context: Domain context for targeted searches

        Returns:
            List of search queries for validation
        """
        queries = []

        # Extract key information from test results
        if 'compensations' in test_results:
            # For executive compensation analysis
            queries.extend([
                f"{domain_context} executive compensation best practices 2024",
                "SEC proxy filing compensation disclosure requirements",
                "executive compensation data quality standards"
            ])

        if 'extraction_method' in test_results:
            # For data extraction validation
            queries.extend([
                f"{domain_context} data extraction best practices",
                "automated data extraction quality standards",
                "data validation techniques 2024"
            ])

        if 'code_quality' in test_results:
            # For code quality validation
            queries.extend([
                f"{domain_context} code quality standards 2024",
                "software engineering best practices",
                "code review quality metrics"
            ])

        # Add general validation queries
        if domain_context and domain_context != 'software development':
            queries.append(f"{domain_context} industry standards 2024")

        # Remove duplicates and limit
        return list(dict.fromkeys(queries))[:5]
