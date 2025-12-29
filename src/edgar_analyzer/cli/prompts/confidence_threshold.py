"""CLI prompt for confidence threshold selection.

This module provides an interactive Rich UI prompt for users to select
confidence thresholds during pattern analysis workflows (1M-362).

Design Decisions:
- **Rich UI**: Professional formatting with panels, tables, and color coding
- **Preset Options**: Conservative (0.8), Balanced (0.7), Aggressive (0.6), Custom
- **Visual Feedback**: Pattern distribution displayed before selection
- **User Guidance**: Clear descriptions and recommendations
- **Validation**: Input validation with helpful error messages

Usage:
    >>> from edgar_analyzer.cli.prompts.confidence_threshold import ConfidenceThresholdPrompt
    >>> from extract_transform_platform.models.patterns import ParsedExamples
    >>>
    >>> prompt = ConfidenceThresholdPrompt()
    >>> threshold = prompt.prompt_for_threshold(parsed_examples)
    >>> print(f"Selected threshold: {threshold}")

Example Output:
    ┌──────────────────────────────────────────────────────────┐
    │ Pattern Detection Complete                               │
    ├──────────────────────────────────────────────────────────┤
    │ Detected 5 patterns:                                     │
    │   • 3 high confidence (≥ 0.9) - 60%                      │
    │   • 1 medium confidence (0.7-0.89) - 20%                 │
    │   • 1 low confidence (< 0.7) - 20%                       │
    └──────────────────────────────────────────────────────────┘
"""

from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from extract_transform_platform.models.patterns import ParsedExamples
from extract_transform_platform.services.analysis.pattern_filter import (
    PatternFilterService,
)

console = Console()


class ConfidenceThresholdPrompt:
    """Interactive prompt for selecting confidence threshold.

    Provides a professional Rich UI experience for threshold selection with:
    - Pattern distribution visualization
    - Preset options with descriptions
    - Custom threshold input with validation
    - Impact preview (patterns included/excluded)

    Example:
        >>> prompt = ConfidenceThresholdPrompt()
        >>> parsed = parser.parse_examples(examples)
        >>> threshold = prompt.prompt_for_threshold(parsed)
        >>> print(f"User selected: {threshold}")
        0.7
    """

    def __init__(self) -> None:
        """Initialize prompt with pattern filter service."""
        self.filter_service = PatternFilterService()

    def prompt_for_threshold(
        self, parsed_examples: ParsedExamples, default: str = "balanced"
    ) -> float:
        """Prompt user to select confidence threshold.

        Args:
            parsed_examples: Patterns detected from examples
            default: Default preset choice ("conservative", "balanced", "aggressive")

        Returns:
            Selected confidence threshold (0.0-1.0)

        Example:
            >>> prompt = ConfidenceThresholdPrompt()
            >>> threshold = prompt.prompt_for_threshold(parsed)
            >>> assert 0.0 <= threshold <= 1.0
        """
        # Display pattern summary
        summary = self.filter_service.format_confidence_summary(parsed_examples)
        console.print(
            Panel(summary, title="Pattern Detection Complete", border_style="green")
        )

        # Display threshold options
        presets = self.filter_service.get_threshold_presets()
        table = Table(title="Confidence Threshold Options", show_header=True)
        table.add_column("Option", style="cyan", width=12)
        table.add_column("Threshold", style="magenta", width=12)
        table.add_column("Description", style="white")

        # Build options map
        options_map = {}
        option_emojis = {
            "conservative": "Shield",
            "balanced": "Balance",
            "aggressive": "Lightning",
        }

        for idx, (name, (threshold_val, desc)) in enumerate(presets.items(), 1):
            emoji = option_emojis.get(name, "")

            # Calculate impact for this threshold
            included_count = sum(
                1 for p in parsed_examples.all_patterns if p.confidence >= threshold_val
            )
            excluded_count = len(parsed_examples.all_patterns) - included_count

            # Format description with impact
            full_desc = f"{desc}\n[dim]Result: {included_count} patterns included, {excluded_count} excluded[/dim]"

            # Highlight recommended option
            if name == "balanced":
                table.add_row(
                    f"[bold yellow][{idx}] {emoji}[/bold yellow]",
                    f"[bold yellow]{threshold_val}[/bold yellow]",
                    full_desc,
                )
            else:
                table.add_row(f"[{idx}] {emoji}", str(threshold_val), full_desc)

            options_map[str(idx)] = threshold_val

        # Add custom option
        table.add_row("[4] Target", "Custom", "Enter custom threshold (0.0-1.0)")
        console.print(table)

        # Prompt for selection
        choice = Prompt.ask(
            "\n[bold cyan]Select minimum confidence threshold[/bold cyan]",
            choices=["1", "2", "3", "4"],
            default="2",  # Balanced
        )

        if choice == "4":
            # Custom threshold with validation
            threshold = self._prompt_custom_threshold()
        else:
            threshold = options_map[choice]

        console.print(
            f"\n[green]OK[/green] Using confidence threshold: [bold]{threshold}[/bold]"
        )
        return threshold

    def _prompt_custom_threshold(self) -> float:
        """Prompt for custom threshold with validation.

        Returns:
            Valid threshold (0.0-1.0)

        Note:
            Loops until valid input received or default used.
        """
        console.print("\n[bold]Custom Threshold[/bold]")
        console.print("[dim]Examples:[/dim]")
        console.print("  [dim]• 0.9 = Very strict (only 90%+ confidence)[/dim]")
        console.print("  [dim]• 0.75 = Moderate (75%+ confidence)[/dim]")
        console.print("  [dim]• 0.5 = Lenient (50%+ confidence)[/dim]\n")

        while True:
            threshold_str = Prompt.ask(
                "[bold cyan]Enter custom threshold (0.0-1.0)[/bold cyan]", default="0.7"
            )

            try:
                threshold = float(threshold_str)
                if not 0.0 <= threshold <= 1.0:
                    console.print(
                        "[red]WARNING: Threshold must be between 0.0 and 1.0[/red]"
                    )
                    continue
                return threshold
            except ValueError:
                console.print(
                    "[red]WARNING: Invalid number. Please enter a decimal value (e.g., 0.7)[/red]"
                )
                continue
