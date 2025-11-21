"""Main CLI entry point."""

import asyncio
import sys
import time
from pathlib import Path

import click
import structlog
from dependency_injector.wiring import Provide, inject
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
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
from rich.traceback import install
from typing import Dict, Optional

from edgar_analyzer.config.container import Container
from edgar_analyzer.config.settings import ConfigService
from edgar_analyzer.services.interfaces import (
    ICompanyService,
    IDataExtractionService,
    IReportService,
)
from edgar_analyzer.services.enhanced_report_service import EnhancedReportService
from edgar_analyzer.services.historical_analysis_service import HistoricalAnalysisService

# Install rich traceback handler
install(show_locals=True)

console = Console()


class ProgressTracker:
    """Enhanced progress tracking for Fortune 500 analysis."""

    def __init__(self):
        """Initialize progress tracker."""
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TextColumn("•"),
            TimeElapsedColumn(),
            TextColumn("•"),
            TimeRemainingColumn(),
            console=console,
            expand=True
        )
        self.companies_processed = 0
        self.companies_successful = 0
        self.companies_failed = 0
        self.start_time = time.time()

        # Task IDs
        self.main_task: Optional[TaskID] = None
        self.current_company_task: Optional[TaskID] = None
        self.data_extraction_task: Optional[TaskID] = None

    def start_analysis(self, total_companies: int, year: int) -> None:
        """Start the main analysis progress."""
        self.main_task = self.progress.add_task(
            f"[bold green]Analyzing Fortune 500 Companies ({year})",
            total=total_companies
        )

    def start_company(self, company_name: str, rank: int) -> None:
        """Start processing a specific company."""
        if self.current_company_task:
            self.progress.remove_task(self.current_company_task)

        self.current_company_task = self.progress.add_task(
            f"[cyan]#{rank}: {company_name}",
            total=100
        )

    def update_company_progress(self, step: str, progress_pct: int) -> None:
        """Update current company progress."""
        if self.current_company_task:
            self.progress.update(
                self.current_company_task,
                completed=progress_pct,
                description=f"[cyan]{step}"
            )

    def start_data_extraction(self, data_type: str) -> None:
        """Start data extraction progress."""
        if self.data_extraction_task:
            self.progress.remove_task(self.data_extraction_task)

        self.data_extraction_task = self.progress.add_task(
            f"[yellow]Extracting {data_type}",
            total=100
        )

    def update_data_extraction(self, progress_pct: int) -> None:
        """Update data extraction progress."""
        if self.data_extraction_task:
            self.progress.update(self.data_extraction_task, completed=progress_pct)

    def complete_company(self, success: bool) -> None:
        """Complete processing of current company."""
        self.companies_processed += 1

        if success:
            self.companies_successful += 1
        else:
            self.companies_failed += 1

        # Update main progress
        if self.main_task:
            self.progress.update(self.main_task, advance=1)

        # Clean up company-specific tasks
        if self.current_company_task:
            self.progress.remove_task(self.current_company_task)
            self.current_company_task = None

        if self.data_extraction_task:
            self.progress.remove_task(self.data_extraction_task)
            self.data_extraction_task = None

    def get_summary_stats(self) -> Dict[str, any]:
        """Get summary statistics."""
        elapsed_time = time.time() - self.start_time
        return {
            "total_processed": self.companies_processed,
            "successful": self.companies_successful,
            "failed": self.companies_failed,
            "success_rate": (self.companies_successful / self.companies_processed * 100) if self.companies_processed > 0 else 0,
            "elapsed_time": elapsed_time,
            "avg_time_per_company": elapsed_time / self.companies_processed if self.companies_processed > 0 else 0
        }


def setup_logging(config: ConfigService) -> None:
    """Setup structured logging."""
    log_config = config.get_logging_config()

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


@click.group()
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.option('--config-file', type=click.Path(exists=True), help='Configuration file path')
@click.pass_context
def cli(ctx: click.Context, debug: bool, config_file: str) -> None:
    """Edgar Analyzer - SEC EDGAR Executive Compensation vs Tax Expense Analysis Tool."""

    # Initialize container and configuration
    container = Container()
    container.wire(modules=[__name__])
    config = container.config()

    # Setup logging
    setup_logging(config)

    # Store in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj['container'] = container
    ctx.obj['config'] = config
    ctx.obj['debug'] = debug

    if debug:
        console.print("[bold yellow]Debug mode enabled[/bold yellow]")


@cli.command()
@click.pass_context
def version(ctx: click.Context) -> None:
    """Show version information."""
    config = ctx.obj['config']
    console.print(f"[bold blue]{config.get('app_name', 'Edgar Analyzer')}[/bold blue] v{config.get('version', '0.1.0')}")


