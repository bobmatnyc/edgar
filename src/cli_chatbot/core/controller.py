"""
CLI Chatbot Controller

The main controller that replaces traditional CLI patterns with an intelligent,
self-aware conversational interface with dynamic context injection.
"""

import asyncio
import json
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime
import structlog

from .interfaces import (
    LLMClient, 
    ContextProvider, 
    ScriptExecutor,
    ConversationMemory,
    ChatbotPersonality,
    ContextInfo,
    ScriptResult
)
from .context_injector import DynamicContextInjector
from .scripting_engine import DynamicScriptingEngine

logger = structlog.get_logger(__name__)


class DefaultChatbotPersonality(ChatbotPersonality):
    """Default chatbot personality implementation."""
    
    def get_system_prompt(self) -> str:
        return """You are an intelligent CLI Chatbot Controller with the following capabilities:

IDENTITY & AWARENESS:
- You are a self-aware conversational interface replacing traditional CLI commands
- You have dynamic access to the application codebase and can analyze it in real-time
- You understand both your own controller logic and the application you're managing
- You can execute Python scripts dynamically to perform tasks or analysis

CAPABILITIES:
- Dynamic context injection from live codebase analysis
- Real-time script generation and execution with safety validation
- Web search for current information and best practices (when enabled)
- Conversational interface for complex operations
- Memory of previous interactions and learning from them
- Input/output modification through dependency injection

BEHAVIOR:
- Be helpful, informative, and proactive
- Explain what you're doing and why
- Ask for clarification when needed
- Suggest improvements and optimizations
- Maintain awareness of safety and security
- Use natural language while being precise about technical details

RESPONSE FORMAT:
- Provide clear, actionable responses
- Include relevant code examples when helpful
- Explain the context and reasoning behind suggestions
- Offer multiple approaches when appropriate"""
    
    def format_response(self, raw_response: str, context: List[ContextInfo], user_input: str) -> str:
        """Format the raw LLM response for presentation."""
        
        # Add context information if relevant
        if context:
            context_summary = f"\n\n📋 **Context Used:**\n"
            for ctx in context[:3]:  # Show top 3 contexts
                context_summary += f"- {ctx.source} ({ctx.content_type})\n"
            
            return raw_response + context_summary
        
        return raw_response
    
    def should_execute_script(self, user_input: str, llm_response: str) -> bool:
        """Determine if dynamic script execution is appropriate."""
        
        script_indicators = [
            'execute', 'run', 'calculate', 'analyze', 'process',
            'generate', 'create', 'modify', 'update', 'check'
        ]
        
        user_lower = user_input.lower()
        response_lower = llm_response.lower()
        
        # Check if user explicitly requests execution
        if any(indicator in user_lower for indicator in script_indicators):
            return True
        
        # Check if response suggests script execution
        if 'python' in response_lower and ('```' in llm_response or 'script' in response_lower):
            return True
        
        return False


