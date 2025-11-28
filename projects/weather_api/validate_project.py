#!/usr/bin/env python3
"""
Weather API Project Validation Script

Validates the complete project template including:
- project.yaml schema compliance
- Example file format and content
- File structure completeness
- Example diversity and coverage
- Configuration correctness

Usage:
    python validate_project.py
    python validate_project.py --verbose
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import yaml
from pydantic import ValidationError

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from edgar_analyzer.models.project_config import ProjectConfig


class ProjectValidator:
    """Validates Weather API project template."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []

    def validate_all(self) -> bool:
        """Run all validation checks.

        Returns:
            True if all validations pass, False otherwise
        """
        print("🔍 Validating Weather API Project Template\n")
        print(f"Project Directory: {self.project_dir}\n")

        # Run all validation checks
        checks = [
            ("File Structure", self.validate_file_structure),
            ("project.yaml Schema", self.validate_project_yaml),
            ("Example Files", self.validate_example_files),
            ("Example Diversity", self.validate_example_diversity),
            ("Configuration Quality", self.validate_configuration),
            ("Documentation", self.validate_documentation),
        ]

        all_passed = True
        for check_name, check_func in checks:
            print(f"▶ {check_name}...")
            passed = check_func()
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {status}\n")
            if not passed:
                all_passed = False

        # Print summary
        self._print_summary()

        return all_passed

    def validate_file_structure(self) -> bool:
        """Validate that all required files and directories exist."""
        required_files = [
            "project.yaml",
            "README.md",
            ".env.example",
            "examples/london.json",
            "examples/tokyo.json",
            "examples/moscow.json",
            "examples/dubai.json",
            "examples/oslo.json",
            "examples/singapore.json",
            "examples/new_york.json",
        ]

        required_dirs = [
            "examples",
            "generated",
            "output",
        ]

        passed = True

        # Check files
        for file_path in required_files:
            full_path = self.project_dir / file_path
            if not full_path.exists():
                self.errors.append(f"Missing required file: {file_path}")
                passed = False
            else:
                self.info.append(f"Found: {file_path}")

        # Check directories
        for dir_path in required_dirs:
            full_path = self.project_dir / dir_path
            if not full_path.exists():
                self.errors.append(f"Missing required directory: {dir_path}")
                passed = False
            else:
                self.info.append(f"Found directory: {dir_path}/")

        return passed

    def validate_project_yaml(self) -> bool:
        """Validate project.yaml against schema."""
        yaml_path = self.project_dir / "project.yaml"

        if not yaml_path.exists():
            self.errors.append("project.yaml not found")
            return False

        try:
            # Load and validate with Pydantic
            config = ProjectConfig.from_yaml(yaml_path)

            # Basic checks
            if config.project.name != "weather_api_extractor":
                self.warnings.append(
                    f"Project name is '{config.project.name}', expected 'weather_api_extractor'"
                )

            if len(config.data_sources) == 0:
                self.errors.append("No data sources configured")
                return False

            if len(config.examples) < 5:
                self.warnings.append(
                    f"Only {len(config.examples)} examples (recommended: 5+)"
                )

            # Check data source configuration
            weather_source = next(
                (s for s in config.data_sources if s.name == "openweathermap"), None
            )
            if not weather_source:
                self.errors.append("OpenWeatherMap data source not found")
                return False

            if not weather_source.endpoint:
                self.errors.append("Data source missing endpoint")
                return False

            if weather_source.auth.key != "${OPENWEATHER_API_KEY}":
                self.warnings.append(
                    "API key should use environment variable: ${OPENWEATHER_API_KEY}"
                )

            # Validate output configuration
            if len(config.output.formats) == 0:
                self.errors.append("No output formats configured")
                return False

            csv_output = next((f for f in config.output.formats if f.type.value == "csv"), None)
            json_output = next((f for f in config.output.formats if f.type.value == "json"), None)

            if not csv_output:
                self.warnings.append("CSV output format not configured")
            if not json_output:
                self.warnings.append("JSON output format not configured")

            self.info.append(f"✓ Valid project.yaml with {len(config.examples)} examples")
            return True

        except ValidationError as e:
            self.errors.append(f"project.yaml validation failed: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Error loading project.yaml: {e}")
            return False

    def validate_example_files(self) -> bool:
        """Validate individual example JSON files."""
        example_files = [
            "london.json",
            "tokyo.json",
            "moscow.json",
            "dubai.json",
            "oslo.json",
            "singapore.json",
            "new_york.json",
        ]

        passed = True
        for filename in example_files:
            file_path = self.project_dir / "examples" / filename
            if not file_path.exists():
                self.errors.append(f"Example file missing: {filename}")
                passed = False
                continue

            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)

                # Validate structure
                if "input" not in data:
                    self.errors.append(f"{filename}: Missing 'input' field")
                    passed = False
                if "output" not in data:
                    self.errors.append(f"{filename}: Missing 'output' field")
                    passed = False

                # Validate input structure
                if "input" in data:
                    required_input_fields = ["coord", "weather", "main", "name"]
                    for field in required_input_fields:
                        if field not in data["input"]:
                            self.errors.append(
                                f"{filename}: Missing input field '{field}'"
                            )
                            passed = False

                # Validate output structure
                if "output" in data:
                    required_output_fields = [
                        "city",
                        "country",
                        "temperature_c",
                        "humidity_percent",
                        "conditions",
                    ]
                    for field in required_output_fields:
                        if field not in data["output"]:
                            self.errors.append(
                                f"{filename}: Missing output field '{field}'"
                            )
                            passed = False

                self.info.append(f"✓ Valid example: {filename}")

            except json.JSONDecodeError as e:
                self.errors.append(f"{filename}: Invalid JSON - {e}")
                passed = False
            except Exception as e:
                self.errors.append(f"{filename}: Error reading file - {e}")
                passed = False

        return passed

    def validate_example_diversity(self) -> bool:
        """Validate that examples cover diverse weather conditions."""
        yaml_path = self.project_dir / "project.yaml"

        if not yaml_path.exists():
            return False

        try:
            config = ProjectConfig.from_yaml(yaml_path)

            # Collect temperature range
            temperatures = [
                example.output.get("temperature_c", 0)
                for example in config.examples
            ]
            temp_range = max(temperatures) - min(temperatures)

            if temp_range < 30:
                self.warnings.append(
                    f"Temperature range only {temp_range}°C (recommended: >30°C for diversity)"
                )

            # Collect humidity range
            humidities = [
                example.output.get("humidity_percent", 50)
                for example in config.examples
            ]
            humidity_range = max(humidities) - min(humidities)

            if humidity_range < 40:
                self.warnings.append(
                    f"Humidity range only {humidity_range}% (recommended: >40% for diversity)"
                )

            # Check for negative temperatures
            has_negative_temp = any(t < 0 for t in temperatures)
            if not has_negative_temp:
                self.warnings.append(
                    "No examples with negative temperatures (cold climate missing)"
                )

            # Check for high temperatures
            has_high_temp = any(t > 30 for t in temperatures)
            if not has_high_temp:
                self.warnings.append(
                    "No examples with high temperatures >30°C (hot climate missing)"
                )

            # Check for various weather conditions
            conditions = [
                example.output.get("conditions", "").lower()
                for example in config.examples
            ]

            condition_types = {
                "rain": any("rain" in c for c in conditions),
                "snow": any("snow" in c for c in conditions),
                "clear": any("clear" in c for c in conditions),
                "clouds": any("cloud" in c for c in conditions),
            }

            missing_conditions = [k for k, v in condition_types.items() if not v]
            if missing_conditions:
                self.warnings.append(
                    f"Missing weather conditions: {', '.join(missing_conditions)}"
                )

            self.info.append(
                f"✓ Temperature range: {min(temperatures):.1f}°C to {max(temperatures):.1f}°C"
            )
            self.info.append(
                f"✓ Humidity range: {min(humidities)}% to {max(humidities)}%"
            )
            self.info.append(
                f"✓ Weather conditions covered: {sum(condition_types.values())}/4"
            )

            return True

        except Exception as e:
            self.errors.append(f"Error validating diversity: {e}")
            return False

    def validate_configuration(self) -> bool:
        """Validate configuration quality and best practices."""
        yaml_path = self.project_dir / "project.yaml"

        if not yaml_path.exists():
            return False

        try:
            config = ProjectConfig.from_yaml(yaml_path)

            # Run comprehensive validation
            results = config.validate_comprehensive()

            # Add any errors/warnings from comprehensive validation
            self.errors.extend(results.get('errors', []))
            self.warnings.extend(results.get('warnings', []))

            # Check cache configuration
            weather_source = next(
                (s for s in config.data_sources if s.name == "openweathermap"), None
            )
            if weather_source:
                if not weather_source.cache.enabled:
                    self.warnings.append("Cache is disabled (will exceed rate limits)")

                if weather_source.cache.ttl < 600:
                    self.warnings.append(
                        f"Cache TTL is {weather_source.cache.ttl}s (recommended: ≥600s)"
                    )

                # Check rate limiting
                if weather_source.rate_limit:
                    if weather_source.rate_limit.requests_per_second > 1:
                        self.warnings.append(
                            "Rate limit >1 req/s may exceed free tier limits (60/min)"
                        )
                else:
                    self.warnings.append("No rate limiting configured")

            # Check validation rules
            if len(config.validation.required_fields) < 3:
                self.warnings.append("Few required fields configured (recommended: ≥3)")

            if len(config.validation.constraints) < 2:
                self.warnings.append("Few constraints configured (recommended: ≥2)")

            self.info.append("✓ Configuration quality checks completed")
            return len(results.get('errors', [])) == 0

        except Exception as e:
            self.errors.append(f"Error validating configuration: {e}")
            return False

    def validate_documentation(self) -> bool:
        """Validate documentation completeness."""
        readme_path = self.project_dir / "README.md"

        if not readme_path.exists():
            self.errors.append("README.md not found")
            return False

        try:
            with open(readme_path, 'r') as f:
                content = f.read()

            required_sections = [
                "Overview",
                "Quick Start",
                "Example Diversity",
                "Generated Code",
                "Usage",
                "Output",
                "Configuration",
                "Validation",
                "Troubleshooting",
            ]

            missing_sections = []
            for section in required_sections:
                if section.lower() not in content.lower():
                    missing_sections.append(section)

            if missing_sections:
                self.warnings.append(
                    f"README missing sections: {', '.join(missing_sections)}"
                )

            # Check for code examples
            if "```bash" not in content and "```python" not in content:
                self.warnings.append("README missing code examples")

            # Check for API key setup instructions
            if "OPENWEATHER_API_KEY" not in content:
                self.warnings.append("README missing API key setup instructions")

            self.info.append(
                f"✓ README.md found ({len(content)} characters, {len(required_sections) - len(missing_sections)}/{len(required_sections)} sections)"
            )

            # Check .env.example
            env_example_path = self.project_dir / ".env.example"
            if env_example_path.exists():
                with open(env_example_path, 'r') as f:
                    env_content = f.read()

                if "OPENWEATHER_API_KEY" not in env_content:
                    self.errors.append(".env.example missing OPENWEATHER_API_KEY")
                    return False

                self.info.append("✓ .env.example properly configured")
            else:
                self.errors.append(".env.example not found")
                return False

            return len(missing_sections) == 0

        except Exception as e:
            self.errors.append(f"Error validating documentation: {e}")
            return False

    def _print_summary(self) -> None:
        """Print validation summary."""
        print("\n" + "=" * 70)
        print("VALIDATION SUMMARY")
        print("=" * 70 + "\n")

        if self.errors:
            print(f"❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"   - {error}")
            print()

        if self.warnings:
            print(f"⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   - {warning}")
            print()

        if not self.errors and not self.warnings:
            print("✅ All validations passed with no errors or warnings!\n")
        elif not self.errors:
            print("✅ All critical validations passed (warnings only)\n")
        else:
            print("❌ Validation failed with errors\n")

        # Overall status
        if self.errors:
            print("Status: FAIL ❌")
            print("Action: Fix errors before proceeding")
        elif self.warnings:
            print("Status: PASS WITH WARNINGS ⚠️")
            print("Action: Review warnings, project is functional")
        else:
            print("Status: PASS ✅")
            print("Action: Ready for code generation")

        print()


def main():
    """Main validation entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate Weather API project template"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed information messages"
    )
    parser.add_argument(
        "--project-dir",
        type=Path,
        default=Path(__file__).parent,
        help="Project directory (default: script directory)"
    )

    args = parser.parse_args()

    validator = ProjectValidator(args.project_dir)
    passed = validator.validate_all()

    if args.verbose:
        print("\n" + "=" * 70)
        print("DETAILED INFO")
        print("=" * 70 + "\n")
        for info in validator.info:
            print(f"ℹ️  {info}")
        print()

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
