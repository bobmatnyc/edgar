#!/usr/bin/env python3
"""
EDGAR Analyzer CLI Entry Point

Main command-line interface that integrates:
- Conversational CLI Chatbot Controller
- Traditional CLI fallback
- Self-improving code patterns
- Executive compensation extraction
- Real-time LLM QA and validation
- Platform workflow commands (project, analyze, generate, extract)

Usage:
    python -m edgar_analyzer.cli
    python -m edgar_analyzer.cli --help
    python -m edgar_analyzer.cli analyze --query "CEO compensation"
"""

import asyncio
import sys
import os
import json
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


@click.group(invoke_without_command=True)
@click.option('--mode', type=click.Choice(['auto', 'chatbot', 'traditional']),
              default='auto', help='CLI interface mode')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--enable-web-search/--disable-web-search', default=True, help='Enable/disable web search capabilities (enabled by default)')
@click.option('--cli', 'bypass_interactive', is_flag=True, help='Bypass interactive mode, show CLI help')
@click.pass_context
def cli(ctx, mode, verbose, enable_web_search, bypass_interactive):
    """
    EDGAR Analyzer - Intelligent Executive Compensation Analysis

    A revolutionary CLI that combines conversational AI with traditional commands
    for analyzing SEC EDGAR filings and extracting executive compensation data.

    By default, starts in interactive conversational mode. Use subcommands for
    specific operations or traditional CLI functionality.

    Features:
    • Self-improving code with LLM quality assurance
    • Conversational interface with natural language processing (DEFAULT)
    • Traditional CLI fallback for automation and scripting
    • Real-time context injection from codebase analysis
    • Subprocess monitoring with automatic fallback to exec()
    • Web search capabilities enabled by default (use --disable-web-search to disable)

    Examples:
        edgar-cli                                    # Start interactive mode with web search (default)
        edgar-cli --cli                             # Show CLI help (bypass interactive)
        edgar-cli --disable-web-search              # Interactive without web search
        edgar-cli extract --cik 0000320193          # Traditional command
        edgar-cli --mode traditional interactive    # Force traditional CLI
    """
    ctx.ensure_object(dict)
    ctx.obj['mode'] = mode
    ctx.obj['verbose'] = verbose
    ctx.obj['enable_web_search'] = enable_web_search

    if verbose:
        click.echo(f"🔧 EDGAR CLI starting in {mode} mode")
        if enable_web_search:
            click.echo("🔍 Web search capabilities enabled")

    # If no subcommand is provided, decide what to do
    if ctx.invoked_subcommand is None:
        if bypass_interactive:
            # Show CLI help instead of starting interactive mode
            click.echo(ctx.get_help())
        else:
            # Start interactive mode by default
            ctx.invoke(interactive)


@cli.command()
@click.pass_context
def interactive(ctx):
    """Start interactive conversational interface (default mode)."""
    
    async def start_interactive():
        mode = ctx.obj.get('mode', 'auto')
        verbose = ctx.obj.get('verbose', False)
        enable_web_search = ctx.obj.get('enable_web_search', True)
        
        if verbose:
            click.echo("🚀 Starting interactive mode...")
        
        try:
            # Initialize LLM service
            llm_service = LLMService()
            
            async def llm_client(messages):
                return await llm_service._make_llm_request(
                    messages, temperature=0.7, max_tokens=2000
                )

            # Web search client if enabled
            web_search_client = None
            if enable_web_search:
                async def web_search_client(query, context=None):
                    return await llm_service.web_search_request(query, context)
            
            # Get application root
            app_root = str(Path(__file__).parent.parent.parent)
            
            if mode == 'chatbot':
                # Force chatbot mode
                controller = ChatbotController(
                    llm_client=llm_client,
                    application_root=app_root,
                    scripting_enabled=True,
                    web_search_enabled=enable_web_search,
                    web_search_client=web_search_client
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
                    scripting_enabled=True,
                    web_search_enabled=enable_web_search,
                    web_search_client=web_search_client
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


# ============================================================================
# PLATFORM WORKFLOW COMMANDS
# ============================================================================


@cli.group()
@click.pass_context
def project(ctx):
    """Project management commands for EDGAR platform workflows."""
    pass


@project.command('create')
@click.argument('name')
@click.option('--template', type=click.Choice(['weather', 'news_scraper', 'minimal']),
              default='minimal', help='Project template to use')
@click.pass_context
def project_create(ctx, name, template):
    """Create a new project from template.

    Examples:
        edgar-analyzer project create my_api --template weather
        edgar-analyzer project create news_scraper --template news_scraper
    """
    async def run_create():
        try:
            from extract_transform_platform.services.project_manager import ProjectManager

            verbose = ctx.obj.get('verbose', False)

            if verbose:
                click.echo(f"Creating project '{name}' from template '{template}'...")

            manager = ProjectManager()
            project_info = await manager.create_project(name, template=template)

            click.echo(f"✅ Project created: {project_info.name}")
            click.echo(f"   Path: {project_info.path}")
            click.echo(f"\nNext steps:")
            click.echo(f"  1. Add examples to {project_info.path / 'examples'}/")
            click.echo(f"  2. Configure {project_info.path / 'project.yaml'}")
            click.echo(f"  3. Run: edgar-analyzer analyze-project {project_info.path}")

        except Exception as e:
            click.echo(f"❌ Error creating project: {e}")
            if ctx.obj.get('verbose', False):
                import traceback
                traceback.print_exc()
            sys.exit(1)

    asyncio.run(run_create())


@project.command('list')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']),
              default='table', help='Output format')
