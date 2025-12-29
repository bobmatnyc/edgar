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
    else:
        print("EDGAR Platform CLI")
        print("\nCommands:")
        print("  e2e-test    Run end-to-end extraction test")
        print("\nUsage:")
        print("  edgar e2e-test [-v] [--phase N]")


if __name__ == "__main__":
    main()