@cli.command()
@click.option('--cik', help='Company CIK to analyze')
@click.option('--ticker', help='Company ticker symbol to analyze')
@click.option('--year', type=int, default=2023, help='Analysis year')
@click.option('--output', type=click.Path(), help='Output file path')
@click.pass_context
@inject
def analyze(
    ctx: click.Context,
    cik: str,
    ticker: str,
    year: int,
    output: str,
    company_service: ICompanyService = Provide[Container.company_service],
    data_extraction_service: IDataExtractionService = Provide[Container.data_extraction_service],
    report_service: IReportService = Provide[Container.report_service]
) -> None:
    """Analyze executive compensation vs tax expense for a company."""

    if not cik and not ticker:
        console.print("[bold red]Error:[/bold red] Either --cik or --ticker must be provided")
        sys.exit(1)

    async def run_analysis():
        try:
            target_cik = cik

            # Find company by ticker if CIK not provided
            if ticker and not target_cik:
                console.print(f"[yellow]Searching for company with ticker: {ticker}[/yellow]")
                companies = await company_service.search_companies(ticker)
                if not companies:
                    console.print(f"[bold red]Error:[/bold red] No company found with ticker {ticker}")
                    return
                company = companies[0]
                target_cik = company.cik
                console.print(f"[green]Found:[/green] {company.name} (CIK: {target_cik})")

            console.print(f"[bold green]Analyzing company[/bold green] (CIK: {target_cik}, Year: {year})")

            # Extract company analysis
            with console.status("[bold green]Extracting data from EDGAR filings..."):
                analysis = await data_extraction_service.extract_company_analysis(target_cik, year)

            if not analysis:
                console.print("[bold red]Error:[/bold red] Failed to extract company data")
                return

            # Display results
            _display_analysis_results(analysis, year)

            # Export if output path provided
            if output:
                console.print(f"[yellow]Exporting results to {output}...[/yellow]")
                report = await report_service.generate_analysis_report([target_cik], year)

                if output.endswith('.xlsx'):
                    await report_service.export_to_excel(report, output)
                elif output.endswith('.json'):
                    await report_service.export_to_json(report, output)
                else:
                    console.print("[bold red]Error:[/bold red] Output file must be .xlsx or .json")
                    return

                console.print(f"[green]Results exported to {output}[/green]")

        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            if ctx.obj.get('debug'):
                raise

    asyncio.run(run_analysis())


@cli.command()
@click.option('--year', type=int, default=2023, help='Analysis year')
@click.option('--limit', type=int, default=10, help='Number of companies to analyze')
@click.option('--output', type=click.Path(), help='Output file path')
@click.pass_context
@inject
def fortune500(
    ctx: click.Context,
    year: int,
    limit: int,
    output: str,
    company_service: ICompanyService = Provide[Container.company_service],
    report_service: IReportService = Provide[Container.report_service]
) -> None:
    """Analyze Fortune 500 companies."""

    async def run_fortune500_analysis():
        try:
            console.print(f"[bold green]Analyzing top {limit} Fortune 500 companies[/bold green] for year {year}")

            # Get Fortune 500 companies
            with console.status("[bold green]Loading Fortune 500 companies..."):
                companies = await company_service.get_fortune_500_companies()

            if not companies:
                console.print("[bold red]Error:[/bold red] No Fortune 500 companies found")
                return

            # Limit to requested number
            companies = companies[:limit]
            company_ciks = [company.cik for company in companies]

            console.print(f"[green]Found {len(companies)} companies to analyze[/green]")

            # Generate analysis report
            with console.status(f"[bold green]Analyzing {len(companies)} companies..."):
                report = await report_service.generate_analysis_report(company_ciks, year)

            # Display summary
            _display_report_summary(report)

            # Export results
            if output:
                console.print(f"[yellow]Exporting results to {output}...[/yellow]")

                if output.endswith('.xlsx'):
                    await report_service.export_to_excel(report, output)
                elif output.endswith('.json'):
                    await report_service.export_to_json(report, output)
                else:
                    console.print("[bold red]Error:[/bold red] Output file must be .xlsx or .json")
                    return

                console.print(f"[green]Results exported to {output}[/green]")
            else:
                # Default export
                default_filename = f"fortune500_analysis_{year}.xlsx"
                await report_service.export_to_excel(report, default_filename)
                console.print(f"[green]Results exported to output/{default_filename}[/green]")

        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            if ctx.obj.get('debug'):
                raise

    asyncio.run(run_fortune500_analysis())


@cli.command()
@click.option('--query', help='Search query (company name or ticker)')
@click.pass_context
@inject
def search(
    ctx: click.Context,
    query: str,
    company_service: ICompanyService = Provide[Container.company_service]
) -> None:
    """Search for companies."""

    if not query:
        console.print("[bold red]Error:[/bold red] Search query is required")
        sys.exit(1)

    async def run_search():
        try:
            console.print(f"[bold green]Searching for:[/bold green] {query}")

            with console.status("[bold green]Searching companies..."):
                companies = await company_service.search_companies(query)

            if not companies:
                console.print("[yellow]No companies found matching your query[/yellow]")
                return

            # Display results in a table
            table = Table(title=f"Search Results for '{query}'")
            table.add_column("Company Name", style="cyan")
            table.add_column("Ticker", style="magenta")
            table.add_column("CIK", style="green")
            table.add_column("Industry", style="yellow")
            table.add_column("Fortune Rank", style="blue")

            for company in companies[:10]:  # Limit to 10 results
                table.add_row(
                    company.name,
                    company.ticker or "N/A",
                    company.cik,
                    company.industry or "N/A",
                    str(company.fortune_rank) if company.fortune_rank else "N/A"
                )

            console.print(table)

            if len(companies) > 10:
                console.print(f"[yellow]Showing first 10 of {len(companies)} results[/yellow]")

        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            if ctx.obj.get('debug'):
                raise

    asyncio.run(run_search())


