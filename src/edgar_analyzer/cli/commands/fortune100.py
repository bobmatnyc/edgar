"""
CLI commands for Fortune 100 pipeline (SCT + Tax extraction).

Commands:
- edgar fortune100 extract - Full pipeline (SCT + Tax)
- edgar fortune100 extract-sct - SCT only (DEF 14A)
- edgar fortune100 extract-tax - Tax only (10-K)
- edgar fortune100 list - List Fortune 100 companies

Example:
    edgar fortune100 extract --rank-start 1 --rank-end 10 --output results/
    edgar fortune100 extract-sct --rank-start 1 --rank-end 5 --format json
    edgar fortune100 list --sector Technology
"""

import asyncio
from pathlib import Path
from typing import Optional

import click
import structlog
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table

from edgar_analyzer.extractors.fortune100 import SCTAdapter, TaxAdapter

logger = structlog.get_logger(__name__)
console = Console()


# Fortune 100 companies (hardcoded for MVP - replace with DB later)
FORTUNE_100_COMPANIES = [
    {"rank": 1, "name": "Walmart Inc.", "ticker": "WMT", "cik": "0000104169", "sector": "Retail"},
    {"rank": 2, "name": "Amazon.com, Inc.", "ticker": "AMZN", "cik": "0001018724", "sector": "Technology"},
    {"rank": 3, "name": "Apple Inc.", "ticker": "AAPL", "cik": "0000320193", "sector": "Technology"},
    {"rank": 4, "name": "CVS Health Corporation", "ticker": "CVS", "cik": "0000064803", "sector": "Healthcare"},
    {"rank": 5, "name": "UnitedHealth Group Inc.", "ticker": "UNH", "cik": "0000731766", "sector": "Healthcare"},
    {"rank": 6, "name": "Exxon Mobil Corporation", "ticker": "XOM", "cik": "0000034088", "sector": "Energy"},
    {"rank": 7, "name": "Berkshire Hathaway Inc.", "ticker": "BRK.A", "cik": "0001067983", "sector": "Financial"},
    {"rank": 8, "name": "Alphabet Inc.", "ticker": "GOOGL", "cik": "0001652044", "sector": "Technology"},
    {"rank": 9, "name": "McKesson Corporation", "ticker": "MCK", "cik": "0000927653", "sector": "Healthcare"},
    {"rank": 10, "name": "AmerisourceBergen Corporation", "ticker": "ABC", "cik": "0001140859", "sector": "Healthcare"},
    # Add more companies as needed...
]


@click.group(name="fortune100")
def fortune100_cli():
    """Fortune 100 pipeline commands (SCT + Tax extraction)."""
    pass


@fortune100_cli.command(name="extract")
@click.option(
    "--rank-start",
    "-s",
    type=int,
    default=1,
    help="Start rank (default: 1)",
)
@click.option(
    "--rank-end",
    "-e",
    type=int,
    default=100,
    help="End rank (default: 100)",
)
@click.option(
    "--sector",
    type=str,
    default=None,
    help="Filter by sector (e.g., Technology, Healthcare)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=Path("output/fortune100"),
    help="Output directory (default: output/fortune100)",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "csv", "both"]),
    default="json",
    help="Output format (default: json)",
)
@click.option(
    "--max-concurrent",
    type=int,
    default=5,
    help="Max concurrent workers (default: 5)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Verbose output",
)
def extract_full(
    rank_start: int,
    rank_end: int,
    sector: Optional[str],
    output: Path,
    format: str,
    max_concurrent: int,
    verbose: bool,
):
    """
    Extract both SCT (DEF 14A) and Tax (10-K) data for Fortune 100 companies.

    This command runs the full pipeline:
    1. Extract Summary Compensation Table data from DEF 14A filings
    2. Extract Tax Expense data from 10-K filings
    3. Combine results into unified output

    Example:
        edgar fortune100 extract --rank-start 1 --rank-end 10 --output results/
    """
    console.print("[bold green]Fortune 100 Full Pipeline[/bold green]")
    console.print(f"  Ranks: {rank_start}-{rank_end}")
    console.print(f"  Sector: {sector or 'All'}")
    console.print(f"  Output: {output}")
    console.print(f"  Format: {format}")
    console.print(f"  Workers: {max_concurrent}")

    # Filter companies
    companies = _filter_companies(rank_start, rank_end, sector)
    console.print(f"\n[cyan]Processing {len(companies)} companies[/cyan]\n")

    # Run extraction
    asyncio.run(
        _run_full_pipeline(
            companies=companies,
            output=output,
            format=format,
            max_concurrent=max_concurrent,
            verbose=verbose,
        )
    )


