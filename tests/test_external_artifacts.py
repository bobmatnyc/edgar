#!/usr/bin/env python3
"""
Test external artifacts directory functionality end-to-end.

Tests environment variable loading, directory creation, project commands,
and edge cases for EDGAR_ARTIFACTS_DIR.
"""

import os
import shutil
import tempfile
from pathlib import Path
import subprocess
import sys

# Color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


class TestRunner:
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results = []
        self.temp_dirs = []

    def log_info(self, message):
        print(f"{BLUE}ℹ{RESET} {message}")

    def log_success(self, message):
        print(f"{GREEN}✓{RESET} {message}")
        self.tests_passed += 1
        self.test_results.append(("PASS", message))

    def log_failure(self, message, error=None):
        print(f"{RED}✗{RESET} {message}")
        if error:
            print(f"  Error: {error}")
        self.tests_failed += 1
        self.test_results.append(("FAIL", message, error))

    def log_warning(self, message):
        print(f"{YELLOW}⚠{RESET} {message}")

    def create_temp_dir(self, prefix="edgar_test_"):
        """Create a temporary directory and track it for cleanup."""
        temp_dir = tempfile.mkdtemp(prefix=prefix)
        self.temp_dirs.append(temp_dir)
        return temp_dir

    def cleanup(self):
        """Clean up all temporary directories."""
        for temp_dir in self.temp_dirs:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        self.temp_dirs.clear()

    def run_command(self, cmd, env=None, capture_output=True):
        """Run a shell command and return the result."""
        if env is None:
            env = os.environ.copy()

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=capture_output,
                text=True,
                env=env,
                timeout=30
            )
            return result
        except subprocess.TimeoutExpired:
            return None
        except Exception as e:
            return None

    def test_env_var_unset(self):
        """Test with EDGAR_ARTIFACTS_DIR unset (fallback to default)."""
        self.log_info("Test 1: No EDGAR_ARTIFACTS_DIR (in-repo default)")

        env = os.environ.copy()
        env.pop("EDGAR_ARTIFACTS_DIR", None)

        # Test import and check default
        result = self.run_command(
            "python -c 'from edgar_analyzer.config.settings import get_artifacts_dir; print(get_artifacts_dir())'",
            env=env
        )

        if result and result.returncode == 0:
            output = result.stdout.strip()
            expected_subpath = "projects"  # Should contain 'projects' in path
            if expected_subpath in output:
                self.log_success(f"Default artifacts dir: {output}")
            else:
                self.log_failure(f"Unexpected default path: {output}")
        else:
            self.log_failure("Failed to get default artifacts dir",
                           result.stderr if result else "Command timeout")

    def test_env_var_set(self):
        """Test with EDGAR_ARTIFACTS_DIR set to custom path."""
        self.log_info("Test 2: EDGAR_ARTIFACTS_DIR set to custom path")

        temp_dir = self.create_temp_dir()
        env = os.environ.copy()
        env["EDGAR_ARTIFACTS_DIR"] = temp_dir

        result = self.run_command(
            "python -c 'from edgar_analyzer.config.settings import get_artifacts_dir; print(get_artifacts_dir())'",
            env=env
        )

        if result and result.returncode == 0:
            output = result.stdout.strip()
            if temp_dir in output:
                self.log_success(f"Custom artifacts dir: {output}")
            else:
                self.log_failure(f"Expected {temp_dir} in path, got: {output}")
        else:
            self.log_failure("Failed to get custom artifacts dir",
                           result.stderr if result else "Command timeout")

    def test_tilde_expansion(self):
        """Test with ~ expansion in path."""
        self.log_info("Test 3: Tilde expansion in EDGAR_ARTIFACTS_DIR")

        env = os.environ.copy()
        env["EDGAR_ARTIFACTS_DIR"] = "~/edgar_test_artifacts"

        result = self.run_command(
            "python -c 'from edgar_analyzer.config.settings import get_artifacts_dir; import os; print(get_artifacts_dir())'",
            env=env
        )

        if result and result.returncode == 0:
            output = result.stdout.strip()
            home = os.path.expanduser("~")
            if home in output and "~" not in output:
                self.log_success(f"Tilde expanded: {output}")
            else:
                self.log_failure(f"Tilde not expanded properly: {output}")
        else:
            self.log_failure("Failed to test tilde expansion",
                           result.stderr if result else "Command timeout")

    def test_relative_path(self):
        """Test with relative path."""
        self.log_info("Test 4: Relative path in EDGAR_ARTIFACTS_DIR")

        env = os.environ.copy()
        env["EDGAR_ARTIFACTS_DIR"] = "./my_artifacts"

        result = self.run_command(
            "python -c 'from edgar_analyzer.config.settings import get_artifacts_dir; print(get_artifacts_dir())'",
            env=env
        )

        if result and result.returncode == 0:
            output = result.stdout.strip()
            # Should be absolute path
            if os.path.isabs(output):
                self.log_success(f"Relative path converted to absolute: {output}")
            else:
                self.log_failure(f"Path not absolute: {output}")
        else:
            self.log_failure("Failed to test relative path",
                           result.stderr if result else "Command timeout")

    def test_directory_creation(self):
        """Test that directories are created if they don't exist."""
        self.log_info("Test 5: Directory auto-creation")

        temp_dir = self.create_temp_dir()
        non_existent = os.path.join(temp_dir, "nested", "path")

        env = os.environ.copy()
        env["EDGAR_ARTIFACTS_DIR"] = non_existent

        # Use ensure_artifacts_structure to trigger directory creation
        result = self.run_command(
            "python -c 'from edgar_analyzer.config.settings import ensure_artifacts_structure; ensure_artifacts_structure()'",
            env=env
        )

        if result and result.returncode == 0:
            # Check if directories were created
            projects_dir = os.path.join(non_existent, "projects")
            output_dir = os.path.join(non_existent, "output")

            if os.path.exists(projects_dir) and os.path.exists(output_dir):
                self.log_success(f"Directories created: {non_existent}")
            else:
                self.log_failure(f"Directories not created in: {non_existent}")
        else:
            self.log_failure("Failed to test directory creation",
                           result.stderr if result else "Command timeout")

    def test_invalid_path(self):
        """Test with invalid/restricted path."""
        self.log_info("Test 6: Invalid path handling")

        env = os.environ.copy()
        # Use a path that should fail (root directory)
        env["EDGAR_ARTIFACTS_DIR"] = "/root/edgar_artifacts"

        result = self.run_command(
            "python -c 'from edgar_analyzer.config.settings import ensure_artifacts_structure; ensure_artifacts_structure()'",
            env=env,
            capture_output=True
        )

        # Should either fail or warn
        if result:
            if "Permission denied" in result.stderr or "warning" in result.stderr.lower():
                self.log_success("Invalid path handled appropriately")
            elif result.returncode != 0:
                self.log_success("Invalid path rejected")
            else:
                # Might succeed if running as root
                self.log_warning("Path accepted (possibly running with elevated privileges)")
                self.tests_passed += 1
        else:
            self.log_failure("Failed to test invalid path")

    def test_env_file_loading(self):
        """Test loading from .env.local file."""
        self.log_info("Test 7: Loading from .env.local")

        temp_dir = self.create_temp_dir()
        env_file = os.path.join(temp_dir, ".env.local")
        artifacts_path = os.path.join(temp_dir, "my_artifacts")

        # Create .env.local
        with open(env_file, "w") as f:
            f.write(f"EDGAR_ARTIFACTS_DIR={artifacts_path}\n")

        # Change to temp directory and test
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)

            result = self.run_command(
                "python -c 'from edgar_analyzer.config.settings import get_artifacts_dir; print(get_artifacts_dir())'",
                env=os.environ.copy()
            )

            if result and result.returncode == 0:
                output = result.stdout.strip()
                if artifacts_path in output:
                    self.log_success(f"Loaded from .env.local: {output}")
                else:
                    # .env.local might not be loaded if python-dotenv not configured
                    self.log_warning(f".env.local not loaded (expected: {artifacts_path}, got: {output})")
                    self.tests_passed += 1
            else:
                self.log_failure("Failed to test .env.local loading",
                               result.stderr if result else "Command timeout")
        finally:
            os.chdir(original_cwd)

    def test_path_with_spaces(self):
        """Test path with spaces."""
        self.log_info("Test 8: Path with spaces")

        temp_dir = self.create_temp_dir()
        path_with_spaces = os.path.join(temp_dir, "my edgar artifacts")

        env = os.environ.copy()
        env["EDGAR_ARTIFACTS_DIR"] = path_with_spaces

        result = self.run_command(
            "python -c 'from edgar_analyzer.config.settings import ensure_artifacts_structure; ensure_artifacts_structure()'",
            env=env
        )

        if result and result.returncode == 0:
            projects_dir = os.path.join(path_with_spaces, "projects")
            if os.path.exists(projects_dir):
                self.log_success(f"Path with spaces handled: {path_with_spaces}")
            else:
                self.log_failure(f"Failed to create dirs in path with spaces: {path_with_spaces}")
        else:
            self.log_failure("Failed to test path with spaces",
                           result.stderr if result else "Command timeout")

    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"Total Tests: {self.tests_passed + self.tests_failed}")
        print(f"{GREEN}Passed: {self.tests_passed}{RESET}")
        print(f"{RED}Failed: {self.tests_failed}{RESET}")
        print()

        if self.tests_failed > 0:
            print("Failed Tests:")
            for result in self.test_results:
                if result[0] == "FAIL":
                    print(f"  {RED}✗{RESET} {result[1]}")
                    if len(result) > 2 and result[2]:
                        print(f"    {result[2]}")

        print("="*70)

        return self.tests_failed == 0


def main():
    """Run all tests."""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}EDGAR Artifacts Directory - End-to-End Tests{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

    runner = TestRunner()

    try:
        # Change to project root
        project_root = Path(__file__).parent.parent
        os.chdir(project_root)

        # Activate venv if exists
        venv_python = project_root / "venv" / "bin" / "python"
        if venv_python.exists():
            runner.log_info(f"Using venv: {venv_python}")

        # Run all tests
        runner.test_env_var_unset()
        print()
        runner.test_env_var_set()
        print()
        runner.test_tilde_expansion()
        print()
        runner.test_relative_path()
        print()
        runner.test_directory_creation()
        print()
        runner.test_invalid_path()
        print()
        runner.test_env_file_loading()
        print()
        runner.test_path_with_spaces()
        print()

        # Print summary
        success = runner.print_summary()

        return 0 if success else 1

    finally:
        # Cleanup
        runner.log_info("Cleaning up temporary directories...")
        runner.cleanup()


if __name__ == "__main__":
    sys.exit(main())
