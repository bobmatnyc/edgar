"""EDGAR CLI entry point."""

import sys
from pathlib import Path


def main() -> None:
    """Main CLI entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "e2e-test":
        # Import and run E2E test
        scripts_dir = Path(__file__).parent.parent.parent / "scripts"
        sys.path.insert(0, str(scripts_dir))

        # Remove 'e2e-test' from args
        sys.argv = [sys.argv[0]] + sys.argv[2:]

        from e2e_edgar_extraction import main as run_e2e

        run_e2e()
    elif len(sys.argv) > 1 and sys.argv[1] == "fortune100":
        # Import and run Fortune 100 analysis
        scripts_dir = Path(__file__).parent.parent.parent / "scripts"
        sys.path.insert(0, str(scripts_dir))

        # Remove 'fortune100' from args
        sys.argv = [sys.argv[0]] + sys.argv[2:]

        from fortune100_analysis import main as run_fortune100

        sys.exit(run_fortune100())
    else:
        print("EDGAR Platform CLI")
        print("\nCommands:")
        print("  e2e-test     Run end-to-end extraction test")
        print("  fortune100   Run Fortune 100 compensation vs. tax analysis")
        print("\nUsage:")
        print("  edgar e2e-test [-v] [--phase N]")
        print("  edgar fortune100 [-c 1-10] [-v] [-o OUTPUT_DIR]")


if __name__ == "__main__":
    main()
