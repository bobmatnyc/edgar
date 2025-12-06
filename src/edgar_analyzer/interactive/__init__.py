"""Interactive chat mode for EDGAR extraction.

This module provides an Auggie-style interactive REPL interface for data extraction
workflows. It's designed to provide a conversational, stateful interface for working
with data extraction projects.

Features:
- Rich terminal UI with tables, progress bars, and formatted output
- Command history with persistent storage
- Tab completion for commands
- Stateful session management
- Integration with platform services (ProjectManager, SchemaAnalyzer, OpenRouterClient)

Example Usage:
    >>> from edgar_analyzer.interactive import InteractiveExtractionSession
    >>> import asyncio
    >>>
    >>> # Start with no project (user will load one)
    >>> session = InteractiveExtractionSession()
    >>> asyncio.run(session.start())
    >>>
    >>> # Or auto-load a project
    >>> session = InteractiveExtractionSession(project_path=Path("projects/weather_test/"))
    >>> asyncio.run(session.start())

Available in main CLI:
    edgar-analyzer chat --project projects/weather_test/
"""

from edgar_analyzer.interactive.session import InteractiveExtractionSession

__all__ = ["InteractiveExtractionSession"]
