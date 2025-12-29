"""
CLI commands for extractor management.

Commands:
- edgar extractors create - Create new extractor from examples
- edgar extractors list - List registered extractors
- edgar extractors validate - Validate an extractor
- edgar extractors info - Show extractor details
"""

import click
from pathlib import Path
from typing import Optional

import structlog

from edgar_analyzer.extractors.meta_extractor import MetaExtractor
from edgar_analyzer.extractors.registry import ExtractorRegistry

logger = structlog.get_logger(__name__)


@click.group(name="extractors")
def extractors_cli():
    """Manage extractors (create, list, validate)."""
    pass


@extractors_cli.command(name="create")
@click.argument("name")
@click.option(
    "--examples", "-e",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Directory containing example JSON files"
)
@click.option(
    "--description", "-d",
    default="",
    help="Human-readable description"
)
@click.option(
    "--domain",
    default=None,
    help="Domain slug (defaults to name without '_extractor')"
)
@click.option(
    "--no-register",
    is_flag=True,
    help="Skip registry registration"
)
@click.option(
    "--skip-validation",
    is_flag=True,
    help="Skip code validation (not recommended)"
)
def create_extractor(
    name: str,
    examples: Path,
    description: str,
    domain: Optional[str],
    no_register: bool,
    skip_validation: bool,
):
    """
    Create a new extractor from examples.

    Example:
        edgar extractors create sct_extractor -e examples/sct/ -d "Extract SCT"
    """
    click.echo(f"🔧 Creating extractor: {name}")
    click.echo(f"   Examples: {examples}")

    meta = MetaExtractor()

    result = meta.create(
        name=name,
        examples_dir=examples,
        description=description,
        domain=domain,
        auto_register=not no_register,
        skip_validation=skip_validation,
    )

    if result.status == "success":
        click.echo(f"\n✅ Extractor created successfully!")
        click.echo(f"   Domain: {result.domain}")
        click.echo(f"   Confidence: {result.analysis.confidence:.1%}")
        click.echo(f"   Files: {len(result.files_created)}")
        click.echo(f"   Time: {result.total_time_seconds:.2f}s")

        if result.deployment.registered:
            click.echo(f"   Registered as: {result.deployment.registry_name}")

        click.echo(f"\n📁 Output: {result.deployment.extractor_path}")
    else:
        click.echo(f"\n❌ Creation failed: {result.status}")
        click.echo(f"   Error: {result.error_message}")
        click.echo(f"   Stage: {result.error_stage}")
        raise SystemExit(1)


@extractors_cli.command(name="list")
@click.option(
    "--domain", "-d",
    default=None,
    help="Filter by domain"
)
@click.option(
    "--min-confidence", "-c",
    type=float,
    default=0.0,
    help="Minimum confidence threshold (0.0-1.0)"
)
@click.option(
    "--format", "-f",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format"
)
def list_extractors(domain: Optional[str], min_confidence: float, format: str):
    """
    List registered extractors.

    Example:
        edgar extractors list --domain sct --min-confidence 0.8
    """
    registry = ExtractorRegistry()
    extractors = registry.list(domain=domain, min_confidence=min_confidence)

    if format == "json":
        import json
        data = [e.to_dict() for e in extractors]
        click.echo(json.dumps(data, indent=2))
    else:
        if not extractors:
            click.echo("No extractors found.")
            return

        click.echo(f"\n{'Name':<25} {'Domain':<10} {'Confidence':<12} {'Version':<10}")
        click.echo("-" * 60)

        for ext in extractors:
            click.echo(
                f"{ext.name:<25} {ext.domain:<10} {ext.confidence:>10.1%}  {ext.version:<10}"
            )

        click.echo(f"\nTotal: {len(extractors)} extractors")


@extractors_cli.command(name="info")
@click.argument("name")
def extractor_info(name: str):
    """
    Show detailed info about an extractor.

    Example:
        edgar extractors info sct_extractor
    """
    registry = ExtractorRegistry()

    try:
        metadata = registry.get_metadata(name)
    except KeyError:
        click.echo(f"❌ Extractor not found: {name}")
        raise SystemExit(1)

    click.echo(f"\n📦 {metadata.name}")
    click.echo(f"   Description: {metadata.description}")
    click.echo(f"   Domain: {metadata.domain}")
    click.echo(f"   Version: {metadata.version}")
    click.echo(f"   Confidence: {metadata.confidence:.1%}")
    click.echo(f"   Examples: {metadata.examples_count}")
    click.echo(f"   Tags: {', '.join(metadata.tags)}")
    click.echo(f"   Class: {metadata.class_path}")
    click.echo(f"   Created: {metadata.created_at}")
    click.echo(f"   Updated: {metadata.updated_at}")


@extractors_cli.command(name="validate")
@click.argument("name")
def validate_extractor(name: str):
    """
    Validate a registered extractor.

    Example:
        edgar extractors validate sct_extractor
    """
    registry = ExtractorRegistry()

    click.echo(f"🔍 Validating extractor: {name}")

    try:
        # Try to load the extractor class
        extractor_class = registry.get(name)
        click.echo(f"✅ Dynamic import successful")
        click.echo(f"   Class: {extractor_class.__name__}")

        # Check for required methods
        if hasattr(extractor_class, 'extract'):
            click.echo(f"✅ Has 'extract' method")
        else:
            click.echo(f"❌ Missing 'extract' method")
            raise SystemExit(1)

        click.echo(f"\n✅ Extractor validation passed!")

    except KeyError:
        click.echo(f"❌ Extractor not found in registry: {name}")
        raise SystemExit(1)
    except ImportError as e:
        click.echo(f"❌ Import failed: {e}")
        raise SystemExit(1)
    except Exception as e:
        click.echo(f"❌ Validation failed: {e}")
        raise SystemExit(1)
