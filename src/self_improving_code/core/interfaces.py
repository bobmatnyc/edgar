"""
Abstract interfaces for the Self-Improving Code pattern.

These interfaces define the contracts that users must implement
to use the library with their specific use cases.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass
from datetime import datetime

# Type aliases for clarity
TestFunction = Callable[[Any], Any]  # Function that tests the current implementation
QualityEvaluator = Callable[[Any], Dict[str, Any]]  # Function that evaluates test results


@dataclass
class ImprovementResult:
    """Result of an improvement iteration."""
    iteration: int
    test_results: Dict[str, Any]
    evaluation: Dict[str, Any]
    code_changed: bool
    files_modified: List[str]
    checkpoint_id: Optional[str]
    success: bool
    error: Optional[str] = None


@dataclass
class FinalResult:
    """Final result of the improvement process."""
    iterations: List[ImprovementResult]
    final_success: bool
    total_iterations: int
    improvements_made: List[str]
    final_test_results: Dict[str, Any]


class SupervisorLLM(ABC):
    """Abstract interface for Supervisor + QA LLM."""
    
    @abstractmethod
    async def evaluate_results(
        self, 
        test_results: Dict[str, Any], 
        iteration: int,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate test results and determine if improvement is needed.
        
        Args:
            test_results: Results from running the test function
            iteration: Current iteration number
            context: Additional context (domain, requirements, etc.)
            
        Returns:
            Evaluation dict with keys:
            - needs_improvement: bool
            - quality_score: float (0.0-1.0)
            - qa_status: str ("PASS", "FAIL", "CONDITIONAL")
            - issues_found: List[str]
            - improvement_directions: List[str]
            - confidence: float
        """
        pass


class EngineerLLM(ABC):
    """Abstract interface for Engineer LLM."""
    
    @abstractmethod
    async def implement_improvements(
        self,
        evaluation: Dict[str, Any],
        test_results: Dict[str, Any],
        current_code: Dict[str, str],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Implement code improvements based on evaluation.
        
        Args:
            evaluation: Supervisor evaluation results
            test_results: Original test results
            current_code: Dict of {file_path: file_content}
            context: Additional context
            
        Returns:
            Changes dict with keys:
            - changes_made: bool
            - files_modified: List[str]
            - changes: Dict[str, Dict] # file_path -> change_info
            - summary: str
        """
        pass


class TestRunner(ABC):
    """Abstract interface for running tests."""
    
    @abstractmethod
    async def run_test(self, test_function: TestFunction, test_data: Any) -> Dict[str, Any]:
        """Run a test function and return structured results."""
        pass


class CodeModifier(ABC):
    """Abstract interface for modifying code files."""
    
    @abstractmethod
    def apply_changes(self, changes: Dict[str, Any]) -> List[str]:
        """Apply code changes and return list of modified files."""
        pass


class SafetyManager(ABC):
    """Abstract interface for safety mechanisms."""
    
    @abstractmethod
    def create_checkpoint(self, message: str) -> str:
        """Create a safety checkpoint and return checkpoint ID."""
        pass
    
    @abstractmethod
    def rollback_to_checkpoint(self, checkpoint_id: str) -> bool:
        """Rollback to a checkpoint. Returns success status."""
        pass
