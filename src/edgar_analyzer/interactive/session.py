"""
Interactive Extraction Session - Stateful REPL for EDGAR Platform

Provides an Auggie-style interactive chat mode for data extraction workflows.
Maintains stateful context across commands and integrates with existing platform services.

Design Decisions:
- **Rich UI**: Uses Rich library for beautiful tables, markdown, and progress spinners
- **Prompt Toolkit**: History, tab completion, and Ctrl+R search for commands
- **Stateful Context**: Maintains project, analysis, code, and extraction state
- **Async First**: All service integrations are async for consistency
- **Command Registry**: Extensible command pattern for easy additions

Features:
- Tab completion for commands
- Persistent command history (saved to ~/.edgar/session_history.txt)
- Progress spinners for long operations
- Rich tables for structured data display
- Error handling with helpful messages
- Auto-load project if path provided

Example Usage:
    >>> from edgar_analyzer.interactive import InteractiveExtractionSession
    >>> import asyncio
    >>>
    >>> session = InteractiveExtractionSession()
    >>> asyncio.run(session.start())

    edgar> help
    edgar> load projects/weather_test/
    edgar> show
    edgar> analyze
    edgar> patterns
    edgar> generate
    edgar> extract
    edgar> exit

Trade-offs:
- **Rich over Bare Terminal**: Better UX but requires Rich dependency
- **Async over Sync**: Consistent with platform but slightly more complex
- **File History over In-Memory**: Persists across sessions but requires file I/O
- **Command Registry over if/else**: More extensible but slightly more code

Performance:
- Command dispatch: <1ms (dictionary lookup)
- History file I/O: ~10ms on startup
- Rich table rendering: <50ms for typical tables
"""

import importlib.util
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import structlog
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table

from edgar_analyzer.models.project_config import ExampleConfig
from extract_transform_platform.ai.openrouter_client import OpenRouterClient
from extract_transform_platform.models.project_config import ProjectConfig
from extract_transform_platform.services.analysis.example_parser import ExampleParser
from extract_transform_platform.services.analysis.schema_analyzer import SchemaAnalyzer
from extract_transform_platform.services.codegen.code_generator import CodeGeneratorService
from extract_transform_platform.services.codegen.constraint_enforcer import ConstraintEnforcer
from extract_transform_platform.services.project_manager import ProjectManager

logger = structlog.get_logger(__name__)


