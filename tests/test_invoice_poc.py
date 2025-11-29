"""
Test Invoice POC Integration

This test validates that the Invoice Transform POC project is correctly set up
and can be processed by the PDFDataSource.

Validates:
- PDFDataSource can extract invoice table data
- Column names match expected structure
- Data types are correctly inferred (int, float, str)
- Row count and data integrity
- Example transformation patterns are correct
"""

import json
import pytest
import yaml
from pathlib import Path

# Test imports
from edgar_analyzer.data_sources import PDFDataSource


class TestInvoicePOC:
    """Test suite for Invoice Transform POC validation."""

    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).parent.parent / "projects" / "invoice_transform"

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
        assert (project_root / "input" / "invoice_001.pdf").exists(), "invoice_001.pdf missing"

        # Example files
        assert (project_root / "examples" / "invoice_001.json").exists(), "invoice_001.json missing"
        assert (project_root / "examples" / "invoice_002.json").exists(), "invoice_002.json missing"

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
        assert data_source["type"] == "pdf"
        assert "config" in data_source
        assert "file_path" in data_source["config"]
        assert data_source["config"]["file_path"] == "input/invoice_001.pdf"
        assert data_source["config"]["page_number"] == 0
        assert data_source["config"]["table_strategy"] == "lines"

        # Examples
        examples = project_config["examples"]
        assert len(examples) == 2
        assert "examples/invoice_001.json" in examples
        assert "examples/invoice_002.json" in examples

    def test_example_format(self, examples):
        """Test that example files have correct format."""
        assert len(examples) == 2

        for name, example in examples.items():
            # Required fields
            assert "example_id" in example, f"{name}: missing example_id"
            assert "description" in example, f"{name}: missing description"
            assert "input" in example, f"{name}: missing input"
            assert "output" in example, f"{name}: missing output"

            # Input structure (raw PDF table columns)
            input_data = example["input"]
            assert "Item" in input_data
            assert "Qty" in input_data
            assert "Price" in input_data
            assert "Total" in input_data

            # Output structure (transformed schema)
            output_data = example["output"]
            assert "product" in output_data
            assert "quantity" in output_data
            assert "unit_price" in output_data
            assert "line_total" in output_data

    @pytest.mark.asyncio
    async def test_pdf_data_source_integration(self, project_root):
        """Test that PDFDataSource can read invoice_001.pdf."""
        pdf_file = project_root / "input" / "invoice_001.pdf"

        # Initialize data source
        data_source = PDFDataSource(
            file_path=pdf_file,
            page_number=0,
            table_strategy="lines"
        )

        # Fetch data
        result = await data_source.fetch()

        # Validate result structure
        assert result is not None
        assert "rows" in result
        assert "columns" in result
        assert "row_count" in result
        assert "page_number" in result
        assert "source_file" in result
        assert "file_name" in result

        # Validate row count (3 line items)
        assert len(result["rows"]) == 3
        assert result["row_count"] == 3

        # Validate columns (Item, Qty, Price, Total)
        assert set(result["columns"]) == {"Item", "Qty", "Price", "Total"}

        # Validate first row (Widget A)
        row1 = result["rows"][0]
        assert row1["Item"] == "Widget A"
        assert row1["Qty"] == 5  # Should be int (type inferred)
        assert row1["Price"] == "$10.00"  # String (has $ symbol)
        assert row1["Total"] == "$50.00"  # String (has $ symbol)

    @pytest.mark.asyncio
    async def test_type_inference(self, project_root):
        """Test that PDFDataSource correctly infers data types."""
        pdf_file = project_root / "input" / "invoice_001.pdf"

        data_source = PDFDataSource(
            file_path=pdf_file,
            page_number=0,
            table_strategy="lines"
        )

        result = await data_source.fetch()

        # Check type inference for first row
        row1 = result["rows"][0]

        # Item should be string
        assert isinstance(row1["Item"], str)

        # Qty should be integer (inferred from "5")
        assert isinstance(row1["Qty"], int)
        assert row1["Qty"] == 5

        # Price should be string (has $ symbol, can't be auto-converted)
        # Note: Transformation will handle $ removal
        assert isinstance(row1["Price"], str)
        assert "$" in row1["Price"]

        # Total should be string (has $ symbol)
        assert isinstance(row1["Total"], str)
        assert "$" in row1["Total"]

    def test_transformation_coverage(self, examples):
        """Test that examples demonstrate all transformation types."""
        # Check first example (invoice_001)
        example1 = examples["invoice_001"]

        # Field rename: Item → product
        assert example1["input"]["Item"] == example1["output"]["product"]

        # Type conversion: Qty (string) → quantity (int)
        assert isinstance(example1["output"]["quantity"], int)
        assert example1["output"]["quantity"] == 5

        # Field rename + type conversion + $ removal: Price → unit_price
        assert isinstance(example1["output"]["unit_price"], float)
        assert example1["output"]["unit_price"] == 10.00

        # Field rename + type conversion + $ removal: Total → line_total
        assert isinstance(example1["output"]["line_total"], float)
        assert example1["output"]["line_total"] == 50.00

    def test_transformation_consistency(self, examples):
        """Test that transformations are consistent across examples."""
        # Both examples should follow same transformation pattern
        for name, example in examples.items():
            # Product is always Item renamed
            assert example["input"]["Item"] == example["output"]["product"]

            # Quantity is always Qty converted to int
            assert isinstance(example["output"]["quantity"], int)

            # Unit price is always float
            assert isinstance(example["output"]["unit_price"], float)

            # Line total is always float
            assert isinstance(example["output"]["line_total"], float)

    @pytest.mark.asyncio
    async def test_data_quality(self, project_root):
        """Test that extracted data is clean and complete."""
        pdf_file = project_root / "input" / "invoice_001.pdf"

        data_source = PDFDataSource(
            file_path=pdf_file,
            page_number=0,
            table_strategy="lines"
        )

        result = await data_source.fetch()
        rows = result["rows"]

        # All records should have all required fields
        required_fields = ["Item", "Qty", "Price", "Total"]

        for i, row in enumerate(rows):
            for field in required_fields:
                assert field in row, f"Row {i}: missing {field}"
                assert row[field] is not None, f"Row {i}: {field} is None"
                assert row[field] != "", f"Row {i}: {field} is empty"

    @pytest.mark.asyncio
    async def test_example_matches_source_data(self, project_root, examples):
        """Test that example inputs match actual PDF data."""
        pdf_file = project_root / "input" / "invoice_001.pdf"

        data_source = PDFDataSource(
            file_path=pdf_file,
            page_number=0,
            table_strategy="lines"
        )

        result = await data_source.fetch()
        rows = result["rows"]

        # Verify first example matches first row (Widget A)
        example1_input = examples["invoice_001"]["input"]
        row1 = rows[0]
        assert example1_input["Item"] == row1["Item"]
        assert int(example1_input["Qty"]) == row1["Qty"]
        assert example1_input["Price"] == row1["Price"]
        assert example1_input["Total"] == row1["Total"]

        # Verify second example matches second row (Widget B)
        example2_input = examples["invoice_002"]["input"]
        row2 = rows[1]
        assert example2_input["Item"] == row2["Item"]
        assert int(example2_input["Qty"]) == row2["Qty"]
        assert example2_input["Price"] == row2["Price"]
        assert example2_input["Total"] == row2["Total"]

    def test_pattern_compliance(self, project_config):
        """Test that project follows Employee Roster template pattern."""
        # Required configuration structure
        assert "data_source" in project_config
        assert "type" in project_config["data_source"]
        assert "config" in project_config["data_source"]
        assert "examples" in project_config

        # Examples should be list of file paths
        assert isinstance(project_config["examples"], list)
        assert len(project_config["examples"]) >= 2

        # Target schema (if present)
        if "target_schema" in project_config:
            schema = project_config["target_schema"]
            assert "product" in schema
            assert "quantity" in schema
            assert "unit_price" in schema
            assert "line_total" in schema

    @pytest.mark.asyncio
    async def test_end_to_end_poc_validation(self, project_root):
        """End-to-end test: Extract PDF → Validate against examples."""
        pdf_file = project_root / "input" / "invoice_001.pdf"

        # 1. Extract data from PDF
        data_source = PDFDataSource(
            file_path=pdf_file,
            page_number=0,
            table_strategy="lines"
        )

        result = await data_source.fetch()

        # 2. Validate extraction success
        assert result is not None
        assert len(result["rows"]) >= 3  # At least 3 line items

        # 3. Validate columns match example input schema
        assert set(result["columns"]) == {"Item", "Qty", "Price", "Total"}

        # 4. Validate data types
        for row in result["rows"]:
            assert isinstance(row["Item"], str)
            assert isinstance(row["Qty"], int)
            assert isinstance(row["Price"], str)  # Has $, not converted
            assert isinstance(row["Total"], str)  # Has $, not converted

        # 5. Validate specific values (first row)
        assert result["rows"][0]["Item"] == "Widget A"
        assert result["rows"][0]["Qty"] == 5
        assert "$10.00" in result["rows"][0]["Price"]
        assert "$50.00" in result["rows"][0]["Total"]

        print(f"✅ Invoice POC validation passed: {len(result['rows'])} line items extracted")
        print(f"   Columns: {result['columns']}")
        print(f"   First item: {result['rows'][0]}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
