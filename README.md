# 🚀 EDGAR → Extract & Transform Platform

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Active Development](https://img.shields.io/badge/Status-Active%20Development-orange.svg)](https://github.com/bobmatnyc/zach-edgar)

**General-purpose extract & transform platform - transforming EDGAR into example-driven data extraction for any source.**

*Last updated: November 30, 2025*

## 🆕 What's New

### **November 30, 2025** - T4: Code Generation Pipeline Migration ✅
- Migrated 3 code generation services to platform (1,266 LOC)
  - `PromptGenerator` (436 LOC) - Generate Sonnet 4.5 prompts from patterns
  - `CodeGeneratorService` (590 LOC) - End-to-end code generation pipeline
  - `ConstraintEnforcer` (240 LOC) - AST-based code validation
- **Package**: `extract_transform_platform.services.codegen`
- **Status**: 100% code reuse, zero breaking changes
- **Ticket**: [1M-379](https://linear.app/1m-hyperdev/issue/1M-379)

### **November 29, 2025** - T3: Schema Services Migration ✅
- Migrated 3 schema analysis services to platform (1,645 LOC)
  - `PatternModels` (530 LOC) - 14 transformation pattern types
  - `SchemaAnalyzer` (436 LOC) - Schema inference and comparison
  - `ExampleParser` (679 LOC) - Pattern extraction from examples
- **Package**: `extract_transform_platform.models.patterns` & `extract_transform_platform.services.analysis`
- **Status**: 100% code reuse, 60/60 tests passing
- **Ticket**: [1M-378](https://linear.app/1m-hyperdev/issue/1M-378)

### **November 28, 2025** - T2: Data Source Abstractions Migration ✅
- Migrated 4 data sources to platform (2,180 LOC)
  - `ExcelDataSource` - Excel file parsing with pandas
  - `PDFDataSource` - PDF table extraction with pdfplumber
  - `CSVDataSource` - CSV/JSON/YAML file parsing
  - `APIDataSource` - REST API integration
- **Package**: `extract_transform_platform.data_sources`
- **Status**: 120/120 tests passing, zero breaking changes
- **Ticket**: [1M-377](https://linear.app/1m-hyperdev/issue/1M-377)

### **November 27, 2025** - Phase 2: Platform Architecture Launch 🚀
- Created `extract_transform_platform` package structure
- Established core abstractions (`IDataSource`, `BaseDataSource`)
- Set up generic data models (no EDGAR dependencies)
- **Epic**: [EDGAR → General-Purpose Extract & Transform Platform](https://linear.app/1m-hyperdev/project/edgar-%E2%86%92-general-purpose-extract-and-transform-platform-e4cb3518b13e)

---

## 🎯 What Makes This Revolutionary

### 🤖 **Conversational AI Interface**
- Natural language queries: *"Analyze Apple's executive compensation"*
- Context-aware responses with real-time codebase analysis
- Automatic LLM detection with graceful fallback to traditional CLI

### 🔄 **Self-Improving Code**
- **LLM Supervisor**: Professional quality assurance with Grok 4.1 Fast
- **LLM Engineer**: Real code improvements with Claude 3.5 Sonnet
- **Git-Safe Enhancement**: Automatic checkpoints and branch management
- **Iterative Improvement**: Multi-iteration enhancement process

### ⚡ **Enterprise-Grade Process Control**
- **Real-time Subprocess Monitoring**: Line-by-line output streaming
- **Process Control**: Timeout handling and termination capabilities
- **Automatic Fallback**: Graceful degradation when subprocess unavailable
- **Enhanced Security**: Process isolation and comprehensive validation

### 🔍 **Web Search Integration**
- **OpenRouter Web Search**: Real-time information access using OpenRouter standard
- **Validation Enhancement**: Supervisor validation with current standards
- **Best Practices Research**: Engineer improvements using latest practices
- **Contextual Search**: Domain-specific query generation and analysis

## 🚀 Quick Start

### 1. **Clone and Setup**
```bash
git clone https://github.com/bobmatnyc/zach-edgar.git
cd zach-edgar
python3 setup_edgar_cli.py
```

### 2. **Configure API Keys** 🔒
```bash
# Copy the secure template
cp .env.template .env.local

# Get your API key from https://openrouter.ai/keys
# Edit .env.local and replace 'your_openrouter_api_key_here' with your actual key
```

**🔒 SECURITY NOTE**: `.env.local` is gitignored to protect your API keys from accidental exposure.

### 3. **Start the Revolutionary CLI**
```bash
source venv/bin/activate

# Interactive mode (default)
python -m edgar_analyzer

# Bypass interactive, show CLI help
python -m edgar_analyzer --cli

# With web search capabilities (requires OpenRouter API key)
python -m edgar_analyzer --enable-web-search

# Specific modes
python -m edgar_analyzer --mode chatbot    # Force conversational mode
python -m edgar_analyzer --mode traditional # Force traditional CLI
```

## 💬 Usage Examples

### **Conversational Interface**
```bash
💬 You: What is this application about?
🤖 AI: This is an intelligent EDGAR analysis system that extracts executive 
       compensation data from SEC filings using self-improving code patterns...

💬 You: Analyze Apple's CEO compensation for 2023
🤖 AI: I'll extract Apple's executive compensation data. Let me fetch their 
       latest proxy filing and run the analysis...
```

### **CLI Usage Examples**
```bash
# Default: Interactive conversational mode
python -m edgar_analyzer

# Bypass interactive, show CLI help
python -m edgar_analyzer --cli

# Extract specific company
python -m edgar_analyzer extract --cik 0000320193 --year 2023

# Extract with web search validation
python -m edgar_analyzer --enable-web-search extract --cik 0000320193 --year 2023

# Run system test
python -m edgar_analyzer test --companies 10

# Show application info
python -m edgar_analyzer trad-info

# Analyze codebase with web search
python -m edgar_analyzer --enable-web-search trad-analyze --query "compensation extraction"
```

## 🏗️ Architecture

### **Core Components**
- **CLI Chatbot Controller**: Conversational interface with dynamic context
- **Self-Improving Engine**: LLM-powered code enhancement and QA
- **Subprocess Monitor**: Real-time process control and output streaming
- **Context Injector**: Dynamic codebase analysis and injection
- **Safety Validator**: AST-based script validation and sandboxing

### **LLM Integration**
- **Primary Model**: Grok 4.1 Fast (OpenRouter)
- **Fallback Model**: Claude 3.5 Sonnet (Anthropic)
- **Supervisor**: Quality assurance and improvement detection
- **Engineer**: Code modifications and enhancements

## 📊 System Validation

### **✅ 50 Companies Test - PASSED**
- **LLM QA Accuracy**: 100% (correctly identified data quality issues)
- **Self-Improvement Active**: Multiple iterations per company
- **Processing Rate**: ~30 seconds per company
- **Success Rate**: 100% completion with comprehensive analysis

### **✅ Component Status**
- **LLM Service**: ✅ Grok 4.1 Fast + Claude 3.5 Sonnet
- **Context Injection**: ✅ Real-time codebase analysis
- **Subprocess Monitoring**: ✅ Process control and streaming
- **Safety Validation**: ✅ AST parsing and sandboxing
- **Git Management**: ✅ Automatic checkpoints and branches

## 🛡️ Safety & Security

### **Enterprise-Grade Safety**
- **AST-based Script Validation**: Prevents dangerous code execution
- **Sandboxed Environments**: Isolated execution contexts
- **Process Monitoring**: Real-time control and termination
- **Git Checkpoints**: Automatic backup and recovery
- **Professional Error Handling**: Comprehensive error recovery

### **Automatic Fallback Layers**
1. **Primary**: Conversational interface with LLM
2. **Secondary**: Traditional CLI with full functionality
3. **Tertiary**: Subprocess execution with monitoring
4. **Fallback**: exec() mode with safety validation

## 📁 Project Structure

```
edgar-cli/
├── src/
│   ├── cli_chatbot/           # Conversational interface
│   ├── edgar_analyzer/        # Core analysis engine
│   └── self_improving_code/   # Self-improvement patterns
├── tests/                     # Comprehensive test suite
├── setup_edgar_cli.py        # One-command setup script
└── SYSTEM_READY_SUMMARY.md   # Complete system documentation
```

## 🎯 Key Features

### **🧠 Intelligent Context Awareness**
- Dynamic codebase analysis and injection
- Real-time help and guidance
- Context-aware responses and suggestions
- Professional conversation flow management

### **🔧 Professional Development Tools**
- Git-safe iterative enhancement
- Automatic code quality assessment
- Real-time improvement suggestions
- Professional validation and testing

### **⚡ Performance & Reliability**
- Subprocess monitoring with timeout protection
- Automatic service detection and fallback
- Cross-platform compatibility
- Enterprise-grade error handling

## 📚 Documentation

**📖 [Complete Documentation](docs/README.md)** - Comprehensive documentation hub

### **Quick Links**
- **[System Overview](docs/SYSTEM_READY_SUMMARY.md)** - Complete system capabilities
- **[Quick Start Guide](docs/guides/QUICK_START.md)** - Get started in 5 minutes
- **[CLI Usage Guide](docs/guides/CLI_USAGE.md)** - Master the conversational interface
- **[Web Search Guide](docs/guides/WEB_SEARCH_CAPABILITIES.md)** - Real-time information access
- **[Security Guidelines](docs/guides/SECURITY.md)** - Enterprise security practices
- **[API Reference](docs/api/)** - Technical documentation
- **[Architecture](docs/architecture/)** - System design and patterns

## 🤝 Contributing

This is a production-ready system demonstrating revolutionary CLI interface concepts. The codebase showcases:

- Self-improving code patterns with LLM integration
- Conversational AI interfaces for command-line tools
- Enterprise-grade process monitoring and control
- Professional safety and validation systems

### **🔒 Security Requirements**
- Follow [Security Guidelines](SECURITY.md) for API key management
- Use [Code Governance](CODE_GOVERNANCE.md) standards for all contributions
- Never commit API keys or sensitive configuration
- Use `.env.local` for local development (gitignored)

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🎉 **Welcome to the Future of CLI Interfaces!**

**Experience the world's first self-improving conversational CLI:**

```bash
source venv/bin/activate

# Start interactive mode (default)
python -m edgar_analyzer

# Bypass interactive, show CLI help
python -m edgar_analyzer --cli

# With web search capabilities
python -m edgar_analyzer --enable-web-search
```

## 🏗️ Project Organization

**📋 [Project Overview](PROJECT_OVERVIEW.md)** - Complete project structure and organization

The project is now cleanly organized with:
- **📚 [Documentation](docs/)** - Comprehensive guides and references
- **🧪 [Tests](tests/)** - Complete test suite and validation
- **🔧 [Source Code](src/)** - Clean, modular implementation
- **⚙️ [Configuration](.)** - Setup scripts and environment files

**Revolutionary. Intelligent. Production-Ready.** 🚀
