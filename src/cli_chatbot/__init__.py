"""
CLI Chatbot Controller Library

A revolutionary replacement for traditional CLI patterns using an intelligent,
self-aware chatbot controller with dynamic context injection and scripting.

Features:
- Self-aware controller that understands both itself and the application
- Dynamic context injection from live codebase analysis
- Conversational interface replacing traditional CLI commands
- Runtime code generation and execution
- Dependency injection for input/output modification
- Real-time documentation extraction and awareness

Usage:
    from cli_chatbot import ChatbotController
    
    controller = ChatbotController(
        application_root="path/to/your/app",
        llm_client=your_llm_client,
        scripting_enabled=True
    )
    
    await controller.start_conversation()
"""

from .core.controller import ChatbotController
from .core.context_injector import DynamicContextInjector
from .core.scripting_engine import DynamicScriptingEngine
from .core.interfaces import (
    LLMClient,
    ContextProvider,
    ScriptExecutor,
    InputOutputModifier
)
from .fallback.traditional_cli import TraditionalCLI, create_fallback_cli

__version__ = "1.0.0"
__author__ = "CLI Chatbot Controller"

__all__ = [
    "ChatbotController",
    "DynamicContextInjector",
    "DynamicScriptingEngine",
    "LLMClient",
    "ContextProvider",
    "ScriptExecutor",
    "InputOutputModifier",
    "TraditionalCLI",
    "create_fallback_cli"
]