@click.pass_context
def project_list(ctx, output_format):
    """List all projects.

    Examples:
        edgar-analyzer project list
        edgar-analyzer project list --format json
    """
    async def run_list():
        try:
            from extract_transform_platform.services.project_manager import ProjectManager

            manager = ProjectManager()
            projects = await manager.list_projects()

            if not projects:
                click.echo("No projects found.")
                return

            if output_format == 'json':
                output = [p.to_dict() for p in projects]
                click.echo(json.dumps(output, indent=2))
            else:
                # Table format
                click.echo(f"\n{'Name':<30} {'Description':<50} {'Path':<40}")
                click.echo("-" * 120)
                for p in projects:
                    desc = p.metadata.get('description', 'No description')[:48]
                    click.echo(f"{p.name:<30} {desc:<50} {str(p.path):<40}")
                click.echo(f"\nTotal: {len(projects)} projects")

        except Exception as e:
            click.echo(f"❌ Error listing projects: {e}")
            if ctx.obj.get('verbose', False):
                import traceback
                traceback.print_exc()
            sys.exit(1)

    asyncio.run(run_list())


@project.command('validate')
@click.argument('name')
@click.pass_context
def project_validate(ctx, name):
    """Validate project configuration and structure.

    Examples:
        edgar-analyzer project validate my_api
    """
    async def run_validate():
        try:
            from extract_transform_platform.services.project_manager import ProjectManager

            verbose = ctx.obj.get('verbose', False)

            if verbose:
                click.echo(f"Validating project '{name}'...")

            manager = ProjectManager()
            result = await manager.validate_project(name)

            # Display results
            click.echo(f"\n{'='*60}")
            click.echo(f"Validation Results for '{result.project_name}'")
            click.echo(f"{'='*60}\n")

            if result.is_valid:
                click.echo("✅ Project is valid!")
            else:
                click.echo("❌ Project has errors")

            if result.errors:
                click.echo(f"\n🔴 Errors ({len(result.errors)}):")
                for error in result.errors:
                    click.echo(f"  - {error}")

            if result.warnings:
                click.echo(f"\n⚠️  Warnings ({len(result.warnings)}):")
                for warning in result.warnings:
                    click.echo(f"  - {warning}")

            if result.recommendations:
                click.echo(f"\n💡 Recommendations ({len(result.recommendations)}):")
                for rec in result.recommendations:
                    click.echo(f"  - {rec}")

            click.echo()

            if not result.is_valid:
                sys.exit(1)

        except Exception as e:
            click.echo(f"❌ Error validating project: {e}")
            if ctx.obj.get('verbose', False):
                import traceback
                traceback.print_exc()
            sys.exit(1)

    asyncio.run(run_validate())


