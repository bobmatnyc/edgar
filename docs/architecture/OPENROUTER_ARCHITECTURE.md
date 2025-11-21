# 🏗️ OpenRouter Service Architecture

Centralized, model-independent architecture for OpenRouter API integration.

## 📋 Overview

The OpenRouter Service Architecture provides a clean, maintainable approach to LLM API integration with:
- **Single Point of API Interaction**: All OpenRouter calls go through one service
- **Model Independence**: Same interface works with any supported model
- **Centralized Configuration**: Model-specific parameters managed centrally
- **Unified Error Handling**: Consistent error handling and fallback logic

## 🎯 Design Principles

### **1. Single Responsibility**
Each component has a clear, focused responsibility:
- `OpenRouterService`: API communication and model management
- `LLMService`: High-level business logic and domain operations
- `CLI Components`: User interface and interaction handling

### **2. Model Independence**
The architecture abstracts model-specific details:
```python
# Same interface for any model
response = await service.chat_completion(
    messages=messages,
    model="any-supported-model",  # Model-agnostic
    enable_web_search=True
)
```

### **3. Centralized Configuration**
Model configurations are managed in one place:
```python
model_configs = {
    "x-ai/grok-4.1-fast:free": {
        "max_tokens": 4000,
        "supports_web_search": True,
        "context_window": 131072
    }
}
```

## 🏗️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    CLI Layer                            │
├─────────────────────────────────────────────────────────┤
│  Interactive CLI  │  Traditional CLI  │  Web Interface  │
└─────────────────────┬───────────────────┬───────────────┘
                      │                   │
┌─────────────────────▼───────────────────▼───────────────┐
│                  LLM Service Layer                      │
├─────────────────────────────────────────────────────────┤
│  • Business Logic     • Domain Operations              │
│  • High-level APIs    • Result Processing              │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│              OpenRouter Service Layer                   │
├─────────────────────────────────────────────────────────┤
│  • Model Management   • API Communication              │
│  • Web Search Tools   • Error Handling                 │
│  • Fallback Logic     • Response Processing            │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                OpenRouter API                           │
├─────────────────────────────────────────────────────────┤
│  • Grok Models        • Claude Models                  │
│  • Web Search         • Function Calling               │
└─────────────────────────────────────────────────────────┘
```

## 🔧 Component Architecture

### **OpenRouterService**
**Location**: `src/edgar_analyzer/services/openrouter_service.py`

**Responsibilities:**
- Direct API communication with OpenRouter
- Model configuration management
- Web search tool integration
- Error handling and retry logic
- Response processing and validation

**Key Methods:**
```python
class OpenRouterService:
    async def chat_completion(...)           # Single model request
    async def chat_completion_with_fallback(...) # Multi-model fallback
    def get_model_config(...)               # Model configuration
    def supports_web_search(...)            # Feature detection
```

### **LLMService**
**Location**: `src/edgar_analyzer/services/llm_service.py`

**Responsibilities:**
- High-level business operations
- Domain-specific logic
- Result processing and formatting
- Integration with other system components

**Integration Pattern:**
```python
class LLMService:
    def __init__(self):
        self.openrouter = OpenRouterService()  # Composition
    
    async def _make_llm_request(self, ...):
        return await self.openrouter.chat_completion_with_fallback(...)
```

## 🔄 Data Flow

### **Request Flow**
1. **CLI Layer**: User input or command
2. **LLM Service**: Business logic processing
3. **OpenRouter Service**: API request preparation
4. **OpenRouter API**: Model execution
5. **Response Processing**: Result formatting
6. **CLI Layer**: Output to user

### **Fallback Flow**
1. **Primary Model**: Attempt with preferred model
2. **Error Detection**: Catch and log failures
3. **Fallback Model**: Try next model in sequence
4. **Success/Failure**: Return result or final error

## 🔍 Web Search Integration

### **Architecture**
```python
# Web search is integrated at the OpenRouter service level
if enable_web_search and model_config.get("supports_web_search"):
    request_params["tools"] = self.prepare_web_search_tools()
    request_params["tool_choice"] = "auto"
```

### **Tool Configuration**
```python
def prepare_web_search_tools(self) -> List[Dict[str, Any]]:
    return [{
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for real-time information",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        }
    }]
```

## 🛡️ Error Handling Architecture

### **Layered Error Handling**
1. **OpenRouter Service**: API-level errors and retries
2. **LLM Service**: Business logic errors and fallbacks
3. **CLI Layer**: User-facing error messages

### **Fallback Strategy**
```python
models_to_try = [primary_model] + fallback_models
for model in models_to_try:
    try:
        return await self.chat_completion(messages, model, **kwargs)
    except Exception as e:
        logger.warning(f"Model {model} failed: {e}")
        continue
```

## 📊 Configuration Management

### **Environment-Based Configuration**
```python
# Service configuration
self.api_key = os.getenv("OPENROUTER_API_KEY")
self.base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

# Model selection
primary_model = os.getenv("PRIMARY_MODEL", "x-ai/grok-4.1-fast:free")
fallback_model = os.getenv("FALLBACK_MODEL", "anthropic/claude-3.5-sonnet")
```

### **Model Configuration Schema**
```python
{
    "model_name": {
        "max_tokens": int,           # Maximum tokens for this model
        "supports_web_search": bool, # Web search capability
        "context_window": int,       # Context window size
        "cost_tier": str            # Cost classification
    }
}
```

## 🚀 Benefits

### **Maintainability**
- **Single Point of Change**: All API logic in one place
- **Clear Separation**: Business logic separate from API details
- **Easy Testing**: Mock OpenRouter service for unit tests

### **Scalability**
- **Model Addition**: Add new models by updating configuration
- **Feature Extension**: Add new capabilities without changing interfaces
- **Performance Optimization**: Centralized optimization points

### **Reliability**
- **Automatic Fallback**: Multiple model tiers for reliability
- **Error Recovery**: Comprehensive error handling
- **Monitoring**: Centralized logging and metrics

## 🎯 Future Enhancements

### **Planned Features**
- **Response Caching**: Cache frequent requests for performance
- **Load Balancing**: Distribute requests across multiple endpoints
- **Advanced Fallback**: Intelligent model selection based on request type
- **Metrics Collection**: Detailed performance and usage metrics

### **Extension Points**
- **Custom Models**: Easy addition of new model providers
- **Advanced Tools**: Additional function calling capabilities
- **Streaming Support**: Real-time response streaming
- **Batch Processing**: Efficient batch request handling

---

**The OpenRouter Service Architecture provides a robust, scalable foundation for enterprise-grade LLM integration.** 🏗️🚀
