"""
Test Employee Roster POC Integration

This test validates that the Employee Roster POC project is correctly set up
and can be processed by the ExcelDataSource.
"""

import json
import pytest
import yaml
from pathlib import Path

# Test imports
from edgar_analyzer.data_sources.excel_source import ExcelDataSource


class TestEmployeeRosterPOC:
    """Test suite for Employee Roster POC validation."""

    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).parent.parent / "projects" / "employee_roster"

    @pytest.fixture
    def project_config(self, project_root):
        """Load project.yaml configuration."""
        config_path = project_root / "project.yaml"
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    @pytest.fixture
    def examples(self, project_root):
        """Load all example files."""
        examples_dir = project_root / "examples"
        examples = {}
        for example_file in examples_dir.glob("*.json"):
            with open(example_file, 'r') as f:
                example_data = json.load(f)
                examples[example_file.stem] = example_data
        return examples

    def test_project_structure(self, project_root):
        """Test that all required directories and files exist."""
        # Required directories
        assert (project_root / "input").exists(), "input/ directory missing"
        assert (project_root / "examples").exists(), "examples/ directory missing"
        assert (project_root / "output").exists(), "output/ directory missing"

        # Required files
        assert (project_root / "project.yaml").exists(), "project.yaml missing"
        assert (project_root / "README.md").exists(), "README.md missing"
        assert (project_root / "input" / "hr_roster.xlsx").exists(), "hr_roster.xlsx missing"

        # Example files
        assert (project_root / "examples" / "alice.json").exists(), "alice.json missing"
        assert (project_root / "examples" / "bob.json").exists(), "bob.json missing"
        assert (project_root / "examples" / "carol.json").exists(), "carol.json missing"

    def test_project_configuration(self, project_config):
        """Test that project.yaml has correct structure."""
        # Required top-level fields
        assert "name" in project_config
        assert "description" in project_config
        assert "version" in project_config
        assert "data_source" in project_config
        assert "examples" in project_config

        # Data source configuration
        data_source = project_config["data_source"]
        assert data_source["type"] == "excel"
        assert "config" in data_source
        assert "file_path" in data_source["config"]
        assert data_source["config"]["file_path"] == "input/hr_roster.xlsx"

        # Examples
        examples = project_config["examples"]
        assert len(examples) == 3
        assert "examples/alice.json" in examples
        assert "examples/bob.json" in examples
        assert "examples/carol.json" in examples

    def test_example_format(self, examples):
        """Test that example files have correct format."""
        assert len(examples) == 3

        for name, example in examples.items():
            # Required fields
            assert "example_id" in example, f"{name}: missing example_id"
            assert "description" in example, f"{name}: missing description"
            assert "input" in example, f"{name}: missing input"
            assert "output" in example, f"{name}: missing output"

            # Input structure
            input_data = example["input"]
            assert "employee_id" in input_data
            assert "first_name" in input_data
            assert "last_name" in input_data
            assert "department" in input_data
            assert "hire_date" in input_data
            assert "salary" in input_data
            assert "is_manager" in input_data

            # Output structure
            output_data = example["output"]
            assert "id" in output_data
            assert "full_name" in output_data
            assert "dept" in output_data
            assert "hired" in output_data
            assert "annual_salary_usd" in output_data
            assert "manager" in output_data

    def test_excel_data_source_integration(self, project_root):
        """Test that ExcelDataSource can read hr_roster.xlsx."""
        excel_file = project_root / "input" / "hr_roster.xlsx"

        # Initialize data source
        data_source = ExcelDataSource(
            file_path=str(excel_file),
            sheet_name=0,
            header_row=0
        )

        # Fetch data
        result = data_source.fetch()

        # Validate result
        assert result is not None
        assert "records" in result
        assert len(result["records"]) == 3

        # Check first record (Alice)
        alice = result["records"][0]
        assert alice["employee_id"] == "E1001"
        assert alice["first_name"] == "Alice"
        assert alice["last_name"] == "Johnson"
        assert alice["department"] == "Engineering"
        assert alice["salary"] == 95000
        assert alice["is_manager"] == "Yes"

    def test_transformation_coverage(self, examples):
        """Test that examples demonstrate all transformation types."""
        # Check Alice example for transformations
        alice = examples["alice"]

        # Field rename: employee_id → id
        assert alice["input"]["employee_id"] == alice["output"]["id"]

        # String concatenation: first_name + last_name → full_name
        expected_full_name = f"{alice['input']['first_name']} {alice['input']['last_name']}"
        assert alice["output"]["full_name"] == expected_full_name

        # Field rename: department → dept
        assert alice["input"]["department"] == alice["output"]["dept"]

        # Field rename: hire_date → hired
        assert alice["input"]["hire_date"] == alice["output"]["hired"]

        # Type conversion: salary (int) → annual_salary_usd (float)
        assert isinstance(alice["output"]["annual_salary_usd"], float)
        assert alice["output"]["annual_salary_usd"] == float(alice["input"]["salary"])

        # Boolean conversion: is_manager (Yes/No) → manager (true/false)
        assert isinstance(alice["output"]["manager"], bool)
        assert alice["output"]["manager"] is True  # "Yes" → true

    def test_boolean_conversion_consistency(self, examples):
        """Test that boolean conversion is consistent across examples."""
        # Alice and Carol are managers (Yes → true)
        assert examples["alice"]["input"]["is_manager"] == "Yes"
        assert examples["alice"]["output"]["manager"] is True

        assert examples["carol"]["input"]["is_manager"] == "Yes"
        assert examples["carol"]["output"]["manager"] is True

        # Bob is not a manager (No → false)
        assert examples["bob"]["input"]["is_manager"] == "No"
        assert examples["bob"]["output"]["manager"] is False

    def test_data_quality(self, project_root):
        """Test that source data is clean and complete."""
        excel_file = project_root / "input" / "hr_roster.xlsx"

        data_source = ExcelDataSource(
            file_path=str(excel_file),
            sheet_name=0,
            header_row=0
        )

        result = data_source.fetch()
        records = result["records"]

        # All records should have all required fields
        required_fields = [
            "employee_id", "first_name", "last_name",
            "department", "hire_date", "salary", "is_manager"
        ]

        for i, record in enumerate(records):
            for field in required_fields:
                assert field in record, f"Record {i}: missing {field}"
                assert record[field] is not None, f"Record {i}: {field} is None"
                assert record[field] != "", f"Record {i}: {field} is empty"

    def test_example_matches_source_data(self, project_root, examples):
        """Test that example inputs match actual Excel data."""
        excel_file = project_root / "input" / "hr_roster.xlsx"

        data_source = ExcelDataSource(
            file_path=str(excel_file),
            sheet_name=0,
            header_row=0
        )

        result = data_source.fetch()
        records = result["records"]

        # Map employee_id to record
        excel_records = {r["employee_id"]: r for r in records}

        # Verify Alice (E1001)
        alice_example = examples["alice"]["input"]
        alice_excel = excel_records["E1001"]
        assert alice_example["employee_id"] == alice_excel["employee_id"]
        assert alice_example["first_name"] == alice_excel["first_name"]
        assert alice_example["last_name"] == alice_excel["last_name"]

        # Verify Bob (E1002)
        bob_example = examples["bob"]["input"]
        bob_excel = excel_records["E1002"]
        assert bob_example["employee_id"] == bob_excel["employee_id"]
        assert bob_example["first_name"] == bob_excel["first_name"]
        assert bob_example["last_name"] == bob_excel["last_name"]

        # Verify Carol (E1003)
        carol_example = examples["carol"]["input"]
        carol_excel = excel_records["E1003"]
        assert carol_example["employee_id"] == carol_excel["employee_id"]
        assert carol_example["first_name"] == carol_excel["first_name"]
        assert carol_example["last_name"] == carol_excel["last_name"]

    def test_pattern_compliance(self, project_config):
        """Test that project follows Weather API template pattern."""
        # Required configuration structure
        assert "data_source" in project_config
        assert "type" in project_config["data_source"]
        assert "config" in project_config["data_source"]
        assert "examples" in project_config

        # Examples should be list of file paths
        assert isinstance(project_config["examples"], list)
        assert len(project_config["examples"]) >= 3

        # Target schema (if present)
        if "target_schema" in project_config:
            schema = project_config["target_schema"]
            assert "id" in schema
            assert "full_name" in schema
            assert "dept" in schema


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