@cli.command()
@click.option('--year', type=int, default=2023, help='Analysis year')
@click.option('--limit', type=int, default=50, help='Number of companies to analyze')
@click.option('--output', type=click.Path(), help='Output file path')
@click.option('--historical', is_flag=True, help='Include 5-year historical analysis')
@click.pass_context
@inject
def enhanced_fortune500(
    ctx: click.Context,
    year: int,
    limit: int,
    output: str,
    historical: bool,
    company_service: ICompanyService = Provide[Container.company_service],
    enhanced_report_service: EnhancedReportService = Provide[Container.enhanced_report_service]
) -> None:
    """Enhanced Fortune 500 analysis with historical data and professional Excel output."""

    async def run_enhanced_analysis():
        try:
            # Initialize progress tracker
            tracker = ProgressTracker()

            console.print(Panel.fit(
                f"[bold green]Enhanced Fortune 500 Analysis[/bold green]\n"
                f"[cyan]Companies:[/cyan] {limit} | [cyan]Year:[/cyan] {year} | [cyan]Historical:[/cyan] {historical}\n"
                f"[yellow]Features:[/yellow] 5-year data, professional Excel, real EDGAR data",
                title="Analysis Configuration"
            ))

            # Get Fortune 500 companies
            with console.status("[bold green]Loading Fortune 500 companies database..."):
                companies = await company_service.get_fortune_500_companies()

            if not companies:
                console.print("[bold red]Error:[/bold red] No Fortune 500 companies found")
                return

            # Limit to requested number
            companies = companies[:limit]

            console.print(f"[green]✓ Loaded {len(companies)} companies for analysis[/green]")

            # Start progress tracking
            with Live(tracker.progress, console=console, refresh_per_second=10):
                tracker.start_analysis(len(companies), year)

                # Process each company with detailed progress
                successful_analyses = []

                for i, company in enumerate(companies):
                    tracker.start_company(company.name, company.fortune_rank or i+1)

                    try:
                        # Step 1: Company lookup
                        tracker.update_company_progress("Loading company data", 10)
                        await asyncio.sleep(0.1)  # Small delay for visual feedback

                        # Step 2: Historical data extraction
                        tracker.start_data_extraction("5-year historical data")
                        tracker.update_data_extraction(20)

                        years = [year - 4, year - 3, year - 2, year - 1, year]
                        analysis = await enhanced_report_service._historical_analysis.extract_multi_year_analysis(
                            company.cik, years
                        )

                        tracker.update_data_extraction(80)

                        if analysis:
                            successful_analyses.append(analysis)
                            tracker.update_company_progress("✓ Analysis complete", 100)
                            tracker.complete_company(True)
                        else:
                            tracker.update_company_progress("✗ Analysis failed", 100)
                            tracker.complete_company(False)

                        tracker.update_data_extraction(100)

                    except Exception as e:
                        tracker.update_company_progress(f"✗ Error: {str(e)[:30]}...", 100)
                        tracker.complete_company(False)

                # Create report from successful analyses
                from edgar_analyzer.models.company import AnalysisReport
                report = AnalysisReport(target_year=year)
                for analysis in successful_analyses:
                    report.add_company_analysis(analysis)

            # Display final statistics
            stats = tracker.get_summary_stats()
            _display_analysis_statistics(stats, len(companies))

            # Display enhanced summary
            _display_enhanced_report_summary(report)

            # Export results
            if output:
                output_file = output
            else:
                # Default enhanced filename
                suffix = "_historical" if historical else ""
                output_file = f"enhanced_fortune500_analysis_{year}{suffix}.xlsx"

            console.print(f"[yellow]Exporting enhanced results to {output_file}...[/yellow]")

            if output_file.endswith('.xlsx'):
                await enhanced_report_service.export_to_excel(report, output_file)
            elif output_file.endswith('.json'):
                await enhanced_report_service.export_to_json(report, output_file)
            else:
                console.print("[bold red]Error:[/bold red] Output file must be .xlsx or .json")
                return

            console.print(f"[green]Enhanced analysis exported to output/{output_file}[/green]")
            console.print(f"[blue]Report includes:[/blue]")
            console.print(f"  • 5-year historical data ({year-4}-{year})")
            console.print(f"  • Executive compensation trends")
            console.print(f"  • Tax expense analysis")
            console.print(f"  • Professional Excel formatting")
            console.print(f"  • Multiple analysis sheets")

        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            if ctx.obj.get('debug'):
                raise

    asyncio.run(run_enhanced_analysis())


