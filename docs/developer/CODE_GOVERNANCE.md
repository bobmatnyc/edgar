# 🏛️ Code Governance & Organization Standards

## 📋 Overview

This document establishes strict governance standards for the EDGAR CLI system to maintain code quality, modularity, and architectural integrity. All code contributions must follow these patterns to preserve the revolutionary nature of this self-improving system.

---

## 🎯 Core Principles

### **1. Separation of Concerns**
- **Core Application Code**: Business logic, services, and infrastructure
- **Scripts**: Utilities, tests, and operational tools
- **Clear Boundaries**: No mixing of concerns between categories

### **2. Modular Architecture**
- **Service-Oriented**: Each service has a single responsibility
- **Dependency Injection**: Services depend on interfaces, not implementations
- **Granular Components**: Small, focused, testable units

### **3. Documentation-First**
- **HOW**: Technical implementation details and patterns
- **WHY**: Business rationale and architectural decisions
- **WHEN**: Modification history and reasoning

---

## 🏗️ Core Application Code Standards

### **📁 Directory Structure**
```
src/
├── edgar_analyzer/           # Core business logic
│   ├── services/            # Business services (single responsibility)
│   ├── models/              # Data models and entities
│   ├── controllers/         # Orchestration and workflow
│   ├── extractors/          # Data extraction components
│   ├── validation/          # Quality assurance and validation
│   ├── utils/               # Shared utilities
│   └── config/              # Configuration management
├── cli_chatbot/             # Conversational interface
│   ├── core/                # Core chatbot functionality
│   ├── context/             # Context management
│   ├── fallback/            # Traditional CLI fallback
│   └── interfaces/          # Interface definitions
└── self_improving_code/     # Self-improvement patterns
    ├── core/                # Core improvement engine
    ├── examples/            # Implementation examples
    ├── patterns/            # Reusable patterns
    └── validation/          # Improvement validation
```

### **🔒 Core Code Restrictions**

#### **File Size Limits**
- **Maximum 500 lines** per file (including comments and docstrings)
- **Recommended 200-300 lines** for optimal maintainability
- **Split large files** into focused, single-responsibility modules

#### **Service Pattern Requirements**
```python
# ✅ REQUIRED: Service interface definition
class ServiceInterface(ABC):
    """Clear interface with documented methods."""
    
    @abstractmethod
    async def primary_operation(self, params: DataModel) -> ResultModel:
        """
        Primary service operation.
        
        Args:
            params: Input parameters with validation
            
        Returns:
            Structured result with error handling
            
        Raises:
            ServiceException: When operation fails
        """
        pass

# ✅ REQUIRED: Service implementation
class ConcreteService(ServiceInterface):
    """
    Service implementation following established patterns.
    
    WHY: Implements specific business logic for [purpose]
    HOW: Uses [pattern/technology] to achieve [goal]
    WHEN: Created [date] for [reason]
    """
    
    def __init__(self, dependencies: List[ServiceInterface]):
        """Dependency injection constructor."""
        self.dependencies = dependencies
        self.logger = structlog.get_logger(__name__)
    
    async def primary_operation(self, params: DataModel) -> ResultModel:
        """Implementation with comprehensive error handling."""
        try:
            # Implementation here
            pass
        except Exception as e:
            self.logger.error("Operation failed", error=str(e))
            raise ServiceException(f"Service operation failed: {e}")
```

#### **Dependency Management**
```python
# ✅ REQUIRED: Dependency injection pattern
@dataclass
class ServiceContainer:
    """
    Service container for dependency injection.
    
    WHY: Enables testable, modular architecture
    HOW: Provides centralized service management
    WHEN: Modified [date] to add [service] for [reason]
    """
    
    llm_service: LLMServiceInterface
    edgar_service: EdgarServiceInterface
    validation_service: ValidationServiceInterface
    
    @classmethod
    def create_production(cls) -> 'ServiceContainer':
        """Create production service container."""
        return cls(
            llm_service=LLMService(),
            edgar_service=EdgarService(),
            validation_service=ValidationService()
        )
```

### **📝 Documentation Requirements**

#### **Class Documentation**
```python
class ExampleService:
    """
    Brief description of service purpose.
    
    WHY: Business rationale for this service
    - Solves [specific problem]
    - Enables [specific capability]
    - Supports [business requirement]
    
    HOW: Technical implementation approach
    - Uses [pattern/technology]
    - Integrates with [other services]
    - Follows [architectural principle]
    
    WHEN: Modification history
    - Created: [date] - [reason]
    - Modified: [date] - [change] - [reason]
    - Enhanced: [date] - [improvement] - [rationale]
    
    Examples:
        >>> service = ExampleService(dependencies)
        >>> result = await service.process(data)
        >>> assert result.success
    """
```

#### **Method Documentation**
```python
async def complex_operation(self, input_data: InputModel) -> ResultModel:
    """
    Perform complex business operation.
    
    WHY: This operation is needed because [business reason]
    HOW: Implementation uses [approach] to achieve [goal]
    
    Args:
        input_data: Validated input with [specific requirements]
        
    Returns:
        ResultModel containing:
        - success: Operation success status
        - data: Processed result data
        - metadata: Operation metadata
        
    Raises:
        ValidationError: When input validation fails
        ServiceError: When operation cannot complete
        
    Examples:
        >>> result = await service.complex_operation(valid_input)
        >>> assert result.success
        >>> assert result.data is not None
    """
```

