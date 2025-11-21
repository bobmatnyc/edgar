"""
Self-Improving Extraction Controller - IMMUTABLE CONTROL LAYER

This is the control layer that cannot be modified. It uses the self-improving
code pattern to evaluate extraction results and direct improvements.
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
import structlog

from edgar_analyzer.patterns.self_improving_code import SelfImprovingCode
from edgar_analyzer.extractors.adaptive_compensation_extractor import AdaptiveCompensationExtractor
from edgar_analyzer.services.llm_service import LLMService

logger = structlog.get_logger(__name__)


class SelfImprovingExtractionController:
    """
    IMMUTABLE CONTROL LAYER: Controls the self-improving extraction process.
    
    This class implements the coding pattern where:
    1. It tests the current extraction implementation
    2. Evaluates results using LLM supervision
    3. Directs code improvements when needed
    4. Maintains safety through git checkpoints
    """
    
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        
        # Define which files can be modified (implementation layer)
        self.mutable_files = [
            "src/edgar_analyzer/extractors/adaptive_compensation_extractor.py"
        ]
        
        # Define which files are protected (control layer)
        self.protected_files = [
            "src/edgar_analyzer/controllers/self_improving_extraction_controller.py",
            "src/edgar_analyzer/patterns/self_improving_code.py",
            "src/edgar_analyzer/services/llm_service.py"
        ]
        
        # Initialize the self-improving code pattern
        self.self_improving_code = SelfImprovingCode(
            supervisor_llm=self._supervisor_llm_call,
            engineer_llm=self._engineer_llm_call,
            target_files=self.mutable_files,
            protected_files=self.protected_files
        )
        
        logger.info("Self-Improving Extraction Controller initialized",
                   mutable_files=len(self.mutable_files),
                   protected_files=len(self.protected_files))
    
    async def extract_with_improvement(
        self, 
        html_content: str, 
        company_cik: str, 
        company_name: str, 
        year: int,
        max_iterations: int = 3
    ) -> Dict[str, Any]:
        """
        Main method: Extract compensation data with self-improvement.
        
        This method uses the self-improving code pattern to:
        1. Test current extraction implementation
        2. Evaluate results
        3. Improve code if needed
        4. Repeat until satisfactory results
        """
        
        logger.info("Starting self-improving extraction",
                   company=company_name, year=year, max_iterations=max_iterations)
        
        # Create test function for this specific extraction
        async def test_extraction(test_data):
            extractor = AdaptiveCompensationExtractor()
            results = await extractor.extract_compensation(
                test_data['html_content'],
                test_data['company_cik'],
                test_data['company_name'],
                test_data['year']
            )
            
            # Convert to serializable format for evaluation
            serializable_results = []
            for comp in results:
                serializable_results.append({
                    'name': comp.executive_name,
                    'title': comp.title,
                    'total_compensation': float(comp.total_compensation),
                    'salary': float(comp.salary) if comp.salary else 0,
                    'bonus': float(comp.bonus) if comp.bonus else 0,
                    'stock_awards': float(comp.stock_awards) if comp.stock_awards else 0,
                    'option_awards': float(comp.option_awards) if comp.option_awards else 0
                })
            
            return {
                'executives': serializable_results,
                'count': len(serializable_results),
                'company': test_data['company_name'],
                'year': test_data['year']
            }
        
        # Test data for this extraction
        test_data = {
            'html_content': html_content,
            'company_cik': company_cik,
            'company_name': company_name,
            'year': year
        }
        
        # Run the self-improving code pattern
        improvement_results = await self.self_improving_code.improve_code(
            test_function=test_extraction,
            test_data=test_data,
            max_iterations=max_iterations
        )
        
        # Get final extraction results
        final_extractor = AdaptiveCompensationExtractor()
        final_compensations = await final_extractor.extract_compensation(
            html_content, company_cik, company_name, year
        )
        
        return {
            'compensations': final_compensations,
            'improvement_process': improvement_results,
            'final_count': len(final_compensations),
            'iterations_used': improvement_results.get('total_iterations', 0),
            'improvements_made': improvement_results.get('improvements_made', []),
            'final_success': improvement_results.get('final_success', False)
        }
    
    async def _supervisor_llm_call(self, prompt: str) -> str:
        """Supervisor LLM call - evaluates extraction results."""
        
        messages = [
            {
                "role": "system", 
                "content": "You are the SUPERVISOR in a self-improving code system. You evaluate executive compensation extraction results and determine if the extraction code needs improvement. You are an expert financial analyst who knows real executives and compensation patterns."
            },
            {
                "role": "user", 
                "content": prompt
            }
        ]
        
        # Use Grok for supervision (evaluation)
        response = await self.llm_service._make_llm_request(
            messages, temperature=0.1, max_tokens=2000
        )
        
        return response
    
    async def _engineer_llm_call(self, prompt: str) -> str:
        """Engineer LLM call - implements code improvements."""
        
        messages = [
            {
                "role": "system", 
                "content": "You are the ENGINEER in a self-improving code system. You implement specific code improvements to executive compensation extraction logic based on supervisor evaluation. You are an expert Python developer who writes clean, efficient code."
            },
            {
                "role": "user", 
                "content": prompt
            }
        ]
        
        # Use Claude for engineering (code writing)
        # Temporarily switch to engineer model
        original_model = self.llm_service.primary_model
        self.llm_service.primary_model = "anthropic/claude-3.5-sonnet"
        
        try:
            response = await self.llm_service._make_llm_request(
                messages, temperature=0.1, max_tokens=4000
            )
        finally:
            # Restore original model
            self.llm_service.primary_model = original_model
        
        return response
