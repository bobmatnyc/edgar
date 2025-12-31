#!/usr/bin/env python3
"""
Comprehensive QA Test Suite for Interactive Chat Mode

Tests all 15 commands, natural language understanding, session persistence,
error handling, and performance metrics.

Usage:
    python test_interactive_qa.py
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Dict, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from edgar_analyzer.interactive.session import InteractiveExtractionSession


class InteractiveTester:
    """Automated tester for interactive session."""

    def __init__(self):
        self.results: Dict[str, Dict] = {}
        self.session = None
        self.test_project = Path(__file__).parent / "projects" / "weather_test"

    async def setup(self):
        """Initialize test session."""
        print("🔧 Setting up test environment...")
        self.session = InteractiveExtractionSession(project_path=self.test_project)
        print(f"✅ Session initialized with project: {self.test_project}")

    async def test_command(
        self, name: str, command: str, args: str = "", expect_error: bool = False
    ) -> Dict:
        """Test a single command and capture results."""
        print(f"\n🧪 Testing: {name}")
        print(f"   Command: {command} {args}")

        start_time = time.time()
        error = None
        success = False

        try:
            cmd_func = self.session.commands.get(command)
            if not cmd_func:
                raise ValueError(f"Command not found: {command}")

            result = await cmd_func(args)
            success = True if not expect_error else False
            print(f"   ✅ Success (took {time.time() - start_time:.3f}s)")

        except Exception as e:
            error = str(e)
            success = True if expect_error else False
            status = "✅ Expected error" if expect_error else "❌ Unexpected error"
            print(f"   {status}: {error}")

        return {
            "name": name,
            "command": command,
            "args": args,
            "success": success,
            "error": error,
            "duration": time.time() - start_time,
            "expect_error": expect_error,
        }

    async def test_basic_commands(self) -> List[Dict]:
        """Test all 15 basic commands."""
        print("\n" + "=" * 80)
        print("TEST SUITE 1: Basic Command Testing (15 commands)")
        print("=" * 80)

        results = []

        # Test each command in logical workflow order
        commands = [
            ("Help command", "help", ""),
            ("Load project", "load", str(self.test_project)),
            ("Show status", "show", ""),
            ("Show examples", "examples", ""),
            ("Analyze project", "analyze", ""),
            ("Show patterns", "patterns", ""),
            ("Generate code", "generate", ""),
            ("Validate code", "validate", ""),
            ("Extract data", "extract", ""),
            ("Set confidence", "confidence", "0.85"),
            ("Get threshold", "threshold", ""),
            ("Save session", "save", "test_qa"),
            ("List sessions", "sessions", ""),
            ("Resume session", "resume", "test_qa"),
            # Don't test exit as it would end the session
        ]

        for name, cmd, args in commands:
            result = await self.test_command(name, cmd, args)
            results.append(result)
            await asyncio.sleep(0.1)  # Brief delay between commands

        return results

    async def test_natural_language(self) -> List[Dict]:
        """Test natural language understanding."""
        print("\n" + "=" * 80)
        print("TEST SUITE 2: Natural Language Understanding")
        print("=" * 80)

        results = []

        # Test NL queries (we'll parse them manually)
        nl_queries = [
            ("What patterns did you detect?", "patterns", ""),
            ("Show me the examples", "examples", ""),
            ("Can you analyze the project?", "analyze", ""),
            ("Generate the extraction code", "generate", ""),
            ("Set confidence to 0.9", "confidence", "0.9"),
        ]

        for query, expected_cmd, expected_args in nl_queries:
            print(f"\n🧪 Testing NL: '{query}'")
            cmd, args = await self.session._parse_natural_language(query)

            success = cmd == expected_cmd
            status = "✅" if success else "❌"
            print(
                f"   {status} Parsed as: {cmd} {args} (expected: {expected_cmd} {expected_args})"
            )

            results.append(
                {
                    "name": f"NL: {query}",
                    "query": query,
                    "parsed_command": cmd,
                    "parsed_args": args,
                    "expected_command": expected_cmd,
                    "success": success,
                }
            )

        return results

    async def test_error_handling(self) -> List[Dict]:
        """Test error scenarios."""
        print("\n" + "=" * 80)
        print("TEST SUITE 3: Error Handling")
        print("=" * 80)

        results = []

        error_cases = [
            ("Invalid confidence value", "confidence", "5.0", True),
            ("Resume nonexistent session", "resume", "nonexistent_session_xyz", True),
            (
                "Generate without analyze",
                "generate",
                "",
                False,
            ),  # Should work with previous state
        ]

        for name, cmd, args, expect_error in error_cases:
            result = await self.test_command(name, cmd, args, expect_error)
            results.append(result)

        return results

    async def test_session_persistence(self) -> Dict:
        """Test session save and restore."""
        print("\n" + "=" * 80)
        print("TEST SUITE 4: Session Persistence")
        print("=" * 80)

        # Save session
        print("\n🧪 Testing session save...")
        await self.session.cmd_save_session("persist_test")

        # Check if session file exists
        session_file = Path.home() / ".edgar" / "sessions" / "persist_test_session.json"
        save_success = session_file.exists()
        print(f"   {'✅' if save_success else '❌'} Session file: {session_file}")

        # Create new session and restore
        print("\n🧪 Testing session restore...")
        new_session = InteractiveExtractionSession()
        await new_session.cmd_resume_session("persist_test")

        restore_success = new_session.project_config is not None
        print(
            f"   {'✅' if restore_success else '❌'} Session restored with project config"
        )

        return {
            "save_success": save_success,
            "restore_success": restore_success,
            "session_file": str(session_file),
        }

    async def test_performance(self) -> Dict:
        """Test performance metrics."""
        print("\n" + "=" * 80)
        print("TEST SUITE 5: Performance Testing")
        print("=" * 80)

        metrics = {}

        # Test full workflow timing
        print("\n🧪 Testing full workflow performance...")
        start = time.time()

        await self.session.cmd_load_project(str(self.test_project))
        await self.session.cmd_analyze("")
        await self.session.cmd_generate_code("")
        await self.session.cmd_validate_code("")
        await self.session.cmd_run_extraction("")

        total_time = time.time() - start
        metrics["full_workflow"] = total_time
        print(f"   ⏱️  Full workflow: {total_time:.2f}s")

        # Individual command timings (already captured in basic tests)
        return metrics

    async def run_all_tests(self):
        """Execute all test suites."""
        print("\n" + "=" * 80)
        print("🚀 INTERACTIVE CHAT MODE - COMPREHENSIVE QA TESTING")
        print("=" * 80)

        await self.setup()

        # Run test suites
        basic_results = await self.test_basic_commands()
        nl_results = await self.test_natural_language()
        error_results = await self.test_error_handling()
        persistence_results = await self.test_session_persistence()
        performance_results = await self.test_performance()

        # Compile final report
        self.generate_report(
            basic_results,
            nl_results,
            error_results,
            persistence_results,
            performance_results,
        )

    def generate_report(
        self,
        basic_results: List[Dict],
        nl_results: List[Dict],
        error_results: List[Dict],
        persistence_results: Dict,
        performance_results: Dict,
    ):
        """Generate comprehensive test report."""
        print("\n\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST REPORT")
        print("=" * 80)

        # Basic commands summary
        basic_pass = sum(1 for r in basic_results if r["success"])
        basic_total = len(basic_results)
        print(
            f"\n✅ Basic Commands: {basic_pass}/{basic_total} passed ({basic_pass/basic_total*100:.1f}%)"
        )

        for r in basic_results:
            status = "✅" if r["success"] else "❌"
            print(f"   {status} {r['name']} - {r['duration']:.3f}s")

        # NL understanding summary
        nl_pass = sum(1 for r in nl_results if r["success"])
        nl_total = len(nl_results)
        print(
            f"\n✅ Natural Language: {nl_pass}/{nl_total} passed ({nl_pass/nl_total*100:.1f}%)"
        )

        for r in nl_results:
            status = "✅" if r["success"] else "❌"
            print(f"   {status} '{r['query'][:50]}...' → {r['parsed_command']}")

        # Error handling summary
        error_pass = sum(1 for r in error_results if r["success"])
        error_total = len(error_results)
        print(
            f"\n✅ Error Handling: {error_pass}/{error_total} passed ({error_pass/error_total*100:.1f}%)"
        )

        # Session persistence summary
        persist_success = (
            persistence_results["save_success"]
            and persistence_results["restore_success"]
        )
        print(f"\n{'✅' if persist_success else '❌'} Session Persistence")
        print(f"   Save: {'✅' if persistence_results['save_success'] else '❌'}")
        print(f"   Restore: {'✅' if persistence_results['restore_success'] else '❌'}")

        # Performance summary
        print("\n⏱️  Performance Metrics")
        print(f"   Full workflow: {performance_results['full_workflow']:.2f}s")
        target = 10.0
        perf_status = "✅" if performance_results["full_workflow"] < target else "❌"
        print(f"   {perf_status} Target: <{target}s")

        # Overall summary
        print("\n" + "=" * 80)
        total_tests = basic_total + nl_total + error_total + 1  # +1 for persistence
        total_pass = basic_pass + nl_pass + error_pass + (1 if persist_success else 0)
        print(
            f"🎯 OVERALL: {total_pass}/{total_tests} tests passed ({total_pass/total_tests*100:.1f}%)"
        )

        # Production readiness check
        is_ready = (
            basic_pass == basic_total
            and nl_pass >= nl_total * 0.8  # 80% NL accuracy acceptable
            and error_pass == error_total
            and persist_success
            and performance_results["full_workflow"] < 10.0
        )

        print("\n" + "=" * 80)
        if is_ready:
            print("✅ PRODUCTION READY - All critical tests passed")
        else:
            print("❌ NOT PRODUCTION READY - Some tests failed")
        print("=" * 80)

        # Save detailed report
        report_file = Path(__file__).parent / "INTERACTIVE_CHAT_QA_REPORT.json"
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "basic_commands": basic_results,
            "natural_language": nl_results,
            "error_handling": error_results,
            "session_persistence": persistence_results,
            "performance": performance_results,
            "summary": {
                "total_tests": total_tests,
                "total_passed": total_pass,
                "pass_rate": total_pass / total_tests,
                "production_ready": is_ready,
            },
        }

        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        print(f"\n📄 Detailed report saved to: {report_file}")


async def main():
    """Main entry point."""
    tester = InteractiveTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