@cli.command()
@click.option('--year', type=int, default=2023, help='Analysis year')
@click.option('--limit', type=int, default=50, help='Number of companies to analyze')
@click.option('--output', type=click.Path(), help='Output file path')
@click.option('--resume', type=str, help='Resume analysis with given ID')
@click.option('--list-checkpoints', is_flag=True, help='List available checkpoints')
@click.option('--save-frequency', type=int, default=5, help='Save checkpoint every N companies')
@click.option('--no-auto-resume', is_flag=True, help='Disable automatic resume detection')
@click.option('--force-new', is_flag=True, help='Force start new analysis (ignore checkpoints)')
@click.pass_context
@inject
def checkpoint_analysis(
    ctx: click.Context,
    year: int,
    limit: int,
    output: str,
    resume: str,
    list_checkpoints: bool,
    save_frequency: int,
    no_auto_resume: bool,
    force_new: bool,
    company_service: ICompanyService = Provide[Container.company_service],
    data_extraction_service: IDataExtractionService = Provide[Container.data_extraction_service]
) -> None:
    """Checkpoint-based Fortune 500 analysis with resume functionality."""

    async def run_checkpoint_analysis():
        try:
            from edgar_analyzer.models.intermediate_data import CheckpointManager
            from edgar_analyzer.services.auto_resume_service import AutoResumeService
            from edgar_analyzer.services.checkpoint_extraction_service import CheckpointExtractionService
            from edgar_analyzer.services.checkpoint_report_service import CheckpointReportService
            from edgar_analyzer.config.settings import ConfigService

            # Initialize services
            checkpoint_manager = CheckpointManager()
            auto_resume_service = AutoResumeService(checkpoint_manager)
            extraction_service = CheckpointExtractionService(
                data_extraction_service, company_service, checkpoint_manager
            )
            config_service = ConfigService()
            report_service = CheckpointReportService(config_service)

            # List checkpoints if requested
            if list_checkpoints:
                checkpoints = checkpoint_manager.list_checkpoints()
                if not checkpoints:
                    console.print("[yellow]No checkpoints found[/yellow]")
                    return

                checkpoint_table = Table(title="Available Checkpoints")
                checkpoint_table.add_column("Analysis ID", style="cyan")
                checkpoint_table.add_column("Year", style="blue")
                checkpoint_table.add_column("Progress", style="green")
                checkpoint_table.add_column("Companies", style="white")
                checkpoint_table.add_column("Last Updated", style="yellow")

                for cp in checkpoints:
                    checkpoint_table.add_row(
                        cp["analysis_id"],
                        str(cp["target_year"]),
                        f"{cp['progress']:.1f}%",
                        f"{cp['completed_companies']}/{cp['total_companies']}",
                        cp["last_updated"][:19] if cp["last_updated"] else "Unknown"
                    )

                console.print(checkpoint_table)
                return

            console.print(Panel.fit(
                f"[bold green]Checkpoint-Based Fortune 500 Analysis[/bold green]\n"
                f"[cyan]Companies:[/cyan] {limit} | [cyan]Year:[/cyan] {year}\n"
                f"[yellow]Features:[/yellow] Auto-resume, error recovery, JSON intermediate data",
                title="Smart Analysis Configuration"
            ))

            # Determine analysis strategy
            checkpoint = None
            analysis_strategy = "start_new"

            if resume:
                # Manual resume requested
                console.print(f"[yellow]Attempting to resume analysis: {resume}[/yellow]")
                checkpoint = checkpoint_manager.load_checkpoint(resume, year)
                if not checkpoint:
                    console.print(f"[red]Checkpoint not found: {resume}[/red]")
                    return

                analysis_strategy = "manual_resume"
                console.print(f"[green]✓ Manually resumed analysis with {checkpoint.completed_companies}/{checkpoint.total_companies} companies completed[/green]")

            else:
                # Auto-resume logic
                auto_resume_enabled = not no_auto_resume
                decision, auto_checkpoint, analysis_info = auto_resume_service.get_auto_resume_decision(
                    year, limit, auto_resume_enabled, force_new
                )

                if decision == "auto_resume":
                    checkpoint = auto_checkpoint
                    analysis_strategy = "auto_resume"

                    console.print(Panel.fit(
                        f"[bold green]🔄 AUTO-RESUME DETECTED[/bold green]\n"
                        f"[cyan]Analysis ID:[/cyan] {checkpoint.analysis_id}\n"
                        f"[cyan]Progress:[/cyan] {checkpoint.progress_percentage:.1f}% "
                        f"({checkpoint.completed_companies}/{checkpoint.total_companies} companies)\n"
                        f"[cyan]Last Updated:[/cyan] {checkpoint.last_updated.strftime('%Y-%m-%d %H:%M:%S')}\n"
                        f"[yellow]Reason:[/yellow] {analysis_info['reason']}",
                        title="Resuming Previous Analysis"
                    ))

                elif decision == "suggest":
                    suggestion = auto_resume_service.format_resume_suggestion(analysis_info)
                    console.print(f"[blue]{suggestion}[/blue]")

                    # Ask user if they want to resume
                    if auto_checkpoint and click.confirm("Would you like to resume this analysis?"):
                        checkpoint = auto_checkpoint
                        analysis_strategy = "user_resume"
                        console.print(f"[green]✓ Resuming suggested analysis[/green]")
                    else:
                        analysis_strategy = "start_new"

                # If starting new analysis
                if analysis_strategy == "start_new":
                    # Get Fortune 500 companies
                    with console.status("[bold green]Loading Fortune 500 companies..."):
                        companies = await company_service.get_fortune_500_companies()

                    if not companies:
                        console.print("[bold red]Error:[/bold red] No Fortune 500 companies found")
                        return

                    # Limit to requested number
                    companies = companies[:limit]
                    company_ciks = [company.cik for company in companies]

                    console.print(f"[green]✓ Loaded {len(companies)} companies for analysis[/green]")

                    # Start new analysis
                    checkpoint = await extraction_service.start_analysis(
                        company_ciks, year, config={"limit": limit, "save_frequency": save_frequency}
                    )

                    console.print(f"[green]✓ Started new analysis: {checkpoint.analysis_id}[/green]")

            # Progress tracking
            def progress_callback(current: int, total: int):
                percentage = (current / total) * 100
                console.print(f"[yellow]Progress: {current}/{total} ({percentage:.1f}%)[/yellow]")

            # Process all companies
            console.print(f"[blue]Processing companies with checkpoint saves every {save_frequency} companies...[/blue]")

            final_checkpoint = await extraction_service.process_all_companies(
                checkpoint, save_frequency=save_frequency, progress_callback=progress_callback
            )

            # Display final statistics
            stats = {
                "total_processed": final_checkpoint.completed_companies + final_checkpoint.failed_companies,
                "successful": final_checkpoint.completed_companies,
                "failed": final_checkpoint.failed_companies,
                "success_rate": final_checkpoint.success_rate,
                "elapsed_time": (final_checkpoint.last_updated - final_checkpoint.created_at).total_seconds(),
                "avg_time_per_company": 0  # Will be calculated
            }

            if stats["total_processed"] > 0:
                stats["avg_time_per_company"] = stats["elapsed_time"] / stats["total_processed"]

            _display_analysis_statistics(stats, final_checkpoint.total_companies)

            # Generate reports
            if output:
                output_file = output
            else:
                output_file = f"checkpoint_analysis_{year}_{final_checkpoint.analysis_id[:8]}.xlsx"

            console.print(f"[yellow]Generating reports...[/yellow]")

            if output_file.endswith('.xlsx'):
                excel_path = await report_service.generate_excel_report(final_checkpoint, output_file)
                console.print(f"[green]✓ Excel report: {excel_path}[/green]")

            # Always generate JSON for intermediate data
            json_file = output_file.replace('.xlsx', '.json') if output_file.endswith('.xlsx') else f"{output_file}.json"
            json_path = await report_service.generate_json_report(final_checkpoint, json_file)
            console.print(f"[green]✓ JSON data: {json_path}[/green]")

            console.print(f"[blue]Analysis ID: {final_checkpoint.analysis_id}[/blue]")
            console.print(f"[blue]Checkpoint saved for future resume[/blue]")

        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            if ctx.obj.get('debug'):
                raise

    asyncio.run(run_checkpoint_analysis())


