#!/usr/bin/env python3
"""
Model Configuration Service

PURPOSE:
    Centralized configuration for different models optimized for specific tasks.
    Provides intelligent model selection based on use case and requirements.

FUNCTION:
    Model configuration management:
    - Task-specific model selection
    - Performance optimization per use case
    - Cost-aware model routing
    - Capability-based model assignment

USAGE:
    from edgar_analyzer.services.model_config import ModelConfigService
    
    config = ModelConfigService()
    model = config.get_model_for_task("coding")
    # Returns: "anthropic/claude-4.5-sonnet"

MODIFICATION HISTORY:
    2025-11-21 System - Initial creation
    - WHY: Optimize model selection for different tasks
    - HOW: Task-specific model configuration and routing
    - IMPACT: Better performance and cost optimization

DEPENDENCIES:
    - Environment configuration
    - OpenRouter service compatibility

AUTHOR: EDGAR CLI System
CREATED: 2025-11-21
LAST_MODIFIED: 2025-11-21
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import structlog

# Load environment variables
load_dotenv('.env.local')

logger = structlog.get_logger(__name__)


class ModelConfigService:
    """
    Centralized model configuration service for task-specific optimization.
    
    WHY: Different tasks benefit from different models with specific capabilities
    HOW: Maps tasks to optimal models based on performance and cost
    WHEN: Created 2025-11-21 for intelligent model selection
    """
    
    def __init__(self):
        """Initialize model configuration service."""
        
        # Task-specific model configurations
        self.task_models = {
            # Conversational interface - fast, free model for general chat
            "conversation": {
                "primary": os.getenv("PRIMARY_MODEL", "x-ai/grok-4.1-fast:free"),
                "fallback": os.getenv("FALLBACK_MODEL", "anthropic/claude-sonnet-4.5"),
                "description": "General conversation and user interaction"
            },

            # Coding tasks - Claude Sonnet 4.5 for advanced coding capabilities
            "coding": {
                "primary": "anthropic/claude-sonnet-4.5",
                "fallback": "anthropic/claude-3.5-sonnet",
                "description": "Code generation, review, and engineering tasks"
            },

            # Quality assurance - Grok for fast, reliable QA
            "qa_supervision": {
                "primary": "x-ai/grok-4.1-fast:free",
                "fallback": "anthropic/claude-sonnet-4.5",
                "description": "Quality assurance and result validation"
            },

            # Analysis tasks - balanced model for data analysis
            "analysis": {
                "primary": os.getenv("PRIMARY_MODEL", "x-ai/grok-4.1-fast:free"),
                "fallback": "anthropic/claude-sonnet-4.5",
                "description": "Data analysis and interpretation"
            },

            # Web search enhanced tasks - models with web search capabilities
            "web_search": {
                "primary": "anthropic/claude-sonnet-4.5",
                "fallback": "x-ai/grok-4.1-fast:free",
                "description": "Tasks requiring real-time information access"
            }
        }
        
        # Model capabilities and characteristics
        self.model_info = {
            "x-ai/grok-4.1-fast:free": {
                "cost": "free",
                "speed": "fast",
                "context": 131072,
                "strengths": ["conversation", "general_analysis", "speed"],
                "web_search": True
            },
            "anthropic/claude-sonnet-4.5": {
                "cost": "premium",
                "speed": "medium",
                "context": 1000000,
                "strengths": ["coding", "agentic_workflows", "tool_orchestration", "extended_reasoning"],
                "web_search": True
            },
            "anthropic/claude-3.5-sonnet": {
                "cost": "paid",
                "speed": "medium",
                "context": 200000,
                "strengths": ["coding", "analysis", "reasoning"],
                "web_search": True
            }
        }
        
        logger.info("Model configuration service initialized",
                   tasks_configured=len(self.task_models),
                   models_available=len(self.model_info))
    
    def get_model_for_task(self, task: str, prefer_fallback: bool = False) -> str:
        """
        Get the optimal model for a specific task.
        
        Args:
            task: Task type (conversation, coding, qa_supervision, analysis, web_search)
            prefer_fallback: Whether to prefer fallback model over primary
        
        Returns:
            Model identifier string
        """
        if task not in self.task_models:
            logger.warning(f"Unknown task type: {task}, using conversation default")
            task = "conversation"
        
        config = self.task_models[task]
        model = config["fallback"] if prefer_fallback else config["primary"]
        
        logger.debug("Model selected for task",
                    task=task,
                    model=model,
                    prefer_fallback=prefer_fallback)
        
        return model
    
    def get_task_config(self, task: str) -> Dict[str, Any]:
        """Get complete configuration for a task."""
        return self.task_models.get(task, self.task_models["conversation"])
    
    def get_model_info(self, model: str) -> Dict[str, Any]:
        """Get information about a specific model."""
        return self.model_info.get(model, {
            "cost": "unknown",
            "speed": "unknown",
            "context": 4096,
            "strengths": [],
            "web_search": False
        })
    
    def get_models_for_strength(self, strength: str) -> list:
        """Get all models that have a specific strength."""
        models = []
        for model, info in self.model_info.items():
            if strength in info.get("strengths", []):
                models.append(model)
        return models
    
    def get_best_model_for_context_size(self, required_context: int) -> str:
        """Get the best model that can handle the required context size."""
        suitable_models = []
        for model, info in self.model_info.items():
            if info.get("context", 0) >= required_context:
                suitable_models.append((model, info))
        
        if not suitable_models:
            logger.warning(f"No model found for context size {required_context}, using default")
            return self.get_model_for_task("conversation")
        
        # Sort by cost (free < paid < premium) and context size
        cost_order = {"free": 0, "paid": 1, "premium": 2}
        suitable_models.sort(key=lambda x: (cost_order.get(x[1].get("cost", "premium"), 3), -x[1].get("context", 0)))
        
        return suitable_models[0][0]
    
    def recommend_model_for_use_case(self, 
                                   use_case: str,
                                   context_size: Optional[int] = None,
                                   cost_preference: str = "balanced",
                                   web_search_required: bool = False) -> str:
        """
        Recommend the best model for a specific use case with constraints.
        
        Args:
            use_case: Description of the use case
            context_size: Required context window size
            cost_preference: "free", "paid", "premium", or "balanced"
            web_search_required: Whether web search capability is required
        
        Returns:
            Recommended model identifier
        """
        # Map use case to task type
        use_case_lower = use_case.lower()
        if any(keyword in use_case_lower for keyword in ["code", "programming", "engineer", "development"]):
            task = "coding"
        elif any(keyword in use_case_lower for keyword in ["qa", "quality", "test", "validation"]):
            task = "qa_supervision"
        elif any(keyword in use_case_lower for keyword in ["search", "web", "current", "real-time"]):
            task = "web_search"
        elif any(keyword in use_case_lower for keyword in ["analysis", "analyze", "data"]):
            task = "analysis"
        else:
            task = "conversation"
        
        # Get base recommendation
        model = self.get_model_for_task(task)
        
        # Apply constraints
        if context_size:
            context_model = self.get_best_model_for_context_size(context_size)
            if context_model != model:
                logger.info(f"Switching from {model} to {context_model} for context size {context_size}")
                model = context_model
        
        if web_search_required:
            model_info = self.get_model_info(model)
            if not model_info.get("web_search", False):
                web_search_models = [m for m, info in self.model_info.items() if info.get("web_search", False)]
                if web_search_models:
                    model = web_search_models[0]
                    logger.info(f"Switching to {model} for web search requirement")
        
        logger.info("Model recommended",
                   use_case=use_case,
                   task=task,
                   model=model,
                   context_size=context_size,
                   cost_preference=cost_preference,
                   web_search_required=web_search_required)
        
        return model
