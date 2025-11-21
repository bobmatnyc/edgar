# 🖥️ CLI Usage Guide

Comprehensive guide to using the EDGAR CLI's revolutionary conversational interface and traditional commands.

## 🎯 Interface Modes

### **🤖 Conversational Mode (Default)**
Natural language interface with AI-powered assistance.

```bash
# Start conversational interface (web search enabled by default)
python -m edgar_analyzer

# Disable web search if needed
python -m edgar_analyzer --disable-web-search

# Force conversational mode
python -m edgar_analyzer --mode chatbot
```

### **📋 Traditional CLI Mode**
Structured command-line interface for automation and scripting.

```bash
# Show CLI help (bypass interactive)
python -m edgar_analyzer --cli

# Force traditional mode
python -m edgar_analyzer --mode traditional

# Traditional commands
python -m edgar_analyzer extract --cik 0000320193
```

### **⚡ Auto Mode**
Automatically detects LLM availability and chooses the best interface.

```bash
# Auto mode (default behavior)
python -m edgar_analyzer --mode auto
```

## 🗣️ Conversational Interface

### **Natural Language Commands**
Talk to your CLI like a professional assistant:

```
You: "Help me analyze Apple's executive compensation"
AI: "I can help you extract and analyze Apple's executive compensation data..."

You: "Extract compensation data for CIK 0000320193"
AI: "I'll extract the executive compensation data for Apple (CIK 0000320193)..."

You: "Show me the project structure"
AI: "Here's the current project structure with explanations..."
```

### **Built-in Commands**
Special commands for common operations:

- `help` - Show available commands and capabilities
- `quit` or `exit` - Exit the conversational interface
- `info` - Display system information
- `status` - Show system status and health
- `clear` - Clear the conversation history

### **Dynamic Context**
The AI has access to:
- Live codebase analysis
- Real-time system information
- Current project structure
- Available tools and capabilities
- Web search results (enabled by default)

## 📋 Traditional Commands

### **Core Commands**

#### **Extract Executive Compensation**
```bash
# Basic extraction
python -m edgar_analyzer extract --cik 0000320193 --year 2023

# With output format
python -m edgar_analyzer extract --cik 0000320193 --year 2023 --format json

# Web search is enabled by default
python -m edgar_analyzer extract --cik 0000320193
```

#### **System Testing**
```bash
# Test with multiple companies
python -m edgar_analyzer test --companies 10

# Quick test
python -m edgar_analyzer test --companies 3

# Verbose testing
python -m edgar_analyzer --verbose test --companies 5
```

#### **System Information**
```bash
# Show application info
python -m edgar_analyzer trad-info

# Analyze codebase
python -m edgar_analyzer trad-analyze --query "compensation extraction"

# Execute code safely
python -m edgar_analyzer trad-execute --code "print('Hello EDGAR')"
```

### **Global Options**

#### **Interface Control**
- `--mode [auto|chatbot|traditional]` - Set interface mode
- `--cli` - Bypass interactive mode, show CLI help
- `--verbose` - Enable verbose output

#### **Feature Flags**
- `--enable-web-search/--disable-web-search` - Web search capabilities (enabled by default)
- `--scripting-enabled` - Enable dynamic scripting (default: true)

#### **Examples**
```bash
# Verbose mode (web search enabled by default)
python -m edgar_analyzer --verbose

# Traditional mode without web search
python -m edgar_analyzer --mode traditional --disable-web-search extract --cik 0000320193

# Show help with all options
python -m edgar_analyzer --help
```

## 🔍 Web Search Features

### **Enhanced Analysis**
Web search is enabled by default, providing:
- Access to current SEC requirements
- Latest market benchmarks
- Validation against current standards
- Real-time research capabilities

### **Usage Examples**
```bash
# Interactive mode (web search enabled by default)
python -m edgar_analyzer

# Traditional commands (web search enabled by default)
python -m edgar_analyzer extract --cik 0000320193

# Web search in conversational mode
You: "What are the current SEC executive compensation disclosure requirements?"
AI: [Searches web and provides current information]
```

## 🛠️ Advanced Usage

### **Launcher Scripts**
```bash
# Use launcher script (created by setup)
./edgar_cli.sh                    # Interactive mode (web search enabled)
./edgar_cli.sh --cli              # Show help
./edgar_cli.sh --disable-web-search # Without web search
```

### **Environment Variables**
```bash
# Set default mode
export EDGAR_CLI_MODE=chatbot

# Disable web search (enabled by default)
export EDGAR_DISABLE_WEB_SEARCH=true

# Set verbosity
export EDGAR_VERBOSE=true
```

### **Scripting and Automation**
```bash
# Use in scripts
python -m edgar_analyzer extract --cik 0000320193 --format json > apple_compensation.json

# Batch processing
for cik in 0000320193 0001018724 0000789019; do
    python -m edgar_analyzer extract --cik $cik --year 2023
done

# Pipeline usage
python -m edgar_analyzer extract --cik 0000320193 --format json | jq '.[] | .total_compensation'
```

## 🎯 Best Practices

### **For Interactive Use**
1. **Start with conversational mode** for exploration and learning
2. **Web search is enabled by default** for current information and validation
3. **Ask for help** when unsure about capabilities
4. **Use natural language** - the AI understands context

### **For Automation**
1. **Use traditional commands** for scripts and CI/CD
2. **Specify output formats** for data processing
3. **Handle errors gracefully** with proper exit codes
4. **Use verbose mode** for debugging

### **For Development**
1. **Use --cli flag** to explore available commands
2. **Web search is enabled by default** for best practices research
3. **Use verbose mode** for detailed logging
4. **Test with small datasets** before scaling

## 🆘 Troubleshooting

### **Common Issues**
- **LLM not available**: System falls back to traditional CLI
- **Web search errors**: Check OpenRouter API key configuration
- **Permission errors**: Ensure proper file permissions
- **Memory issues**: Use smaller datasets for testing

### **Debug Commands**
```bash
# Verbose output
python -m edgar_analyzer --verbose trad-info

# Test LLM availability
python -m edgar_analyzer test --companies 1

# Check system status
python -m edgar_analyzer trad-info
```

---

**Master the revolutionary CLI interface and unlock the full power of conversational computing!** 🚀🤖
