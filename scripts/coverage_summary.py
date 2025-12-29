#!/usr/bin/env python3
"""
Coverage Summary Visualization

Quick command-line tool to visualize platform coverage status.

Usage:
    python scripts/coverage_summary.py
    python scripts/coverage_summary.py --format table
    python scripts/coverage_summary.py --format json
    python scripts/coverage_summary.py --category Services
"""

import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List


def load_coverage_data(coverage_file: str = "coverage.json") -> Dict:
    """Load coverage data from JSON file."""
    with open(coverage_file) as f:
        return json.load(f)


def categorize_module(module_name: str) -> str:
    """Categorize module by name."""
    if "data_sources" in module_name:
        return "Data Sources"
    elif "services" in module_name:
        if "codegen" in module_name:
            return "CodeGen"
        return "Services"
    elif "models" in module_name:
        return "Models"
    elif "reports" in module_name:
        return "Reports"
    elif "ai" in module_name:
        return "AI/ML"
    elif "core" in module_name:
        return "Core"
    elif "cli" in module_name:
        return "CLI"
    else:
        return "Other"


def get_module_coverage(data: Dict) -> List[Dict]:
    """Extract module coverage data."""
    modules = []
    for file_path, file_data in data["files"].items():
        if "extract_transform_platform" in file_path and "__pycache__" not in file_path:
            summary = file_data["summary"]
            percent = summary["percent_covered"]
            module_name = (
                file_path.replace("src/extract_transform_platform/", "")
                .replace("/", ".")
                .replace(".py", "")
            )

            modules.append(
                {
                    "name": module_name,
                    "category": categorize_module(module_name),
                    "percent": percent,
                    "statements": summary["num_statements"],
                    "missing": summary["missing_lines"],
                    "covered": summary["covered_lines"],
                }
            )
    return modules


def print_summary_stats(modules: List[Dict]):
    """Print overall summary statistics."""
    total_stmts = sum(m["statements"] for m in modules)
    total_covered = sum(m["covered"] for m in modules)
    avg_coverage = (total_covered / total_stmts * 100) if total_stmts > 0 else 0

    print("=" * 80)
    print("EXTRACT_TRANSFORM_PLATFORM COVERAGE SUMMARY")
    print("=" * 80)
    print()
    print(f"Total Modules: {len(modules)}")
    print(f"Total Statements: {total_stmts}")
    print(f"Covered Statements: {total_covered}")
    print(f"Overall Coverage: {avg_coverage:.1f}%")
    print()


def print_category_breakdown(modules: List[Dict]):
    """Print coverage by category."""
    by_category = defaultdict(list)
    for m in modules:
        by_category[m["category"]].append(m)

    print("COVERAGE BY CATEGORY")
    print("=" * 80)
    print(f"{'Category':<20} | {'Coverage':<8} | {'Statements':<10} | {'Modules':<8}")
    print("-" * 80)

    for category in sorted(by_category.keys()):
        mods = by_category[category]
        total_stmts = sum(m["statements"] for m in mods)
        total_covered = sum(m["covered"] for m in mods)
        avg_coverage = (total_covered / total_stmts * 100) if total_stmts > 0 else 0

        print(
            f"{category:<20} | {avg_coverage:>6.1f}% | {total_stmts:>10d} | {len(mods):>8d}"
        )
    print()


def print_tier_distribution(modules: List[Dict]):
    """Print module distribution by coverage tier."""
    excellent = [m for m in modules if m["percent"] >= 90]
    good = [m for m in modules if 80 <= m["percent"] < 90]
    moderate = [m for m in modules if 70 <= m["percent"] < 80]
    low = [m for m in modules if 50 <= m["percent"] < 70]
    critical = [m for m in modules if m["percent"] < 50]

    print("COVERAGE TIER DISTRIBUTION")
    print("=" * 80)
    print(f"  ✅ Excellent (90-100%): {len(excellent):>3d} modules ({len(excellent)/len(modules)*100:>5.1f}%)")
    print(f"  🟢 Good (80-89%):       {len(good):>3d} modules ({len(good)/len(modules)*100:>5.1f}%)")
    print(f"  🟡 Moderate (70-79%):   {len(moderate):>3d} modules ({len(moderate)/len(modules)*100:>5.1f}%)")
    print(f"  🟠 Low (50-69%):        {len(low):>3d} modules ({len(low)/len(modules)*100:>5.1f}%)")
    print(f"  🔴 Critical (<50%):     {len(critical):>3d} modules ({len(critical)/len(modules)*100:>5.1f}%)")
    print()


def print_top_gaps(modules: List[Dict], limit: int = 10):
    """Print top coverage gaps by statement count."""
    critical = [m for m in modules if m["percent"] < 50]
    critical_sorted = sorted(critical, key=lambda x: -x["statements"])

    print(f"TOP {limit} COVERAGE GAPS (By Statement Count)")
    print("=" * 80)
    print(f"{'Module':<50} | {'Coverage':<8} | {'Statements':<10} | {'Missing':<8}")
    print("-" * 80)

    for m in critical_sorted[:limit]:
        print(
            f"{m['name']:<50} | {m['percent']:>6.1f}% | {m['statements']:>10d} | {m['missing']:>8d}"
        )
    print()


def print_category_detail(modules: List[Dict], category: str):
    """Print detailed breakdown for specific category."""
    category_modules = [m for m in modules if m["category"] == category]

    if not category_modules:
        print(f"No modules found in category: {category}")
        return

    category_modules.sort(key=lambda x: x["percent"])

    print(f"CATEGORY DETAIL: {category}")
    print("=" * 80)
    print(f"{'Module':<50} | {'Coverage':<8} | {'Statements':<10} | {'Missing':<8}")
    print("-" * 80)

    for m in category_modules:
        print(
            f"{m['name']:<50} | {m['percent']:>6.1f}% | {m['statements']:>10d} | {m['missing']:>8d}"
        )
    print()

    total_stmts = sum(m["statements"] for m in category_modules)
    total_covered = sum(m["covered"] for m in category_modules)
    avg_coverage = (total_covered / total_stmts * 100) if total_stmts > 0 else 0

    print(f"Category Average: {avg_coverage:.1f}%")
    print(f"Total Statements: {total_stmts}")
    print()


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Platform coverage summary visualization")
    parser.add_argument(
        "--format",
        choices=["table", "json", "summary"],
        default="summary",
        help="Output format (default: summary)",
    )
    parser.add_argument(
        "--category",
        type=str,
        help="Show detailed breakdown for specific category",
    )
    parser.add_argument(
        "--coverage-file",
        type=str,
        default="coverage.json",
        help="Path to coverage.json file (default: coverage.json)",
    )

    args = parser.parse_args()

    if not Path(args.coverage_file).exists():
        print(f"Error: Coverage file not found: {args.coverage_file}")
        print("Run: pytest --cov=src/extract_transform_platform --cov-report=json")
        sys.exit(1)

    data = load_coverage_data(args.coverage_file)
    modules = get_module_coverage(data)

    if args.format == "json":
        print(json.dumps(modules, indent=2))
    elif args.category:
        print_summary_stats(modules)
        print_category_detail(modules, args.category)
    else:
        print_summary_stats(modules)
        print_category_breakdown(modules)
        print_tier_distribution(modules)
        print_top_gaps(modules)


if __name__ == "__main__":
    main()