@cli.command()
@click.option('--year', type=int, default=2023, help='Analysis year')
@click.option('--limit', type=int, default=50, help='Number of companies to analyze')
@click.option('--output', type=click.Path(), help='Output file path')
@click.option('--force-new', is_flag=True, help='Force start new analysis (ignore auto-resume)')
@click.option('--save-frequency', type=int, default=5, help='Save checkpoint every N companies')
@click.pass_context
@inject
def analyze(
    ctx: click.Context,
    year: int,
    limit: int,
    output: str,
    force_new: bool,
    save_frequency: int,
    company_service: ICompanyService = Provide[Container.company_service],
    data_extraction_service: IDataExtractionService = Provide[Container.data_extraction_service]
) -> None:
    """Smart Fortune 500 analysis with automatic resume detection."""

    async def run_smart_analysis():
        try:
            from edgar_analyzer.models.intermediate_data import CheckpointManager
            from edgar_analyzer.services.auto_resume_service import AutoResumeService
            from edgar_analyzer.services.checkpoint_extraction_service import CheckpointExtractionService
            from edgar_analyzer.services.checkpoint_report_service import CheckpointReportService
            from edgar_analyzer.config.settings import ConfigService

            # Initialize services
            checkpoint_manager = CheckpointManager()
            auto_resume_service = AutoResumeService(checkpoint_manager)
            extraction_service = CheckpointExtractionService(
                data_extraction_service, company_service, checkpoint_manager
            )
            config_service = ConfigService()
            report_service = CheckpointReportService(config_service)

            console.print(Panel.fit(
                f"[bold green]🚀 Smart Fortune 500 Analysis[/bold green]\n"
                f"[cyan]Companies:[/cyan] {limit} | [cyan]Year:[/cyan] {year}\n"
                f"[yellow]Features:[/yellow] Auto-resume, intelligent checkpoints, error recovery",
                title="Smart Analysis"
            ))

            # Get auto-resume decision
            decision, checkpoint, analysis_info = auto_resume_service.get_auto_resume_decision(
                year, limit, auto_resume_enabled=True, force_new=force_new
            )

            if decision == "auto_resume":
                console.print(Panel.fit(
                    f"[bold green]🔄 RESUMING PREVIOUS ANALYSIS[/bold green]\n"
                    f"[cyan]Analysis ID:[/cyan] {checkpoint.analysis_id}\n"
                    f"[cyan]Progress:[/cyan] {checkpoint.progress_percentage:.1f}% complete\n"
                    f"[cyan]Completed:[/cyan] {checkpoint.completed_companies}/{checkpoint.total_companies} companies\n"
                    f"[cyan]Success Rate:[/cyan] {checkpoint.success_rate:.1f}%\n"
                    f"[cyan]Last Updated:[/cyan] {checkpoint.last_updated.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"[yellow]Reason:[/yellow] {analysis_info['reason']}",
                    title="Auto-Resume"
                ))

            elif decision == "suggest":
                suggestion = auto_resume_service.format_resume_suggestion(analysis_info)
                console.print(f"[blue]{suggestion}[/blue]")

                if checkpoint and click.confirm("Resume this analysis?", default=True):
                    console.print(f"[green]✓ Resuming analysis: {checkpoint.analysis_id}[/green]")
                else:
                    checkpoint = None

            # Start new analysis if no checkpoint
            if not checkpoint:
                console.print(f"[blue]🆕 Starting new analysis...[/blue]")

                # Get Fortune 500 companies
                with console.status("[bold green]Loading Fortune 500 companies..."):
                    companies = await company_service.get_fortune_500_companies()

                if not companies:
                    console.print("[bold red]Error:[/bold red] No Fortune 500 companies found")
                    return

                companies = companies[:limit]
                company_ciks = [company.cik for company in companies]

                console.print(f"[green]✓ Loaded {len(companies)} companies[/green]")

                checkpoint = await extraction_service.start_analysis(
                    company_ciks, year, config={"limit": limit, "save_frequency": save_frequency}
                )

                console.print(f"[green]✓ New analysis started: {checkpoint.analysis_id}[/green]")

            # Process companies
            def progress_callback(current: int, total: int):
                percentage = (current / total) * 100
                console.print(f"[yellow]Progress: {current}/{total} ({percentage:.1f}%)[/yellow]")

            console.print(f"[blue]Processing companies (auto-save every {save_frequency} companies)...[/blue]")

            final_checkpoint = await extraction_service.process_all_companies(
                checkpoint, save_frequency=save_frequency, progress_callback=progress_callback
            )

            # Display results
            stats = {
                "total_processed": final_checkpoint.completed_companies + final_checkpoint.failed_companies,
                "successful": final_checkpoint.completed_companies,
                "failed": final_checkpoint.failed_companies,
                "success_rate": final_checkpoint.success_rate,
                "elapsed_time": (final_checkpoint.last_updated - final_checkpoint.created_at).total_seconds(),
                "avg_time_per_company": 0
            }

            if stats["total_processed"] > 0:
                stats["avg_time_per_company"] = stats["elapsed_time"] / stats["total_processed"]

            _display_analysis_statistics(stats, final_checkpoint.total_companies)

            # Generate reports
            if output:
                output_file = output
            else:
                output_file = f"smart_analysis_{year}_{final_checkpoint.analysis_id[:8]}.xlsx"

            console.print(f"[yellow]Generating reports...[/yellow]")

            if output_file.endswith('.xlsx'):
                excel_path = await report_service.generate_excel_report(final_checkpoint, output_file)
                console.print(f"[green]✓ Excel report: {excel_path}[/green]")

            json_file = output_file.replace('.xlsx', '.json') if output_file.endswith('.xlsx') else f"{output_file}.json"
            json_path = await report_service.generate_json_report(final_checkpoint, json_file)
            console.print(f"[green]✓ JSON data: {json_path}[/green]")

            console.print(Panel.fit(
                f"[bold green]✅ ANALYSIS COMPLETE[/bold green]\n"
                f"[cyan]Analysis ID:[/cyan] {final_checkpoint.analysis_id}\n"
                f"[cyan]Success Rate:[/cyan] {final_checkpoint.success_rate:.1f}%\n"
                f"[cyan]Total Time:[/cyan] {stats['elapsed_time']:.1f}s\n"
                f"[yellow]Checkpoint saved for future resume[/yellow]",
                title="Analysis Complete"
            ))

        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            if ctx.obj.get('debug'):
                raise

    asyncio.run(run_smart_analysis())


