"""
Agentic Control Service - LLM-driven self-improving extraction system
"""

import json
import os
import subprocess
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import structlog

from edgar_analyzer.services.llm_service import LLMService

logger = structlog.get_logger(__name__)


class AgenticControlService:
    """
    LLM Control System that evaluates extraction results and directs code improvements.
    
    Architecture:
    - Supervisor LLM (Grok 4.1 Fast): Evaluates results, makes decisions
    - Engineer LLM (Claude Sonnet 4.5): Writes and fixes code
    - Git safety: All changes are committed for easy rollback
    """
    
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.supervisor_model = "x-ai/grok-4.1-fast:free"  # Control/evaluation
        self.engineer_model = "anthropic/claude-3.5-sonnet"  # Code writing
        
        # Paths that can be modified by the system
        self.modifiable_paths = [
            "src/edgar_analyzer/services/data_extraction_service.py",
            "src/edgar_analyzer/extractors/",  # Custom extractors directory
            "src/edgar_analyzer/parsers/",     # Custom parsers directory
        ]
        
        # Control layer - IMMUTABLE
        self.control_files = [
            "src/edgar_analyzer/services/agentic_control_service.py",
            "src/edgar_analyzer/services/llm_service.py"
        ]
        
        logger.info("Agentic Control Service initialized", 
                   supervisor=self.supervisor_model,
                   engineer=self.engineer_model)
    
    async def evaluate_and_improve(
        self, 
        extraction_results: List[Dict[str, Any]], 
        target_company: str,
        iteration: int = 0,
        max_iterations: int = 3
    ) -> Dict[str, Any]:
        """
        Main control loop: Evaluate results and improve extraction if needed.
        """
        logger.info(f"Starting evaluation cycle {iteration+1}/{max_iterations}", 
                   company=target_company)
        
        # Step 1: Supervisor evaluates the results
        evaluation = await self._supervisor_evaluate(extraction_results, target_company)
        
        logger.info("Supervisor evaluation complete",
                   quality_score=evaluation.get('quality_score', 0),
                   needs_improvement=evaluation.get('needs_improvement', False))
        
        # Step 2: If quality is acceptable, return results
        if not evaluation.get('needs_improvement', True) or iteration >= max_iterations:
            return {
                'final_results': extraction_results,
                'evaluation': evaluation,
                'iterations': iteration + 1,
                'improved': iteration > 0
            }
        
        # Step 3: Create git checkpoint before making changes
        checkpoint_id = await self._create_git_checkpoint(f"pre_improvement_{iteration}")
        
        try:
            # Step 4: Engineer implements improvements
            improvement_result = await self._engineer_improve_code(
                evaluation, extraction_results, target_company
            )
            
            if improvement_result.get('code_changed', False):
                # Step 5: Test the improved extraction
                logger.info("Testing improved extraction", iteration=iteration+1)
                
                # Re-run extraction with improved code
                # This would call the updated extraction service
                new_results = await self._test_improved_extraction(target_company)
                
                # Step 6: Recursive evaluation with improved results
                return await self.evaluate_and_improve(
                    new_results, target_company, iteration + 1, max_iterations
                )
            else:
                logger.warning("Engineer could not improve code", iteration=iteration)
                return {
                    'final_results': extraction_results,
                    'evaluation': evaluation,
                    'iterations': iteration + 1,
                    'improved': False,
                    'reason': 'No code improvements possible'
                }
                
        except Exception as e:
            # Rollback on error
            logger.error("Error during improvement, rolling back", 
                        error=str(e), checkpoint=checkpoint_id)
            await self._rollback_to_checkpoint(checkpoint_id)
            
            return {
                'final_results': extraction_results,
                'evaluation': evaluation,
                'iterations': iteration + 1,
                'improved': False,
                'error': str(e)
            }
    
    async def _supervisor_evaluate(
        self, 
        results: List[Dict[str, Any]], 
        company: str
    ) -> Dict[str, Any]:
        """Supervisor LLM evaluates extraction results and decides if improvement is needed."""
        
        prompt = f"""You are the Supervisor AI controlling an agentic extraction system. 

EVALUATION TASK: Analyze these executive compensation extraction results for {company} and determine if the extraction code needs improvement.

EXTRACTION RESULTS:
{json.dumps(results, indent=2)}

As the Supervisor, evaluate:

1. **DATA AUTHENTICITY**: Are these real executives of {company}?
2. **DATA QUALITY**: Do compensation amounts seem realistic?
3. **COMPLETENESS**: Are key executives (CEO, CFO, etc.) present?
4. **EXTRACTION ACCURACY**: Any signs of parsing errors or data corruption?

DECISION FRAMEWORK:
- If quality_score >= 0.8: No improvement needed
- If 0.5 <= quality_score < 0.8: Minor improvements needed
- If quality_score < 0.5: Major improvements needed

OUTPUT (JSON only):
{{
  "quality_score": 0.75,
  "needs_improvement": true,
  "improvement_priority": "high",
  "specific_issues": [
    "Missing CEO data",
    "Compensation amounts too low"
  ],
  "recommended_actions": [
    "Improve CEO detection logic",
    "Fix compensation parsing for large amounts"
  ],
  "target_improvements": {{
    "missing_executives": ["CEO", "CFO"],
    "parsing_issues": ["large_numbers", "title_extraction"],
    "data_quality": ["authenticity_check", "amount_validation"]
  }}
}}"""

        try:
            # Use supervisor model for evaluation
            content = await self.llm_service._make_llm_request([
                {"role": "system", "content": f"You are the Supervisor AI of an agentic extraction system. Use {self.supervisor_model} capabilities for strategic evaluation."},
                {"role": "user", "content": prompt}
            ], temperature=0.1, max_tokens=2000)
            
            # Parse evaluation
            evaluation = self._parse_json_response(content)
            return evaluation
            
        except Exception as e:
            logger.error("Supervisor evaluation failed", error=str(e))
            return {
                "quality_score": 0.0,
                "needs_improvement": True,
                "error": str(e)
            }