@fortune100_cli.command(name="extract-sct")
@click.option(
    "--rank-start",
    "-s",
    type=int,
    default=1,
    help="Start rank (default: 1)",
)
@click.option(
    "--rank-end",
    "-e",
    type=int,
    default=100,
    help="End rank (default: 100)",
)
@click.option(
    "--sector",
    type=str,
    default=None,
    help="Filter by sector",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=Path("output/fortune100/sct"),
    help="Output directory",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "csv", "both"]),
    default="json",
    help="Output format",
)
@click.option(
    "--max-concurrent",
    type=int,
    default=5,
    help="Max concurrent workers",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Verbose output",
)
def extract_sct_only(
    rank_start: int,
    rank_end: int,
    sector: Optional[str],
    output: Path,
    format: str,
    max_concurrent: int,
    verbose: bool,
):
    """
    Extract SCT data only from DEF 14A filings.

    This command extracts Summary Compensation Table data for executives
    from DEF 14A proxy statements.

    Example:
        edgar fortune100 extract-sct --rank-start 1 --rank-end 5 --format json
    """
    console.print("[bold green]Fortune 100 SCT Extraction[/bold green]")
    console.print(f"  Ranks: {rank_start}-{rank_end}")
    console.print(f"  Filing Type: DEF 14A (Proxy Statement)")
    console.print(f"  Output: {output}")

    # Filter companies
    companies = _filter_companies(rank_start, rank_end, sector)
    console.print(f"\n[cyan]Processing {len(companies)} companies[/cyan]\n")

    # Run extraction
    asyncio.run(
        _run_sct_pipeline(
            companies=companies,
            output=output,
            format=format,
            max_concurrent=max_concurrent,
            verbose=verbose,
        )
    )


@fortune100_cli.command(name="extract-tax")
@click.option(
    "--rank-start",
    "-s",
    type=int,
    default=1,
    help="Start rank",
)
@click.option(
    "--rank-end",
    "-e",
    type=int,
    default=100,
    help="End rank",
)
@click.option(
    "--sector",
    type=str,
    default=None,
    help="Filter by sector",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=Path("output/fortune100/tax"),
    help="Output directory",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "csv", "both"]),
    default="json",
    help="Output format",
)
@click.option(
    "--max-concurrent",
    type=int,
    default=5,
    help="Max concurrent workers",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Verbose output",
)
def extract_tax_only(
    rank_start: int,
    rank_end: int,
    sector: Optional[str],
    output: Path,
    format: str,
    max_concurrent: int,
    verbose: bool,
):
    """
    Extract Tax data only from 10-K filings.

    This command extracts Tax Expense data from 10-K annual reports.

    Example:
        edgar fortune100 extract-tax --rank-start 1 --rank-end 10 --output results/
    """
    console.print("[bold green]Fortune 100 Tax Extraction[/bold green]")
    console.print(f"  Ranks: {rank_start}-{rank_end}")
    console.print(f"  Filing Type: 10-K (Annual Report)")
    console.print(f"  Output: {output}")

    # Filter companies
    companies = _filter_companies(rank_start, rank_end, sector)
    console.print(f"\n[cyan]Processing {len(companies)} companies[/cyan]\n")

    # Run extraction
    asyncio.run(
        _run_tax_pipeline(
            companies=companies,
            output=output,
            format=format,
            max_concurrent=max_concurrent,
            verbose=verbose,
        )
    )


