# 📚 EDGAR Platform Documentation

Welcome to the EDGAR Platform documentation! This is a general-purpose, example-driven data extraction and transformation platform.

## 🎯 What is EDGAR Platform?

The EDGAR Platform is a **general-purpose data extraction and transformation system** that supports:

- **📊 File Transformation** - Excel, PDF, DOCX, PPTX → structured data
- **🌐 Web Scraping** - JS-heavy sites with Jina.ai integration
- **💬 Interactive Workflows** - Example-driven, user-prompted confidence threshold
- **📁 Project-based Workflows** - External artifacts directory support

Originally built for SEC EDGAR analysis, it has evolved into a flexible platform for any data extraction task.

## 📋 Documentation Categories

### 👥 [User Documentation](user/)

**Start here if you want to USE the platform.**

Everything you need to know to use the EDGAR Platform effectively:
- Quick start guides
- Interactive chat mode (default)
- File transformation (Excel, PDF)
- Web scraping
- Project management
- Troubleshooting

**→ [Browse User Docs](user/README.md)**

### 🛠️ [Developer Documentation](developer/)

**Start here if you want to DEVELOP or CONTRIBUTE to the platform.**

Technical documentation for contributors and developers:
- Architecture and design patterns
- API reference
- Migration guides
- Development setup
- Code governance

**→ [Browse Developer Docs](developer/README.md)**

### ⚙️ [Operations Documentation](ops/)

**Start here if you want to DEPLOY or OPERATE the platform.**

Deployment, security, and operational guides:
- Security guidelines
- Setup and deployment
- API key management
- Integration guides
- Monitoring and maintenance

**→ [Browse Ops Docs](ops/README.md)**

### 🔬 [Research Documentation](research/)

**Historical research notes and analysis.**

Detailed research, analysis, and design decisions made during platform development:
- Platform transformation analysis
- Test gap analysis
- Performance benchmarks
- Integration studies
- Feature feasibility studies

**→ [Browse Research Docs](research/)**

### 💾 [Session History](sessions/)

**Saved interactive chat sessions.**

Saved sessions from the interactive chat mode for resuming work.

## 🚀 Quick Start

### For New Users
1. **[Quick Start Guide](user/QUICK_START.md)** - Get up and running in 5 minutes
2. **[Interactive Chat Mode](user/INTERACTIVE_CHAT_MODE.md)** - Learn the default interface
3. **[Excel File Transform](user/EXCEL_FILE_TRANSFORM.md)** - Transform your first file

### For Developers
1. **[Development Guide](developer/DEVELOPMENT_GUIDE.md)** - Set up your dev environment
2. **[Project Structure](developer/architecture/PROJECT_STRUCTURE.md)** - Understand the codebase
3. **[Platform API](developer/api/PLATFORM_API.md)** - Explore the API

### For Operators
1. **[Security Guidelines](ops/SECURITY.md)** - Understand security requirements
2. **[Setup Command](ops/SETUP_COMMAND.md)** - Deploy the platform
3. **[API Key Security](ops/API_KEY_SECURITY.md)** - Secure your API keys

## 🎯 Key Features

### 💬 Interactive Chat Mode (Default)
Auggie-style REPL for iterative extraction workflows with natural language understanding.

**Learn more**: [Interactive Chat Mode](user/INTERACTIVE_CHAT_MODE.md)

### 📊 File Transformation
Transform Excel, PDF, DOCX, and PPTX files to structured JSON with automatic pattern detection.

**Learn more**: [Excel Transform](user/EXCEL_FILE_TRANSFORM.md) | [PDF Transform](user/PDF_FILE_TRANSFORM.md)

### ✨ Meta-Extractor (NEW - Phase 4)
Auto-generate custom extractors from 2-3 examples in <5 seconds. Create production-ready extractors for any domain.

**Learn more**: [User Guide](user/META_EXTRACTOR_USER_GUIDE.md) | [API Reference](developer/api/META_EXTRACTOR_API.md) | [Architecture](developer/architecture/META_EXTRACTOR_ARCHITECTURE.md)

### 🌐 Web Scraping
Scrape data from websites, including JavaScript-heavy sites using Jina.ai integration.

**Learn more**: [Web Scraping](user/WEB_SCRAPING.md)

### 🎯 Pattern Detection
Automatically detect transformation patterns from 2-3 examples with confidence scoring.

**Learn more**: [Pattern Detection](user/PATTERN_DETECTION.md)

### 📁 Project Management
Organize extraction projects with external artifacts directory support.

**Learn more**: [Project Management](user/PROJECT_MANAGEMENT.md)

## 📊 Platform Status

- **Phase 2**: ✅ Complete (95.6% test pass rate, 565/591 tests)
- **Code Reuse**: 83% from EDGAR (exceeds 70% target)
- **Current Phase**: Phase 3 - Polish & Testing

## 📞 Getting Help

- **User Issues**: Check [Troubleshooting Guide](user/TROUBLESHOOTING.md)
- **Developer Questions**: See [Developer Docs](developer/README.md)
- **Security Concerns**: Review [Security Guidelines](ops/SECURITY.md)

---

**The EDGAR Platform: From SEC filings to general-purpose data extraction.** 🚀📊✨
