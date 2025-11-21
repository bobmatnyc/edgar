"""
Abstract interfaces for the CLI Chatbot Controller.

These interfaces define the contracts for building self-aware,
context-injected chatbot controllers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass
from datetime import datetime

# Type aliases
LLMClient = Callable[[List[Dict[str, str]]], str]  # Function that calls LLM
InputOutputModifier = Callable[[Any], Any]  # Function that modifies input/output


@dataclass
class ContextInfo:
    """Information about application context."""
    source: str  # File path or source identifier
    content_type: str  # 'function', 'class', 'module', 'docstring', etc.
    content: str  # The actual content
    relevance_score: float  # 0.0-1.0 relevance to current conversation
    last_updated: datetime
    metadata: Dict[str, Any]


@dataclass
class ScriptResult:
    """Result of dynamic script execution."""
    success: bool
    result: Any
    output: str
    error: Optional[str]
    execution_time: float
    side_effects: List[str]  # Files modified, network calls, etc.


class ContextProvider(ABC):
    """Abstract interface for providing application context."""
    
    @abstractmethod
    async def extract_context(
        self, 
        query: str, 
        application_root: str,
        max_contexts: int = 10
    ) -> List[ContextInfo]:
        """
        Extract relevant context from the application codebase.
        
        Args:
            query: User query or conversation context
            application_root: Root directory of the application
            max_contexts: Maximum number of contexts to return
            
        Returns:
            List of relevant context information
        """
        pass
    
    @abstractmethod
    async def get_controller_self_awareness(self) -> ContextInfo:
        """Get information about the controller itself."""
        pass


class ScriptExecutor(ABC):
    """Abstract interface for dynamic script execution."""
    
    @abstractmethod
    async def execute_script(
        self,
        script_code: str,
        context: Dict[str, Any],
        safety_checks: bool = True
    ) -> ScriptResult:
        """
        Execute dynamic script code with context.
        
        Args:
            script_code: Python code to execute
            context: Execution context and variables
            safety_checks: Whether to perform safety validation
            
        Returns:
            Script execution result
        """
        pass
    
    @abstractmethod
    def validate_script_safety(self, script_code: str) -> bool:
        """Validate that script code is safe to execute."""
        pass


class ConversationMemory(ABC):
    """Abstract interface for conversation memory management."""
    
    @abstractmethod
    async def add_exchange(
        self, 
        user_input: str, 
        controller_response: str,
        context_used: List[ContextInfo],
        scripts_executed: List[ScriptResult]
    ):
        """Add a conversation exchange to memory."""
        pass
    
    @abstractmethod
    async def get_conversation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation history."""
        pass
    
    @abstractmethod
    async def search_memory(self, query: str) -> List[Dict[str, Any]]:
        """Search conversation memory for relevant exchanges."""
        pass


class ChatbotPersonality(ABC):
    """Abstract interface for chatbot personality and behavior."""
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the base system prompt for the chatbot."""
        pass
    
    @abstractmethod
    def format_response(
        self, 
        raw_response: str, 
        context: List[ContextInfo],
        user_input: str
    ) -> str:
        """Format the raw LLM response for presentation."""
        pass
    
    @abstractmethod
    def should_execute_script(self, user_input: str, llm_response: str) -> bool:
        """Determine if dynamic script execution is appropriate."""
        pass
