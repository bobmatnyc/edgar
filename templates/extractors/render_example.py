"""
Example script demonstrating how to render extractor templates.

This script shows how to use the Jinja2 templates to generate
a complete extractor package from configuration.

Usage:
    python render_example.py

Output:
    Generated extractor files in templates/extractors/output/
"""

import json
import subprocess
from pathlib import Path
from jinja2 import Environment, FileSystemLoader


def render_extractor_from_config(config_path: Path, output_dir: Path):
    """
    Render all extractor templates from a configuration file.

    Args:
        config_path: Path to JSON configuration file
        output_dir: Directory to write generated files

    Example:
        >>> render_extractor_from_config(
        ...     Path("example_sct_config.json"),
        ...     Path("output/sct_extractor")
        ... )
    """
    # Load configuration
    with open(config_path) as f:
        config = json.load(f)

    # Setup Jinja2 environment
    template_dir = config_path.parent
    env = Environment(loader=FileSystemLoader(str(template_dir)))

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Template files to render
    templates = {
        "base_extractor.py.j2": f"{config['domain']}_extractor.py",
        "data_models.py.j2": f"{config['domain']}_models.py",
        "prompt_template.j2": f"{config['domain']}_prompts.py",
        "test_extractor.py.j2": f"test_{config['domain']}_extractor.py",
        "__init__.py.j2": "__init__.py",
    }

    # Render each template
    for template_file, output_file in templates.items():
        print(f"Rendering {template_file} -> {output_file}")

        # Load template
        template = env.get_template(template_file)

        # Render with configuration
        output = template.render(**config)

        # Write output
        output_path = output_dir / output_file
        output_path.write_text(output)

        print(f"  ✓ Written to {output_path}")

    print(f"\n✅ Generated {len(templates)} files in {output_dir}")

    # Format generated code
    format_generated_code(output_dir)


def format_generated_code(output_dir: Path) -> None:
    """
    Format generated code with black and isort.

    Applies automatic code formatting to Python files in the output directory.
    Handles missing tools gracefully with warnings.

    Args:
        output_dir: Directory containing generated Python files

    Note:
        - Requires black and isort to be installed
        - Continues silently if tools are unavailable
        - Logs success/failure status for user awareness
    """
    print()
    print("Formatting generated code...")

    # Format with black
    try:
        result = subprocess.run(
            ["black", str(output_dir)],
            check=True,
            capture_output=True,
            text=True,
        )
        print(f"✅ Formatted with black: {output_dir}")
    except FileNotFoundError:
        print(f"⚠️  black not installed (optional step)")
        print("   Install with: pip install black")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  black formatting failed: {e.stderr}")

    # Sort imports with isort
    try:
        result = subprocess.run(
            ["isort", str(output_dir)],
            check=True,
            capture_output=True,
            text=True,
        )
        print(f"✅ Sorted imports with isort: {output_dir}")
    except FileNotFoundError:
        print(f"⚠️  isort not installed (optional step)")
        print("   Install with: pip install isort")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  isort import sorting failed: {e.stderr}")


def main():
    """Main entry point for example rendering."""
    # Paths
    script_dir = Path(__file__).parent
    config_path = script_dir / "example_sct_config.json"
    output_dir = script_dir / "output" / "sct_extractor"

    print("=" * 60)
    print("Extractor Template Rendering Example")
    print("=" * 60)
    print()

    # Check config exists
    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        print("   Please ensure example_sct_config.json exists")
        return

    # Render templates
    try:
        render_extractor_from_config(config_path, output_dir)
    except Exception as e:
        print(f"\n❌ Rendering failed: {e}")
        import traceback
        traceback.print_exc()
        return

    print()
    print("=" * 60)
    print("Next Steps")
    print("=" * 60)
    print()
    print("1. Review generated files:")
    print(f"   cd {output_dir}")
    print()
    print("2. Check code quality:")
    print(f"   mypy {output_dir}")
    print()
    print("3. Run tests:")
    print(f"   pytest {output_dir}/test_*.py")
    print()


if __name__ == "__main__":
    main()
