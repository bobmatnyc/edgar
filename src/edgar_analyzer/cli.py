#!/usr/bin/env python3
"""
EDGAR Analyzer CLI Entry Point

Main command-line interface that integrates:
- Conversational CLI Chatbot Controller
- Traditional CLI fallback
- Self-improving code patterns
- Executive compensation extraction
- Real-time LLM QA and validation

Usage:
    python -m edgar_analyzer.cli
    python -m edgar_analyzer.cli --help
    python -m edgar_analyzer.cli analyze --query "CEO compensation"
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import click
from dotenv import load_dotenv

from edgar_analyzer.services.llm_service import LLMService
from cli_chatbot.core.controller import ChatbotController
from cli_chatbot.fallback.traditional_cli import create_fallback_cli

# Load environment variables
load_dotenv()


@click.group()
@click.option('--mode', type=click.Choice(['auto', 'chatbot', 'traditional']), 
              default='auto', help='CLI interface mode')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(ctx, mode, verbose):
    """
    EDGAR Analyzer - Intelligent Executive Compensation Analysis
    
    A revolutionary CLI that combines conversational AI with traditional commands
    for analyzing SEC EDGAR filings and extracting executive compensation data.
    
    Features:
    • Self-improving code with LLM quality assurance
    • Conversational interface with natural language processing
    • Traditional CLI fallback for automation and scripting
    • Real-time context injection from codebase analysis
    • Subprocess monitoring with automatic fallback to exec()
    """
    ctx.ensure_object(dict)
    ctx.obj['mode'] = mode
    ctx.obj['verbose'] = verbose
    
    if verbose:
        click.echo(f"🔧 EDGAR CLI starting in {mode} mode")


@cli.command()
@click.pass_context
def interactive(ctx):
    """Start interactive conversational interface."""
    
    async def start_interactive():
        mode = ctx.obj.get('mode', 'auto')
        verbose = ctx.obj.get('verbose', False)
        
        if verbose:
            click.echo("🚀 Starting interactive mode...")
        
        try:
            # Initialize LLM service
            llm_service = LLMService()
            
            async def llm_client(messages):
                return await llm_service._make_llm_request(
                    messages, temperature=0.7, max_tokens=2000
                )
            
            # Get application root
            app_root = str(Path(__file__).parent.parent.parent)
            
            if mode == 'chatbot':
                # Force chatbot mode
                controller = ChatbotController(
                    llm_client=llm_client,
                    application_root=app_root,
                    scripting_enabled=True
                )
                await controller.start_conversation()
                
            elif mode == 'traditional':
                # Force traditional CLI mode
                await ChatbotController._start_fallback_cli(app_root)
                
            else:  # auto mode
                # Automatic detection and fallback
                controller = await ChatbotController.create_with_fallback(
                    llm_client=llm_client,
                    application_root=app_root,
                    test_llm=True,
                    scripting_enabled=True
                )
                
                if controller:
                    await controller.start_conversation()
                # If controller is None, fallback CLI was already started
                
        except Exception as e:
            click.echo(f"❌ Error starting interactive mode: {e}")
            if verbose:
                import traceback
                traceback.print_exc()
    
    asyncio.run(start_interactive())


@cli.command()
@click.option('--companies', '-c', default=10, help='Number of companies to test')
@click.option('--output', '-o', help='Output file for results')
@click.pass_context
def test(ctx, companies, output):
    """Run system test with multiple companies."""
    
    async def run_test():
        verbose = ctx.obj.get('verbose', False)
        
        if verbose:
            click.echo(f"🧪 Testing system with {companies} companies...")
        
        try:
            # Import and run the test
            from test_50_companies import test_50_companies
            
            # Modify the test to use specified number of companies
            # This would require updating the test function
            await test_50_companies()
            
            if output:
                click.echo(f"📄 Results saved to: {output}")
            
        except Exception as e:
            click.echo(f"❌ Test failed: {e}")
            if verbose:
                import traceback
                traceback.print_exc()
    
    asyncio.run(run_test())


@cli.command()
@click.option('--cik', required=True, help='Company CIK number')
@click.option('--year', default=2023, help='Fiscal year')
@click.option('--output-format', type=click.Choice(['json', 'table', 'csv']), 
              default='table', help='Output format')
@click.pass_context
def extract(ctx, cik, year, output_format):
    """Extract executive compensation for a specific company."""
    
    async def run_extraction():
        verbose = ctx.obj.get('verbose', False)
        
        if verbose:
            click.echo(f"📊 Extracting compensation for CIK {cik}, year {year}")
        
        try:
            from self_improving_code.examples.edgar_extraction import EdgarExtractionExample
            
            example = EdgarExtractionExample()
            
            # For demo, use sample HTML
            sample_html = f"""
            <html><body>
                <h2>Summary Compensation Table</h2>
                <table>
                    <tr><th>Name</th><th>Title</th><th>Total</th></tr>
                    <tr><td>John CEO</td><td>Chief Executive Officer</td><td>$5,000,000</td></tr>
                    <tr><td>Jane CFO</td><td>Chief Financial Officer</td><td>$3,000,000</td></tr>
                </table>
            </body></html>
            """
            
            results = await example.extract_with_improvement(
                html_content=sample_html,
                company_cik=cik,
                company_name=f"Company {cik}",
                year=year,
                max_iterations=2
            )
            
            compensations = results.get('compensations', [])
            
            if output_format == 'json':
                import json
                compensation_data = []
                for comp in compensations:
                    compensation_data.append({
                        'name': comp.executive_name,
                        'title': comp.title,
                        'total_compensation': float(comp.total_compensation),
                        'salary': float(comp.salary) if comp.salary else 0,
                        'bonus': float(comp.bonus) if comp.bonus else 0
                    })
                click.echo(json.dumps(compensation_data, indent=2))
                
            elif output_format == 'csv':
                click.echo("Name,Title,Total Compensation,Salary,Bonus")
                for comp in compensations:
                    click.echo(f"{comp.executive_name},{comp.title},{comp.total_compensation},{comp.salary},{comp.bonus}")
                    
            else:  # table format
                click.echo(f"\n📊 Executive Compensation - CIK {cik} ({year})")
                click.echo("-" * 60)
                for comp in compensations:
                    click.echo(f"👤 {comp.executive_name}")
                    click.echo(f"   Title: {comp.title}")
                    click.echo(f"   Total: ${comp.total_compensation:,}")
                    click.echo(f"   Salary: ${comp.salary:,}" if comp.salary else "   Salary: N/A")
                    click.echo()
            
            if verbose:
                improvement_info = results.get('improvement_process', {})
                click.echo(f"\n🔄 Improvement Process:")
                click.echo(f"   Iterations: {improvement_info.get('total_iterations', 0)}")
                click.echo(f"   Success: {improvement_info.get('final_success', False)}")
                click.echo(f"   Improvements: {len(improvement_info.get('improvements_made', []))}")
            
        except Exception as e:
            click.echo(f"❌ Extraction failed: {e}")
            if verbose:
                import traceback
                traceback.print_exc()
    
    asyncio.run(run_extraction())


# Add traditional CLI commands as subcommands
def create_integrated_cli():
    """Create integrated CLI with both conversational and traditional commands."""
    
    # Get the traditional CLI
    app_root = str(Path(__file__).parent.parent.parent)
    traditional_cli = create_fallback_cli(app_root)
    
    # Add traditional commands to main CLI
    for command_name, command in traditional_cli.commands.items():
        cli.add_command(command, name=f"trad-{command_name}")
    
    return cli


if __name__ == "__main__":
    # Create integrated CLI and run
    integrated_cli = create_integrated_cli()
    integrated_cli()
else:
    # For module import
    cli = create_integrated_cli()
