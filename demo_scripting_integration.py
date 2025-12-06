#!/usr/bin/env python3
"""
Demo script for Dynamic Scripting Engine integration with Interactive Chat Mode.

This script demonstrates the new file operation capabilities in EDGAR's
interactive chat mode.

Usage:
    python demo_scripting_integration.py
"""

import asyncio
from pathlib import Path
from edgar_analyzer.interactive.session import InteractiveExtractionSession


async def demo_file_operations():
    """Demonstrate file operations via scripting engine."""

    print("=" * 60)
    print("EDGAR Interactive Chat - Scripting Engine Demo")
    print("=" * 60)
    print()

    # Create session
    temp_dir = Path("temp_demo_workspace")
    temp_dir.mkdir(exist_ok=True)

    session = InteractiveExtractionSession(
        project_path=temp_dir,
        test_mode=True
    )

    print("✅ Session initialized")
    print(f"📁 Working directory: {temp_dir}")
    print()

    # Demo 1: Simple script execution
    print("Demo 1: Creating project structure")
    print("-" * 60)

    script1 = """
from pathlib import Path

# Create project directory structure
project = Path("my_project")
project.mkdir(exist_ok=True)

# Create subdirectories
(project / "input").mkdir(exist_ok=True)
(project / "output").mkdir(exist_ok=True)
(project / "examples").mkdir(exist_ok=True)

# Create files
(project / "README.md").write_text("# My Project\\n\\nCreated by EDGAR")
(project / "project.yaml").write_text("name: My Project\\nversion: 1.0")

result = f"Created project structure with {len(list(project.rglob('*')))} items"
"""

    result1 = await session.scripting_engine.execute_script(
        script_code=script1,
        context={"base_dir": str(temp_dir)},
        safety_checks=True
    )

    print(f"Result: {result1.result}")
    print(f"Success: {result1.success}")
    print(f"Execution time: {result1.execution_time:.3f}s")
    print()

    # Demo 2: List directory contents
    print("Demo 2: Listing created files")
    print("-" * 60)

    script2 = """
from pathlib import Path
import os

project = Path("my_project")
files = []

for item in sorted(project.rglob("*")):
    rel_path = item.relative_to(project)
    if item.is_file():
        size = item.stat().st_size
        files.append(f"  📄 {rel_path} ({size} bytes)")
    else:
        files.append(f"  📁 {rel_path}/")

result = "\\n".join(files) if files else "No files found"
"""

    result2 = await session.scripting_engine.execute_script(
        script_code=script2,
        context={},
        safety_checks=True
    )

    print(result2.result)
    print()

    # Demo 3: Copy and move operations
    print("Demo 3: File operations (copy, move)")
    print("-" * 60)

    script3 = """
from pathlib import Path
import shutil

# Create a test file
test_file = Path("my_project") / "input" / "data.txt"
test_file.write_text("Sample data for processing")

# Copy it
copy_dest = Path("my_project") / "examples" / "data_example.txt"
shutil.copy2(test_file, copy_dest)

# Create archive (simulated - we'll skip actual zip for demo)
operations = [
    f"Created: {test_file.name}",
    f"Copied to: {copy_dest.relative_to(Path('my_project'))}"
]

result = "\\n".join(operations)
"""

    result3 = await session.scripting_engine.execute_script(
        script_code=script3,
        context={},
        safety_checks=True
    )

    print(result3.result)
    print()

    # Demo 4: Simulated AI response with embedded script
    print("Demo 4: AI response with embedded script")
    print("-" * 60)

    ai_response = """I'll help you organize those files!

```python:execute
from pathlib import Path
import shutil

# Create organized structure
organized = Path("my_project") / "organized"
organized.mkdir(exist_ok=True)

# Organize by file type
docs = organized / "documents"
data = organized / "data"

docs.mkdir(exist_ok=True)
data.mkdir(exist_ok=True)

# Move files
readme = Path("my_project") / "README.md"
if readme.exists():
    shutil.copy2(readme, docs / "README.md")

result = "Files organized into categories"
```

Your files are now organized!
"""

    print("AI Response:")
    print(ai_response)
    print()

    # Execute the embedded script
    await session._execute_scripts_from_response(ai_response)

    print()
    print("=" * 60)
    print("Demo complete!")
    print()
    print("Summary of capabilities:")
    print("  ✅ Create directories and files")
    print("  ✅ List and inspect file contents")
    print("  ✅ Copy and move files")
    print("  ✅ Extract and execute scripts from AI responses")
    print("  ✅ Safety checks for malicious code")
    print()
    print(f"All demo files created in: {temp_dir / 'my_project'}")
    print()


if __name__ == "__main__":
    asyncio.run(demo_file_operations())