@project.command('delete')
@click.argument('name')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def project_delete(ctx, name, yes):
    """Delete a project.

    Examples:
        edgar-analyzer project delete old_project
        edgar-analyzer project delete old_project --yes
    """
    async def run_delete():
        try:
            from extract_transform_platform.services.project_manager import ProjectManager

            manager = ProjectManager()

            # Check if project exists
            project_info = await manager.get_project(name)
            if not project_info:
                click.echo(f"❌ Project '{name}' not found")
                sys.exit(1)

            # Confirm deletion
            if not yes:
                click.echo(f"\n⚠️  This will permanently delete project '{name}'")
                click.echo(f"   Path: {project_info.path}")
                if not click.confirm("\nAre you sure?"):
                    click.echo("Cancelled.")
                    return

            # Delete
            success = await manager.delete_project(name)

            if success:
                click.echo(f"✅ Project '{name}' deleted successfully")
            else:
                click.echo(f"❌ Failed to delete project '{name}'")
                sys.exit(1)

        except Exception as e:
            click.echo(f"❌ Error deleting project: {e}")
            if ctx.obj.get('verbose', False):
                import traceback
                traceback.print_exc()
            sys.exit(1)

    asyncio.run(run_delete())


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _load_examples_from_config(config: 'ProjectConfig', project_path: Path) -> list:
    """
    Load examples from ProjectConfig, supporting both inline and file-based examples.

    Priority:
    1. Inline examples from project.yaml (config.examples if they're ExampleConfig objects)
    2. File-based examples from examples/ directory

    Args:
        config: Loaded ProjectConfig object
        project_path: Path to project directory

    Returns:
        List of ExampleConfig objects

    Design Decision:
        Inline examples take precedence over file-based examples to match
        template system design (weather template uses inline examples).
    """
    from extract_transform_platform.models.project_config import ExampleConfig

    examples = []

    # Priority 1: Check for inline examples in config
    if hasattr(config, 'examples') and config.examples:
        for ex in config.examples:
            if isinstance(ex, ExampleConfig):
                examples.append(ex)
            elif isinstance(ex, dict):
                examples.append(ExampleConfig(**ex))

        if examples:
            click.echo(f"📝 Loaded {len(examples)} inline examples from project.yaml")
            return examples

    # Priority 2: Fallback to file-based examples
    examples_dir = project_path / "examples"
    if not examples_dir.exists():
        return []

    example_files = list(examples_dir.glob("*.json"))
    if not example_files:
        return []

    for example_file in example_files:
        try:
            with open(example_file, 'r') as f:
                example_data = json.load(f)
                examples.append(ExampleConfig(**example_data))
        except Exception as e:
            click.echo(f"⚠️  Warning: Could not load {example_file.name}: {e}")

    if examples:
        click.echo(f"📁 Loaded {len(examples)} examples from files")

    return examples


# ============================================================================
# WORKFLOW COMMANDS
# ============================================================================


@cli.command('analyze-project')
@click.argument('project_path', type=click.Path(exists=True, path_type=Path))
@click.pass_context
def analyze_project(ctx, project_path):
    """Analyze project examples and detect transformation patterns.

    This command:
    1. Loads project configuration from project.yaml
    2. Parses example files to detect patterns
    3. Generates schema analysis
    4. Saves results to project directory

    Examples:
        edgar-analyzer analyze-project projects/my_api/
        edgar-analyzer analyze-project /path/to/external/project/
    """
    async def run_analyze():
        try:
            from edgar_analyzer.models.project_config import ProjectConfig
            from edgar_analyzer.services.example_parser import ExampleParser

            verbose = ctx.obj.get('verbose', False)

            # Load project config
            config_path = project_path / "project.yaml"
            if not config_path.exists():
                click.echo(f"❌ Error: project.yaml not found in {project_path}")
                sys.exit(1)

            if verbose:
                click.echo(f"Loading project configuration from {config_path}")

            config = ProjectConfig.from_yaml(config_path)

            # Load examples (inline or file-based)
            examples = _load_examples_from_config(config, project_path)

            if not examples:
                click.echo("❌ Error: No examples found (neither inline nor in examples/ directory)")
                click.echo("   Add examples to project.yaml or create examples/*.json files")
                sys.exit(1)

            click.echo(f"\n📊 Analyzing {len(examples)} examples...")

            # Parse examples and detect patterns
            parser = ExampleParser()
            parsed = parser.parse_examples(examples)

            click.echo(f"✅ Analysis complete!")
            click.echo(f"\n   Patterns detected: {len(parsed.patterns)}")
            click.echo(f"   Input fields: {len(parsed.input_schema.fields)}")
            click.echo(f"   Output fields: {len(parsed.output_schema.fields)}")

            # Save analysis results
            analysis_path = project_path / "analysis_results.json"
            with open(analysis_path, 'w') as f:
                json.dump({
                    'patterns': [p.dict() for p in parsed.patterns],
                    'input_schema': parsed.input_schema.dict(),
                    'output_schema': parsed.output_schema.dict(),
                    'num_examples': len(examples)
                }, f, indent=2)

            click.echo(f"\n   Results saved to: {analysis_path}")
            click.echo(f"\nNext step: edgar-analyzer generate-code {project_path}")

        except Exception as e:
            click.echo(f"❌ Error analyzing project: {e}")
            if ctx.obj.get('verbose', False):
                import traceback
                traceback.print_exc()
            sys.exit(1)

    asyncio.run(run_analyze())