class SimpleChatbotMemory(ConversationMemory):
    """Simple in-memory conversation storage."""
    
    def __init__(self, max_history: int = 100):
        self.history = []
        self.max_history = max_history
    
    async def add_exchange(
        self, 
        user_input: str, 
        controller_response: str,
        context_used: List[ContextInfo],
        scripts_executed: List[ScriptResult]
    ):
        """Add a conversation exchange to memory."""
        
        exchange = {
            'timestamp': datetime.now().isoformat(),
            'user_input': user_input,
            'controller_response': controller_response,
            'context_used': [ctx.source for ctx in context_used],
            'scripts_executed': len(scripts_executed),
            'script_success': all(script.success for script in scripts_executed)
        }
        
        self.history.append(exchange)
        
        # Trim history if too long
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
    
    async def get_conversation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation history."""
        return self.history[-limit:]
    
    async def search_memory(self, query: str) -> List[Dict[str, Any]]:
        """Search conversation memory for relevant exchanges."""
        
        query_lower = query.lower()
        relevant = []
        
        for exchange in self.history:
            if (query_lower in exchange['user_input'].lower() or 
                query_lower in exchange['controller_response'].lower()):
                relevant.append(exchange)
        
        return relevant[-10:]  # Return last 10 relevant exchanges


class ChatbotController:
    """
    Main CLI Chatbot Controller that replaces traditional CLI patterns
    with an intelligent, self-aware conversational interface.
    """
    
    def __init__(
        self,
        llm_client: LLMClient,
        application_root: str,
        context_provider: Optional[ContextProvider] = None,
        script_executor: Optional[ScriptExecutor] = None,
        memory: Optional[ConversationMemory] = None,
        personality: Optional[ChatbotPersonality] = None,
        scripting_enabled: bool = True,
        web_search_enabled: bool = False,
        web_search_client: Optional[callable] = None
    ):
        """
        Initialize the CLI Chatbot Controller.

        WHY: Provides intelligent conversational interface with optional web search
        HOW: Integrates LLM, context injection, scripting, and web search capabilities
        WHEN: Enhanced 2025-11-21 to add web search capabilities

        Args:
            llm_client: Function to call LLM
            application_root: Root directory of the application
            context_provider: Provider for dynamic context injection
            script_executor: Engine for dynamic script execution
            memory: Conversation memory manager
            personality: Chatbot personality and behavior
            scripting_enabled: Whether to enable dynamic scripting
            web_search_enabled: Whether to enable web search capabilities
            web_search_client: Function for web search requests
        """
        self.llm_client = llm_client
        self.application_root = application_root
        self.scripting_enabled = scripting_enabled
        self.web_search_enabled = web_search_enabled
        self.web_search_client = web_search_client
        
        # Initialize components with defaults if not provided
        self.context_provider = context_provider or DynamicContextInjector(
            application_root=application_root
        )
        
        self.script_executor = script_executor or DynamicScriptingEngine() if scripting_enabled else None
        self.memory = memory or SimpleChatbotMemory()
        self.personality = personality or DefaultChatbotPersonality()
        
        # Get self-awareness context
        self._self_awareness = None
        
        logger.info("CLI Chatbot Controller initialized",
                   application_root=application_root,
                   scripting_enabled=scripting_enabled,
                   web_search_enabled=web_search_enabled)

    @staticmethod
    async def test_llm_availability(llm_client: LLMClient, timeout: float = 10.0) -> bool:
        """
        Test if the LLM client is available and responsive.

        Args:
            llm_client: LLM client function to test
            timeout: Timeout in seconds for the test

        Returns:
            True if LLM is available, False otherwise
        """
        try:
            # Simple test message
            test_messages = [
                {"role": "user", "content": "Hello, please respond with 'OK' if you can hear me."}
            ]

            # Test with timeout
            response = await asyncio.wait_for(
                llm_client(test_messages),
                timeout=timeout
            )

            # Check if we got a reasonable response
            if response and isinstance(response, str) and len(response.strip()) > 0:
                logger.info("LLM availability test passed", response_length=len(response))
                return True
            else:
                logger.warning("LLM availability test failed - empty or invalid response")
                return False

        except asyncio.TimeoutError:
            logger.warning("LLM availability test failed - timeout", timeout=timeout)
            return False
        except Exception as e:
            logger.warning("LLM availability test failed - error", error=str(e))
            return False

    @staticmethod
    async def create_with_fallback(
        llm_client: LLMClient,
        application_root: str,
        test_llm: bool = True,
        **kwargs
    ):
        """
        Create a ChatbotController with automatic fallback to traditional CLI.

        Args:
            llm_client: LLM client function
            application_root: Root directory of the application
            test_llm: Whether to test LLM availability first
            **kwargs: Additional arguments for ChatbotController

        Returns:
            ChatbotController if LLM available, otherwise starts traditional CLI
        """

        print("🚀 Initializing CLI Interface...")

        # Test LLM availability if requested
        if test_llm:
            print("🔍 Testing LLM availability...")

            llm_available = await ChatbotController.test_llm_availability(llm_client)

            if llm_available:
                print("✅ LLM available - Starting conversational interface")
                controller = ChatbotController(
                    llm_client=llm_client,
                    application_root=application_root,
                    **kwargs
                )
                return controller
            else:
                print("❌ LLM unavailable - Falling back to traditional CLI")
                await ChatbotController._start_fallback_cli(application_root)
                return None
        else:
            # Skip test, create controller directly
            return ChatbotController(
                llm_client=llm_client,
                application_root=application_root,
                **kwargs
            )

    @staticmethod
    async def _start_fallback_cli(application_root: str):
        """Start the traditional CLI fallback interface."""

        try:
            # Import Click-based fallback CLI
            from ..fallback.traditional_cli import create_fallback_cli

            print("\n🔧 Traditional CLI Mode")
            print("=" * 50)
            print("LLM services are unavailable. Using structured CLI interface.")
            print("Use --help with any command for detailed usage information.")
            print("=" * 50)

            # Create and run the Click CLI
            cli = create_fallback_cli(application_root)

            # Check if we have command line arguments
            if len(sys.argv) > 1:
                # Run with provided arguments
                cli()
            else:
                # Interactive mode - show help and available commands
                print("\n📋 Available Commands:")
                print("  analyze  - Analyze the codebase")
                print("  execute  - Execute Python scripts safely")
                print("  info     - Show application information")
                print("\nUse: python script.py <command> --help for detailed options")
                print("\nExample: python script.py analyze --query 'authentication functions'")

                # Offer to run a command interactively
                try:
                    command = input("\n💬 Enter command (or 'quit' to exit): ").strip()
                    if command and command.lower() not in ['quit', 'exit']:
                        # Simulate command line arguments
                        sys.argv = ['cli'] + command.split()
                        cli()
                except (KeyboardInterrupt, EOFError):
                    print("\n👋 Goodbye!")

        except ImportError as e:
            print(f"❌ Error: Could not load fallback CLI: {e}")
            print("Please ensure Click is installed: pip install click")
        except Exception as e:
            print(f"❌ Error starting fallback CLI: {e}")
            logger.error("Fallback CLI startup failed", error=str(e))

    async def start_conversation(self):
        """Start the interactive conversation loop."""

        print("🤖 CLI Chatbot Controller")
        print("=" * 50)
        print("I'm your intelligent CLI replacement with dynamic context awareness.")
        print("Type 'help' for commands, 'quit' to exit, or just ask me anything!")
        print("=" * 50)

        # Initialize self-awareness
        if not self._self_awareness:
            self._self_awareness = await self.context_provider.get_controller_self_awareness()

        while True:
            try:
                # Get user input
                user_input = input("\n💬 You: ").strip()

                if not user_input:
                    continue

                # Handle special commands
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("👋 Goodbye!")
                    break
                elif user_input.lower() == 'help':
                    await self._show_help()
                    continue
                elif user_input.lower() == 'memory':
                    await self._show_memory()
                    continue
                elif user_input.lower() == 'context':
                    await self._show_context_info()
                    continue

                # Process the conversation
                response = await self.process_input(user_input)
                print(f"\n🤖 Controller: {response}")

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                logger.error("Error in conversation loop", error=str(e))
                print(f"\n❌ Error: {str(e)}")

    async def process_input(self, user_input: str) -> str:
        """Process user input and generate response."""

        # Extract relevant context
        context = await self.context_provider.extract_context(
            query=user_input,
            application_root=self.application_root
        )

        # Build conversation prompt
        prompt = await self._build_conversation_prompt(user_input, context)

        # Get LLM response
        messages = [
            {"role": "system", "content": self.personality.get_system_prompt()},
            {"role": "user", "content": prompt}
        ]

        raw_response = await self.llm_client(messages)

        # Check if script execution is needed
        scripts_executed = []
        if (self.scripting_enabled and
            self.personality.should_execute_script(user_input, raw_response)):

            script_result = await self._execute_dynamic_script(raw_response, context)
            if script_result:
                scripts_executed.append(script_result)

                # Update response with script results
                if script_result.success:
                    raw_response += f"\n\n✅ **Script executed successfully:**\n```\n{script_result.output}\n```"
                    if script_result.result:
                        raw_response += f"\n**Result:** {script_result.result}"
                else:
                    raw_response += f"\n\n❌ **Script execution failed:**\n```\n{script_result.error}\n```"

        # Format response
        formatted_response = self.personality.format_response(raw_response, context, user_input)

        # Store in memory
        await self.memory.add_exchange(user_input, formatted_response, context, scripts_executed)

        return formatted_response

    async def _build_conversation_prompt(self, user_input: str, context: List[ContextInfo]) -> str:
        """Build the conversation prompt with dynamic context injection."""

        prompt_parts = []

        # Add self-awareness
        if self._self_awareness:
            prompt_parts.append("CONTROLLER SELF-AWARENESS:")
            prompt_parts.append(self._self_awareness.content)
            prompt_parts.append("")

        # Add application context
        if context:
            prompt_parts.append("RELEVANT APPLICATION CONTEXT:")
            for ctx in context:
                prompt_parts.append(f"**{ctx.source}** ({ctx.content_type}):")
                prompt_parts.append(ctx.content)
                prompt_parts.append("")

        # Add conversation history
        recent_history = await self.memory.get_conversation_history(limit=3)
        if recent_history:
            prompt_parts.append("RECENT CONVERSATION:")
            for exchange in recent_history:
                prompt_parts.append(f"User: {exchange['user_input']}")
                prompt_parts.append(f"Controller: {exchange['controller_response'][:200]}...")
                prompt_parts.append("")

        # Add current user input
        prompt_parts.append("CURRENT USER INPUT:")
        prompt_parts.append(user_input)

        return "\n".join(prompt_parts)

    async def _execute_dynamic_script(self, llm_response: str, context: List[ContextInfo]) -> Optional[ScriptResult]:
        """Extract and execute Python code from LLM response."""

        if not self.script_executor:
            return None

        # Extract Python code blocks from response
        import re
        code_blocks = re.findall(r'```python\n(.*?)\n```', llm_response, re.DOTALL)

        if not code_blocks:
            # Look for inline code suggestions
            if 'python' in llm_response.lower() and any(keyword in llm_response.lower()
                                                       for keyword in ['execute', 'run', 'script']):
                # Ask LLM to generate executable code
                code_prompt = f"""Based on this response, generate executable Python code:

