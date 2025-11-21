"""
LLM Engineer Implementation

This implements the Engineer role using any LLM that supports
code generation and modification.
"""

import json
from typing import Dict, Any, Callable, List
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
        coding_standards: Dict[str, Any] = None,
        enable_web_search: bool = False,
        web_search_client: Callable = None
    ):
        """
        Initialize LLM Engineer.

        WHY: Provides intelligent code improvement with optional web search
        HOW: Uses LLM for code generation with real-time best practices
        WHEN: Enhanced 2025-11-21 to add web search capabilities

        Args:
            llm_client: Function that takes messages and returns LLM response
            model_name: Name of the model for logging
            programming_language: Primary programming language
            coding_standards: Custom coding standards dict
            enable_web_search: Whether to enable web search for best practices
            web_search_client: Function for web search requests
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
        self.enable_web_search = enable_web_search
        self.web_search_client = web_search_client
        
        logger.info("LLM Engineer initialized", 
                   model=model_name, 
                   language=programming_language)
    
    async def implement_improvements(
        self,
        evaluation: Dict[str, Any],
        test_results: Dict[str, Any],
        current_code: Dict[str, str],
        context: Dict[str, Any],
        enable_search_for_best_practices: bool = False
    ) -> Dict[str, Any]:
        """
        Implement code improvements based on supervisor evaluation with optional web search.

        WHY: Provides intelligent code improvements with current best practices
        HOW: Uses LLM analysis enhanced with web search for latest standards
        WHEN: Enhanced 2025-11-21 to add web search for best practices

        Args:
            evaluation: Supervisor evaluation results
            test_results: Test results to improve
            current_code: Current code to modify
            context: Improvement context
            enable_search_for_best_practices: Whether to search for current best practices

        Returns:
            Implementation results with code changes
        """
        
        # Build context-aware prompt
        domain_context = context.get('domain', 'software development')
        requirements = context.get('requirements', 'general improvements')

        # Perform web search for best practices if enabled
        best_practices_context = ""
        if (enable_search_for_best_practices and
            self.enable_web_search and
            self.web_search_client):

            try:
                # Generate search queries for best practices
                search_queries = self._generate_best_practices_queries(
                    evaluation, domain_context, self.programming_language
                )

                if search_queries:
                    logger.info("Searching for current best practices",
                               queries=search_queries)

                    search_results = []
                    for query in search_queries[:2]:  # Limit to 2 searches
                        try:
                            result = await self.web_search_client(
                                query=query,
                                context=f"Finding best practices for {domain_context}"
                            )
                            search_results.append(f"Query: {query}\nBest Practices: {result}\n")
                        except Exception as e:
                            logger.warning("Best practices search failed",
                                         query=query, error=str(e))

                    if search_results:
                        best_practices_context = f"""
CURRENT BEST PRACTICES (from web search):
{''.join(search_results)}

Apply these current best practices and standards to your code improvements.
"""
            except Exception as e:
                logger.warning("Best practices search failed", error=str(e))
        
        prompt = f"""You are the ENGINEER in a self-improving code system with access to current best practices.

PROGRAMMING LANGUAGE: {self.programming_language}
MODEL: {self.model_name}
DOMAIN: {domain_context}
REQUIREMENTS: {requirements}

{best_practices_context}

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

    def _generate_best_practices_queries(
        self,
        evaluation: Dict[str, Any],
        domain_context: str,
        programming_language: str
    ) -> List[str]:
        """
        Generate web search queries for current best practices.

        WHY: Finds latest best practices and standards for code improvements
        HOW: Analyzes evaluation issues to generate targeted search queries
        WHEN: Created 2025-11-21 for web search best practices

        Args:
            evaluation: Supervisor evaluation with issues found
            domain_context: Domain context for targeted searches
            programming_language: Programming language for specific practices

        Returns:
            List of search queries for best practices
        """
        queries = []

        # Extract issues from evaluation
        issues = evaluation.get('issues_found', [])
        improvement_directions = evaluation.get('improvement_directions', [])

        # Generate queries based on specific issues
        for issue in issues[:3]:  # Limit to top 3 issues
            if 'performance' in issue.lower():
                queries.append(f"{programming_language} performance optimization best practices 2024")
            elif 'security' in issue.lower():
                queries.append(f"{programming_language} security best practices 2024")
            elif 'error handling' in issue.lower():
                queries.append(f"{programming_language} error handling best practices 2024")
            elif 'testing' in issue.lower():
                queries.append(f"{programming_language} testing best practices 2024")
            elif 'documentation' in issue.lower():
                queries.append(f"{programming_language} documentation standards 2024")

        # Generate queries based on improvement directions
        for direction in improvement_directions[:2]:  # Limit to top 2 directions
            if 'refactor' in direction.lower():
                queries.append(f"{programming_language} refactoring best practices 2024")
            elif 'optimize' in direction.lower():
                queries.append(f"{programming_language} code optimization techniques 2024")

        # Add domain-specific queries
        if domain_context and domain_context != 'software development':
            queries.append(f"{domain_context} {programming_language} best practices 2024")

        # Add general best practices query
        queries.append(f"{programming_language} coding standards best practices 2024")

        # Remove duplicates and limit
        return list(dict.fromkeys(queries))[:4]