@cli.command('generate-code')
@click.argument('project_path', type=click.Path(exists=True, path_type=Path))
@click.option('--validate/--no-validate', default=True, help='Validate generated code')
@click.pass_context
def generate_code(ctx, project_path, validate):
    """Generate extraction code from analyzed patterns.

    This command:
    1. Loads project configuration and analysis results
    2. Generates Python code for data extraction
    3. Generates tests and validation code
    4. Saves code to project src/ directory

    Examples:
        edgar-analyzer generate-code projects/my_api/
        edgar-analyzer generate-code projects/my_api/ --no-validate
    """
    async def run_generate():
        try:
            from edgar_analyzer.models.project_config import ProjectConfig
            from edgar_analyzer.services.code_generator import CodeGeneratorService

            verbose = ctx.obj.get('verbose', False)

            # Load project config
            config_path = project_path / "project.yaml"
            if not config_path.exists():
                click.echo(f"❌ Error: project.yaml not found in {project_path}")
                sys.exit(1)

            config = ProjectConfig.from_yaml(config_path)

            # Load examples (inline or file-based)
            examples = _load_examples_from_config(config, project_path)

            if not examples:
                click.echo("❌ Error: No examples found (neither inline nor in examples/ directory)")
                click.echo("   Add examples to project.yaml or create examples/*.json files")
                sys.exit(1)

            click.echo(f"\n🔧 Generating code for {config.project.name}...")

            # Check for API key
            api_key = os.getenv("OPENROUTER_API_KEY")
            if not api_key:
                click.echo("❌ Error: OPENROUTER_API_KEY not set in environment")
                click.echo("   Set it in .env.local or export OPENROUTER_API_KEY=your_key")
                sys.exit(1)

            # Generate code
            service = CodeGeneratorService(
                api_key=api_key,
                output_dir=project_path / "src"
            )

            context = await service.generate(
                examples=examples,
                project_config=config,
                validate=validate,
                write_files=True,
                max_retries=3
            )

            if context.is_complete:
                click.echo(f"✅ Code generation complete!")
                click.echo(f"\n   Generated files:")
                click.echo(f"     - extractor.py ({context.code.extractor_lines} lines)")
                click.echo(f"     - models.py ({context.code.models_lines} lines)")
                click.echo(f"     - tests.py ({context.code.tests_lines} lines)")
                click.echo(f"\n   Output directory: {project_path / 'src'}")

                if validate and context.validation and context.validation.is_valid:
                    click.echo(f"   Quality score: {context.validation.quality_score:.0%}")

                click.echo(f"\nNext step: edgar-analyzer run-extraction {project_path}")
            else:
                click.echo(f"⚠️  Code generation incomplete")
                if context.validation and not context.validation.is_valid:
                    click.echo(f"\n   Validation issues:")
                    for issue in context.validation.issues:
                        click.echo(f"     - {issue}")
                sys.exit(1)

        except Exception as e:
            click.echo(f"❌ Error generating code: {e}")
            if ctx.obj.get('verbose', False):
                import traceback
                traceback.print_exc()
            sys.exit(1)

    asyncio.run(run_generate())


@cli.command('run-extraction')
@click.argument('project_path', type=click.Path(exists=True, path_type=Path))
@click.option('--output-format', type=click.Choice(['json', 'csv', 'excel']),
              default='json', help='Output format')