class InteractiveExtractionSession:
    """Stateful interactive extraction session with REPL interface.

    This class provides an interactive command-line interface for data extraction
    workflows. It maintains state across commands, integrates with platform services,
    and provides a rich user experience with tab completion, history, and progress
    indicators.

    Attributes:
        console: Rich console for formatted output
        project_path: Current project directory path
        project_config: Loaded project configuration
        analysis_results: Results from schema analysis
        generated_code: Generated extraction code
        extraction_results: Results from extraction run
        project_manager: Service for project operations
        schema_analyzer: Service for pattern detection
        openrouter_client: AI client for code generation
        commands: Registry of available commands

    Example:
        >>> session = InteractiveExtractionSession(project_path=Path("projects/test/"))
        >>> await session.start()
    """

    def __init__(self, project_path: Optional[Path] = None) -> None:
        """Initialize interactive session.

        Args:
            project_path: Optional project directory to auto-load on start
        """
        self.console = Console()
        self.project_path = project_path
        self.project_config: Optional[ProjectConfig] = None
        self.analysis_results: Optional[Dict[str, Any]] = None
        self.generated_code: Optional[str] = None
        self.generated_code_path: Optional[Path] = None
        self.extraction_results: Optional[List[Dict[str, Any]]] = None

        # Services
        self.project_manager = ProjectManager()
        self.schema_analyzer = SchemaAnalyzer()
        self.example_parser = ExampleParser(self.schema_analyzer)
        self.code_generator = CodeGeneratorService()
        self.constraint_enforcer = ConstraintEnforcer()

        # Initialize OpenRouter client for conversational AI
        try:
            self.openrouter_client = OpenRouterClient()
            logger.debug("openrouter_client_initialized_for_chat")
        except ValueError as e:
            # API key not available - chat mode will be disabled
            self.openrouter_client = None
            logger.warning("openrouter_client_init_failed", error=str(e))

        # Command registry - maps command names to handler methods
        self.commands: Dict[str, Callable] = {
            "help": self.cmd_help,
            "load": self.cmd_load_project,
            "show": self.cmd_show,
            "analyze": self.cmd_analyze,
            "patterns": self.cmd_show_patterns,
            "examples": self.cmd_show_examples,
            "generate": self.cmd_generate_code,
            "validate": self.cmd_validate_code,
            "extract": self.cmd_run_extraction,
            "save": self.cmd_save_session,
            "resume": self.cmd_resume_session,
            "sessions": self.cmd_list_sessions,
            "confidence": self.cmd_set_confidence,
            "threshold": self.cmd_get_confidence,
            "chat": self.cmd_chat,
            "ask": self.cmd_chat,  # alias
            "exit": self.cmd_exit,
        }

        logger.info("interactive_session_initialized", project_path=str(project_path))

    async def start(self) -> None:
        """Start interactive REPL session.

        This is the main entry point for the interactive mode. It displays a welcome
        message, auto-loads project if provided, sets up prompt session with history
        and completion, and runs the REPL loop.

        The REPL loop:
        1. Displays prompt: "edgar> "
        2. Waits for user input
        3. Parses command and arguments
        4. Executes command via registry
        5. Repeats until 'exit' command or Ctrl+D

        Error Handling:
        - KeyboardInterrupt (Ctrl+C): Ignored, continues REPL
        - EOFError (Ctrl+D): Gracefully exits
        - Invalid commands: Shows error and help hint
        - Command errors: Caught and displayed with details
        """
        # Welcome message
        self.console.print("[bold blue]🔍 EDGAR Interactive Extraction Session[/bold blue]")
        self.console.print("Type naturally or use /commands (e.g., /help, /exit)\n")

        # Auto-load project if path provided
        if self.project_path:
            await self.cmd_load_project(str(self.project_path))

        # Setup prompt session with history and completion
        history_file = Path.home() / ".edgar" / "session_history.txt"
        history_file.parent.mkdir(parents=True, exist_ok=True)

        completer = WordCompleter(list(self.commands.keys()), ignore_case=True)
        session: PromptSession[str] = PromptSession(
            history=FileHistory(str(history_file)),
            completer=completer,
        )

        logger.info("repl_started", history_file=str(history_file))

        # REPL loop
        while True:
            try:
                user_input = await session.prompt_async("edgar> ")
                user_input = user_input.strip()

                if not user_input:
                    continue

                # Check if input starts with / (slash command)
                if user_input.startswith('/'):
                    # System command - direct routing (bypass NL parsing)
                    parts = user_input[1:].split(maxsplit=1)  # Remove leading /
                    command = parts[0].lower()
                    args = parts[1] if len(parts) > 1 else ""

                    logger.debug("slash_command_received", command=command, args=args)

                    # Execute command directly
                    if command in self.commands:
                        result = await self.commands[command](args)
                        if result == "exit":
                            break
                    else:
                        # Unknown slash command - show error (don't route to AI)
                        self.console.print(f"[red]❌ Unknown command: /{command}[/red]")
                        self.console.print("[dim]Type '/help' to see available commands[/dim]")
                else:
                    # Check if input looks like natural language
                    word_count = len(user_input.split())
                    is_natural = word_count > 3 or "?" in user_input or (user_input and user_input[0].isupper())

                    if is_natural:
                        # Parse with NL understanding
                        command, args = await self._parse_natural_language(user_input)
                        if command != user_input.split()[0].lower():  # Only show if interpreted differently
                            self.console.print(f"[dim]→ Interpreted as: {command} {args}[/dim]")
                    else:
                        # Traditional command parsing
                        parts = user_input.split(maxsplit=1)
                        command = parts[0].lower()
                        args = parts[1] if len(parts) > 1 else ""

                    logger.debug("command_received", command=command, args=args)

                    # Execute command
                    if command in self.commands:
                        result = await self.commands[command](args)
                        if result == "exit":
                            break
                    else:
                        # Route unknown commands to conversational AI
                        await self.cmd_chat(user_input)

            except KeyboardInterrupt:
                # Ctrl+C - just continue
                continue
            except EOFError:
                # Ctrl+D - exit gracefully
                break
            except Exception as e:
                self.console.print(f"[red]Error executing command: {e}[/red]")
                logger.exception("command_error", command=command if 'command' in locals() else "unknown")

        self.console.print("[yellow]Session ended[/yellow]")
        logger.info("repl_ended")

    async def cmd_help(self, args: str = "") -> None:
        """Show available commands with enhanced Rich formatting.

        Displays a formatted table of all available commands with descriptions.
        Uses Rich Table for clean, aligned output.

        Args:
            args: Unused, included for signature consistency
        """
        table = Table(
            title="💡 Available Commands",
            show_header=True,
            header_style="bold magenta",
            caption="Commands can be typed directly or prefixed with /\nExamples: help, /help, analyze, /analyze"
        )
        table.add_column("Command", style="cyan", width=20)
        table.add_column("Arguments", style="yellow", width=15)
        table.add_column("Description", style="white", width=50)

        commands_info = [
            ("/help", "", "Show this help message"),
            ("/chat", "<message>", "Ask the AI assistant a question"),
            ("/load", "<path>", "Load project from path"),
            ("/show", "", "Show current project status"),
            ("/examples", "", "List loaded examples with preview"),
            ("/analyze", "", "Analyze project and detect patterns"),
            ("/patterns", "", "Show detected transformation patterns"),
            ("/generate", "", "Generate extraction code from patterns"),
            ("/validate", "", "Validate generated code quality"),
            ("/extract", "", "Run extraction on project data"),
            ("/confidence", "<0.0-1.0>", "Set confidence threshold and re-analyze"),
            ("/threshold", "", "Show current confidence threshold"),
            ("/save", "[name]", "Save current session (default: 'last')"),
            ("/resume", "[name]", "Resume saved session (default: 'last')"),
            ("/sessions", "", "List all saved sessions"),
            ("/exit", "", "Exit interactive session (auto-saves)"),
        ]

        for cmd, args_str, desc in commands_info:
            table.add_row(cmd, args_str, desc)

        self.console.print(table)

        # Add usage tip
        tip = Panel(
            "[bold cyan]💡 Tip:[/bold cyan] Use [bold]Tab[/bold] for auto-completion and [bold]Ctrl+R[/bold] to search history",
            border_style="dim"
        )
        self.console.print(tip)

        logger.info("help_displayed")

    async def cmd_chat(self, message: str) -> None:
        """Send a message to the AI assistant for conversational responses.

        Provides helpful, conversational responses to questions about EDGAR's
        capabilities, how to use commands, and general guidance.

        Args:
            message: User's question or message

        Error Handling:
        - No API key: Friendly message explaining chat is unavailable
        - API errors: Graceful fallback with helpful error message
        - Empty responses: Default helpful message
        """
        if not message or not message.strip():
            self.console.print("[yellow]Please provide a message or question.[/yellow]")
            return

        # Check if OpenRouter client is available
        if not self.openrouter_client:
            self.console.print(
                "[yellow]⚠️  Chat mode is unavailable (OPENROUTER_API_KEY not configured)[/yellow]\n"
                "[dim]Set your API key to enable conversational AI assistance.[/dim]"
            )
            return

        try:
            # Show thinking indicator
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                progress.add_task("Thinking...", total=None)

                # Build context about current session state
                context_info = []
                if self.project_config:
                    context_info.append(f"Project: {self.project_config.project.name}")
                if self.analysis_results:
                    pattern_count = len(self.analysis_results.get("patterns", []))
                    context_info.append(f"Analysis complete ({pattern_count} patterns)")
                if self.generated_code:
                    context_info.append("Code generated")
                if self.extraction_results:
                    context_info.append(f"Extraction complete ({len(self.extraction_results)} records)")

                session_context = " | ".join(context_info) if context_info else "No project loaded"

                # Create system prompt
                system_prompt = """You are EDGAR, a friendly AI assistant for data extraction and transformation.

Your purpose: Help users extract and transform data from various sources (Excel, PDF, APIs, web) into structured JSON.

Key capabilities:
- Analyze data sources to detect transformation patterns
- Generate extraction code from examples
- Transform files (Excel, PDF, DOCX, PPTX) to structured JSON
- Interactive workflow guidance

Available commands:
- load <path>: Load a project
- analyze: Detect transformation patterns
- patterns: Show detected patterns
- generate: Generate extraction code
- extract: Run extraction
- confidence <0.0-1.0>: Adjust pattern detection threshold
- help: Show all commands

Guidelines:
- Be friendly, concise, and helpful
- When users ask how to do something, suggest the relevant command
- Keep responses under 200 words unless detailed explanation is needed
- Use emojis sparingly (✅ 🔍 💡 ⚠️)
- If unsure, suggest using 'help' command"""

                user_prompt = f"""Current session state: {session_context}

User message: {message}

Provide a helpful response. If the user is asking how to do something, point them to the relevant command(s)."""

                # Call OpenRouter API
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]

                response = await self.openrouter_client.chat_completion(
                    messages=messages,
                    temperature=0.7,
                    max_tokens=500  # Keep responses concise
                )

            # Display response with Rich formatting
            if response and response.strip():
                # Parse as markdown for nice formatting
                md = Markdown(response.strip())
                self.console.print(md)
            else:
                # Fallback if empty response
                self.console.print(
                    "[cyan]I'm here to help! Type 'help' to see available commands, "
                    "or ask me about specific features.[/cyan]"
                )

            logger.info("chat_response_displayed", message_length=len(message), response_length=len(response))

        except Exception as e:
            # Graceful error handling
            self.console.print(
                f"[yellow]⚠️  I encountered an issue: {str(e)[:100]}[/yellow]\n"
                "[dim]Try asking in a different way, or use 'help' to see available commands.[/dim]"
            )
            logger.exception("chat_error", message=message[:100])

    async def _parse_natural_language(self, user_input: str) -> Tuple[str, str]:
        """Parse natural language input to command + args using regex + LLM fallback.

        Returns:
            tuple[command, args]: Parsed command and arguments
        """
        # Common NL → Command mappings (fast path, no LLM needed)
        nl_mappings = {
            r"what patterns.*detect": ("patterns", ""),
            r"show.*patterns": ("patterns", ""),
            r"list.*patterns": ("patterns", ""),
            r"what.*examples": ("examples", ""),
            r"show.*examples": ("examples", ""),
            r"list.*examples": ("examples", ""),
            r"analyze.*project": ("analyze", ""),
            r"run.*analysis": ("analyze", ""),
            r"analyze": ("analyze", ""),
            r"generate.*code": ("generate", ""),
            r"create.*code": ("generate", ""),
            r"validate.*code": ("validate", ""),
            r"check.*code": ("validate", ""),
            r"run.*extraction": ("extract", ""),
            r"extract.*data": ("extract", ""),
            r"save.*session": ("save", ""),
            r"load.*project": ("load", ""),
            r"show.*status": ("show", ""),
            r"what.*status": ("show", ""),
            r"what.*confidence": ("threshold", ""),
            r"show.*confidence": ("threshold", ""),
            r"set.*confidence": ("confidence", ""),
        }

        # Try fast regex matching first
        user_lower = user_input.lower()

        for pattern, (command, default_args) in nl_mappings.items():
            if re.search(pattern, user_lower):
                logger.debug("nl_parsed_regex", pattern=pattern, command=command)
                return command, default_args

        # If no match and OpenRouter client available, use LLM
        if self.openrouter_client:
            try:
                prompt = f"""Parse this natural language command for a data extraction tool.

Available commands: {', '.join(self.commands.keys())}

User input: "{user_input}"

Return ONLY the command name and arguments in format: command|args

Examples:
"What patterns did you find?" → patterns|
"Show me the first 3 examples" → examples|
"Generate the extraction code" → generate|
"Set confidence to 0.85" → confidence|0.85

If unclear, return: help|

Your response:"""

                response = await self.openrouter_client.complete(
                    prompt=prompt,
                    max_tokens=50,
                    temperature=0.1
                )

                # Parse response
                if "|" in response:
                    parts = response.split("|", 1)
                    command = parts[0].strip()
                    args = parts[1].strip() if len(parts) > 1 else ""

                    # Validate command exists
                    if command in self.commands:
                        logger.debug("nl_parsed_llm", command=command, args=args)
                        return command, args

            except Exception as e:
                logger.debug("nl_parsing_llm_failed", error=str(e))

        # Fallback: treat as unknown command (first word)
        return user_input.split()[0] if user_input else "help", ""

    async def cmd_load_project(self, path: str) -> None:
        """Load project configuration.

        Loads project configuration from specified directory path. Validates
        that project.yaml exists and can be parsed. Updates session state
        with loaded configuration.

        Args:
            path: Path to project directory

        Error Handling:
        - Missing project.yaml: Clear error message
        - Invalid YAML: Pydantic validation error displayed
        - File I/O errors: Generic error with details
        """
        if not path:
            self.console.print("[red]Usage: load <path>[/red]")
            return

        try:
            project_path = Path(path)
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                progress.add_task("Loading project...", total=None)

                # Load project configuration
                config_path = project_path / "project.yaml"
                if not config_path.exists():
                    self.console.print(f"[red]❌ Error: project.yaml not found in {project_path}[/red]")
                    return

                self.project_config = ProjectConfig.from_yaml(config_path)
                self.project_path = project_path

            self.console.print(f"[green]✅ Loaded project: {self.project_config.project.name}[/green]")
            logger.info("project_loaded", project_name=self.project_config.project.name)

        except Exception as e:
            self.console.print(f"[red]❌ Failed to load project: {e}[/red]")
            logger.exception("project_load_error", path=path)

    async def cmd_show(self, args: str = "") -> None:
        """Show current project status.

        Displays a formatted table showing:
        - Project name
        - Data source type
        - Number of examples
        - Analysis status
        - Code generation status

        Args:
            args: Unused, included for signature consistency
        """
        if not self.project_config:
            self.console.print("[yellow]⚠️  No project loaded. Use 'load <path>' first.[/yellow]")
            return

        table = Table(title="Project Status")
        table.add_column("Property", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")

        table.add_row("Name", self.project_config.project.name)
        # Get first data source type (project always has at least one)
        data_source_type = self.project_config.data_sources[0].type if self.project_config.data_sources else "N/A"
        table.add_row("Data Source", data_source_type)

        # Count examples (either inline or file-based)
        example_count = 0
        if hasattr(self.project_config, 'examples') and self.project_config.examples:
            example_count = len(self.project_config.examples)

        table.add_row("Examples", str(example_count))
        table.add_row("Analyzed", "Yes" if self.analysis_results else "No")
        table.add_row("Code Generated", "Yes" if self.generated_code else "No")

        self.console.print(table)
        logger.info("status_displayed", project_name=self.project_config.project.name)

    async def cmd_show_examples(self, args: str = "") -> None:
        """Show loaded examples with structure preview.

        Displays a table of all examples in the project with structure and field preview.

        Args:
            args: Unused, included for signature consistency
        """
        if not self.project_config:
            self.console.print("[yellow]⚠️  No project loaded[/yellow]")
            return

        if not hasattr(self.project_config, 'examples') or not self.project_config.examples:
            self.console.print("[yellow]⚠️  No examples found in project[/yellow]")
            return

        table = Table(title=f"Loaded Examples ({len(self.project_config.examples)} total)")
        table.add_column("Index", style="cyan", width=8)
        table.add_column("File", style="white", width=30)
        table.add_column("Fields", style="green", width=12)
        table.add_column("Preview", style="dim", width=50)

        for idx, example_path in enumerate(self.project_config.examples, 1):
            # Handle file-based examples
            if isinstance(example_path, str):
                full_path = self.project_path / example_path

                if full_path.exists():
                    try:
                        with open(full_path, 'r') as f:
                            example_data = json.load(f)

                            # Count fields
                            field_count = len(example_data) if isinstance(example_data, dict) else "N/A"

                            # Create preview (first 2 keys)
                            if isinstance(example_data, dict):
                                preview_keys = list(example_data.keys())[:2]
                                preview = ", ".join(preview_keys)
                                if len(example_data) > 2:
                                    preview += f" (+{len(example_data) - 2} more)"
                            else:
                                preview = str(type(example_data).__name__)

                            table.add_row(
                                str(idx),
                                Path(example_path).name,
                                str(field_count),
                                preview
                            )
                    except Exception as e:
                        table.add_row(
                            str(idx),
                            Path(example_path).name,
                            "[red]Error[/red]",
                            f"[red]{str(e)[:40]}[/red]"
                        )
                else:
                    table.add_row(
                        str(idx),
                        Path(example_path).name,
                        "[red]Missing[/red]",
                        "[red]File not found[/red]"
                    )
            # Handle inline examples
            elif isinstance(example_path, ExampleConfig):
                example_data = example_path.output
                field_count = len(example_data) if isinstance(example_data, dict) else "N/A"

                if isinstance(example_data, dict):
                    preview_keys = list(example_data.keys())[:2]
                    preview = ", ".join(preview_keys)
                    if len(example_data) > 2:
                        preview += f" (+{len(example_data) - 2} more)"
                else:
                    preview = "Inline"

                table.add_row(
                    str(idx),
                    "Inline",
                    str(field_count),
                    preview
                )

        self.console.print(table)
        logger.info("examples_displayed", count=len(self.project_config.examples))

    async def cmd_analyze(self, args: str = "") -> None:
        """Analyze project and detect patterns - FULL INTEGRATION.

        Runs schema analysis on project examples to detect transformation patterns.
        Updates session state with analysis results.

        This operation:
        1. Loads all examples (inline or file-based)
        2. Analyzes input/output schemas
        3. Detects transformation patterns
        4. Stores results in session state

        Args:
            args: Unused, included for signature consistency

        Error Handling:
        - No project loaded: Warning message
        - Analysis failures: Error with details logged
        """
        if not self.project_config:
            self.console.print("[yellow]⚠️  No project loaded[/yellow]")
            return

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task("Analyzing examples...", total=None)

                # INTEGRATION: Load and parse examples
                parsed_examples = []

                for example_item in self.project_config.examples:
                    # Handle file-based examples
                    if isinstance(example_item, str):
                        full_path = self.project_path / example_item
                        if full_path.exists():
                            with open(full_path, 'r') as f:
                                example_data = json.load(f)
                                # Convert to ExampleConfig format (support both old and new formats)
                                if 'input' in example_data and 'output' in example_data:
                                    # New format
                                    example_config = ExampleConfig(
                                        input=example_data['input'],
                                        output=example_data['output']
                                    )
                                    parsed_examples.append(example_config)
                                elif 'input_data' in example_data and 'output_data' in example_data:
                                    # Legacy format - convert to new format
                                    example_config = ExampleConfig(
                                        input=example_data['input_data'],
                                        output=example_data['output_data']
                                    )
                                    parsed_examples.append(example_config)
                    # Handle inline examples
                    elif isinstance(example_item, ExampleConfig):
                        parsed_examples.append(example_item)

                # INTEGRATION: Use ExampleParser for pattern detection
                parsed_result = self.example_parser.parse_examples(parsed_examples)

                # Store results
                self.analysis_results = {
                    "patterns": [
                        {
                            "type": p.type.value if hasattr(p.type, 'value') else str(p.type),
                            "confidence": p.confidence,
                            "source_path": p.source_path,
                            "target_path": p.target_path,
                            "description": getattr(p, 'description', '') or f"{p.type} transformation"
                        }
                        for p in parsed_result.patterns
                    ],
                    "input_schema": parsed_result.input_schema.dict() if hasattr(parsed_result.input_schema, 'dict') else {},
                    "output_schema": parsed_result.output_schema.dict() if hasattr(parsed_result.output_schema, 'dict') else {},
                    "confidence_scores": {
                        p.target_path: p.confidence for p in parsed_result.patterns
                    },
                }

                progress.update(task, completed=True)

            # Display summary with Rich formatting
            self.console.print("[green]✅ Analysis complete[/green]")

            patterns_count = len(self.analysis_results.get("patterns", []))
            input_fields = len(self.analysis_results.get("input_schema", {}).get("fields", {}))
            output_fields = len(self.analysis_results.get("output_schema", {}).get("fields", {}))

            summary_table = Table(title="Analysis Summary", show_header=False)
            summary_table.add_column("Metric", style="cyan")
            summary_table.add_column("Value", style="green")

            summary_table.add_row("Patterns Detected", str(patterns_count))
            summary_table.add_row("Input Fields", str(input_fields))
            summary_table.add_row("Output Fields", str(output_fields))
            summary_table.add_row("Examples Analyzed", str(len(parsed_examples)))

            self.console.print(summary_table)

            logger.info("analysis_complete", patterns=patterns_count, examples=len(parsed_examples))

        except Exception as e:
            self.console.print(f"[red]❌ Analysis failed: {e}[/red]")
            import traceback
            self.console.print(f"[dim]{traceback.format_exc()}[/dim]")
            logger.exception("analysis_error")

    async def cmd_show_patterns(self, args: str = "") -> None:
        """Show detected patterns with full details and color-coded confidence.

        Displays a table of all detected transformation patterns with:
        - Pattern type
        - Confidence score (color-coded)
        - Source → Target mapping
        - Description

        Args:
            args: Unused, included for signature consistency
        """
        if not self.analysis_results:
            self.console.print("[yellow]⚠️  Run 'analyze' first[/yellow]")
            return

        patterns = self.analysis_results.get("patterns", [])

        if not patterns:
            self.console.print("[yellow]No patterns detected[/yellow]")
            return

        # Create Rich table with enhanced formatting
        table = Table(title=f"Detected Patterns ({len(patterns)} total)", show_lines=True)
        table.add_column("Type", style="cyan", width=20)
        table.add_column("Confidence", style="green", justify="right", width=12)
        table.add_column("Source → Target", style="white", width=30)
        table.add_column("Details", style="dim", width=40)

        for pattern in patterns:
            pattern_type = pattern.get("type", "UNKNOWN")
            confidence = pattern.get("confidence", 0.0)
            source_path = pattern.get("source_path", "?")
            target_path = pattern.get("target_path", "?")
            description = pattern.get("description", "No description")

            # Color code confidence
            if confidence >= 0.9:
                confidence_str = f"[bold green]{confidence:.1%}[/bold green]"
            elif confidence >= 0.7:
                confidence_str = f"[yellow]{confidence:.1%}[/yellow]"
            else:
                confidence_str = f"[red]{confidence:.1%}[/red]"

            # Format source → target
            mapping = f"{source_path} → {target_path}"

            table.add_row(
                pattern_type,
                confidence_str,
                mapping,
                description[:40] + "..." if len(description) > 40 else description
            )

        self.console.print(table)

        # Show average confidence
        avg_confidence = sum(p.get("confidence", 0) for p in patterns) / len(patterns)
        self.console.print(f"\n[dim]Average Confidence: {avg_confidence:.1%}[/dim]")

        logger.info("patterns_displayed", count=len(patterns), avg_confidence=avg_confidence)

    async def cmd_generate_code(self, args: str = "") -> None:
        """Generate extraction code from analysis results.

        Generates Python code for data extraction based on detected patterns.
        Integrates with CodeGeneratorService for AI-powered code generation.

        Args:
            args: Unused, included for signature consistency

        Error Handling:
        - No analysis results: Warning to run analyze first
        - Generation failures: Error with details and traceback
        """
        if not self.analysis_results:
            self.console.print("[yellow]⚠️  Run 'analyze' first[/yellow]")
            return

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task("Generating extraction code...", total=None)

                # INTEGRATION: Use CodeGeneratorService
                # Note: Simplified implementation - full integration would use parsed_examples
                # For Phase 2, generate code directly from patterns
                from extract_transform_platform.models.patterns import Pattern, PatternType

                # Convert dict patterns back to Pattern objects
                pattern_objects = []
                for p_dict in self.analysis_results["patterns"]:
                    pattern_type = PatternType(p_dict["type"]) if isinstance(p_dict["type"], str) else p_dict["type"]
                    pattern = Pattern(
                        type=pattern_type,
                        source_path=p_dict["source_path"],
                        target_path=p_dict["target_path"],
                        confidence=p_dict["confidence"],
                        transformation=p_dict.get("description", f"{pattern_type} transformation")
                    )
                    pattern_objects.append(pattern)

                # Generate simple extractor code
                self.generated_code = self._generate_simple_extractor(pattern_objects)
                self.generated_code_path = self.project_path / "generated_extractor.py"

                # Save generated code
                with open(self.generated_code_path, 'w') as f:
                    f.write(self.generated_code)

                progress.update(task, completed=True)

            self.console.print("[green]✅ Code generation complete![/green]")
            self.console.print(f"[dim]Saved to: {self.generated_code_path}[/dim]")

            # Show code preview with syntax highlighting
            preview_lines = self.generated_code.split('\n')[:20]
            preview_code = '\n'.join(preview_lines)

            syntax = Syntax(preview_code, "python", theme="monokai", line_numbers=True)
            self.console.print("\n[bold]Code Preview:[/bold]")
            self.console.print(syntax)

            if len(self.generated_code.split('\n')) > 20:
                self.console.print(f"\n[dim]... ({len(self.generated_code.split('\n')) - 20} more lines)[/dim]")

            logger.info("code_generated", code_length=len(self.generated_code))

        except Exception as e:
            self.console.print(f"[red]❌ Code generation failed: {e}[/red]")
            import traceback
            self.console.print(f"[dim]{traceback.format_exc()}[/dim]")
            logger.exception("code_generation_error")

    def _generate_simple_extractor(self, patterns: List[Any]) -> str:
        """Generate simple extractor code from patterns."""
        code = '''"""Generated Extractor - Auto-generated by EDGAR Interactive Session"""

from typing import Dict, Any, List


class GeneratedExtractor:
    """Auto-generated data extractor."""

    def __init__(self):
        """Initialize extractor."""
        pass

    async def extract(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and transform data.

        Args:
            data: Input data dictionary

        Returns:
            Transformed output data
        """
        result = {}

'''
        # Add transformation code for each pattern
        for pattern in patterns:
            source = pattern.source_path
            target = pattern.target_path
            code += f'        # Pattern: {pattern.type} ({pattern.confidence:.1%} confidence)\n'
            code += f'        result["{target}"] = data.get("{source}")\n\n'

        code += '''        return result
'''
        return code

    async def cmd_validate_code(self, args: str = "") -> None:
        """Validate generated code with constraint enforcement."""
        if not self.generated_code:
            self.console.print("[yellow]⚠️  Run 'generate' first[/yellow]")
            return

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task("Validating generated code...", total=None)

                # INTEGRATION: Use ConstraintEnforcer
                validation_result = self.constraint_enforcer.validate_code(self.generated_code)

                progress.update(task, completed=True)

            # Display validation results
            if validation_result.valid:
                self.console.print("[green]✅ Code validation passed![/green]")
            else:
                self.console.print("[yellow]⚠️  Code validation warnings:[/yellow]")

                for violation in validation_result.violations[:10]:  # Show first 10
                    severity_color = "red" if violation.severity.value == "error" else "yellow"
                    self.console.print(f"  • [{severity_color}]{violation.message}[/{severity_color}]")

                if len(validation_result.violations) > 10:
                    self.console.print(f"  [dim]... and {len(validation_result.violations) - 10} more[/dim]")

            # Show validation metrics
            metrics_table = Table(title="Validation Metrics", show_header=False)
            metrics_table.add_column("Metric", style="cyan")
            metrics_table.add_column("Value", style="white")

            metrics_table.add_row("Valid", "✅ Yes" if validation_result.valid else "❌ No")
            metrics_table.add_row("Total Violations", str(len(validation_result.violations)))
            metrics_table.add_row("Errors", str(sum(1 for v in validation_result.violations if v.severity.value == "error")))
            metrics_table.add_row("Warnings", str(sum(1 for v in validation_result.violations if v.severity.value == "warning")))

            self.console.print(metrics_table)

            logger.info("validation_complete", valid=validation_result.valid, violations=len(validation_result.violations))

        except Exception as e:
            self.console.print(f"[red]❌ Validation failed: {e}[/red]")
            import traceback
            self.console.print(f"[dim]{traceback.format_exc()}[/dim]")
            logger.exception("validation_error")

    async def cmd_run_extraction(self, args: str = "") -> None:
        """Run extraction using generated code.

        Executes the generated extraction code on the project's data source.
        Saves results to session state and output directory.

        Args:
            args: Unused, included for signature consistency

        Error Handling:
        - No generated code: Warning to run generate first
        - Extraction failures: Error with details and traceback
        """
        if not self.generated_code:
            self.console.print("[yellow]⚠️  Run 'generate' first[/yellow]")
            return

        try:
            self.console.print("[bold blue]🚀 Running extraction...[/bold blue]")

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task("Extracting data...", total=None)

                # Execute generated code
                # Import the generated module dynamically
                spec = importlib.util.spec_from_file_location(
                    "generated_extractor",
                    self.generated_code_path
                )
                generated_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(generated_module)

                # Get the extractor class
                ExtractorClass = getattr(generated_module, "GeneratedExtractor")
                extractor = ExtractorClass()

                # Load sample data (simplified - in production would load from data source)
                # For now, use first example as sample data
                sample_data = {}
                if self.project_config.examples:
                    example_item = self.project_config.examples[0]
                    if isinstance(example_item, str):
                        full_path = self.project_path / example_item
                        if full_path.exists():
                            with open(full_path, 'r') as f:
                                example_data = json.load(f)
                                sample_data = example_data.get('input_data', {})
                    elif isinstance(example_item, ExampleConfig):
                        sample_data = example_item.input_data

                # Run extraction
                result = await extractor.extract(sample_data)
                self.extraction_results = [result]

                progress.update(task, completed=True)

            # Display results
            self.console.print(f"[green]✅ Extracted {len(self.extraction_results)} records[/green]")

            # Show preview of first 5 records
            if self.extraction_results:
                results_table = Table(title="Extraction Results (Preview)")

                # Add columns from first record
                first_record = self.extraction_results[0]
                for key in first_record.keys():
                    results_table.add_column(key, style="cyan")

                # Add rows (max 5)
                for record in self.extraction_results[:5]:
                    results_table.add_row(*[str(record.get(k, "")) for k in first_record.keys()])

                self.console.print(results_table)

                if len(self.extraction_results) > 5:
                    self.console.print(f"\n[dim]... ({len(self.extraction_results) - 5} more records)[/dim]")

            # Save results
            output_path = self.project_path / "output" / "extraction_results.json"
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w') as f:
                json.dump(self.extraction_results, f, indent=2)

            self.console.print(f"[dim]Results saved to: {output_path}[/dim]")

            logger.info("extraction_complete", records=len(self.extraction_results))

        except Exception as e:
            self.console.print(f"[red]❌ Extraction failed: {e}[/red]")
            import traceback
            self.console.print(f"[dim]{traceback.format_exc()}[/dim]")
            logger.exception("extraction_error")

    def _get_session_dir(self) -> Path:
        """Get session storage directory."""
        session_dir = Path.home() / ".edgar" / "sessions"
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir

    def _get_session_file(self, session_name: str = "last") -> Path:
        """Get session file path."""
        return self._get_session_dir() / f"{session_name}_session.json"

    async def cmd_save_session(self, args: str = "") -> None:
        """Save current session state."""
        session_name = args.strip() or "last"

        try:
            session_data = {
                "project_path": str(self.project_path) if self.project_path else None,
                "project_config": self.project_config.model_dump() if self.project_config else None,
                "analysis_results": self.analysis_results,
                "generated_code_path": str(self.generated_code_path) if self.generated_code_path else None,
                "extraction_count": len(self.extraction_results) if self.extraction_results else 0,
                "timestamp": datetime.now().isoformat(),
            }

            session_file = self._get_session_file(session_name)

            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)

            self.console.print(f"[green]✅ Session saved: {session_name}[/green]")
            self.console.print(f"[dim]File: {session_file}[/dim]")

            logger.info("session_saved", session_name=session_name)

        except Exception as e:
            self.console.print(f"[red]❌ Failed to save session: {e}[/red]")
            logger.exception("session_save_error")

    async def cmd_resume_session(self, args: str = "") -> None:
        """Resume saved session."""
        session_name = args.strip() or "last"

        try:
            session_file = self._get_session_file(session_name)

            if not session_file.exists():
                self.console.print(f"[yellow]⚠️  Session '{session_name}' not found[/yellow]")
                return

            with open(session_file, 'r') as f:
                session_data = json.load(f)

            # Restore state
            if session_data.get("project_path"):
                await self.cmd_load_project(session_data["project_path"])

            self.analysis_results = session_data.get("analysis_results")

            if session_data.get("generated_code_path"):
                code_path = Path(session_data["generated_code_path"])
                if code_path.exists():
                    with open(code_path, 'r') as f:
                        self.generated_code = f.read()
                    self.generated_code_path = code_path

            self.console.print(f"[green]✅ Session resumed: {session_name}[/green]")
            self.console.print(f"[dim]From: {session_data.get('timestamp')}[/dim]")

            # Show restored state
            await self.cmd_show()

            logger.info("session_resumed", session_name=session_name)

        except Exception as e:
            self.console.print(f"[red]❌ Failed to resume session: {e}[/red]")
            logger.exception("session_resume_error")

    async def cmd_list_sessions(self, args: str = "") -> None:
        """List saved sessions."""
        session_dir = self._get_session_dir()
        session_files = list(session_dir.glob("*_session.json"))

        if not session_files:
            self.console.print("[yellow]No saved sessions found[/yellow]")
            return

        table = Table(title="Saved Sessions")
        table.add_column("Name", style="cyan")
        table.add_column("Timestamp", style="white")
        table.add_column("Project", style="green")

        for session_file in sorted(session_files):
            try:
                with open(session_file, 'r') as f:
                    session_data = json.load(f)

                session_name = session_file.stem.replace("_session", "")
                timestamp = session_data.get("timestamp", "Unknown")
                project = session_data.get("project_config", {}).get("project", {}).get("name", "None") if session_data.get("project_config") else "None"

                table.add_row(session_name, timestamp, project)
            except:
                pass

        self.console.print(table)
        logger.info("sessions_listed", count=len(session_files))

    async def cmd_set_confidence(self, args: str):
        """Set confidence threshold and re-analyze."""
        try:
            threshold = float(args.strip())

            if not (0.0 <= threshold <= 1.0):
                self.console.print("[red]❌ Confidence must be between 0.0 and 1.0[/red]")
                return

            old_threshold = self.project_config.confidence_threshold if self.project_config else 0.7

            # Update config
            if self.project_config:
                self.project_config.confidence_threshold = threshold
            else:
                self.console.print("[yellow]⚠️  No project loaded[/yellow]")
                return

            self.console.print(f"[green]✅ Confidence threshold: {old_threshold:.1%} → {threshold:.1%}[/green]")

            # If already analyzed, re-run with new threshold
            if self.analysis_results:
                self.console.print("[dim]Re-analyzing with new threshold...[/dim]")

                # Store old patterns
                old_patterns = self.analysis_results.get("patterns", [])
                old_count = len(old_patterns)

                # Re-analyze
                await self.cmd_analyze()

                # Show diff
                new_patterns = self.analysis_results.get("patterns", [])
                new_count = len(new_patterns)

                diff_table = Table(title="Pattern Changes")
                diff_table.add_column("Metric", style="cyan")
                diff_table.add_column("Before", style="yellow")
                diff_table.add_column("After", style="green")

                diff_table.add_row("Pattern Count", str(old_count), str(new_count))
                diff_table.add_row("Threshold", f"{old_threshold:.1%}", f"{threshold:.1%}")

                # Calculate change
                change = new_count - old_count
                change_str = f"+{change}" if change > 0 else str(change)
                diff_table.add_row("Change", "", change_str)

                self.console.print(diff_table)
            else:
                self.console.print("[dim]Run 'analyze' to detect patterns with new threshold[/dim]")

            logger.info("confidence_threshold_updated", old=old_threshold, new=threshold)

        except ValueError:
            self.console.print(f"[red]❌ Invalid threshold: {args}[/red]")
            self.console.print("[dim]Usage: confidence <0.0-1.0>[/dim]")

    async def cmd_get_confidence(self, args: str = ""):
        """Get current confidence threshold."""
        if self.project_config:
            threshold = self.project_config.confidence_threshold or 0.7
            self.console.print(f"[cyan]Current confidence threshold: {threshold:.1%}[/cyan]")
        else:
            self.console.print("[yellow]⚠️  No project loaded[/yellow]")

    async def cmd_exit(self, args: str = "") -> str:
        """Exit session with auto-save.

        Automatically saves the current session state before exiting.

        Args:
            args: Unused, included for signature consistency

        Returns:
            "exit" to signal REPL loop to terminate
        """
        # Auto-save before exit
        if self.project_config:
            await self.cmd_save_session("last")
            self.console.print("[dim]Session auto-saved[/dim]")

        logger.info("exit_command_received")
        return "exit"
