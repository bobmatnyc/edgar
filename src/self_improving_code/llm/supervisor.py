"""
LLM Supervisor + QA Implementation

This implements the Supervisor + QA role using any LLM that supports
the OpenAI-compatible chat completions API.
"""

import json
from typing import Dict, Any, Callable
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
        quality_standards: Dict[str, Any] = None
    ):
        """
        Initialize LLM Supervisor.
        
        Args:
            llm_client: Function that takes messages and returns LLM response
            model_name: Name of the model for logging
            domain_expertise: Domain expertise description for prompts
            quality_standards: Custom quality standards dict
        """
        self.llm_client = llm_client
        self.model_name = model_name
        self.domain_expertise = domain_expertise
        self.quality_standards = quality_standards or {
            "pass_threshold": 0.8,
            "conditional_threshold": 0.5,
            "fail_threshold": 0.0
        }
        
        logger.info("LLM Supervisor initialized", 
                   model=model_name, 
                   domain=domain_expertise)
    
    async def evaluate_results(
        self, 
        test_results: Dict[str, Any], 
        iteration: int,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate test results using LLM as Supervisor + QA."""
        
        # Build context-aware prompt
        domain_context = context.get('domain', 'software development')
        requirements = context.get('requirements', 'general quality standards')
        
        prompt = f"""You are the SUPERVISOR + QA ANALYST in a self-improving code system.

DOMAIN EXPERTISE: {self.domain_expertise}
ITERATION: {iteration + 1}
CONTEXT: {domain_context}
REQUIREMENTS: {requirements}

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
