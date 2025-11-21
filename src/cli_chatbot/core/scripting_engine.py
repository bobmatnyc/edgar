"""
Dynamic Scripting Engine

Provides safe, sandboxed execution of dynamically generated Python code
with dependency injection capabilities for input/output modification.
"""

import ast
import sys
import io
import time
import traceback
import subprocess
import tempfile
import os
import threading
import queue
from typing import Dict, Any, List, Optional, Callable
from contextlib import redirect_stdout, redirect_stderr
import structlog

from .interfaces import ScriptExecutor, ScriptResult, InputOutputModifier

logger = structlog.get_logger(__name__)


class ProcessMonitor:
    """Monitor subprocess execution with real-time output streaming."""

    def __init__(self, process: subprocess.Popen, timeout: float = 30.0):
        self.process = process
        self.timeout = timeout
        self.stdout_lines = []
        self.stderr_lines = []
        self.output_queue = queue.Queue()
        self.error_queue = queue.Queue()

    def _read_output(self, stream, output_queue):
        """Read output from stream in a separate thread."""
        try:
            for line in iter(stream.readline, ''):
                if line:
                    # Line is already a string in text mode
                    clean_line = line.rstrip()
                    output_queue.put(clean_line)
                    logger.debug("Process output", line=clean_line)
        except Exception as e:
            logger.warning("Error reading process output", error=str(e))
        finally:
            stream.close()

    def monitor_execution(self) -> Dict[str, Any]:
        """Monitor process execution with real-time output capture."""

        # Start output reading threads
        stdout_thread = threading.Thread(
            target=self._read_output,
            args=(self.process.stdout, self.output_queue)
        )
        stderr_thread = threading.Thread(
            target=self._read_output,
            args=(self.process.stderr, self.error_queue)
        )

        stdout_thread.daemon = True
        stderr_thread.daemon = True
        stdout_thread.start()
        stderr_thread.start()

        start_time = time.time()

        try:
            # Wait for process completion with timeout
            return_code = self.process.wait(timeout=self.timeout)
            execution_time = time.time() - start_time

            # Wait a bit for output threads to finish
            stdout_thread.join(timeout=1.0)
            stderr_thread.join(timeout=1.0)

            # Collect all output
            while not self.output_queue.empty():
                self.stdout_lines.append(self.output_queue.get_nowait())

            while not self.error_queue.empty():
                self.stderr_lines.append(self.error_queue.get_nowait())

            return {
                'success': return_code == 0,
                'return_code': return_code,
                'stdout': '\n'.join(self.stdout_lines),
                'stderr': '\n'.join(self.stderr_lines),
                'execution_time': execution_time,
                'timeout': False
            }

        except subprocess.TimeoutExpired:
            # Process timed out - terminate it
            self.process.terminate()
            try:
                self.process.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()

            execution_time = time.time() - start_time

            return {
                'success': False,
                'return_code': -1,
                'stdout': '\n'.join(self.stdout_lines),
                'stderr': f"Process timed out after {self.timeout} seconds",
                'execution_time': execution_time,
                'timeout': True
            }

        except Exception as e:
            execution_time = time.time() - start_time

            return {
                'success': False,
                'return_code': -1,
                'stdout': '\n'.join(self.stdout_lines),
                'stderr': f"Process monitoring error: {str(e)}",
                'execution_time': execution_time,
                'timeout': False
            }

