"""
Self-Improving Code Library

A reusable library implementing the "Self-Improving Code with LLM QA" pattern.

This library enables any codebase to:
1. Evaluate its own results using LLM-based QA
2. Automatically improve implementation code based on evaluation
3. Maintain safety through git-based rollback mechanisms
4. Separate immutable control logic from mutable implementation

Usage:
    from self_improving_code import SelfImprovingController
    
    controller = SelfImprovingController(
        supervisor_llm=your_supervisor_llm,
        engineer_llm=your_engineer_llm,
        target_files=["path/to/mutable/code.py"],
        protected_files=["path/to/control/code.py"]
    )
    
    results = await controller.improve_implementation(
        test_function=your_test_function,
        test_data=your_test_data,
        quality_evaluator=your_quality_evaluator
    )
"""

from .core.controller import SelfImprovingController
from .core.interfaces import (
    TestFunction,
    QualityEvaluator,
    SupervisorLLM,
    EngineerLLM,
    ImprovementResult
)
from .llm.supervisor import LLMSupervisor
from .llm.engineer import LLMEngineer
from .safety.git_manager import GitSafetyManager

__version__ = "1.0.0"
__author__ = "Self-Improving Code Pattern"

__all__ = [
    "SelfImprovingController",
    "TestFunction", 
    "QualityEvaluator",
    "SupervisorLLM",
    "EngineerLLM",
    "ImprovementResult",
    "LLMSupervisor",
    "LLMEngineer", 
    "GitSafetyManager"
]
