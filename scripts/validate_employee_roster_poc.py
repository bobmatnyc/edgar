#!/usr/bin/env python3
"""
Validate Employee Roster POC

Simple validation script to ensure the POC is correctly set up.
"""

import asyncio
import json
import sys
import yaml
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from edgar_analyzer.data_sources.excel_source import ExcelDataSource


def validate_project_structure(project_root):
    """Validate directory structure."""
    print("📁 Validating project structure...")

    required_dirs = ["input", "examples", "output"]
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            print(f"  ❌ Missing directory: {dir_name}/")
            return False
        print(f"  ✅ {dir_name}/ exists")

    required_files = [
        "project.yaml",
        "README.md",
        "input/hr_roster.xlsx",
        "examples/alice.json",
        "examples/bob.json",
        "examples/carol.json"
    ]

    for file_path in required_files:
        full_path = project_root / file_path
        if not full_path.exists():
            print(f"  ❌ Missing file: {file_path}")
            return False
        print(f"  ✅ {file_path} exists")

    return True


def validate_configuration(project_root):
    """Validate project.yaml configuration."""
    print("\n⚙️  Validating configuration...")

    config_path = project_root / "project.yaml"

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"  ❌ Failed to load project.yaml: {e}")
        return False

    # Check required fields
    required_fields = ["name", "description", "version", "data_source", "examples"]
    for field in required_fields:
        if field not in config:
            print(f"  ❌ Missing field: {field}")
            return False
        print(f"  ✅ Field '{field}' present")

    # Check data source
    data_source = config["data_source"]
    if data_source.get("type") != "excel":
        print(f"  ❌ Invalid data source type: {data_source.get('type')}")
        return False
    print(f"  ✅ Data source type: excel")

    # Check examples
    if len(config["examples"]) != 3:
        print(f"  ❌ Expected 3 examples, found {len(config['examples'])}")
        return False
    print(f"  ✅ 3 example files configured")

    return True


def validate_examples(project_root):
    """Validate example files."""
    print("\n📋 Validating examples...")

    examples_dir = project_root / "examples"
    example_files = ["alice.json", "bob.json", "carol.json"]

    for filename in example_files:
        filepath = examples_dir / filename

        try:
            with open(filepath, 'r') as f:
                example = json.load(f)
        except Exception as e:
            print(f"  ❌ Failed to load {filename}: {e}")
            return False

        # Check required fields
        required_fields = ["example_id", "description", "input", "output"]
        for field in required_fields:
            if field not in example:
                print(f"  ❌ {filename}: missing field '{field}'")
                return False

        # Check input structure
        input_fields = ["employee_id", "first_name", "last_name", "department",
                       "hire_date", "salary", "is_manager"]
        for field in input_fields:
            if field not in example["input"]:
                print(f"  ❌ {filename}: missing input field '{field}'")
                return False

        # Check output structure
        output_fields = ["id", "full_name", "dept", "hired",
                        "annual_salary_usd", "manager"]
        for field in output_fields:
            if field not in example["output"]:
                print(f"  ❌ {filename}: missing output field '{field}'")
                return False

        print(f"  ✅ {filename} is valid")

    return True


async def validate_excel_integration(project_root):
    """Validate ExcelDataSource integration."""
    print("\n📊 Validating Excel integration...")

    excel_file = project_root / "input" / "hr_roster.xlsx"

    try:
        data_source = ExcelDataSource(
            file_path=str(excel_file),
            sheet_name=0,
            header_row=0
        )
        print(f"  ✅ ExcelDataSource initialized")
    except Exception as e:
        print(f"  ❌ Failed to initialize ExcelDataSource: {e}")
        return False

    try:
        result = await data_source.fetch()
        print(f"  ✅ fetch() succeeded")
    except Exception as e:
        print(f"  ❌ Failed to fetch data: {e}")
        return False

    if "rows" not in result:
        print(f"  ❌ Result missing 'rows' key")
        return False
    print(f"  ✅ Result contains 'rows'")

    records = result["rows"]
    if len(records) != 3:
        print(f"  ❌ Expected 3 records, found {len(records)}")
        return False
    print(f"  ✅ Found 3 employee records")

    # Validate first record
    alice = records[0]
    expected_fields = ["employee_id", "first_name", "last_name", "department",
                      "hire_date", "salary", "is_manager"]
    for field in expected_fields:
        if field not in alice:
            print(f"  ❌ Record missing field: {field}")
            return False
    print(f"  ✅ Records have all required fields")

    if alice["employee_id"] != "E1001":
        print(f"  ❌ First record should be E1001, found {alice['employee_id']}")
        return False
    print(f"  ✅ Data matches expected values")

    return True


def validate_transformations(project_root):
    """Validate transformation coverage."""
    print("\n🔄 Validating transformations...")

    # Load Alice example
    alice_path = project_root / "examples" / "alice.json"
    with open(alice_path, 'r') as f:
        alice = json.load(f)

    input_data = alice["input"]
    output_data = alice["output"]

    # Field rename: employee_id → id
    if input_data["employee_id"] != output_data["id"]:
        print(f"  ❌ Field rename failed: employee_id → id")
        return False
    print(f"  ✅ Field rename: employee_id → id")

    # String concatenation: first_name + last_name → full_name
    expected_name = f"{input_data['first_name']} {input_data['last_name']}"
    if output_data["full_name"] != expected_name:
        print(f"  ❌ String concatenation failed")
        return False
    print(f"  ✅ String concatenation: first_name + last_name → full_name")

    # Type conversion: salary → annual_salary_usd
    if not isinstance(output_data["annual_salary_usd"], float):
        print(f"  ❌ Type conversion failed: salary should be float")
        return False
    print(f"  ✅ Type conversion: salary → annual_salary_usd (float)")

    # Boolean conversion: is_manager → manager
    if not isinstance(output_data["manager"], bool):
        print(f"  ❌ Boolean conversion failed: manager should be bool")
        return False
    if input_data["is_manager"] == "Yes" and output_data["manager"] is not True:
        print(f"  ❌ Boolean conversion failed: 'Yes' should be true")
        return False
    print(f"  ✅ Boolean conversion: is_manager (Yes/No) → manager (true/false)")

    return True


async def main():
    """Run all validations."""
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║     EMPLOYEE ROSTER POC - VALIDATION SUITE                     ║")
    print("╚════════════════════════════════════════════════════════════════╝\n")

    project_root = Path(__file__).parent.parent / "projects" / "employee_roster"

    validations = [
        ("Project Structure", validate_project_structure, False),
        ("Configuration", validate_configuration, False),
        ("Examples", validate_examples, False),
        ("Excel Integration", validate_excel_integration, True),  # async
        ("Transformations", validate_transformations, False)
    ]

    all_passed = True
    results = []

    for name, validator, is_async in validations:
        try:
            if is_async:
                passed = await validator(project_root)
            else:
                passed = validator(project_root)
            results.append((name, passed))
            if not passed:
                all_passed = False
        except Exception as e:
            print(f"\n❌ Validation failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
            all_passed = False

    # Summary
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)

    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status:12} {name}")

    print("="*70)

    if all_passed:
        print("\n🎉 ALL VALIDATIONS PASSED!")
        print("✅ Employee Roster POC is ready for schema analysis")
        return 0
    else:
        print("\n⚠️  SOME VALIDATIONS FAILED")
        print("❌ Please fix the issues above")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