class DynamicScriptingEngine(ScriptExecutor):
    """
    Dynamic scripting engine with safety checks and dependency injection.
    
    Provides secure execution of dynamically generated Python code with
    input/output modification capabilities and comprehensive safety validation.
    """
    
    def __init__(
        self,
        allowed_imports: List[str] = None,
        max_execution_time: float = 30.0,
        input_modifiers: List[InputOutputModifier] = None,
        output_modifiers: List[InputOutputModifier] = None,
        prefer_subprocess: bool = True,
        python_executable: str = None
    ):
        """
        Initialize the dynamic scripting engine.

        Args:
            allowed_imports: List of allowed import modules
            max_execution_time: Maximum script execution time in seconds
            input_modifiers: Functions to modify input before script execution
            output_modifiers: Functions to modify output after script execution
            prefer_subprocess: Whether to prefer subprocess execution over exec()
            python_executable: Path to Python executable (defaults to sys.executable)
        """
        self.allowed_imports = allowed_imports or [
            'json', 'datetime', 'math', 'random', 'os', 'sys', 'pathlib',
            'collections', 'itertools', 'functools', 're', 'typing', 'time'
        ]
        self.max_execution_time = max_execution_time
        self.input_modifiers = input_modifiers or []
        self.output_modifiers = output_modifiers or []
        self.prefer_subprocess = prefer_subprocess
        self.python_executable = python_executable or sys.executable

        # Test subprocess availability
        self.subprocess_available = self._test_subprocess_availability()
        
        # Dangerous operations to block
        self.blocked_operations = {
            'eval', 'exec', 'compile', '__import__', 'open', 'file',
            'input', 'raw_input', 'reload', 'vars', 'globals', 'locals',
            'dir', 'hasattr', 'getattr', 'setattr', 'delattr'
        }
        
        logger.info("Dynamic Scripting Engine initialized",
                   allowed_imports=len(self.allowed_imports),
                   max_execution_time=max_execution_time,
                   subprocess_available=self.subprocess_available,
                   prefer_subprocess=prefer_subprocess)

    def _test_subprocess_availability(self) -> bool:
        """Test if subprocess execution is available and working."""
        try:
            # Simple test - run Python with a basic command
            result = subprocess.run(
                [self.python_executable, '-c', 'print("test")'],
                capture_output=True,
                text=True,
                timeout=5.0
            )

            success = result.returncode == 0 and result.stdout.strip() == "test"

            if success:
                logger.info("Subprocess execution available", python_executable=self.python_executable)
            else:
                logger.warning("Subprocess test failed",
                             returncode=result.returncode,
                             stdout=result.stdout,
                             stderr=result.stderr)

            return success

        except Exception as e:
            logger.warning("Subprocess not available", error=str(e))
            return False

    async def execute_script(
        self,
        script_code: str,
        context: Dict[str, Any],
        safety_checks: bool = True
    ) -> ScriptResult:
        """Execute dynamic script code with context and safety checks."""

        start_time = time.time()

        # Apply input modifiers
        modified_context = context.copy()
        for modifier in self.input_modifiers:
            try:
                modified_context = modifier(modified_context)
            except Exception as e:
                logger.warning("Input modifier failed", error=str(e))

        # Safety validation
        if safety_checks and not self.validate_script_safety(script_code):
            return ScriptResult(
                success=False,
                result=None,
                output="",
                error="Script failed safety validation",
                execution_time=time.time() - start_time,
                side_effects=[]
            )

        # Choose execution method
        if self.prefer_subprocess and self.subprocess_available:
            logger.debug("Using subprocess execution")
            return await self._execute_with_subprocess(script_code, modified_context, start_time)
        else:
            logger.debug("Using exec() execution")
            return await self._execute_with_exec(script_code, modified_context, start_time)

    async def _execute_with_subprocess(
        self,
        script_code: str,
        context: Dict[str, Any],
        start_time: float
    ) -> ScriptResult:
        """Execute script using subprocess with real-time monitoring."""

        try:
            # Create temporary script file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
                # Write context setup and script code
                temp_file.write("import json\n")
                temp_file.write("import sys\n")
                temp_file.write("import os\n")

                # Inject context as variables
                temp_file.write("\n# Injected context\n")
                for key, value in context.items():
                    if isinstance(value, (str, int, float, bool, list, dict)):
                        temp_file.write(f"{key} = {repr(value)}\n")

                temp_file.write("\n# User script\n")
                temp_file.write(script_code)

                # Add result capture
                temp_file.write("\n\n# Capture result\n")
                temp_file.write("if 'result' in locals():\n")
                temp_file.write("    import json\n")
                temp_file.write("    print(f'__RESULT__:{json.dumps(result)}')\n")

                temp_file_path = temp_file.name

            # Execute with subprocess
            process = subprocess.Popen(
                [self.python_executable, temp_file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # Monitor execution
            monitor = ProcessMonitor(process, self.max_execution_time)
            execution_result = monitor.monitor_execution()

            # Clean up temp file
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.warning("Failed to clean up temp file", error=str(e))

            # Parse results
            stdout = execution_result['stdout']
            stderr = execution_result['stderr']

            # Extract result if present
            result = None
            output_lines = []

            for line in stdout.split('\n'):
                if line.startswith('__RESULT__:'):
                    try:
                        result_json = line[11:]  # Remove '__RESULT__:' prefix
                        result = json.loads(result_json)
                    except json.JSONDecodeError:
                        pass
                else:
                    output_lines.append(line)

            clean_output = '\n'.join(output_lines).strip()

            # Apply output modifiers
            for modifier in self.output_modifiers:
                try:
                    result = modifier(result)
                except Exception as e:
                    logger.warning("Output modifier failed", error=str(e))

            execution_time = time.time() - start_time

            return ScriptResult(
                success=execution_result['success'],
                result=result,
                output=clean_output,
                error=stderr if not execution_result['success'] else None,
                execution_time=execution_time,
                side_effects=[f"Subprocess execution: PID {process.pid}"]
            )

        except Exception as e:
            execution_time = time.time() - start_time

            logger.error("Subprocess execution failed", error=str(e))

            # Fallback to exec() method
            logger.info("Falling back to exec() execution")
            return await self._execute_with_exec(script_code, context, start_time)

    async def _execute_with_exec(
        self,
        script_code: str,
        context: Dict[str, Any],
        start_time: float
    ) -> ScriptResult:
        """Execute script using exec() with output capture."""

        # Prepare execution environment
        safe_globals = self._create_safe_globals()
        safe_locals = context.copy()

        # Capture output
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                # Execute the script
                exec(script_code, safe_globals, safe_locals)

            # Get the result (look for 'result' variable or last expression)
            result = safe_locals.get('result', None)

            # Apply output modifiers
            for modifier in self.output_modifiers:
                try:
                    result = modifier(result)
                except Exception as e:
                    logger.warning("Output modifier failed", error=str(e))

            execution_time = time.time() - start_time

            return ScriptResult(
                success=True,
                result=result,
                output=stdout_capture.getvalue(),
                error=None,
                execution_time=execution_time,
                side_effects=self._detect_side_effects(safe_locals, context)
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_output = stderr_capture.getvalue()

            logger.error("Exec() execution failed",
                        error=str(e),
                        execution_time=execution_time)

            return ScriptResult(
                success=False,
                result=None,
                output=stdout_capture.getvalue(),
                error=f"{str(e)}\n{error_output}",
                execution_time=execution_time,
                side_effects=[]
            )

    def set_execution_mode(self, prefer_subprocess: bool = True):
        """
        Dynamically change the execution mode preference.

        Args:
            prefer_subprocess: Whether to prefer subprocess over exec()
        """
        self.prefer_subprocess = prefer_subprocess
        logger.info("Execution mode changed",
                   prefer_subprocess=prefer_subprocess,
                   subprocess_available=self.subprocess_available)

    def get_execution_info(self) -> Dict[str, Any]:
        """Get information about current execution capabilities."""
        return {
            'subprocess_available': self.subprocess_available,
            'prefer_subprocess': self.prefer_subprocess,
            'python_executable': self.python_executable,
            'max_execution_time': self.max_execution_time,
            'current_mode': 'subprocess' if (self.prefer_subprocess and self.subprocess_available) else 'exec',
            'allowed_imports': self.allowed_imports,
            'input_modifiers': len(self.input_modifiers),
            'output_modifiers': len(self.output_modifiers)
        }

    def validate_script_safety(self, script_code: str) -> bool:
        """Validate that script code is safe to execute."""
        
        try:
            # Parse the AST
            tree = ast.parse(script_code)
            
            # Check for dangerous operations
            for node in ast.walk(tree):
                # Check for dangerous function calls
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in self.blocked_operations:
                            logger.warning("Blocked dangerous operation", operation=node.func.id)
                            return False
                
                # Check for dangerous imports
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name not in self.allowed_imports:
                            logger.warning("Blocked import", module=alias.name)
                            return False
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module not in self.allowed_imports:
                        logger.warning("Blocked import from", module=node.module)
                        return False
                
                # Check for attribute access to dangerous modules
                elif isinstance(node, ast.Attribute):
                    if isinstance(node.value, ast.Name):
                        if node.value.id in ['os', 'sys'] and node.attr in ['system', 'exit', 'quit']:
                            logger.warning("Blocked dangerous attribute access", 
                                         module=node.value.id, attr=node.attr)
                            return False
            
            return True
            
        except SyntaxError as e:
            logger.warning("Script has syntax error", error=str(e))
            return False

    def _create_safe_globals(self) -> Dict[str, Any]:
        """Create a safe globals dictionary for script execution."""

        safe_globals = {
            '__builtins__': {
                # Safe built-in functions
                'len': len, 'str': str, 'int': int, 'float': float, 'bool': bool,
                'list': list, 'dict': dict, 'tuple': tuple, 'set': set,
                'range': range, 'enumerate': enumerate, 'zip': zip,
                'map': map, 'filter': filter, 'sorted': sorted,
                'sum': sum, 'min': min, 'max': max, 'abs': abs, 'round': round,
                'print': print,
                # Safe exceptions
                'Exception': Exception, 'ValueError': ValueError,
                'TypeError': TypeError, 'KeyError': KeyError, 'IndexError': IndexError,
            }
        }

        # Add allowed modules
        for module_name in self.allowed_imports:
            try:
                module = __import__(module_name)
                safe_globals[module_name] = module
            except ImportError:
                logger.debug("Could not import allowed module", module=module_name)

        return safe_globals

    def _detect_side_effects(self, final_locals: Dict[str, Any], initial_context: Dict[str, Any]) -> List[str]:
        """Detect side effects from script execution."""

        side_effects = []

        # Check for new variables created
        new_vars = set(final_locals.keys()) - set(initial_context.keys())
        if new_vars:
            side_effects.append(f"Created variables: {', '.join(new_vars)}")

        # Check for modified variables
        for key, value in initial_context.items():
            if key in final_locals and final_locals[key] != value:
                side_effects.append(f"Modified variable: {key}")

        return side_effects
