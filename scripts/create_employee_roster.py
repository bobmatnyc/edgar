#!/usr/bin/env python3
"""Create the hr_roster.xlsx test file for Employee Roster POC."""

import pandas as pd
from pathlib import Path

# Define project root
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_PATH = PROJECT_ROOT / "projects" / "employee_roster" / "input" / "hr_roster.xlsx"

# Employee data
data = {
    "employee_id": ["E1001", "E1002", "E1003"],
    "first_name": ["Alice", "Bob", "Carol"],
    "last_name": ["Johnson", "Smith", "Davis"],
    "department": ["Engineering", "Marketing", "Engineering"],
    "hire_date": ["2020-03-15", "2019-07-22", "2021-01-10"],
    "salary": [95000, 78000, 85000],
    "is_manager": ["Yes", "No", "Yes"]
}

# Create DataFrame
df = pd.DataFrame(data)

# Ensure output directory exists
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

# Write to Excel
df.to_excel(OUTPUT_PATH, index=False, sheet_name="Sheet1")

print(f"✅ Created {OUTPUT_PATH}")
print(f"📊 {len(df)} employee records")
print("\nPreview:")
print(df.to_string(index=False))