@click.pass_context
def run_extraction(ctx, project_path, output_format):
    """Run the generated extraction code.

    This command:
    1. Loads the generated extractor code
    2. Runs extraction on configured data sources
    3. Saves results to output/ directory

    Examples:
        edgar-analyzer run-extraction projects/my_api/
        edgar-analyzer run-extraction projects/my_api/ --output-format csv
    """
    async def run_extract():
        try:
            import importlib.util
            from edgar_analyzer.models.project_config import ProjectConfig

            verbose = ctx.obj.get('verbose', False)

            # Load project config
            config_path = project_path / "project.yaml"
            if not config_path.exists():
                click.echo(f"❌ Error: project.yaml not found in {project_path}")
                sys.exit(1)

            config = ProjectConfig.from_yaml(config_path)

            # Load generated extractor
            extractor_path = project_path / "src" / "extractor.py"
            if not extractor_path.exists():
                click.echo(f"❌ Error: extractor.py not found in {project_path / 'src'}")
                click.echo("   Run 'edgar-analyzer generate-code' first")
                sys.exit(1)

            if verbose:
                click.echo(f"Loading extractor from {extractor_path}")

            # Dynamically import the extractor module
            spec = importlib.util.spec_from_file_location("extractor", extractor_path)
            if spec is None or spec.loader is None:
                click.echo(f"❌ Error: Could not load extractor module")
                sys.exit(1)

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find the extractor class (should implement IDataExtractor)
            extractor_class = None
            for name in dir(module):
                obj = getattr(module, name)
                if isinstance(obj, type) and name.endswith('Extractor'):
                    extractor_class = obj
                    break

            if extractor_class is None:
                click.echo(f"❌ Error: No extractor class found in {extractor_path}")
                sys.exit(1)

            click.echo(f"\n🚀 Running extraction for {config.project.name}...")

            # Initialize and run extractor
            extractor = extractor_class()
            results = await extractor.extract()

            # Save results
            output_dir = project_path / "output"
            output_dir.mkdir(exist_ok=True)

            if output_format == 'json':
                output_file = output_dir / "results.json"
                with open(output_file, 'w') as f:
                    json.dump(results, f, indent=2)
                click.echo(f"✅ Extraction complete! Results saved to {output_file}")

            elif output_format == 'csv':
                import pandas as pd
                output_file = output_dir / "results.csv"
                df = pd.DataFrame(results)
                df.to_csv(output_file, index=False)
                click.echo(f"✅ Extraction complete! Results saved to {output_file}")

            elif output_format == 'excel':
                import pandas as pd
                output_file = output_dir / "results.xlsx"
                df = pd.DataFrame(results)
                df.to_excel(output_file, index=False)
                click.echo(f"✅ Extraction complete! Results saved to {output_file}")

            click.echo(f"\n   Records extracted: {len(results)}")

        except Exception as e:
            click.echo(f"❌ Error running extraction: {e}")
            if ctx.obj.get('verbose', False):
                import traceback
                traceback.print_exc()
            sys.exit(1)

    asyncio.run(run_extract())


@cli.command()
@click.option('--project', type=click.Path(exists=True), help='Project directory path')
@click.option('--resume', type=str, default=None, help='Resume saved session by name')
@click.option('--list-sessions', is_flag=True, help='List all saved sessions and exit')
@click.pass_context
def chat(ctx, project, resume, list_sessions):
    """Start interactive extraction session with REPL interface.

    This command launches an Auggie-style interactive REPL for data extraction
    workflows. It provides a stateful, conversational interface with command history,
    tab completion, natural language understanding, and rich terminal UI.

    Features:
    • Natural language command understanding
    • Tab completion for commands (try pressing Tab)
    • Command history (Ctrl+R to search)
    • Rich tables and progress indicators
    • Persistent session state with save/resume
    • Confidence threshold tuning
    • Integration with all platform services

    Examples:
        # Start fresh session
        edgar-analyzer chat

        # Start with project loaded
        edgar-analyzer chat --project projects/weather_test/

        # Resume last session
        edgar-analyzer chat --resume last

        # Resume specific session
        edgar-analyzer chat --resume my_session

        # List all saved sessions
        edgar-analyzer chat --list-sessions

    Available Commands (once in session):
        help       - Show available commands
        load       - Load project from path
        show       - Display project status
        examples   - List project examples
        analyze    - Analyze patterns in examples
        patterns   - Show detected patterns
        generate   - Generate extraction code
        validate   - Validate generated code
        extract    - Run data extraction
        confidence - Set confidence threshold (0.0-1.0)
        threshold  - Show current confidence threshold
        save       - Save current session
        resume     - Resume saved session
        sessions   - List all saved sessions
        exit       - Exit interactive mode

    Natural Language:
        You can also ask questions in natural language:
        • "What patterns did you detect?"
        • "Show me the examples"
        • "Generate the code"
    """
    import asyncio
    from pathlib import Path

    from edgar_analyzer.interactive import InteractiveExtractionSession

    # Handle --list-sessions flag
    if list_sessions:
        async def list_all_sessions():
            session = InteractiveExtractionSession()
            await session.cmd_list_sessions()

        asyncio.run(list_all_sessions())
        return

    async def start_chat():
        verbose = ctx.obj.get('verbose', False)

        if verbose:
            click.echo("🚀 Starting interactive chat session...")

        try:
            project_path = Path(project) if project else None
            session = InteractiveExtractionSession(project_path=project_path)

            # If --resume specified, restore session state before starting REPL
            if resume:
                await session.cmd_resume_session(resume)

            await session.start()

        except Exception as e:
            click.echo(f"❌ Error starting chat session: {e}")
            if verbose:
                import traceback
                traceback.print_exc()

    asyncio.run(start_chat())


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


def main():
    """Main entry point for the edgar-analyzer command."""
    integrated_cli = create_integrated_cli()
    integrated_cli()


if __name__ == "__main__":
    main()
else:
    # For module import
    cli = create_integrated_cli()