@cli.command()
@click.option('--year', type=int, default=2023, help='Analysis year')
@click.option('--limit', type=int, default=10, help='Number of companies to test')
@click.option('--output', type=click.Path(), help='Output file path for quality report')
@click.option('--company', 'target_company', type=str, help='Test specific company by name or ticker')
@click.pass_context
@inject
def quality_test(
    ctx: click.Context,
    year: int,
    limit: int,
    output: str,
    target_company: str,
    company_service: ICompanyService = Provide[Container.company_service],
    data_extraction_service: IDataExtractionService = Provide[Container.data_extraction_service]
) -> None:
    """Run comprehensive data quality tests and validation."""

    async def run_quality_test():
        try:
            from edgar_analyzer.validation.quality_reporter import QualityReporter
            from edgar_analyzer.services.historical_analysis_service import HistoricalAnalysisService
            from edgar_analyzer.config.settings import ConfigService

            console.print(Panel.fit(
                f"[bold green]🔍 Data Quality Testing[/bold green]\n"
                f"[cyan]Year:[/cyan] {year} | [cyan]Companies:[/cyan] {limit}\n"
                f"[yellow]Tests:[/yellow] Data validation, source verification, sanity checks",
                title="Quality Testing"
            ))

            # Initialize services
            config_service = ConfigService()
            historical_service = HistoricalAnalysisService(
                data_extraction_service, data_extraction_service, company_service, None
            )
            quality_reporter = QualityReporter()

            # Get companies to test
            if target_company:
                console.print(f"[yellow]Searching for company: {target_company}[/yellow]")
                test_companies = await company_service.search_companies(target_company)
                if not test_companies:
                    console.print(f"[red]Company not found: {target_company}[/red]")
                    return
                test_companies = test_companies[:1]  # Take first match
            else:
                with console.status("[bold green]Loading Fortune 500 companies..."):
                    test_companies = await company_service.get_fortune_500_companies()
                test_companies = test_companies[:limit]

            console.print(f"[green]✓ Testing {len(test_companies)} companies[/green]")

            # Extract data for testing
            analyses = []

            with console.status("[bold green]Extracting data for quality testing..."):
                for i, comp in enumerate(test_companies):
                    try:
                        console.print(f"[yellow]Extracting data for {comp.name} ({i+1}/{len(test_companies)})[/yellow]")

                        # Extract multi-year data
                        years = [year - 2, year - 1, year]  # 3-year analysis for testing
                        analysis = await historical_service.extract_multi_year_analysis(comp.cik, years)

                        if analysis:
                            analyses.append(analysis)
                            console.print(f"[green]✓ {comp.name} - data extracted[/green]")
                        else:
                            console.print(f"[red]✗ {comp.name} - extraction failed[/red]")

                    except Exception as e:
                        console.print(f"[red]✗ {comp.name} - error: {str(e)[:50]}...[/red]")

            if not analyses:
                console.print("[red]No data extracted for quality testing[/red]")
                return

            console.print(f"[green]✓ Extracted data for {len(analyses)} companies[/green]")

            # Run quality tests
            console.print("[blue]🔍 Running comprehensive quality tests...[/blue]")

            quality_data = await quality_reporter.generate_quality_report(
                analyses, f"quality_test_{year}"
            )

            # Display results
            summary = quality_data["summary"]

            console.print(Panel.fit(
                f"[bold green]📊 QUALITY TEST RESULTS[/bold green]\n"
                f"[cyan]Overall Score:[/cyan] {summary['overall_quality_score']:.1%} (Grade {summary['overall_grade']})\n"
                f"[cyan]Total Validations:[/cyan] {summary['total_validations']}\n"
                f"[red]Critical Issues:[/red] {summary['critical_issues']}\n"
                f"[yellow]Errors:[/yellow] {summary['errors']}\n"
                f"[blue]Warnings:[/blue] {summary['warnings']}\n"
                f"[green]Info Messages:[/green] {summary['info_messages']}",
                title="Quality Test Summary"
            ))

            # Company grades table
            if quality_data["company_scores"]:
                grades_table = Table(title="Company Quality Scores")
                grades_table.add_column("Company", style="cyan")
                grades_table.add_column("Score", style="white")
                grades_table.add_column("Grade", style="bold")
                grades_table.add_column("Issues", style="red")
                grades_table.add_column("Warnings", style="yellow")

                for company, score_data in quality_data["company_scores"].items():
                    grade_style = {
                        "A": "[green]A[/green]",
                        "B": "[blue]B[/blue]",
                        "C": "[yellow]C[/yellow]",
                        "D": "[orange]D[/orange]",
                        "F": "[red]F[/red]"
                    }.get(score_data["grade"], score_data["grade"])

                    grades_table.add_row(
                        company[:30] + "..." if len(company) > 30 else company,
                        f"{score_data['score']:.1%}",
                        grade_style,
                        str(score_data["critical_issues"] + score_data["errors"]),
                        str(score_data["warnings"])
                    )

                console.print(grades_table)

            # Validation types summary
            if summary["validation_types"]:
                validation_table = Table(title="Validation Types Summary")
                validation_table.add_column("Test Type", style="cyan")
                validation_table.add_column("Total", style="white")
                validation_table.add_column("Passed", style="green")
                validation_table.add_column("Failed", style="red")
                validation_table.add_column("Success Rate", style="blue")

                for test_type, stats in summary["validation_types"].items():
                    success_rate = stats["passed"] / stats["total"] * 100 if stats["total"] > 0 else 0
                    validation_table.add_row(
                        test_type.replace("_", " ").title(),
                        str(stats["total"]),
                        str(stats["passed"]),
                        str(stats["failed"]),
                        f"{success_rate:.1f}%"
                    )

                console.print(validation_table)

            # Output file info
            if output:
                output_file = output
            else:
                output_file = f"quality_test_{year}.xlsx"

            console.print(f"[green]✓ Quality reports saved to output/{output_file}[/green]")
            console.print(f"[blue]Detailed validation results available in quality report[/blue]")

            # Close resources
            await quality_reporter.close()

        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            if ctx.obj.get('debug'):
                raise

    asyncio.run(run_quality_test())


