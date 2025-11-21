"""
Dynamic Context Injector

Automatically extracts relevant documentation and code context from the
application codebase to make the chatbot controller self-aware.
"""

import os
import ast
import inspect
import importlib.util
from typing import List, Dict, Any, Optional
from datetime import datetime
import structlog
from pathlib import Path

from .interfaces import ContextProvider, ContextInfo

logger = structlog.get_logger(__name__)


class DynamicContextInjector(ContextProvider):
    """
    Dynamic context injector that makes the chatbot aware of both
    itself and the application it's controlling.
    """
    
    def __init__(
        self,
        application_root: str,
        controller_root: str = None,
        file_extensions: List[str] = None,
        max_file_size: int = 100000  # 100KB max per file
    ):
        """
        Initialize the dynamic context injector.
        
        Args:
            application_root: Root directory of the application
            controller_root: Root directory of the controller (for self-awareness)
            file_extensions: File extensions to analyze
            max_file_size: Maximum file size to analyze
        """
        self.application_root = Path(application_root)
        self.controller_root = Path(controller_root) if controller_root else Path(__file__).parent.parent
        self.file_extensions = file_extensions or ['.py', '.md', '.txt', '.yaml', '.yml', '.json']
        self.max_file_size = max_file_size
        
        # Cache for parsed code structures
        self._code_cache = {}
        self._last_scan = None
        
        logger.info("Dynamic Context Injector initialized",
                   app_root=str(self.application_root),
                   controller_root=str(self.controller_root))
    
    async def extract_context(
        self, 
        query: str, 
        application_root: str = None,
        max_contexts: int = 10
    ) -> List[ContextInfo]:
        """Extract relevant context based on user query."""
        
        if application_root:
            self.application_root = Path(application_root)
        
        contexts = []
        
        # 1. Extract function and class definitions
        code_contexts = await self._extract_code_contexts(query, max_contexts // 2)
        contexts.extend(code_contexts)
        
        # 2. Extract documentation
        doc_contexts = await self._extract_documentation_contexts(query, max_contexts // 2)
        contexts.extend(doc_contexts)
        
        # 3. Sort by relevance and limit
        contexts.sort(key=lambda x: x.relevance_score, reverse=True)
        
        logger.info("Context extraction complete",
                   query_length=len(query),
                   contexts_found=len(contexts),
                   top_relevance=contexts[0].relevance_score if contexts else 0)
        
        return contexts[:max_contexts]
    
    async def get_controller_self_awareness(self) -> ContextInfo:
        """Get information about the controller itself."""
        
        # Read the controller's main files
        controller_info = []
        
        for py_file in self.controller_root.rglob("*.py"):
            if py_file.stat().st_size > self.max_file_size:
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract docstrings and key information
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef) and 'Controller' in node.name:
                        docstring = ast.get_docstring(node)
                        if docstring:
                            controller_info.append(f"Class {node.name}: {docstring}")
                    
                    elif isinstance(node, ast.FunctionDef) and node.name.startswith('_'):
                        continue  # Skip private methods
                    elif isinstance(node, ast.FunctionDef):
                        docstring = ast.get_docstring(node)
                        if docstring:
                            controller_info.append(f"Method {node.name}: {docstring}")
                            
            except Exception as e:
                logger.warning("Failed to parse controller file", file=str(py_file), error=str(e))
        
        self_awareness_content = "\n\n".join(controller_info)
        
        return ContextInfo(
            source="controller_self_awareness",
            content_type="self_documentation",
            content=f"""CONTROLLER SELF-AWARENESS:

I am a CLI Chatbot Controller with the following capabilities:

{self_awareness_content}

IDENTITY:
- I am a self-aware conversational interface
- I can dynamically analyze and understand the application I'm controlling
- I can execute scripts and modify my behavior based on context
- I maintain separation between my controller logic and the application logic
- I provide intelligent assistance through natural language interaction

CAPABILITIES:
- Dynamic context injection from live codebase analysis
- Real-time script generation and execution
- Dependency injection for input/output modification
- Conversation memory and learning
- Safety-first script execution with validation""",
            relevance_score=1.0,
            last_updated=datetime.now(),
            metadata={"type": "self_awareness", "controller_root": str(self.controller_root)}
        )
    
    async def _extract_code_contexts(self, query: str, max_contexts: int) -> List[ContextInfo]:
        """Extract relevant code contexts (functions, classes, etc.)."""
        
        contexts = []
        query_lower = query.lower()
        
        for py_file in self.application_root.rglob("*.py"):
            if py_file.stat().st_size > self.max_file_size:
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                        # Calculate relevance based on name and docstring
                        relevance = self._calculate_relevance(
                            query_lower, 
                            node.name.lower(),
                            ast.get_docstring(node) or ""
                        )
                        
                        if relevance > 0.1:  # Minimum relevance threshold
                            # Extract the actual code
                            code_lines = content.split('\n')
                            start_line = node.lineno - 1
                            end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line + 20
                            
                            code_snippet = '\n'.join(code_lines[start_line:end_line])
                            
                            contexts.append(ContextInfo(
                                source=str(py_file.relative_to(self.application_root)),
                                content_type="function" if isinstance(node, ast.FunctionDef) else "class",
                                content=f"```python\n{code_snippet}\n```",
                                relevance_score=relevance,
                                last_updated=datetime.fromtimestamp(py_file.stat().st_mtime),
                                metadata={
                                    "name": node.name,
                                    "line_number": node.lineno,
                                    "docstring": ast.get_docstring(node)
                                }
                            ))
                            
            except Exception as e:
                logger.debug("Failed to parse Python file", file=str(py_file), error=str(e))
        
        return contexts[:max_contexts]

    async def _extract_documentation_contexts(self, query: str, max_contexts: int) -> List[ContextInfo]:
        """Extract relevant documentation contexts."""

        contexts = []
        query_lower = query.lower()

        # Look for documentation files
        doc_patterns = ['README*', '*.md', '*.txt', 'docs/**/*']

        for pattern in doc_patterns:
            for doc_file in self.application_root.glob(pattern):
                if doc_file.is_file() and doc_file.stat().st_size <= self.max_file_size:
                    try:
                        with open(doc_file, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # Calculate relevance based on content
                        relevance = self._calculate_relevance(query_lower, "", content.lower())

                        if relevance > 0.1:
                            contexts.append(ContextInfo(
                                source=str(doc_file.relative_to(self.application_root)),
                                content_type="documentation",
                                content=content[:2000],  # Limit content size
                                relevance_score=relevance,
                                last_updated=datetime.fromtimestamp(doc_file.stat().st_mtime),
                                metadata={"file_type": doc_file.suffix}
                            ))

                    except Exception as e:
                        logger.debug("Failed to read documentation file", file=str(doc_file), error=str(e))

        return contexts[:max_contexts]

    def _calculate_relevance(self, query: str, name: str, content: str) -> float:
        """Calculate relevance score between query and content."""

        if not query:
            return 0.0

        query_words = set(query.split())
        name_words = set(name.split('_'))
        content_words = set(content.lower().split())

        # Name matching (higher weight)
        name_matches = len(query_words.intersection(name_words))
        name_score = (name_matches / len(query_words)) * 0.6 if query_words else 0

        # Content matching
        content_matches = len(query_words.intersection(content_words))
        content_score = (content_matches / len(query_words)) * 0.4 if query_words else 0

        # Boost for exact phrase matches
        phrase_boost = 0.2 if query in content else 0

        total_score = min(1.0, name_score + content_score + phrase_boost)

        return total_score