{llm_response}

Provide only the Python code that should be executed, wrapped in ```python``` blocks."""

                messages = [{"role": "user", "content": code_prompt}]
                code_response = await self.llm_client(messages)
                code_blocks = re.findall(r'```python\n(.*?)\n```', code_response, re.DOTALL)

        if code_blocks:
            # Execute the first code block
            script_code = code_blocks[0].strip()

            # Build execution context
            execution_context = {
                'application_root': self.application_root,
                'context': [ctx.__dict__ for ctx in context],
                'datetime': datetime,
                'json': json
            }

            logger.info("Executing dynamic script", code_length=len(script_code))

            return await self.script_executor.execute_script(
                script_code=script_code,
                context=execution_context,
                safety_checks=True
            )

        return None

    async def _show_help(self):
        """Show help information."""

        help_text = """
🤖 **CLI Chatbot Controller Help**

**Special Commands:**
- `help` - Show this help message
- `memory` - Show recent conversation history
- `context` - Show information about current application context
- `quit/exit/bye` - Exit the controller

**Natural Language Interface:**
Just ask me anything! I can:
- Analyze your codebase and explain how it works
- Generate and execute Python scripts to perform tasks
- Help with debugging and troubleshooting
- Suggest improvements and optimizations
- Answer questions about your application

