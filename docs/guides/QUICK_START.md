# 🚀 Quick Start Guide

Get up and running with the EDGAR CLI in minutes!

## ⚡ Prerequisites

- **Python 3.8+** installed
- **Git** for cloning the repository
- **OpenRouter API Key** (required, for web search features enabled by default)

## 🎯 5-Minute Setup

### 1. **Clone and Setup**
```bash
# Clone the repository
git clone https://github.com/bobmatnyc/zach-edgar.git
cd zach-edgar

# Run automated setup
python3 setup_edgar_cli.py
```

### 2. **Configure API Key (Optional)**
```bash
# Copy environment template
cp .env.template .env.local

# Edit .env.local and add your OpenRouter API key
# OPENROUTER_API_KEY=your_key_here
```

### 3. **Start Using**
```bash
# Activate environment
source venv/bin/activate

# Start conversational interface (web search enabled by default)
python -m edgar_analyzer

# Or show CLI help
python -m edgar_analyzer --cli

# Or disable web search if needed
python -m edgar_analyzer --disable-web-search
```

## 🎯 First Commands

### **Interactive Mode (Default)**
```bash
# Start conversational interface
python -m edgar_analyzer

# Example conversation:
You: "Help me analyze executive compensation"
AI: "I can help you extract and analyze executive compensation..."
```

### **Traditional CLI**
```bash
# Extract compensation for Apple
python -m edgar_analyzer extract --cik 0000320193 --year 2023

# Run system test
python -m edgar_analyzer test --companies 5

# Show system info
python -m edgar_analyzer trad-info
```

### **Web Search (Enabled by Default)**
```bash
# Interactive with real-time information (default)
python -m edgar_analyzer

# Traditional commands with web search (default)
python -m edgar_analyzer extract --cik 0000320193
```

## 🔧 Key Features to Try

### **1. Conversational Interface**
- Natural language queries
- Context-aware responses
- Dynamic code execution
- Real-time help and guidance

### **2. Web Search Integration (Enabled by Default)**
- Current market data access
- Latest SEC requirements
- Best practices research
- Real-time validation

### **3. Self-Improving Code**
- Automatic quality assurance
- Code enhancement suggestions
- Performance optimization
- Error detection and fixing

### **4. Enterprise Features**
- Subprocess monitoring
- Security validation
- Comprehensive logging
- Fallback mechanisms

## 📚 Next Steps

### **Learn More**
- [CLI Usage Guide](CLI_USAGE.md) - Complete interface reference
- [Web Search Guide](WEB_SEARCH_CAPABILITIES.md) - Advanced features
- [Configuration Guide](CONFIGURATION.md) - Customize your setup

### **Explore Examples**
- [Basic Examples](../examples/BASIC_USAGE.md) - Common use cases
- [Advanced Examples](../examples/ADVANCED_USAGE.md) - Complex scenarios

### **For Developers**
- [Development Setup](DEVELOPMENT.md) - Development environment
- [API Reference](../api/) - Technical documentation
- [Architecture](../architecture/) - System design

## 🆘 Need Help?

### **Common Issues**
- **API Key Error**: Configure OpenRouter API key in `.env.local`
- **Python Version**: Ensure Python 3.8+ is installed
- **Dependencies**: Run `python3 setup_edgar_cli.py` to install

### **Get Support**
- Check [Troubleshooting Guide](TROUBLESHOOTING.md)
- Review [FAQ](FAQ.md)
- See [Security Guidelines](SECURITY.md) for security issues

---

**You're now ready to experience the future of CLI interfaces!** 🚀
