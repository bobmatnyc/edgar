"""EDGAR CLI entry point.

Usage:
    edgar                           Show help
    edgar fortune100                Run Fortune 100 analysis (all companies)
    edgar fortune100 -c 1-10 -v     Top 10 companies, verbose
    edgar e2e-test                  Run E2E extraction test
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path


def fortune100_command(args: argparse.Namespace) -> int:
    """Run Fortune 100 analysis pipeline."""
    from edgar.pipelines import Fortune100Pipeline, PipelineConfig

    # Parse company range
    try:
        start, end = map(int, args.companies.split("-"))
        if not (1 <= start <= 100 and 1 <= end <= 100):
            print("Error: Company ranks must be between 1 and 100")
            return 1
        if start > end:
            print(f"Error: Start rank {start} must be <= end rank {end}")
            return 1
    except ValueError:
        print(f"Error: Invalid company range format: {args.companies}")
        return 1

    config = PipelineConfig(
        companies_range=(start, end),
        fiscal_year=args.year,
        output_dir=Path(args.output),
        verbose=args.verbose,
        max_concurrent=args.concurrent,
        skip_def14a=args.skip_def14a,
        skip_10k=args.skip_10k,
    )

    print("=" * 60)
    print("Fortune 100 Executive Compensation vs. Corporate Tax Analysis")
    print("=" * 60)
    print(f"Companies: Ranks {start}-{end}")
    print(f"Output: {config.output_dir}")
    if config.fiscal_year:
        print(f"Fiscal Year: {config.fiscal_year}")
    print()

    pipeline = Fortune100Pipeline(config)
    result = asyncio.run(pipeline.run())

    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Status: {'SUCCESS' if result.success else 'FAILED'}")
    print(f"Duration: {result.total_duration:.1f}s")
    print(f"Companies: {result.companies_processed}")

    if result.def14a_results:
        print(
            f"DEF 14A: {result.def14a_results.success_count} succeeded, "
            f"{result.def14a_results.failure_count} failed "
            f"({result.def14a_results.success_rate:.1%} success rate)"
        )

    if result.form10k_results:
        print(
            f"10-K: {result.form10k_results.success_count} succeeded, "
            f"{result.form10k_results.failure_count} failed "
            f"({result.form10k_results.success_rate:.1%} success rate)"
        )

    print(f"\nOutput Files ({len(result.output_files)}):")
    for path in result.output_files:
        print(f"  - {path}")

    return 0 if result.success else 1


def e2e_test_command(args: argparse.Namespace) -> int:
    """Run E2E extraction test."""
    scripts_dir = Path(__file__).parent.parent.parent / "scripts"
    sys.path.insert(0, str(scripts_dir))

    from e2e_edgar_extraction import main as run_e2e

    run_e2e()
    return 0


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="edgar",
        description="EDGAR Platform - SEC Filing Data Extraction",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  edgar fortune100                    # All 100 companies
  edgar fortune100 -c 1-10 -v         # Top 10, verbose
  edgar fortune100 -c 1-20 -o ./out   # Top 20, custom output
  edgar e2e-test                      # Run E2E test
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # fortune100 command
    f100_parser = subparsers.add_parser(
        "fortune100",
        help="Run Fortune 100 compensation vs. tax analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    f100_parser.add_argument(
        "--companies",
        "-c",
        type=str,
        default="1-100",
        help="Company rank range (default: 1-100)",
    )
    f100_parser.add_argument(
        "--year",
        "-y",
        type=int,
        default=None,
        help="Specific fiscal year (default: most recent)",
    )
    f100_parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="output/fortune100",
        help="Output directory (default: output/fortune100)",
    )
    f100_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )
    f100_parser.add_argument(
        "--concurrent",
        type=int,
        default=5,
        help="Max concurrent requests (default: 5)",
    )
    f100_parser.add_argument(
        "--skip-def14a",
        action="store_true",
        help="Skip DEF 14A (executive compensation) extraction",
    )
    f100_parser.add_argument(
        "--skip-10k",
        action="store_true",
        help="Skip 10-K (corporate tax) extraction",
    )
    f100_parser.set_defaults(func=fortune100_command)

    # e2e-test command
    e2e_parser = subparsers.add_parser(
        "e2e-test",
        help="Run end-to-end extraction test",
    )
    e2e_parser.set_defaults(func=e2e_test_command)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
