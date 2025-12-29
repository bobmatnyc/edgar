# Self-Improving Code Library

A reusable Python library implementing the "Self-Improving Code with LLM QA" pattern.

## Overview

This library enables any codebase to automatically evaluate its own results and improve its implementation through LLM-powered quality assurance and code generation, while maintaining safety through git-based rollback mechanisms.

## Key Features

- 🔍 **LLM-Powered QA**: Automatic quality assurance using domain-expert LLMs
- 🛠️ **Automatic Code Improvement**: LLM-driven code modifications based on QA feedback
- 🔒 **Git-Based Safety**: Automatic checkpoints and rollback capabilities
- 🏗️ **Modular Architecture**: Pluggable components for different domains and LLMs
- 📊 **Professional Standards**: Configurable quality thresholds and evaluation criteria
- 🔄 **Iterative Improvement**: Continuous refinement until quality standards are met

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 CONTROL LAYER (Immutable)                   │
│  SelfImprovingController - Orchestrates the process        │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│              LLM COMPONENTS (Configurable)                  │
│  • LLMSupervisor (QA + Decision Making)                    │
│  • LLMEngineer (Code Generation)                           │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│              IMPLEMENTATION LAYER (Mutable)                 │
│  Your business logic - can be modified by the system       │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                 SAFETY LAYER (Git-based)                    │
│  GitSafetyManager - Checkpoints and rollback               │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Installation

```python
# Add to your project
from self_improving_code import SelfImprovingController, LLMSupervisor, LLMEngineer
```

### Basic Usage

```python
import asyncio
from self_improving_code import SelfImprovingController, LLMSupervisor, LLMEngineer

async def main():
    # Configure domain-specific LLMs
    supervisor = LLMSupervisor(
        llm_client=your_supervisor_llm_function,
        domain_expertise="your domain expertise",
        quality_standards={"pass_threshold": 0.8}
    )
    
    engineer = LLMEngineer(
        llm_client=your_engineer_llm_function,
        programming_language="Python"
    )
    
    # Initialize controller
    controller = SelfImprovingController(
        supervisor_llm=supervisor,
        engineer_llm=engineer,
        target_files=["path/to/your/mutable/code.py"],
        protected_files=["path/to/your/control/code.py"]
    )
    
    # Define your test function
    async def test_my_implementation(test_data):
        # Your test logic here
        return {"result": "test results"}
    
    # Run improvement process
    result = await controller.improve_implementation(
        test_function=test_my_implementation,
        test_data=your_test_data,
        context={
            "domain": "your domain",
            "requirements": "your quality requirements"
        },
        max_iterations=3
    )
    
    print(f"Success: {result.final_success}")
    print(f"Iterations: {result.total_iterations}")
    print(f"Files modified: {result.improvements_made}")

asyncio.run(main())
```

## Components

### SelfImprovingController

The main controller that orchestrates the improvement process:

- Tests current implementation
- Evaluates results using Supervisor LLM
- Directs improvements using Engineer LLM
- Manages safety through git checkpoints
- Iterates until quality standards are met

### LLMSupervisor

Acts as both process supervisor and quality assurance analyst:

- Evaluates test results for quality and correctness
- Provides domain-specific expertise
- Sets quality standards and thresholds
- Identifies specific issues and improvement directions
- Makes go/no-go decisions for iterations

### LLMEngineer

Implements code improvements based on supervisor evaluation:

- Generates code modifications
- Follows programming best practices
- Addresses specific issues identified by supervisor
- Maintains code quality and documentation

### GitSafetyManager

Provides git-based safety mechanisms:

- Creates automatic checkpoints before changes
- Enables rollback on failures
- Manages cleanup of old checkpoints
- Ensures no permanent damage from failed improvements

## Domain-Specific Examples

### EDGAR Financial Data Extraction

```python
from self_improving_code.examples import EdgarExtractionExample

example = EdgarExtractionExample()
results = await example.extract_with_improvement(
    html_content=proxy_filing_html,
    company_cik="0000320193",
    company_name="Apple Inc.",
    year=2023
)
```

## Configuration

### Quality Standards

```python
quality_standards = {
    "pass_threshold": 0.8,      # Score >= 0.8: No improvement needed
    "conditional_threshold": 0.5, # Score 0.5-0.8: Minor improvements
    "fail_threshold": 0.0       # Score < 0.5: Major improvements required
}
```

### Coding Standards

```python
coding_standards = {
    "max_function_length": 50,
    "prefer_composition": True,
    "require_docstrings": True,
    "follow_pep8": True
}
```

## Safety Features

- **Git Checkpoints**: Automatic branch creation before changes
- **Rollback Capability**: Instant rollback on failures
- **Protected Files**: Immutable control layer files
- **Error Handling**: Comprehensive error handling and logging
- **Stash Management**: Automatic stashing of uncommitted changes

## Use Cases

- **Data Extraction**: Self-improving parsers and extractors
- **API Integration**: Adaptive handlers for changing APIs
- **ML Pipelines**: Self-optimizing feature engineering
- **Web Scraping**: Adaptive scrapers for evolving sites
- **Business Logic**: Quality-driven algorithm improvement

## Requirements

- Python 3.8+
- Git repository (for safety mechanisms)
- LLM access (OpenAI, Anthropic, local models, etc.)
- structlog for logging

## License

MIT License - See LICENSE file for details.