---

## 📜 Script Organization Standards

### **📁 Script Directory Structure**
```
scripts/
├── setup/                   # Environment and installation
│   ├── setup_edgar_cli.py  # Main setup script
│   ├── install_deps.py     # Dependency installation
│   └── configure_env.py    # Environment configuration
├── testing/                 # Test and validation scripts
│   ├── test_50_companies.py
│   ├── test_subprocess_monitoring.py
│   └── validate_system.py
├── analysis/                # Data analysis and reporting
│   ├── run_compensation_analysis.py
│   ├── generate_reports.py
│   └── quality_assessment.py
├── maintenance/             # System maintenance
│   ├── cleanup_cache.py
│   ├── backup_data.py
│   └── update_dependencies.py
└── utilities/               # General utilities
    ├── data_conversion.py
    ├── file_management.py
    └── logging_setup.py
```

### **🔒 Script Standards**

#### **Script Header Template**
```python
#!/usr/bin/env python3
"""
Script Name: [descriptive_name.py]

PURPOSE:
    Brief description of what this script does and why it exists.

FUNCTION:
    Detailed explanation of the script's functionality:
    - Primary operations performed
    - Input requirements and sources
    - Output format and destination
    - Dependencies and prerequisites

USAGE:
    python script_name.py [arguments]
    
    Arguments:
        --arg1: Description of argument 1
        --arg2: Description of argument 2
    
    Examples:
        python script_name.py --input data.json --output results.csv
        python script_name.py --mode production --verbose

MODIFICATION HISTORY:
    [YYYY-MM-DD] [Author] - [Change Description]
    - WHY: Reason for the change
    - HOW: Technical approach used
    - IMPACT: What this change affects
    
    [YYYY-MM-DD] [Author] - Initial creation
    - WHY: Business need or requirement
    - HOW: Implementation approach
    - IMPACT: System capabilities added

DEPENDENCIES:
    - Python 3.8+
    - Required packages: [list]
    - External services: [list]
    - Environment variables: [list]

AUTHOR: [Name]
CREATED: [Date]
LAST_MODIFIED: [Date]
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import structlog

logger = structlog.get_logger(__name__)
```

#### **Script Function Organization**
```python
def main():
    """
    Main script execution function.
    
    WHY: Centralized entry point for script execution
    HOW: Orchestrates all script operations in logical sequence
    """
    try:
        # Parse arguments
        args = parse_arguments()
        
        # Validate prerequisites
        validate_environment(args)
        
        # Execute main logic
        result = execute_script_logic(args)
        
        # Handle results
        process_results(result, args)
        
        logger.info("Script completed successfully")
        
    except Exception as e:
        logger.error("Script execution failed", error=str(e))
        sys.exit(1)

def parse_arguments() -> Dict[str, Any]:
    """
    Parse and validate command-line arguments.
    
    WHY: Provides consistent argument handling across scripts
    HOW: Uses argparse with comprehensive validation
    """
    # Implementation here
    pass

def validate_environment(args: Dict[str, Any]) -> None:
    """
    Validate script prerequisites and environment.
    
    WHY: Ensures script can execute successfully
    HOW: Checks dependencies, permissions, and resources
    """
    # Implementation here
    pass

def execute_script_logic(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the core script functionality.
    
    WHY: Contains the main business logic of the script
    HOW: [Specific implementation approach]
    """
    # Implementation here
    pass

def process_results(result: Dict[str, Any], args: Dict[str, Any]) -> None:
    """
    Process and output script results.
    
    WHY: Handles result formatting and output
    HOW: Formats results according to specified output format
    """
    # Implementation here
    pass

if __name__ == "__main__":
    main()
```

---

## 🔍 Code Review Requirements

### **Pre-Commit Checklist**
- [ ] **File Size**: No file exceeds 500 lines
- [ ] **Documentation**: All classes and methods documented with WHY/HOW/WHEN
- [ ] **Service Pattern**: Services follow interface-implementation pattern
- [ ] **Dependency Injection**: No hard-coded dependencies
- [ ] **Error Handling**: Comprehensive exception handling
- [ ] **Logging**: Structured logging with appropriate levels
- [ ] **Type Hints**: Complete type annotations
- [ ] **Tests**: Unit tests for new functionality

### **Architecture Review**
- [ ] **Single Responsibility**: Each component has one clear purpose
- [ ] **Interface Segregation**: Interfaces are focused and minimal
- [ ] **Dependency Inversion**: Depends on abstractions, not concretions
- [ ] **Open/Closed**: Open for extension, closed for modification
- [ ] **Modularity**: Can be tested and deployed independently

---

## 📊 Enforcement Mechanisms

### **Automated Checks**
```python
# Pre-commit hook example
def validate_file_size(file_path: str) -> bool:
    """Validate file does not exceed size limits."""
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    if len(lines) > 500:
        print(f"❌ {file_path} exceeds 500 line limit ({len(lines)} lines)")
        return False
    
    return True

def validate_documentation(file_path: str) -> bool:
    """Validate required documentation exists."""
    # Check for WHY/HOW/WHEN documentation
    # Implementation here
    pass
```

### **Quality Gates**
- **Automated**: File size, documentation presence, type hints
- **Manual**: Architecture review, business logic validation
- **Continuous**: Code quality metrics and technical debt monitoring

This governance framework ensures the EDGAR CLI system maintains its revolutionary architecture while enabling controlled, high-quality evolution.
