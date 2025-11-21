# 🧪 EDGAR CLI Tests

Comprehensive test suite and testing artifacts for the EDGAR CLI system.

## 📁 Directory Structure

### **🧪 Test Files**
- `test_*.py` - Automated test scripts
- `debug_*.py` - Debug and diagnostic utilities
- `run_*.py` - Analysis and execution scripts

### **📊 Test Artifacts**
- `results/` - Test execution results and outputs
- `output/` - Generated test data and reports
- `scripts/` - Testing and utility scripts
- `logs/` - Test execution logs and debugging information

## 📋 Test Categories

### **🏗️ Architecture Tests**
- `test_centralized_openrouter.py` - Centralized OpenRouter service architecture
- `test_web_search_structure.py` - Web search integration structure validation

### **🔍 Integration Tests**
- `test_web_search_integration.py` - Full web search integration testing
- `test_subprocess_monitoring.py` - Subprocess monitoring and control

### **📊 System Tests**
- `test_50_companies.py` - Large-scale system validation
- `test_system_validation.py` - End-to-end system testing

### **🔧 Analysis Scripts**
- `run_top_100_enhanced.py` - Enhanced Fortune 100 analysis with LLM validation
- `edgar_analyzer_prototype.py` - Original prototype implementation
- `debug_proxy_content.py` - Debug utility for proxy filing content

### **📁 Test Artifacts**
- `results/` - Test execution results and analysis outputs
- `output/` - Generated test data, reports, and Excel files
- `scripts/` - Utility scripts for setup, quality assurance, and maintenance
- `logs/` - Test execution logs and debugging information

## 🚀 Running Tests

### **Individual Tests**
```bash
# Test centralized architecture
python tests/test_centralized_openrouter.py

# Test web search structure (no API key required)
python tests/test_web_search_structure.py

# Test web search integration (requires API key)
python tests/test_web_search_integration.py --test-llm-service

# Test subprocess monitoring
python tests/test_subprocess_monitoring.py
```

### **System Validation**
```bash
# Quick system test
python tests/test_50_companies.py --companies 5

# Full system validation
python tests/test_system_validation.py
```

## 🔧 Test Requirements

### **Basic Tests**
- Python 3.8+
- Virtual environment activated
- Basic dependencies installed

### **API-Dependent Tests**
- OpenRouter API key configured in `.env.local`
- Network connectivity
- API quota available

### **System Tests**
- Full EDGAR CLI installation
- All dependencies installed
- Sufficient system resources

## 📊 Test Coverage

### **✅ Architecture Validation**
- Centralized service design
- Model-independent interfaces
- Configuration management
- Error handling patterns

### **✅ Feature Testing**
- Web search integration
- Subprocess monitoring
- CLI interface modes
- Fallback mechanisms

### **✅ Integration Testing**
- Component interactions
- API integrations
- End-to-end workflows
- Error scenarios

### **✅ Performance Testing**
- Response times
- Resource usage
- Scalability limits
- Stress testing

## 🎯 Test Execution Guide

### **Development Testing**
```bash
# Quick validation
python tests/test_web_search_structure.py

# Architecture validation
python tests/test_centralized_openrouter.py

# Basic functionality
python tests/test_subprocess_monitoring.py
```

### **Pre-Deployment Testing**
```bash
# Full integration test
python tests/test_web_search_integration.py --test-all

# System validation
python tests/test_system_validation.py

# Performance test
python tests/test_50_companies.py --companies 10
```

### **Production Validation**
```bash
# Health check
python tests/test_centralized_openrouter.py

# Feature validation
python tests/test_web_search_structure.py

# System status
python -m edgar_analyzer trad-info
```

## 🛡️ Test Safety

### **API Usage**
- Tests use minimal API calls
- Fallback to mock responses when possible
- Rate limiting respected
- Error handling validated

### **System Safety**
- No destructive operations
- Isolated test environments
- Proper cleanup procedures
- Resource management

### **Data Protection**
- No real sensitive data used
- Mock data for testing
- Secure credential handling
- Privacy compliance

## 📈 Test Metrics

### **Success Criteria**
- All architecture tests pass
- Integration tests complete successfully
- System tests validate core functionality
- Performance tests meet benchmarks

### **Performance Benchmarks**
- API response time < 10 seconds
- System startup < 5 seconds
- Memory usage < 500MB
- CPU usage < 50% during normal operation

## 🔍 Debugging Tests

### **Common Issues**
- **API Key Missing**: Configure in `.env.local`
- **Network Errors**: Check connectivity and firewall
- **Permission Errors**: Ensure proper file permissions
- **Resource Limits**: Check available memory and CPU

### **Debug Commands**
```bash
# Verbose test execution
python tests/test_centralized_openrouter.py --verbose

# Check system status
python -m edgar_analyzer --verbose trad-info

# Validate configuration
python -c "from src.edgar_analyzer.services.openrouter_service import OpenRouterService; print('Config OK')"
```

## 🎯 Contributing Tests

### **Adding New Tests**
1. Follow existing test patterns
2. Include comprehensive documentation
3. Add to appropriate category
4. Update this README

### **Test Standards**
- Clear test names and descriptions
- Comprehensive error handling
- Proper cleanup procedures
- Performance considerations

---

**Comprehensive testing ensures the EDGAR CLI maintains enterprise-grade quality and reliability.** 🧪🚀
