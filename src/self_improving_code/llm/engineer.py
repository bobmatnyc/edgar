"""
LLM Engineer Implementation

This implements the Engineer role using any LLM that supports
code generation and modification.
"""

import json
from typing import Dict, Any, Callable
import structlog

from ..core.interfaces import EngineerLLM

logger = structlog.get_logger(__name__)


class LLMEngineer(EngineerLLM):
    """
    LLM-based Engineer implementation.
    
    This class can work with any LLM that supports code generation
    (Claude, GPT-4, CodeLlama, etc.)
    """
    
    def __init__(
        self, 
        llm_client: Callable,
        model_name: str = "claude-3.5-sonnet",
        programming_language: str = "Python",
        coding_standards: Dict[str, Any] = None
    ):
        """
        Initialize LLM Engineer.
        
        Args:
            llm_client: Function that takes messages and returns LLM response
            model_name: Name of the model for logging
            programming_language: Primary programming language
            coding_standards: Custom coding standards dict
        """
        self.llm_client = llm_client
        self.model_name = model_name
        self.programming_language = programming_language
        self.coding_standards = coding_standards or {
            "max_function_length": 50,
            "prefer_composition": True,
            "require_docstrings": True,
            "follow_pep8": True
        }
        
        logger.info("LLM Engineer initialized", 
                   model=model_name, 
                   language=programming_language)
    
    async def implement_improvements(
        self,
        evaluation: Dict[str, Any],
        test_results: Dict[str, Any],
        current_code: Dict[str, str],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Implement code improvements based on supervisor evaluation."""
        
        # Build context-aware prompt
        domain_context = context.get('domain', 'software development')
        requirements = context.get('requirements', 'general improvements')
        
        prompt = f"""You are the ENGINEER in a self-improving code system.

PROGRAMMING LANGUAGE: {self.programming_language}
MODEL: {self.model_name}
DOMAIN: {domain_context}
REQUIREMENTS: {requirements}

SUPERVISOR EVALUATION:
{json.dumps(evaluation, indent=2)}

TEST RESULTS:
{json.dumps(test_results, indent=2)}

CURRENT CODE:
{json.dumps(current_code, indent=2)}

ENGINEERING TASK:
Implement specific code improvements based on the supervisor's evaluation and QA findings.

CODING STANDARDS:
{json.dumps(self.coding_standards, indent=2)}

CONSTRAINTS:
1. Make minimal, focused changes that address specific issues
2. Preserve existing functionality while fixing problems
3. Follow {self.programming_language} best practices
4. Add appropriate error handling and logging
5. Include clear comments explaining changes

IMPROVEMENT DIRECTIONS:
{json.dumps(evaluation.get('improvement_directions', []), indent=2)}

OUTPUT (JSON only):
{{
  "changes_made": true,
  "files_modified": ["path/to/file.py"],
  "changes": {{
    "path/to/file.py": {{
      "old_code": "original code snippet",
      "new_code": "improved code snippet", 
      "line_range": [10, 20],
      "reason": "Specific reason for this change"
    }}
  }},
  "summary": "Brief description of all changes made",
  "addresses_issues": ["Issue 1", "Issue 2"],
  "testing_notes": "How to test the changes"
}}

If no improvements can be made, return changes_made: false with explanation."""

        try:
            messages = [
                {
                    "role": "system", 
                    "content": f"You are an expert {self.programming_language} engineer using {self.model_name}. Write clean, maintainable, well-documented code that follows best practices."
                },
                {"role": "user", "content": prompt}
            ]
            
            response = await self.llm_client(messages)
            changes = self._parse_json_response(response)
            
            logger.info("Engineer implementation complete",
                       changes_made=changes.get('changes_made', False),
                       files_modified=len(changes.get('files_modified', [])))
            
            return changes
            
        except Exception as e:
            logger.error("Engineer implementation failed", error=str(e))
            return {
                "changes_made": False,
                "error": str(e),
                "summary": "Failed to implement improvements due to error"
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