@fortune100_cli.command(name="list")
@click.option(
    "--rank-start",
    "-s",
    type=int,
    default=1,
    help="Start rank",
)
@click.option(
    "--rank-end",
    "-e",
    type=int,
    default=100,
    help="End rank",
)
@click.option(
    "--sector",
    type=str,
    default=None,
    help="Filter by sector",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
def list_companies(
    rank_start: int,
    rank_end: int,
    sector: Optional[str],
    format: str,
):
    """
    List Fortune 100 companies.

    Example:
        edgar fortune100 list --sector Technology
        edgar fortune100 list --rank-start 1 --rank-end 10 --format json
    """
    companies = _filter_companies(rank_start, rank_end, sector)

    if format == "json":
        import json
        console.print(json.dumps(companies, indent=2))
    else:
        # Display as table
        table = Table(title=f"Fortune 100 Companies ({len(companies)} total)")
        table.add_column("Rank", style="cyan", justify="right")
        table.add_column("Company", style="white")
        table.add_column("Ticker", style="magenta")
        table.add_column("CIK", style="green")
        table.add_column("Sector", style="yellow")

        for company in companies:
            table.add_row(
                str(company["rank"]),
                company["name"],
                company["ticker"],
                company["cik"],
                company["sector"],
            )

        console.print(table)

        # Summary by sector
        sector_counts = {}
        for company in companies:
            sector = company["sector"]
            sector_counts[sector] = sector_counts.get(sector, 0) + 1

        console.print("\n[bold]By Sector:[/bold]")
        for sector, count in sorted(sector_counts.items()):
            console.print(f"  {sector}: {count}")


# ============================================================================
# Helper Functions
# ============================================================================


def _filter_companies(
    rank_start: int,
    rank_end: int,
    sector: Optional[str],
) -> list[dict]:
    """
    Filter Fortune 100 companies by rank and sector.

    Args:
        rank_start: Starting rank (inclusive)
        rank_end: Ending rank (inclusive)
        sector: Sector filter (optional)

    Returns:
        List of company dictionaries matching filters
    """
    companies = [
        c
        for c in FORTUNE_100_COMPANIES
        if rank_start <= c["rank"] <= rank_end
    ]

    if sector:
        companies = [c for c in companies if c["sector"] == sector]

    return companies


async def _run_full_pipeline(
    companies: list[dict],
    output: Path,
    format: str,
    max_concurrent: int,
    verbose: bool,
):
    """
    Run full pipeline: SCT + Tax extraction.

    Args:
        companies: List of company dictionaries
        output: Output directory
        format: Output format (json, csv, both)
        max_concurrent: Max concurrent workers
        verbose: Verbose logging
    """
    # Create output directory
    output.mkdir(parents=True, exist_ok=True)

    # Progress tracking
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        TextColumn("•"),
        TimeRemainingColumn(),
        console=console,
    )

    with progress:
        task = progress.add_task(
            "[cyan]Processing companies...",
            total=len(companies),
        )

        results = []
        for company in companies:
            progress.update(
                task,
                description=f"[cyan]Processing {company['name']} (#{company['rank']})",
            )

            # Extract SCT data
            sct_result = await _extract_sct_for_company(company, verbose)

            # Extract Tax data
            tax_result = await _extract_tax_for_company(company, verbose)

            # Combine results
            combined = {
                "company": company,
                "sct_data": sct_result,
                "tax_data": tax_result,
            }
            results.append(combined)

            progress.advance(task)

    # Write results
    _write_results(results, output, format)

    # Display summary
    _display_summary(results, "Full Pipeline")


async def _run_sct_pipeline(
    companies: list[dict],
    output: Path,
    format: str,
    max_concurrent: int,
    verbose: bool,
):
    """Run SCT extraction pipeline."""
    output.mkdir(parents=True, exist_ok=True)

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
    )

    with progress:
        task = progress.add_task(
            "[cyan]Extracting SCT data...",
            total=len(companies),
        )

        results = []
        for company in companies:
            progress.update(
                task,
                description=f"[cyan]{company['name']} (#{company['rank']})",
            )

            result = await _extract_sct_for_company(company, verbose)
            results.append({"company": company, "sct_data": result})

            progress.advance(task)

    _write_results(results, output, format)
    _display_summary(results, "SCT Extraction")