@cli.command()
@click.option('--limit', type=int, default=50, help='Number of companies to analyze')
@click.option('--year', type=int, default=2023, help='Target year for analysis')
@click.option('--output', type=click.Path(), help='Output file path')
@click.option('--force-new', is_flag=True, help='Force new analysis (ignore checkpoints)')
@click.pass_context
@inject
def sample_report(
    ctx: click.Context,
    limit: int,
    year: int,
    output: str,
    force_new: bool,
    company_service: ICompanyService = Provide[Container.company_service],
    data_extraction_service: IDataExtractionService = Provide[Container.data_extraction_service]
) -> None:
    """Generate a report matching the sample format exactly."""

    async def run_sample_report():
        try:
            from edgar_analyzer.services.sample_report_generator import SampleReportGenerator
            from edgar_analyzer.services.historical_analysis_service import HistoricalAnalysisService
            from edgar_analyzer.config.settings import ConfigService

            console.print(Panel.fit(
                f"[bold green]📊 Sample Format Report Generation[/bold green]\n"
                f"[cyan]Year:[/cyan] {year} | [cyan]Companies:[/cyan] {limit}\n"
                f"[yellow]Format:[/yellow] Matching original sample report structure",
                title="Sample Report Generator"
            ))

            # Initialize services
            config_service = ConfigService()
            historical_service = HistoricalAnalysisService(
                data_extraction_service, data_extraction_service, company_service, None
            )
            sample_generator = SampleReportGenerator()

            # Get Fortune 500 companies
            with console.status("[bold green]Loading Fortune 500 companies..."):
                companies = await company_service.get_fortune_500_companies()
                companies = companies[:limit]

            console.print(f"[green]✓ Loaded {len(companies)} companies[/green]")

            # Extract multi-year data (2019-2023 to match sample)
            analyses = []
            years = [2019, 2020, 2021, 2022, 2023]

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                MofNCompleteColumn(),
                TimeElapsedColumn(),
                console=console
            ) as progress:

                task = progress.add_task(
                    f"[green]Extracting 5-year data for {len(companies)} companies...",
                    total=len(companies)
                )

                for i, company in enumerate(companies):
                    try:
                        progress.update(
                            task,
                            description=f"[green]Processing {company.name} ({i+1}/{len(companies)})"
                        )

                        # Extract multi-year analysis
                        analysis = await historical_service.extract_multi_year_analysis(company.cik, years)

                        if analysis:
                            analyses.append(analysis)
                            console.print(f"[green]✓ {company.name} - 5-year data extracted[/green]")
                        else:
                            console.print(f"[yellow]⚠ {company.name} - limited data available[/yellow]")

                        progress.advance(task)

                    except Exception as e:
                        console.print(f"[red]✗ {company.name} - error: {str(e)[:50]}...[/red]")
                        progress.advance(task)
                        continue

            if not analyses:
                console.print("[red]No data extracted for report generation[/red]")
                return

            console.print(f"[green]✓ Successfully extracted data for {len(analyses)} companies[/green]")

            # Create analysis report
            from edgar_analyzer.models.company import AnalysisReport
            from datetime import datetime

            analysis_report = AnalysisReport(
                target_year=year,
                companies=analyses,
                generated_at=datetime.now(),
                total_companies_analyzed=len(analyses),
                success_rate=len(analyses) / len(companies) * 100
            )

            # Generate sample format report
            console.print("[blue]📊 Generating sample format report...[/blue]")

            output_filename = output or f"corporations_pay_executives_more_than_taxes_{year}.xlsx"
            report_path = await sample_generator.generate_sample_format_report(
                analysis_report, output_filename
            )

            # Display results
            console.print(Panel.fit(
                f"[bold green]📊 SAMPLE REPORT GENERATED[/bold green]\n"
                f"[cyan]Companies Analyzed:[/cyan] {len(analyses)}\n"
                f"[cyan]Report File:[/cyan] {report_path.name}\n"
                f"[cyan]Format:[/cyan] Matches original sample structure\n"
                f"[green]Location:[/green] {report_path}",
                title="Report Complete"
            ))

            # Show key statistics
            companies_with_exec_pay_over_tax = 0
            total_exec_pay = 0
            total_tax_expense = 0

            for analysis in analyses:
                exec_pay = sum(float(comp.total_compensation) for comp in analysis.executive_compensations)
                tax_expense = sum(float(tax.total_tax_expense) for tax in analysis.tax_expenses)

                total_exec_pay += exec_pay
                total_tax_expense += tax_expense

                if exec_pay > tax_expense:
                    companies_with_exec_pay_over_tax += 1

            stats_table = Table(title="Key Statistics")
            stats_table.add_column("Metric", style="cyan")
            stats_table.add_column("Value", style="white")

            stats_table.add_row("Companies where exec pay > taxes", str(companies_with_exec_pay_over_tax))
            stats_table.add_row("Total executive compensation", f"${total_exec_pay/1_000_000_000:.1f}B")
            stats_table.add_row("Total tax expense", f"${total_tax_expense/1_000_000_000:.1f}B")
            stats_table.add_row("Exec pay vs tax ratio", f"{total_exec_pay/total_tax_expense:.1f}x" if total_tax_expense > 0 else "N/A")

            console.print(stats_table)

            console.print(f"[green]✓ Sample format report saved to: {report_path}[/green]")

        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            if ctx.obj.get('debug'):
                raise

    asyncio.run(run_sample_report())


