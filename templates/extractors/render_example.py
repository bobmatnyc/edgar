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
    print(f"   black {output_dir}")
    print(f"   isort {output_dir}")
    print(f"   mypy {output_dir}")
    print()
    print("3. Run tests:")
    print(f"   pytest {output_dir}/test_*.py")
    print()


if __name__ == "__main__":
    main()
