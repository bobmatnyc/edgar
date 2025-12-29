#!/usr/bin/env python3
"""End-to-end EDGAR extraction runbook.

This script executes the complete extraction pipeline:
1. Data Acquisition - Fetch SEC filing
2. Pattern Analysis - Detect transformation patterns
3. Code Generation - (Pre-built extractor used)
4. Extraction Execution - Run extractor and validate

Usage:
    python scripts/e2e_edgar_extraction.py           # Full run
    python scripts/e2e_edgar_extraction.py --verbose # Verbose output
    python scripts/e2e_edgar_extraction.py --phase 2 # Run specific phase only
"""

import argparse
import asyncio
import json
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from edgar.services.sec_edgar_client import SecEdgarClient
from edgar.services.pattern_analyzer import PatternAnalyzer
from edgar.extractors.sct import SCTExtractor


@dataclass
class PhaseResult:
    """Result of a phase execution."""

    phase: int
    name: str
    status: str  # PASSED, FAILED, SKIPPED
    duration: float
    message: str = ""
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class RunbookResult:
    """Result of full runbook execution."""

    success: bool
    phases: list[PhaseResult]
    total_duration: float
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "total_duration": self.total_duration,
            "timestamp": self.timestamp,
            "phases": [
                {
                    "phase": p.phase,
                    "name": p.name,
                    "status": p.status,
                    "duration": p.duration,
                    "message": p.message,
                }
                for p in self.phases
            ],
        }


# Configuration
APPLE_CIK = "0000320193"
DATA_DIR = Path("/Users/masa/Projects/edgar/data/e2e_test")
OUTPUT_DIR = Path("/Users/masa/Projects/edgar/output/e2e_test")


async def phase1_acquire_data(verbose: bool = False) -> PhaseResult:
    """Phase 1: Data Acquisition - Fetch Apple's DEF 14A filing."""
    start = time.time()

    try:
        if verbose:
            print("  Fetching company submissions...")

        client = SecEdgarClient(user_agent="EDGAR E2E Test edgar-test@example.com")

        # Get latest DEF 14A
        filing = await client.get_latest_filing(APPLE_CIK, "DEF 14A")

        if verbose:
            print(f"  Found filing: {filing['filing_date']}")
            print("  Downloading HTML...")

        # Fetch HTML
        html = await client.fetch_filing_html(filing["url"])

        # Save to file
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        html_path = DATA_DIR / "apple_def14a_raw.html"
        html_path.write_text(html)

        # Create ground truth
        ground_truth = {
            "company": "Apple Inc.",
            "cik": APPLE_CIK,
            "filing_type": "DEF 14A",
            "filing_date": filing["filing_date"],
            "validation_rules": {
                "min_executives": 5,
                "ceo_name_contains": "Cook",
                "ceo_total_min": 60000000,
            },
        }

        gt_path = DATA_DIR / "apple_sct_ground_truth.json"
        with open(gt_path, "w") as f:
            json.dump(ground_truth, f, indent=2)

        duration = time.time() - start

        return PhaseResult(
            phase=1,
            name="Data Acquisition",
            status="PASSED",
            duration=duration,
            message=f"Downloaded {len(html):,} bytes, filing date {filing['filing_date']}",
            data={"html_size": len(html), "filing_date": filing["filing_date"]},
        )

    except Exception as e:
        return PhaseResult(
            phase=1,
            name="Data Acquisition",
            status="FAILED",
            duration=time.time() - start,
            message=str(e),
        )