async def _run_tax_pipeline(
    companies: list[dict],
    output: Path,
    format: str,
    max_concurrent: int,
    verbose: bool,
):
    """Run Tax extraction pipeline."""
    output.mkdir(parents=True, exist_ok=True)

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
    )

    with progress:
        task = progress.add_task(
            "[cyan]Extracting Tax data...",
            total=len(companies),
        )

        results = []
        for company in companies:
            progress.update(
                task,
                description=f"[cyan]{company['name']} (#{company['rank']})",
            )

            result = await _extract_tax_for_company(company, verbose)
            results.append({"company": company, "tax_data": result})

            progress.advance(task)

    _write_results(results, output, format)
    _display_summary(results, "Tax Extraction")


async def _extract_sct_for_company(company: dict, verbose: bool) -> Optional[dict]:
    """
    Extract SCT data for a single company.

    Args:
        company: Company dictionary with name, cik, ticker
        verbose: Verbose logging

    Returns:
        Extracted SCT data dict or None if extraction failed
    """
    try:
        adapter = SCTAdapter(company=company["name"], cik=company["cik"])

        # TODO: Fetch DEF 14A filing HTML from EDGAR
        # For now, return placeholder
        if verbose:
            console.print(f"  [yellow]TODO: Fetch DEF 14A for {company['ticker']}[/yellow]")

        # Mock extraction (replace with actual EDGAR fetching)
        result = None  # await adapter.extract(filing_type="DEF 14A", html=html)

        if verbose and result:
            console.print(f"  [green]✓ SCT extracted: {len(result.get('executives', []))} executives[/green]")

        return result

    except Exception as e:
        if verbose:
            console.print(f"  [red]✗ SCT extraction failed: {e}[/red]")
        logger.error("SCT extraction failed", company=company["name"], error=str(e))
        return None


async def _extract_tax_for_company(company: dict, verbose: bool) -> Optional[dict]:
    """
    Extract Tax data for a single company.

    Args:
        company: Company dictionary
        verbose: Verbose logging

    Returns:
        Extracted Tax data dict or None
    """
    try:
        adapter = TaxAdapter(company=company["name"], fiscal_year_end="2023-12-31")

        # TODO: Fetch 10-K filing HTML from EDGAR
        if verbose:
            console.print(f"  [yellow]TODO: Fetch 10-K for {company['ticker']}[/yellow]")

        # Mock extraction
        result = None  # await adapter.extract(filing_type="10-K", html=html)

        if verbose and result:
            console.print(f"  [green]✓ Tax extracted[/green]")

        return result

    except Exception as e:
        if verbose:
            console.print(f"  [red]✗ Tax extraction failed: {e}[/red]")
        logger.error("Tax extraction failed", company=company["name"], error=str(e))
        return None


def _write_results(results: list[dict], output: Path, format: str):
    """
    Write results to output directory.

    Args:
        results: List of result dictionaries
        output: Output directory path
        format: Output format (json, csv, both)
    """
    import json

    if format in ["json", "both"]:
        json_path = output / "results.json"
        with open(json_path, "w") as f:
            json.dump(results, f, indent=2, default=str)
        console.print(f"[green]✓ Results saved to {json_path}[/green]")

    if format in ["csv", "both"]:
        csv_path = output / "results.csv"
        # TODO: Implement CSV export
        console.print(f"[yellow]CSV export not yet implemented: {csv_path}[/yellow]")


def _display_summary(results: list[dict], pipeline_name: str):
    """
    Display extraction summary.

    Args:
        results: List of result dictionaries
        pipeline_name: Name of pipeline (for display)
    """
    total = len(results)
    successful = sum(1 for r in results if r.get("sct_data") or r.get("tax_data"))
    failed = total - successful

    console.print(f"\n[bold]{pipeline_name} Summary:[/bold]")
    console.print(f"  Total: {total}")
    console.print(f"  [green]Successful: {successful}[/green]")
    console.print(f"  [red]Failed: {failed}[/red]")

    if total > 0:
        success_rate = (successful / total) * 100
        console.print(f"  Success Rate: {success_rate:.1f}%")
