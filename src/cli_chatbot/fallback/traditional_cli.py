"""
Traditional CLI Fallback Interface

Provides a structured CLI interface using Click when LLM services are unavailable.
This maintains functionality while gracefully degrading from conversational to traditional CLI.
"""

import click
import os
import json
import asyncio
from typing import Dict, Any, Optional, List
from pathlib import Path
import structlog

from ..core.context_injector import DynamicContextInjector
from ..core.scripting_engine import DynamicScriptingEngine

logger = structlog.get_logger(__name__)


class TraditionalCLI:
    """
    Traditional CLI interface that provides structured commands
    when the conversational LLM interface is unavailable.
    """
    
    def __init__(self, application_root: str):
        """Initialize traditional CLI with application context."""
        self.application_root = Path(application_root)
        self.context_injector = DynamicContextInjector(str(self.application_root))
        self.script_engine = DynamicScriptingEngine()
        
        logger.info("Traditional CLI initialized", app_root=str(self.application_root))
    
    async def analyze_codebase(self, query: str = "", max_results: int = 10) -> Dict[str, Any]:
        """Analyze the codebase and return structured information."""
        
        if not query:
            query = "main functions classes modules"
        
        contexts = await self.context_injector.extract_context(
            query=query,
            application_root=str(self.application_root),
            max_contexts=max_results
        )
        
        analysis = {
            'total_contexts': len(contexts),
            'contexts': []
        }
        
        for ctx in contexts:
            analysis['contexts'].append({
                'source': ctx.source,
                'type': ctx.content_type,
                'relevance': ctx.relevance_score,
                'content_preview': ctx.content[:200] + "..." if len(ctx.content) > 200 else ctx.content
            })
        
        return analysis
    
    async def execute_script(self, script_code: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a Python script safely."""
        
        execution_context = context or {}
        execution_context.update({
            'application_root': str(self.application_root),
            'os': os,
            'json': json,
            'Path': Path
        })
        
        result = await self.script_engine.execute_script(
            script_code=script_code,
            context=execution_context,
            safety_checks=True
        )
        
        return {
            'success': result.success,
            'result': result.result,
            'output': result.output,
            'error': result.error,
            'execution_time': result.execution_time,
            'side_effects': result.side_effects
        }
    
    async def get_application_info(self) -> Dict[str, Any]:
        """Get basic information about the application."""
        
        info = {
            'root_directory': str(self.application_root),
            'exists': self.application_root.exists(),
            'python_files': [],
            'directories': [],
            'config_files': []
        }
        
        if self.application_root.exists():
            # Count Python files
            python_files = list(self.application_root.rglob("*.py"))
            info['python_files'] = [str(f.relative_to(self.application_root)) for f in python_files[:20]]
            info['total_python_files'] = len(python_files)
            
            # List directories
            directories = [d for d in self.application_root.iterdir() if d.is_dir() and not d.name.startswith('.')]
            info['directories'] = [d.name for d in directories[:10]]
            
            # Find config files
            config_patterns = ['*.json', '*.yaml', '*.yml', '*.toml', '*.ini', 'requirements.txt', 'setup.py']
            config_files = []
            for pattern in config_patterns:
                config_files.extend(self.application_root.glob(pattern))
            info['config_files'] = [str(f.relative_to(self.application_root)) for f in config_files[:10]]
        
        return info


def create_fallback_cli(application_root: str) -> click.Group:
    """
    Create a Click-based CLI interface as fallback when LLM is unavailable.
    
    Args:
        application_root: Root directory of the application
        
    Returns:
        Click Group object that can be used as CLI entry point
    """
    
    cli_instance = TraditionalCLI(application_root)
    
    @click.group()
    @click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
    @click.pass_context
    def cli(ctx, verbose):
        """
        Traditional CLI Interface (LLM Fallback Mode)
        
        This structured CLI provides core functionality when the conversational
        LLM interface is unavailable. Use subcommands to interact with your application.
        """
        ctx.ensure_object(dict)
        ctx.obj['verbose'] = verbose
        ctx.obj['cli_instance'] = cli_instance
        
        if verbose:
            click.echo("🔧 Running in Traditional CLI mode (LLM unavailable)")
    
    @cli.command()
    @click.option('--query', '-q', default="", help='Search query for code analysis')
    @click.option('--max-results', '-n', default=10, help='Maximum number of results')
    @click.option('--format', 'output_format', default='table', 
                  type=click.Choice(['table', 'json', 'list']), help='Output format')
    @click.pass_context
    def analyze(ctx, query, max_results, output_format):
        """Analyze the codebase and show relevant functions, classes, and modules."""
        
        async def run_analysis():
            cli_instance = ctx.obj['cli_instance']
            analysis = await cli_instance.analyze_codebase(query, max_results)
            
            if output_format == 'json':
                click.echo(json.dumps(analysis, indent=2))
            elif output_format == 'list':
                for ctx_info in analysis['contexts']:
                    click.echo(f"• {ctx_info['source']} ({ctx_info['type']}) - {ctx_info['relevance']:.2f}")
            else:  # table format
                click.echo(f"\n📊 Found {analysis['total_contexts']} relevant contexts:")
                click.echo("-" * 80)
                for ctx_info in analysis['contexts']:
                    click.echo(f"📁 {ctx_info['source']}")
                    click.echo(f"   Type: {ctx_info['type']} | Relevance: {ctx_info['relevance']:.2f}")
                    click.echo(f"   Preview: {ctx_info['content_preview']}")
                    click.echo()
        
        asyncio.run(run_analysis())
    
    @cli.command()
    @click.option('--file', '-f', type=click.Path(exists=True), help='Execute script from file')
    @click.option('--code', '-c', help='Execute inline Python code')
    @click.option('--context', help='JSON context to pass to script')
    @click.pass_context
    def execute(ctx, file, code, context):
        """Execute Python code safely in a sandboxed environment."""
        
        if not file and not code:
            click.echo("❌ Error: Must provide either --file or --code")
            return
        
        script_code = code
        if file:
            with open(file, 'r') as f:
                script_code = f.read()
        
        script_context = {}
        if context:
            try:
                script_context = json.loads(context)
            except json.JSONDecodeError:
                click.echo("❌ Error: Invalid JSON in --context")
                return
        
        async def run_script():
            cli_instance = ctx.obj['cli_instance']
            result = await cli_instance.execute_script(script_code, script_context)
            
            if result['success']:
                click.echo("✅ Script executed successfully")
                if result['output']:
                    click.echo(f"Output:\n{result['output']}")
                if result['result']:
                    click.echo(f"Result: {result['result']}")
                if result['side_effects']:
                    click.echo(f"Side effects: {', '.join(result['side_effects'])}")
                click.echo(f"Execution time: {result['execution_time']:.3f}s")
            else:
                click.echo("❌ Script execution failed")
                click.echo(f"Error: {result['error']}")
        
        asyncio.run(run_script())
    
    @cli.command()
    @click.option('--format', 'output_format', default='table',
                  type=click.Choice(['table', 'json']), help='Output format')
    @click.pass_context
    def info(ctx, output_format):
        """Show information about the application."""
        
        async def show_info():
            cli_instance = ctx.obj['cli_instance']
            app_info = await cli_instance.get_application_info()
            
            if output_format == 'json':
                click.echo(json.dumps(app_info, indent=2))
            else:
                click.echo(f"\n📋 Application Information")
                click.echo("=" * 50)
                click.echo(f"Root Directory: {app_info['root_directory']}")
                click.echo(f"Exists: {'✅' if app_info['exists'] else '❌'}")
                
                if app_info['exists']:
                    click.echo(f"Python Files: {app_info['total_python_files']}")
                    click.echo(f"Directories: {len(app_info['directories'])}")
                    click.echo(f"Config Files: {len(app_info['config_files'])}")
                    
                    if app_info['directories']:
                        click.echo(f"\n📁 Main Directories:")
                        for directory in app_info['directories']:
                            click.echo(f"  • {directory}")
                    
                    if app_info['config_files']:
                        click.echo(f"\n⚙️  Configuration Files:")
                        for config_file in app_info['config_files']:
                            click.echo(f"  • {config_file}")
        
        asyncio.run(show_info())
    
    return cli
