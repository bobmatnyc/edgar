"""
Unit tests for inline examples support in CLI commands (Bug #3 fix).

Tests the _load_examples_from_config helper function that enables both
inline examples (from project.yaml) and file-based examples (from examples/*.json).
"""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from edgar_analyzer.main_cli import _load_examples_from_config
from extract_transform_platform.models.project_config import (
    DataSourceConfig,
    DataSourceType,
    ExampleConfig,
    OutputConfig,
    OutputDestinationConfig,
    OutputFormat,
    ProjectConfig,
    ProjectMetadata,
)


class TestInlineExamplesCLI:
    """Test suite for inline examples support in CLI."""

    def test_load_inline_examples(self):
        """Test loading inline examples from project.yaml."""
        # Create config with inline examples
        config = ProjectConfig(
            project=ProjectMetadata(name="test_inline"),
            data_sources=[
                DataSourceConfig(
                    type=DataSourceType.API,
                    name="test_api",
                    endpoint="https://api.example.com",
                )
            ],
            examples=[
                ExampleConfig(
                    input={"city": "London", "temp": 15.5},
                    output={"location": "London", "temperature_c": 15.5},
                ),
                ExampleConfig(
                    input={"city": "Tokyo", "temp": 22.3},
                    output={"location": "Tokyo", "temperature_c": 22.3},
                ),
            ],
            output=OutputConfig(
                formats=[
                    OutputDestinationConfig(
                        type=OutputFormat.JSON, path="output/results.json"
                    )
                ]
            ),
        )

        with TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            # Load examples
            examples = _load_examples_from_config(config, project_path)

            # Verify
            assert len(examples) == 2
            assert all(isinstance(ex, ExampleConfig) for ex in examples)
            assert examples[0].input["city"] == "London"
            assert examples[1].input["city"] == "Tokyo"

    def test_load_file_examples_when_no_inline(self):
        """Test fallback to file-based examples when no inline examples exist."""
        # Create config WITHOUT inline examples
        config = ProjectConfig(
            project=ProjectMetadata(name="test_files"),
            data_sources=[
                DataSourceConfig(
                    type=DataSourceType.FILE,
                    name="test_file",
                    file_path="input/data.csv",
                )
            ],
            examples=[],  # No inline examples
            output=OutputConfig(
                formats=[
                    OutputDestinationConfig(
                        type=OutputFormat.JSON, path="output/results.json"
                    )
                ]
            ),
        )

        with TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            # Create examples directory with example files
            examples_dir = project_path / "examples"
            examples_dir.mkdir()

            # Create example files
            ex1 = {"input": {"name": "Alice"}, "output": {"full_name": "Alice"}}
            ex2 = {"input": {"name": "Bob"}, "output": {"full_name": "Bob"}}

            (examples_dir / "ex1.json").write_text(json.dumps(ex1))
            (examples_dir / "ex2.json").write_text(json.dumps(ex2))

            # Load examples
            examples = _load_examples_from_config(config, project_path)

            # Verify
            assert len(examples) == 2
            assert all(isinstance(ex, ExampleConfig) for ex in examples)

    def test_inline_examples_take_precedence(self):
        """Test that inline examples take precedence over file-based examples."""
        # Create config WITH inline examples
        config = ProjectConfig(
            project=ProjectMetadata(name="test_precedence"),
            data_sources=[
                DataSourceConfig(
                    type=DataSourceType.API,
                    name="test_api",
                    endpoint="https://api.example.com",
                )
            ],
            examples=[
                ExampleConfig(input={"source": "inline"}, output={"type": "inline"})
            ],
            output=OutputConfig(
                formats=[
                    OutputDestinationConfig(
                        type=OutputFormat.JSON, path="output/results.json"
                    )
                ]
            ),
        )

        with TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            # Create examples directory with example files
            examples_dir = project_path / "examples"
            examples_dir.mkdir()

            # Create file-based example
            file_ex = {"input": {"source": "file"}, "output": {"type": "file"}}
            (examples_dir / "file_ex.json").write_text(json.dumps(file_ex))

            # Load examples
            examples = _load_examples_from_config(config, project_path)

            # Verify inline examples are used (not file-based)
            assert len(examples) == 1
            assert examples[0].input["source"] == "inline"

    def test_no_examples_returns_empty_list(self):
        """Test that empty list is returned when no examples exist."""
        # Create config without examples
        config = ProjectConfig(
            project=ProjectMetadata(name="test_empty"),
            data_sources=[
                DataSourceConfig(
                    type=DataSourceType.FILE,
                    name="test_file",
                    file_path="input/data.csv",
                )
            ],
            examples=[],
            output=OutputConfig(
                formats=[
                    OutputDestinationConfig(
                        type=OutputFormat.JSON, path="output/results.json"
                    )
                ]
            ),
        )

        with TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            # No examples directory created

            # Load examples
            examples = _load_examples_from_config(config, project_path)

            # Verify empty list
            assert examples == []

    def test_invalid_file_example_skipped_with_warning(self, capsys):
        """Test that invalid example files are skipped with a warning."""
        # Create config without inline examples
        config = ProjectConfig(
            project=ProjectMetadata(name="test_invalid"),
            data_sources=[
                DataSourceConfig(
                    type=DataSourceType.FILE,
                    name="test_file",
                    file_path="input/data.csv",
                )
            ],
            examples=[],
            output=OutputConfig(
                formats=[
                    OutputDestinationConfig(
                        type=OutputFormat.JSON, path="output/results.json"
                    )
                ]
            ),
        )

        with TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            # Create examples directory
            examples_dir = project_path / "examples"
            examples_dir.mkdir()

            # Create valid and invalid example files
            valid_ex = {"input": {"name": "Valid"}, "output": {"full_name": "Valid"}}
            (examples_dir / "valid.json").write_text(json.dumps(valid_ex))
            (examples_dir / "invalid.json").write_text("{invalid json")

            # Load examples
            examples = _load_examples_from_config(config, project_path)

            # Verify only valid example is loaded
            assert len(examples) == 1
            assert examples[0].input["name"] == "Valid"

            # Check for warning message
            captured = capsys.readouterr()
            assert "Warning: Could not load invalid.json" in captured.out

    def test_weather_template_scenario(self):
        """Test scenario matching weather template (3 inline examples)."""
        # Create config similar to weather template
        config = ProjectConfig(
            project=ProjectMetadata(
                name="weather_data_extractor", description="Extract weather data"
            ),
            data_sources=[
                DataSourceConfig(
                    type=DataSourceType.API,
                    name="openweathermap_current",
                    endpoint="https://api.openweathermap.org/data/2.5/weather",
                )
            ],
            examples=[
                ExampleConfig(
                    description="Rainy weather in London",
                    input={
                        "city": "London",
                        "raw_response": {
                            "main": {"temp": 15.5, "humidity": 72},
                            "weather": [{"description": "light rain"}],
                        },
                    },
                    output={
                        "city": "London",
                        "temperature_c": 15.5,
                        "humidity_percent": 72,
                        "conditions": "light rain",
                    },
                ),
                ExampleConfig(
                    description="Clear sky in Tokyo",
                    input={
                        "city": "Tokyo",
                        "raw_response": {
                            "main": {"temp": 22.3, "humidity": 65},
                            "weather": [{"description": "clear sky"}],
                        },
                    },
                    output={
                        "city": "Tokyo",
                        "temperature_c": 22.3,
                        "humidity_percent": 65,
                        "conditions": "clear sky",
                    },
                ),
                ExampleConfig(
                    description="Snowy weather in Moscow",
                    input={
                        "city": "Moscow",
                        "raw_response": {
                            "main": {"temp": -5.2, "humidity": 85},
                            "weather": [{"description": "light snow"}],
                        },
                    },
                    output={
                        "city": "Moscow",
                        "temperature_c": -5.2,
                        "humidity_percent": 85,
                        "conditions": "light snow",
                    },
                ),
            ],
            output=OutputConfig(
                formats=[
                    OutputDestinationConfig(
                        type=OutputFormat.CSV, path="output/weather_data.csv"
                    )
                ]
            ),
        )

        with TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            # Load examples
            examples = _load_examples_from_config(config, project_path)

            # Verify 3 examples loaded
            assert len(examples) == 3
            assert examples[0].input["city"] == "London"
            assert examples[1].input["city"] == "Tokyo"
            assert examples[2].input["city"] == "Moscow"
