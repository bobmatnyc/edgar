"""
Self-Improving Code Pattern

A coding pattern where:
1. Control Layer (immutable) - evaluates results and directs changes
2. Implementation Layer (mutable) - code that can be modified
3. Safety Layer - git-based rollback mechanism
4. Feedback Loop - continuous improvement through evaluation

This is a SOFTWARE ENGINEERING PATTERN that uses LLMs as tools.
"""

import os
import subprocess
import json
import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import structlog
from pathlib import Path

logger = structlog.get_logger(__name__)


class SelfImprovingCode:
    """
    CODING PATTERN: Self-Improving Code with LLM Supervision
    
    This pattern allows code to evaluate its own results and improve itself
    while maintaining safety through git version control.
    """
    
    def __init__(
        self, 
        supervisor_llm: Callable,  # LLM for evaluation
        engineer_llm: Callable,    # LLM for code generation
        target_files: List[str],   # Files that can be modified
        protected_files: List[str] = None  # Files that cannot be modified
    ):
        self.supervisor_llm = supervisor_llm
        self.engineer_llm = engineer_llm
        self.target_files = target_files
        self.protected_files = protected_files or []
        
        # Ensure we're in a git repository
        self._ensure_git_repo()
        
        logger.info("Self-Improving Code Pattern initialized",
                   target_files=len(target_files),
                   protected_files=len(self.protected_files))
    
    def _ensure_git_repo(self):
        """Ensure we're in a git repository for safety."""
        try:
            subprocess.run(['git', 'status'], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            raise RuntimeError("Must be in a git repository for safety")
    
    def _create_checkpoint(self, message: str) -> str:
        """Create a git checkpoint before making changes."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        branch_name = f"self_improve_{timestamp}"
        
        try:
            # Create and switch to new branch
            subprocess.run(['git', 'checkout', '-b', branch_name], check=True, capture_output=True)
            
            # Commit current state
            subprocess.run(['git', 'add', '.'], check=True, capture_output=True)
            subprocess.run(['git', 'commit', '-m', f"Checkpoint: {message}"], 
                         check=True, capture_output=True)
            
            logger.info("Git checkpoint created", branch=branch_name, message=message)
            return branch_name
            
        except subprocess.CalledProcessError as e:
            logger.error("Failed to create git checkpoint", error=str(e))
            raise
    
    def _rollback_to_checkpoint(self, branch_name: str):
        """Rollback to a previous checkpoint."""
        try:
            subprocess.run(['git', 'checkout', 'main'], check=True, capture_output=True)
            subprocess.run(['git', 'branch', '-D', branch_name], check=True, capture_output=True)
            logger.info("Rolled back to main branch", deleted_branch=branch_name)
        except subprocess.CalledProcessError as e:
            logger.error("Failed to rollback", error=str(e))
            raise
    
    async def improve_code(
        self, 
        test_function: Callable,
        test_data: Any,
        max_iterations: int = 3
    ) -> Dict[str, Any]:
        """
        Main pattern implementation: Test -> Evaluate -> Improve -> Repeat
        
        Args:
            test_function: Function to test the current implementation
            test_data: Data to test with
            max_iterations: Maximum improvement iterations
            
        Returns:
            Results of the improvement process
        """
        
        results = {
            'iterations': [],
            'final_success': False,
            'total_iterations': 0,
            'improvements_made': []
        }
        
        for iteration in range(max_iterations):
            logger.info(f"Starting improvement iteration {iteration + 1}/{max_iterations}")
            
            # Step 1: Test current implementation
            test_results = await self._run_test(test_function, test_data)
            
            # Step 2: Supervisor evaluates results
            evaluation = await self._supervisor_evaluate(test_results, iteration)
            
            iteration_result = {
                'iteration': iteration + 1,
                'test_results': test_results,
                'evaluation': evaluation,
                'code_changed': False,
                'checkpoint': None
            }
            
            # Step 3: Check if improvement is needed
            if not evaluation.get('needs_improvement', True):
                logger.info("Supervisor determined no improvement needed")
                iteration_result['success'] = True
                results['iterations'].append(iteration_result)
                results['final_success'] = True
                break
            
            # Step 4: Create safety checkpoint
            checkpoint = self._create_checkpoint(f"iteration_{iteration + 1}")
            iteration_result['checkpoint'] = checkpoint
            
            try:
                # Step 5: Engineer implements improvements
                code_changes = await self._engineer_improve(evaluation, test_results)
                
                if code_changes.get('changes_made', False):
                    iteration_result['code_changed'] = True
                    iteration_result['changes'] = code_changes
                    results['improvements_made'].extend(code_changes.get('files_modified', []))
                    
                    logger.info("Code improvements implemented",
                               files_modified=len(code_changes.get('files_modified', [])))
                else:
                    logger.warning("Engineer could not implement improvements")
                    iteration_result['success'] = False
                    
            except Exception as e:
                logger.error("Error during code improvement", error=str(e))
                self._rollback_to_checkpoint(checkpoint)
                iteration_result['error'] = str(e)
                iteration_result['rolled_back'] = True
            
            results['iterations'].append(iteration_result)
            results['total_iterations'] = iteration + 1
        
        return results
    
    async def _run_test(self, test_function: Callable, test_data: Any) -> Dict[str, Any]:
        """Run the test function and capture results."""
        try:
            start_time = datetime.now()
            result = await test_function(test_data) if asyncio.iscoroutinefunction(test_function) else test_function(test_data)
            end_time = datetime.now()
            
            return {
                'success': True,
                'result': result,
                'execution_time': (end_time - start_time).total_seconds(),
                'timestamp': start_time.isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def _supervisor_evaluate(self, test_results: Dict[str, Any], iteration: int) -> Dict[str, Any]:
        """Supervisor evaluates test results and determines if improvement is needed."""

        evaluation_prompt = f"""You are the SUPERVISOR in a self-improving code pattern.

CURRENT ITERATION: {iteration + 1}
TEST RESULTS: {json.dumps(test_results, indent=2)}

Your job is to evaluate these test results and determine if the code needs improvement.

EVALUATION CRITERIA:
1. Did the test succeed?
2. Are the results of acceptable quality?
3. Are there obvious errors or issues?
4. Is performance acceptable?

DECISION FRAMEWORK:
- If results are acceptable: needs_improvement = false
- If results have issues: needs_improvement = true

Provide specific, actionable feedback for the engineer.

OUTPUT (JSON only):
{{
  "needs_improvement": true,
  "quality_score": 0.6,
  "issues_found": [
    "Specific issue 1",
    "Specific issue 2"
  ],
  "improvement_directions": [
    "Fix parsing logic for edge cases",
    "Improve error handling"
  ],
  "priority": "high",
  "confidence": 0.9
}}"""

        try:
            response = await self.supervisor_llm(evaluation_prompt)
            evaluation = json.loads(response)

            logger.info("Supervisor evaluation complete",
                       needs_improvement=evaluation.get('needs_improvement'),
                       quality_score=evaluation.get('quality_score', 0))

            return evaluation

        except Exception as e:
            logger.error("Supervisor evaluation failed", error=str(e))
            return {
                "needs_improvement": True,
                "quality_score": 0.0,
                "issues_found": [f"Evaluation error: {str(e)}"],
                "improvement_directions": ["Manual review required"],
                "priority": "high",
                "confidence": 0.0
            }

    async def _engineer_improve(self, evaluation: Dict[str, Any], test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Engineer implements code improvements based on supervisor evaluation."""

        # Read current code from target files
        current_code = {}
        for file_path in self.target_files:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    current_code[file_path] = f.read()

        improvement_prompt = f"""You are the ENGINEER in a self-improving code pattern.

SUPERVISOR EVALUATION: {json.dumps(evaluation, indent=2)}
TEST RESULTS: {json.dumps(test_results, indent=2)}

CURRENT CODE:
{json.dumps(current_code, indent=2)}

Your job is to implement specific code improvements based on the supervisor's evaluation.

CONSTRAINTS:
1. Only modify files in the target_files list
2. Do not modify protected files
3. Make minimal, focused changes
4. Preserve existing functionality while fixing issues

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
      "reason": "Fixed parsing logic for edge cases"
    }}
  }},
  "summary": "Brief description of changes made"
}}

If no improvements can be made, return changes_made: false"""

        try:
            response = await self.engineer_llm(improvement_prompt)
            changes = json.loads(response)

            if changes.get('changes_made', False):
                # Apply the changes
                files_modified = []
                for file_path, change_info in changes.get('changes', {}).items():
                    if file_path in self.target_files and file_path not in self.protected_files:
                        self._apply_code_change(file_path, change_info)
                        files_modified.append(file_path)

                changes['files_modified'] = files_modified

                logger.info("Engineer implemented improvements",
                           files_modified=len(files_modified))

            return changes

        except Exception as e:
            logger.error("Engineer improvement failed", error=str(e))
            return {
                "changes_made": False,
                "error": str(e)
            }

    def _apply_code_change(self, file_path: str, change_info: Dict[str, Any]):
        """Apply a specific code change to a file."""
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()

            # If line_range is specified, replace those lines
            if 'line_range' in change_info:
                start_line, end_line = change_info['line_range']
                start_idx = start_line - 1  # Convert to 0-based indexing
                end_idx = end_line

                new_code_lines = change_info['new_code'].split('\n')
                # Add newlines back
                new_code_lines = [line + '\n' for line in new_code_lines[:-1]] + [new_code_lines[-1]]

                # Replace the lines
                lines[start_idx:end_idx] = new_code_lines
            else:
                # Replace entire file content
                lines = change_info['new_code'].split('\n')
                lines = [line + '\n' for line in lines[:-1]] + [lines[-1]]

            # Write back to file
            with open(file_path, 'w') as f:
                f.writelines(lines)

            logger.info("Applied code change",
                       file=file_path,
                       reason=change_info.get('reason', 'No reason provided'))

        except Exception as e:
            logger.error("Failed to apply code change", file=file_path, error=str(e))
            raise