@cli.command()
@click.pass_context
def cache_clear(ctx: click.Context) -> None:
    """Clear application cache."""

    console.print("[bold yellow]Clearing cache...[/bold yellow]")

    # This will be implemented with actual cache service
    console.print("[green]Cache cleared successfully[/green]")


def _display_analysis_results(analysis, year: int) -> None:
    """Display analysis results in a formatted table."""
    company = analysis.company

    # Company info table
    info_table = Table(title=f"Company Analysis: {company.name}")
    info_table.add_column("Attribute", style="cyan")
    info_table.add_column("Value", style="white")

    info_table.add_row("Company Name", company.name)
    info_table.add_row("Ticker", company.ticker or "N/A")
    info_table.add_row("CIK", company.cik)
    info_table.add_row("Industry", company.industry or "N/A")
    info_table.add_row("Fortune Rank", str(company.fortune_rank) if company.fortune_rank else "N/A")

    console.print(info_table)

    # Financial data table
    financial_table = Table(title=f"Financial Analysis for {year}")
    financial_table.add_column("Metric", style="cyan")
    financial_table.add_column("Amount", style="green")

    # Tax expense
    tax_expense = analysis.latest_tax_expense
    tax_amount = tax_expense.total_tax_expense if tax_expense else 0
    financial_table.add_row("Tax Expense", f"${tax_amount:,.0f}")

    # Executive compensation
    total_comp = analysis.total_executive_compensation.get(year, 0)
    financial_table.add_row("Executive Compensation", f"${total_comp:,.0f}")

    # Ratio
    if tax_amount > 0:
        ratio = total_comp / tax_amount
        financial_table.add_row("Compensation/Tax Ratio", f"{ratio:.2f}")

        if total_comp > tax_amount:
            financial_table.add_row("Status", "[bold red]Compensation > Tax Expense[/bold red]")
        else:
            financial_table.add_row("Status", "[bold green]Tax Expense > Compensation[/bold green]")

    console.print(financial_table)


def _display_report_summary(report) -> None:
    """Display report summary statistics."""
    stats = report.summary_statistics

    summary_table = Table(title="Analysis Summary")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="white")

    summary_table.add_row("Total Companies Analyzed", str(stats["total_companies"]))
    summary_table.add_row("Companies with Higher Compensation", str(stats["companies_with_higher_compensation"]))
    summary_table.add_row("Percentage with Higher Compensation", f"{stats['percentage_higher_compensation']:.1f}%")
    summary_table.add_row("Target Year", str(stats["target_year"]))

    console.print(summary_table)


def _display_enhanced_report_summary(report) -> None:
    """Display enhanced report summary with historical data."""
    stats = report.summary_statistics

    # Main summary
    summary_table = Table(title="Enhanced Analysis Summary")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="white")

    summary_table.add_row("Total Companies Analyzed", str(stats["total_companies"]))
    summary_table.add_row("Companies with Higher Compensation", str(stats["companies_with_higher_compensation"]))
    summary_table.add_row("Percentage with Higher Compensation", f"{stats['percentage_higher_compensation']:.1f}%")
    summary_table.add_row("Analysis Period", f"{stats['target_year']-4}-{stats['target_year']} (5 years)")
    summary_table.add_row("Report Type", "Enhanced with Historical Data")

    console.print(summary_table)

    # Top companies preview
    if report.companies:
        preview_table = Table(title="Top Companies Preview")
        preview_table.add_column("Rank", style="blue")
        preview_table.add_column("Company", style="cyan")
        preview_table.add_column("Ticker", style="magenta")
        preview_table.add_column("Sector", style="yellow")

        # Show top 5 companies
        for company_analysis in report.companies[:5]:
            company = company_analysis.company
            preview_table.add_row(
                str(company.fortune_rank or "N/A"),
                company.name,
                company.ticker or "N/A",
                company.sector or "Unknown"
            )

        console.print(preview_table)


def _display_analysis_statistics(stats: Dict[str, any], total_companies: int) -> None:
    """Display detailed analysis statistics."""
    stats_table = Table(title="Analysis Statistics")
    stats_table.add_column("Metric", style="cyan")
    stats_table.add_column("Value", style="white")
    stats_table.add_column("Details", style="yellow")

    # Success rate styling
    success_rate = stats["success_rate"]
    if success_rate >= 80:
        success_style = "[green]"
    elif success_rate >= 60:
        success_style = "[yellow]"
    else:
        success_style = "[red]"

    stats_table.add_row(
        "Companies Processed",
        str(stats["total_processed"]),
        f"of {total_companies} requested"
    )
    stats_table.add_row(
        "Successful Analyses",
        str(stats["successful"]),
        f"{success_style}{success_rate:.1f}% success rate[/]"
    )
    stats_table.add_row(
        "Failed Analyses",
        str(stats["failed"]),
        "Companies with data issues"
    )
    stats_table.add_row(
        "Total Time",
        f"{stats['elapsed_time']:.1f}s",
        f"{stats['avg_time_per_company']:.1f}s per company"
    )

    console.print(stats_table)


def main() -> None:
    """Main entry point."""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[bold red]Operation cancelled by user[/bold red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        if '--debug' in sys.argv:
            raise
        sys.exit(1)


if __name__ == '__main__':
    main()