def phase2_analyze_patterns(verbose: bool = False) -> PhaseResult:
    """Phase 2: Pattern Analysis - Detect transformation patterns."""
    start = time.time()

    try:
        # Load Phase 1 data
        html_path = DATA_DIR / "apple_def14a_raw.html"
        if not html_path.exists():
            raise FileNotFoundError("Phase 1 data not found. Run Phase 1 first.")

        html = html_path.read_text()

        with open(DATA_DIR / "apple_sct_ground_truth.json") as f:
            ground_truth = json.load(f)

        if verbose:
            print("  Running pattern analysis...")

        # Analyze patterns
        analyzer = PatternAnalyzer()
        result = analyzer.analyze(html, {}, ground_truth)

        if verbose:
            print(f"  Detected {len(result.patterns)} patterns")
            print(f"  Overall confidence: {result.overall_confidence:.1%}")

        # Save results
        output = {
            "patterns": [p.model_dump() for p in result.patterns],
            "overall_confidence": result.overall_confidence,
            "input_schema": result.input_schema,
            "output_schema": result.output_schema,
            "recommendations": result.recommendations,
        }

        with open(DATA_DIR / "pattern_analysis.json", "w") as f:
            json.dump(output, f, indent=2)

        duration = time.time() - start

        # Check confidence threshold
        if result.overall_confidence < 0.85:
            return PhaseResult(
                phase=2,
                name="Pattern Analysis",
                status="FAILED",
                duration=duration,
                message=f"Confidence {result.overall_confidence:.1%} < 85% threshold",
                data={
                    "patterns": len(result.patterns),
                    "confidence": result.overall_confidence,
                },
            )

        return PhaseResult(
            phase=2,
            name="Pattern Analysis",
            status="PASSED",
            duration=duration,
            message=f"{len(result.patterns)} patterns, {result.overall_confidence:.1%} confidence",
            data={
                "patterns": len(result.patterns),
                "confidence": result.overall_confidence,
            },
        )

    except Exception as e:
        return PhaseResult(
            phase=2,
            name="Pattern Analysis",
            status="FAILED",
            duration=time.time() - start,
            message=str(e),
        )


def phase3_verify_extractor(verbose: bool = False) -> PhaseResult:
    """Phase 3: Verify SCT Extractor is available."""
    start = time.time()

    try:
        if verbose:
            print("  Verifying extractor module...")

        # Import and instantiate extractor
        from edgar.extractors.sct import SCTExtractor

        # Verify extractor can be instantiated
        _ = SCTExtractor(company="Apple Inc.", cik=APPLE_CIK)

        if verbose:
            print("  Extractor loaded successfully")

        duration = time.time() - start

        return PhaseResult(
            phase=3,
            name="Extractor Verification",
            status="PASSED",
            duration=duration,
            message="SCTExtractor ready",
            data={"extractor_type": "SCTExtractor"},
        )

    except ImportError as e:
        return PhaseResult(
            phase=3,
            name="Extractor Verification",
            status="FAILED",
            duration=time.time() - start,
            message=f"Import error: {e}",
        )
    except Exception as e:
        return PhaseResult(
            phase=3,
            name="Extractor Verification",
            status="FAILED",
            duration=time.time() - start,
            message=str(e),
        )


def phase4_run_extraction(verbose: bool = False) -> PhaseResult:
    """Phase 4: Run extraction and validate results."""
    start = time.time()

    try:
        # Load data
        html_path = DATA_DIR / "apple_def14a_raw.html"
        if not html_path.exists():
            raise FileNotFoundError("Phase 1 data not found")

        html = html_path.read_text()

        with open(DATA_DIR / "apple_sct_ground_truth.json") as f:
            ground_truth = json.load(f)

        if verbose:
            print("  Running extraction...")

        # Run extractor
        extractor = SCTExtractor(company="Apple Inc.", cik=APPLE_CIK)
        result = extractor.extract({"html": html})

        if verbose:
            print(f"  Extracted {len(result.executives)} executives")

        # Save results
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_DIR / "apple_sct_extracted.json", "w") as f:
            json.dump(result.model_dump(), f, indent=2)

        # Validate
        rules = ground_truth.get("validation_rules", {})
        min_execs = rules.get("min_executives", 5)
        ceo_pattern = rules.get("ceo_name_contains", "Cook")
        ceo_min_total = rules.get("ceo_total_min", 60000000)

        # Check executive count
        if len(result.executives) < min_execs:
            return PhaseResult(
                phase=4,
                name="Extraction Execution",
                status="FAILED",
                duration=time.time() - start,
                message=f"Only {len(result.executives)} executives (need {min_execs})",
            )

        # Check CEO
        ceo = next((e for e in result.executives if ceo_pattern in e.name), None)
        if not ceo:
            return PhaseResult(
                phase=4,
                name="Extraction Execution",
                status="FAILED",
                duration=time.time() - start,
                message=f"CEO not found (expected '{ceo_pattern}')",
            )

        ceo_total = ceo.compensation[0].total if ceo.compensation else 0
        if ceo_total < ceo_min_total:
            return PhaseResult(
                phase=4,
                name="Extraction Execution",
                status="FAILED",
                duration=time.time() - start,
                message=f"CEO total ${ceo_total:,.0f} < ${ceo_min_total:,.0f}",
            )

        duration = time.time() - start

        return PhaseResult(
            phase=4,
            name="Extraction Execution",
            status="PASSED",
            duration=duration,
            message=f"{len(result.executives)} executives, CEO total ${ceo_total:,.0f}",
            data={
                "executives": len(result.executives),
                "ceo_total": ceo_total,
                "total_compensation": result.total_compensation,
            },
        )

    except Exception as e:
        return PhaseResult(
            phase=4,
            name="Extraction Execution",
            status="FAILED",
            duration=time.time() - start,
            message=str(e),
        )


