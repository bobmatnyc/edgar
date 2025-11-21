"""
Example: Using Self-Improving Code Library for EDGAR Extraction

This demonstrates how to use the reusable library for executive
compensation extraction with domain-specific QA and improvements.
"""

import asyncio
from typing import Dict, Any, List
import sys
import os

# Add parent directories to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from self_improving_code import SelfImprovingController, LLMSupervisor, LLMEngineer
from edgar_analyzer.services.llm_service import LLMService
from edgar_analyzer.extractors.adaptive_compensation_extractor import AdaptiveCompensationExtractor


class EdgarExtractionExample:
    """
    Example implementation using the Self-Improving Code library
    for EDGAR executive compensation extraction.
    """
    
    def __init__(self):
        """Initialize the example with EDGAR-specific configuration."""
        
        # Initialize LLM service
        self.llm_service = LLMService()
        
        # Create domain-specific supervisor (Grok for financial QA)
        self.supervisor = LLMSupervisor(
            llm_client=self._grok_llm_call,
            model_name="grok-4.1-fast",
            domain_expertise="executive compensation and SEC filings analysis",
            quality_standards={
                "pass_threshold": 0.8,
                "conditional_threshold": 0.6,
                "fail_threshold": 0.0
            }
        )
        
        # Create domain-specific engineer (Claude for Python coding)
        self.engineer = LLMEngineer(
            llm_client=self._claude_llm_call,
            model_name="claude-3.5-sonnet",
            programming_language="Python",
            coding_standards={
                "max_function_length": 50,
                "prefer_composition": True,
                "require_docstrings": True,
                "follow_pep8": True
            }
        )
        
        # Define files that can be modified
        target_files = [
            "src/edgar_analyzer/extractors/adaptive_compensation_extractor.py"
        ]
        
        # Define files that must be protected
        protected_files = [
            "src/self_improving_code/core/controller.py",
            "src/self_improving_code/llm/supervisor.py",
            "src/self_improving_code/llm/engineer.py"
        ]
        
        # Initialize the self-improving controller
        self.controller = SelfImprovingController(
            supervisor_llm=self.supervisor,
            engineer_llm=self.engineer,
            target_files=target_files,
            protected_files=protected_files
        )
    
    async def _grok_llm_call(self, messages: List[Dict[str, str]]) -> str:
        """LLM call for Grok (Supervisor + QA)."""
        return await self.llm_service._make_llm_request(
            messages, temperature=0.1, max_tokens=2000
        )
    
    async def _claude_llm_call(self, messages: List[Dict[str, str]]) -> str:
        """LLM call for Claude (Engineer)."""
        # Temporarily switch to Claude
        original_model = self.llm_service.primary_model
        self.llm_service.primary_model = "anthropic/claude-3.5-sonnet"
        
        try:
            return await self.llm_service._make_llm_request(
                messages, temperature=0.1, max_tokens=4000
            )
        finally:
            self.llm_service.primary_model = original_model
    
    async def extract_with_improvement(
        self, 
        html_content: str, 
        company_cik: str, 
        company_name: str, 
        year: int,
        max_iterations: int = 3
    ) -> Dict[str, Any]:
        """
        Extract executive compensation with self-improvement.
        
        This is the main method that demonstrates using the library
        for a specific domain (EDGAR extraction).
        """
        
        # Define the test function
        async def test_extraction(test_data):
            extractor = AdaptiveCompensationExtractor()
            results = await extractor.extract_compensation(
                test_data['html_content'],
                test_data['company_cik'],
                test_data['company_name'],
                test_data['year']
            )
            
            # Convert to serializable format
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
        
        # Test data
        test_data = {
            'html_content': html_content,
            'company_cik': company_cik,
            'company_name': company_name,
            'year': year
        }
        
        # Domain-specific context for LLMs
        context = {
            'domain': 'SEC EDGAR executive compensation extraction',
            'requirements': f'Extract authentic executive compensation data for {company_name} ({year})',
            'quality_standards': 'Professional financial analysis standards',
            'data_sources': 'SEC DEF 14A proxy statements',
            'expected_executives': ['CEO', 'CFO', 'COO', 'General Counsel', 'Other Named Executive Officers']
        }
        
        # Run the self-improving process
        result = await self.controller.improve_implementation(
            test_function=test_extraction,
            test_data=test_data,
            context=context,
            max_iterations=max_iterations
        )
        
        # Get final extraction results
        final_extractor = AdaptiveCompensationExtractor()
        final_compensations = await final_extractor.extract_compensation(
            html_content, company_cik, company_name, year
        )
        
        return {
            'compensations': final_compensations,
            'improvement_process': result,
            'final_count': len(final_compensations),
            'iterations_used': result.total_iterations,
            'improvements_made': result.improvements_made,
            'final_success': result.final_success
        }
