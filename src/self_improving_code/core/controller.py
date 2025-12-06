"""
Self-Improving Controller - Reusable Library Implementation

This is the main controller that implements the Self-Improving Code pattern
as a reusable library that can be applied to any project.
"""

import asyncio
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog

from ..safety.git_manager import GitSafetyManager
from .interfaces import (
    CodeModifier,
    EngineerLLM,
    FinalResult,
    ImprovementResult,
    SafetyManager,
    SupervisorLLM,
    TestFunction,
    TestRunner,
)

logger = structlog.get_logger(__name__)


class DefaultTestRunner(TestRunner):
    """Default implementation of TestRunner."""

    async def run_test(
        self, test_function: TestFunction, test_data: Any
    ) -> Dict[str, Any]:
        """Run test function and capture results."""
        try:
            start_time = datetime.now()

            if asyncio.iscoroutinefunction(test_function):
                result = await test_function(test_data)
            else:
                result = test_function(test_data)

            end_time = datetime.now()

            return {
                "success": True,
                "result": result,
                "execution_time": (end_time - start_time).total_seconds(),
                "timestamp": start_time.isoformat(),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }


class DefaultCodeModifier(CodeModifier):
    """Default implementation of CodeModifier."""

    def apply_changes(self, changes: Dict[str, Any]) -> List[str]:
        """Apply code changes to files."""
        files_modified = []

        for file_path, change_info in changes.get("changes", {}).items():
            try:
                self._apply_file_change(file_path, change_info)
                files_modified.append(file_path)

                logger.info(
                    "Applied code change",
                    file=file_path,
                    reason=change_info.get("reason", "No reason provided"),
                )

            except Exception as e:
                logger.error(
                    "Failed to apply code change", file=file_path, error=str(e)
                )

        return files_modified

    def _apply_file_change(self, file_path: str, change_info: Dict[str, Any]):
        """Apply a specific change to a file."""
        with open(file_path, "r") as f:
            lines = f.readlines()

        if "line_range" in change_info:
            # Replace specific lines
            start_line, end_line = change_info["line_range"]
            start_idx = start_line - 1  # Convert to 0-based
            end_idx = end_line

            new_code_lines = change_info["new_code"].split("\n")
            new_code_lines = [line + "\n" for line in new_code_lines[:-1]] + [
                new_code_lines[-1]
            ]

            lines[start_idx:end_idx] = new_code_lines
        else:
            # Replace entire file
            lines = change_info["new_code"].split("\n")
            lines = [line + "\n" for line in lines[:-1]] + [lines[-1]]

        with open(file_path, "w") as f:
            f.writelines(lines)


class SelfImprovingController:
    """
    REUSABLE LIBRARY: Self-Improving Code Controller

    This controller can be used in any project to implement the
    self-improving code pattern with LLM-based QA and engineering.
    """

    def __init__(
        self,
        supervisor_llm: SupervisorLLM,
        engineer_llm: EngineerLLM,
        target_files: List[str],
        protected_files: List[str] = None,
        safety_manager: Optional[SafetyManager] = None,
        test_runner: Optional[TestRunner] = None,
        code_modifier: Optional[CodeModifier] = None,
    ):
        """
        Initialize the self-improving controller.

        Args:
            supervisor_llm: LLM for evaluation and QA
            engineer_llm: LLM for code generation
            target_files: Files that can be modified
            protected_files: Files that cannot be modified
            safety_manager: Safety mechanism (defaults to Git)
            test_runner: Test execution handler
            code_modifier: Code modification handler
        """
        self.supervisor_llm = supervisor_llm
        self.engineer_llm = engineer_llm
        self.target_files = target_files
        self.protected_files = protected_files or []

        # Use default implementations if not provided
        self.safety_manager = safety_manager or GitSafetyManager()
        self.test_runner = test_runner or DefaultTestRunner()
        self.code_modifier = code_modifier or DefaultCodeModifier()

        logger.info(
            "Self-Improving Controller initialized",
            target_files=len(self.target_files),
            protected_files=len(self.protected_files),
        )

    async def improve_implementation(
        self,
        test_function: TestFunction,
        test_data: Any,
        context: Dict[str, Any] = None,
        max_iterations: int = 3,
    ) -> FinalResult:
        """
        Main method: Improve implementation through iterative testing and refinement.

        Args:
            test_function: Function to test current implementation
            test_data: Data to test with
            context: Additional context for LLMs (domain, requirements, etc.)
            max_iterations: Maximum improvement iterations

        Returns:
            FinalResult with complete improvement process details
        """
        context = context or {}
        iterations = []

        logger.info(
            "Starting self-improving process",
            max_iterations=max_iterations,
            context_keys=list(context.keys()),
        )

        for iteration in range(max_iterations):
            logger.info(f"Starting iteration {iteration + 1}/{max_iterations}")

            # Step 1: Run test
            test_results = await self.test_runner.run_test(test_function, test_data)

            # Step 2: Supervisor evaluation + QA
            evaluation = await self.supervisor_llm.evaluate_results(
                test_results, iteration, context
            )

            iteration_result = ImprovementResult(
                iteration=iteration + 1,
                test_results=test_results,
                evaluation=evaluation,
                code_changed=False,
                files_modified=[],
                checkpoint_id=None,
                success=False,
            )

            # Step 3: Check if improvement needed
            if not evaluation.get("needs_improvement", True):
                logger.info("Supervisor determined no improvement needed")
                iteration_result.success = True
                iterations.append(iteration_result)
                break

            # Step 4: Create safety checkpoint
            try:
                checkpoint_id = self.safety_manager.create_checkpoint(
                    f"Self-improving iteration {iteration + 1}"
                )
                iteration_result.checkpoint_id = checkpoint_id

                # Step 5: Engineer implements improvements
                current_code = self._read_current_code()

                changes = await self.engineer_llm.implement_improvements(
                    evaluation, test_results, current_code, context
                )

                if changes.get("changes_made", False):
                    # Apply changes
                    files_modified = self.code_modifier.apply_changes(changes)

                    iteration_result.code_changed = True
                    iteration_result.files_modified = files_modified
                    iteration_result.success = True

                    logger.info(
                        "Code improvements applied", files_modified=len(files_modified)
                    )
                else:
                    logger.warning("Engineer could not implement improvements")

            except Exception as e:
                logger.error(
                    "Error during improvement iteration",
                    iteration=iteration + 1,
                    error=str(e),
                )

                # Rollback on error
                if iteration_result.checkpoint_id:
                    self.safety_manager.rollback_to_checkpoint(
                        iteration_result.checkpoint_id
                    )

                iteration_result.error = str(e)

            iterations.append(iteration_result)

        # Final test to get end results
        final_test_results = await self.test_runner.run_test(test_function, test_data)

        return FinalResult(
            iterations=iterations,
            final_success=any(iter_result.success for iter_result in iterations),
            total_iterations=len(iterations),
            improvements_made=[
                f for iter_result in iterations for f in iter_result.files_modified
            ],
            final_test_results=final_test_results,
        )

    def _read_current_code(self) -> Dict[str, str]:
        """Read current code from target files."""
        current_code = {}

        for file_path in self.target_files:
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    current_code[file_path] = f.read()

        return current_code