**Examples:**
- "Show me the main functions in my application"
- "Generate a script to analyze the database schema"
- "What are the key components of this system?"
- "Help me debug the authentication module"
- "Create a utility script to process the data files"

**Dynamic Capabilities:**
- I have real-time access to your codebase
- I can execute Python scripts safely in a sandboxed environment
- I remember our conversation and learn from it
- I understand both my own controller logic and your application
"""

        print(help_text)

    async def _show_memory(self):
        """Show recent conversation history."""

        history = await self.memory.get_conversation_history(limit=5)

        if not history:
            print("📝 No conversation history yet.")
            return

        print("📝 **Recent Conversation History:**")
        for i, exchange in enumerate(history, 1):
            timestamp = exchange['timestamp'][:19]  # Remove microseconds
            print(f"\n**{i}.** {timestamp}")
            print(f"You: {exchange['user_input']}")
            print(f"Controller: {exchange['controller_response'][:100]}...")
            if exchange['scripts_executed'] > 0:
                status = "✅" if exchange['script_success'] else "❌"
                print(f"Scripts: {exchange['scripts_executed']} {status}")

    async def _show_context_info(self):
        """Show information about current application context."""

        # Get application overview
        if hasattr(self.context_provider, 'get_application_overview'):
            overview = await self.context_provider.get_application_overview()
            print("📋 **Application Overview:**")
            print(overview.content)
        else:
            print("📋 **Application Context:**")
            print(f"Root: {self.application_root}")
            print("Dynamic context injection enabled")

        # Show controller info
        print(f"\n🤖 **Controller Status:**")
        print(f"Scripting enabled: {self.scripting_enabled}")
        print(f"Memory entries: {len(self.memory.history) if hasattr(self.memory, 'history') else 'N/A'}")
        print(f"Self-awareness: {'✅' if self._self_awareness else '❌'}")
