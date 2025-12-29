# CLI Chatbot Controller

A revolutionary replacement for traditional CLI patterns using an intelligent, self-aware chatbot controller with dynamic context injection and scripting capabilities.

## Overview

This library transforms command-line interfaces from rigid, memorizable commands into natural language conversations with an intelligent controller that understands both itself and your application.

## Key Features

- 🤖 **Self-Aware Controller**: Understands its own capabilities and the application it's managing
- 🔍 **Dynamic Context Injection**: Real-time analysis and understanding of your codebase
- 💬 **Natural Language Interface**: Replace complex CLI commands with conversational interaction
- 🐍 **Dynamic Script Execution**: Generate and execute Python scripts based on conversation
- 🧠 **Conversation Memory**: Learn from interactions and maintain context
- 🔒 **Safety-First Scripting**: Sandboxed execution with comprehensive safety validation
- 📚 **Live Documentation**: Auto-extracts relevant docs and code context

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                CLI CHATBOT CONTROLLER                        │
│  • Self-aware conversational interface                     │
│  • Natural language command processing                     │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│              DYNAMIC CONTEXT INJECTOR                       │
│  • Real-time codebase analysis                            │
│  • Automatic documentation extraction                      │
│  • Relevance-based context selection                      │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│              DYNAMIC SCRIPTING ENGINE                       │
│  • Safe Python script execution                           │
│  • Input/output modification via DI                       │
│  • Comprehensive safety validation                        │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                 YOUR APPLICATION                            │
│  • Automatically analyzed and understood                   │
│  • Accessible through natural language                     │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Basic Usage

```python
import asyncio
from cli_chatbot import ChatbotController

async def main():
    # Your LLM client function
    async def llm_client(messages):
        # Call your LLM service here
        return await your_llm_service.chat(messages)
    
    # Initialize the controller
    controller = ChatbotController(
        llm_client=llm_client,
        application_root="/path/to/your/app",
        scripting_enabled=True
    )
    
    # Start conversational interface
    await controller.start_conversation()

asyncio.run(main())
```

### Example Interactions

Instead of traditional CLI commands:
```bash
# Traditional CLI
./app --analyze --input data.csv --output results.json --format json --verbose
./app --list-functions --module auth --filter public
./app --generate-docs --target api --format markdown
```

Use natural language:
```
💬 You: Analyze the data.csv file and output results as JSON
💬 You: Show me the public functions in the auth module  
💬 You: Generate API documentation in markdown format
```

## Core Components

### ChatbotController

The main controller that orchestrates the conversational interface:

```python
controller = ChatbotController(
    llm_client=your_llm_function,
    application_root="/path/to/app",
    scripting_enabled=True,
    # Optional: custom components
    context_provider=custom_context_provider,
    script_executor=custom_script_executor,
    memory=custom_memory,
    personality=custom_personality
)
```

### Dynamic Context Injector

Automatically analyzes your codebase and provides relevant context:

- **Code Analysis**: Functions, classes, modules
- **Documentation Extraction**: README, docstrings, comments
- **Relevance Scoring**: Context ranked by relevance to conversation
- **Self-Awareness**: Controller understands its own capabilities

### Dynamic Scripting Engine

Safe execution of generated Python scripts:

- **Safety Validation**: AST analysis blocks dangerous operations
- **Sandboxed Execution**: Controlled environment with limited globals
- **Input/Output Modification**: Dependency injection for data transformation
- **Side Effect Detection**: Tracks variable changes and modifications

## Advanced Features

### Custom Context Providers

```python
from cli_chatbot.core.interfaces import ContextProvider, ContextInfo

class DatabaseContextProvider(ContextProvider):
    async def extract_context(self, query, application_root, max_contexts=10):
        # Custom logic to extract database schema, queries, etc.
        return [ContextInfo(...)]
```

### Input/Output Modifiers

```python
def sanitize_input(data):
    """Remove sensitive information from input."""
    if isinstance(data, dict):
        return {k: v for k, v in data.items() if 'password' not in k.lower()}
    return data

def format_output(result):
    """Format output for better presentation."""
    if isinstance(result, list):
        return f"Found {len(result)} items: {result[:3]}..."
    return result

# Add to scripting engine
controller.script_executor.add_input_modifier(sanitize_input)
controller.script_executor.add_output_modifier(format_output)
```

### Custom Personalities

```python
from cli_chatbot.core.interfaces import ChatbotPersonality

class DevOpsPersonality(ChatbotPersonality):
    def get_system_prompt(self):
        return """You are a DevOps-focused CLI assistant specializing in:
        - Infrastructure management
        - Deployment automation  
        - Monitoring and alerting
        - Security best practices"""
    
    def should_execute_script(self, user_input, llm_response):
        # Custom logic for when to execute scripts
        return 'deploy' in user_input.lower() or 'monitor' in user_input.lower()
```

## Safety Features

### Script Execution Safety

- **AST Analysis**: Blocks dangerous operations before execution
- **Sandboxed Environment**: Limited globals and built-ins
- **Import Restrictions**: Only allowed modules can be imported
- **Timeout Protection**: Scripts automatically terminated after timeout
- **Side Effect Tracking**: Monitor and report all changes

### Blocked Operations

The system automatically blocks:
- File system access (`open`, `file`)
- System commands (`os.system`, `subprocess`)
- Dynamic code execution (`eval`, `exec`, `compile`)
- Introspection functions (`globals`, `locals`, `vars`)
- Network operations (configurable)

## Use Cases

### Development Assistant

```
💬 You: Show me all the API endpoints in this Flask app
💬 You: Generate a test script for the user authentication
💬 You: What's the database schema for the orders table?
```

### DevOps Automation

```
💬 You: Check the status of all microservices
💬 You: Generate a deployment script for staging
💬 You: Analyze the error logs from the last hour
```

### Data Analysis

```
💬 You: Analyze the sales data and show trends
💬 You: Generate a report of user activity patterns  
💬 You: Create a script to clean the customer database
```

### Code Review Assistant

```
💬 You: Review the recent changes in the auth module
💬 You: Check for potential security issues in the API
💬 You: Suggest optimizations for the database queries
```

## Configuration

### Context Injection Settings

```python
context_provider = DynamicContextInjector(
    application_root="/path/to/app",
    file_extensions=['.py', '.js', '.md', '.yaml'],
    max_file_size=100000,  # 100KB max per file
)
```

### Scripting Engine Settings

```python
script_executor = DynamicScriptingEngine(
    allowed_imports=['json', 'datetime', 'math', 'requests'],
    max_execution_time=30.0,  # 30 seconds max
    input_modifiers=[sanitize_sensitive_data],
    output_modifiers=[format_for_display]
)
```

## Requirements

- Python 3.8+
- LLM access (OpenAI, Anthropic, local models, etc.)
- structlog for logging
- Application codebase for context injection

## License

MIT License - See LICENSE file for details.
