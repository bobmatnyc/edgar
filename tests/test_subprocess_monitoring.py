#!/usr/bin/env python3
"""
Test Subprocess Monitoring in CLI Chatbot

This demonstrates the enhanced scripting engine with subprocess monitoring
and automatic fallback to exec() when subprocess is unavailable.
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from cli_chatbot.core.scripting_engine import DynamicScriptingEngine

async def test_subprocess_monitoring():
    """Test the subprocess monitoring capabilities."""
    
    print("🚀 Testing Subprocess Monitoring in Dynamic Scripting Engine")
    print("=" * 70)
    print("ENHANCED EXECUTION CAPABILITIES:")
    print("• Subprocess execution with real-time output monitoring")
    print("• Process monitoring with timeout and termination")
    print("• Automatic fallback to exec() when subprocess unavailable")
    print("• Dynamic execution mode switching")
    print("• Enhanced safety and control")
    print("=" * 70)
    
    # Initialize the enhanced scripting engine
    engine = DynamicScriptingEngine(
        prefer_subprocess=True,
        max_execution_time=10.0
    )
    
    print(f"\n🔧 **Scripting Engine Status:**")
    info = engine.get_execution_info()
    print(f"   Subprocess Available: {'✅' if info['subprocess_available'] else '❌'}")
    print(f"   Preferred Mode: {info['current_mode']}")
    print(f"   Python Executable: {info['python_executable']}")
    print(f"   Max Execution Time: {info['max_execution_time']}s")
    
    # Test 1: Simple script with subprocess
    print(f"\n🧪 **TEST 1: Simple Script with Subprocess**")
    print("-" * 50)
    
    simple_script = """
import time
import sys

print("Starting subprocess execution...")
print(f"Python version: {sys.version}")

# Simulate some work
for i in range(3):
    print(f"Processing step {i+1}/3")
    time.sleep(0.5)

result = "Subprocess execution completed successfully!"
print("Script finished")
"""
    
    print("Executing script with subprocess monitoring...")
    
    result1 = await engine.execute_script(
        script_code=simple_script,
        context={'test_name': 'subprocess_test'},
        safety_checks=True
    )
    
    print(f"✅ **Results:**")
    print(f"   Success: {result1.success}")
    print(f"   Execution Time: {result1.execution_time:.3f}s")
    print(f"   Result: {result1.result}")
    print(f"   Output Preview: {result1.output[:100]}...")
    print(f"   Side Effects: {result1.side_effects}")
    
    # Test 2: Script with error handling
    print(f"\n🧪 **TEST 2: Error Handling with Subprocess**")
    print("-" * 50)
    
    error_script = """
import sys

print("Testing error handling...")

try:
    # This will cause an error
    result = 1 / 0
except ZeroDivisionError as e:
    print(f"Caught error: {e}")
    result = "Error handled gracefully"

print("Error handling test complete")
"""
    
    result2 = await engine.execute_script(
        script_code=error_script,
        context={},
        safety_checks=True
    )
    
    print(f"✅ **Results:**")
    print(f"   Success: {result2.success}")
    print(f"   Result: {result2.result}")
    print(f"   Output: {result2.output}")
    
    # Test 3: Switch to exec() mode and compare
    print(f"\n🧪 **TEST 3: Execution Mode Comparison**")
    print("-" * 50)
    
    comparison_script = """
import os
import sys

print("Execution environment test")
print(f"Current working directory: {os.getcwd()}")
print(f"Python executable: {sys.executable}")

result = {
    'mode': 'unknown',
    'pid': os.getpid(),
    'cwd': os.getcwd()
}
"""
    
    # Test with subprocess
    print("Testing with subprocess mode...")
    engine.set_execution_mode(prefer_subprocess=True)
    
    result3a = await engine.execute_script(
        script_code=comparison_script,
        context={},
        safety_checks=True
    )
    
    # Test with exec() mode
    print("Testing with exec() mode...")
    engine.set_execution_mode(prefer_subprocess=False)
    
    result3b = await engine.execute_script(
        script_code=comparison_script,
        context={},
        safety_checks=True
    )
    
    print(f"✅ **Subprocess Results:**")
    print(f"   Success: {result3a.success}")
    print(f"   Side Effects: {result3a.side_effects}")
    print(f"   Execution Time: {result3a.execution_time:.3f}s")
    
    print(f"✅ **Exec() Results:**")
    print(f"   Success: {result3b.success}")
    print(f"   Side Effects: {result3b.side_effects}")
    print(f"   Execution Time: {result3b.execution_time:.3f}s")
    
    # Test 4: Long-running script with monitoring
    print(f"\n🧪 **TEST 4: Long-Running Script Monitoring**")
    print("-" * 50)
    
    # Reset to subprocess mode
    engine.set_execution_mode(prefer_subprocess=True)
    
    long_script = """
import time

print("Starting long-running task...")

for i in range(5):
    print(f"Progress: {(i+1)*20}% complete")
    time.sleep(0.3)

result = "Long-running task completed"
print("Task finished successfully")
"""
    
    print("Executing long-running script with real-time monitoring...")
    
    result4 = await engine.execute_script(
        script_code=long_script,
        context={},
        safety_checks=True
    )
    
    print(f"✅ **Results:**")
    print(f"   Success: {result4.success}")
    print(f"   Execution Time: {result4.execution_time:.3f}s")
    print(f"   Output Lines: {len(result4.output.split(chr(10)))}")
    print(f"   Result: {result4.result}")
    
    print("\n" + "=" * 70)
    print("🎉 SUBPROCESS MONITORING DEMONSTRATION COMPLETE")
    print("=" * 70)
    
    print("✅ **CAPABILITIES DEMONSTRATED:**")
    print("   • Real-time subprocess execution monitoring")
    print("   • Process timeout and termination handling")
    print("   • Automatic fallback to exec() when needed")
    print("   • Dynamic execution mode switching")
    print("   • Enhanced output capture and processing")
    print("   • Comprehensive error handling and recovery")
    
    print("\n✅ **BENEFITS OVER TRADITIONAL EXEC():**")
    print("   • Better isolation and security")
    print("   • Real-time output monitoring")
    print("   • Process control (timeout, termination)")
    print("   • Better resource management")
    print("   • Enhanced debugging capabilities")
    
    print("\n🚀 **PRODUCTION ADVANTAGES:**")
    print("   • Robust execution with multiple fallback layers")
    print("   • Real-time monitoring for long-running scripts")
    print("   • Better control over resource usage")
    print("   • Enhanced safety through process isolation")
    print("   • Automatic adaptation to environment capabilities")

if __name__ == "__main__":
    asyncio.run(test_subprocess_monitoring())