async def run_e2e_test(
    verbose: bool = False,
    phase_only: int | None = None,
) -> RunbookResult:
    """Run the complete E2E test pipeline."""
    start = time.time()
    phases: list[PhaseResult] = []

    print("\n" + "=" * 60)
    print("EDGAR E2E Extraction Test")
    print("=" * 60 + "\n")

    # Phase 1: Data Acquisition
    if phase_only is None or phase_only == 1:
        print("Phase 1: Data Acquisition")
        result = await phase1_acquire_data(verbose)
        phases.append(result)
        print(f"  → {result.status}: {result.message} ({result.duration:.1f}s)\n")

        if result.status == "FAILED" and phase_only is None:
            # Can't continue without data
            return RunbookResult(
                success=False,
                phases=phases,
                total_duration=time.time() - start,
                timestamp=datetime.now().isoformat(),
            )

    # Phase 2: Pattern Analysis
    if phase_only is None or phase_only == 2:
        print("Phase 2: Pattern Analysis")
        result = phase2_analyze_patterns(verbose)
        phases.append(result)
        print(f"  → {result.status}: {result.message} ({result.duration:.1f}s)\n")

    # Phase 3: Extractor Verification
    if phase_only is None or phase_only == 3:
        print("Phase 3: Extractor Verification")
        result = phase3_verify_extractor(verbose)
        phases.append(result)
        print(f"  → {result.status}: {result.message} ({result.duration:.1f}s)\n")

        if result.status == "FAILED" and phase_only is None:
            return RunbookResult(
                success=False,
                phases=phases,
                total_duration=time.time() - start,
                timestamp=datetime.now().isoformat(),
            )

    # Phase 4: Extraction Execution
    if phase_only is None or phase_only == 4:
        print("Phase 4: Extraction Execution")
        result = phase4_run_extraction(verbose)
        phases.append(result)
        print(f"  → {result.status}: {result.message} ({result.duration:.1f}s)\n")

    # Calculate overall status
    total_duration = time.time() - start
    success = all(p.status == "PASSED" for p in phases)

    # Print summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for phase in phases:
        status_icon = "✅" if phase.status == "PASSED" else "❌"
        print(f"  {status_icon} Phase {phase.phase}: {phase.name} - {phase.status}")

    print(f"\nTotal Duration: {total_duration:.1f}s")
    print(f"Overall Status: {'✅ PASSED' if success else '❌ FAILED'}")
    print("=" * 60 + "\n")

    # Save results
    runbook_result = RunbookResult(
        success=success,
        phases=phases,
        total_duration=total_duration,
        timestamp=datetime.now().isoformat(),
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_DIR / "e2e_runbook_result.json", "w") as f:
        json.dump(runbook_result.to_dict(), f, indent=2)

    return runbook_result


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="EDGAR E2E Extraction Test Runbook",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/e2e_edgar_extraction.py           # Run full E2E test
  python scripts/e2e_edgar_extraction.py -v        # Verbose output
  python scripts/e2e_edgar_extraction.py --phase 2 # Run Phase 2 only
        """,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "--phase",
        type=int,
        choices=[1, 2, 3, 4],
        help="Run specific phase only",
    )

    args = parser.parse_args()

    # Run async event loop
    result = asyncio.run(
        run_e2e_test(
            verbose=args.verbose,
            phase_only=args.phase,
        )
    )

    # Exit with appropriate code
    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
