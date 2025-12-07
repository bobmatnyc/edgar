# 🔧 OpenRouter Service API

Centralized OpenRouter API service providing model-independent interface for all LLM interactions.

## 📋 Overview

The `OpenRouterService` provides a single, unified interface to OpenRouter's API with:
- Model-independent request handling
- Centralized configuration management
- Automatic fallback logic
- Web search integration
- Consistent error handling

## 🏗️ Architecture

```python
from edgar_analyzer.services.openrouter_service import OpenRouterService

# Initialize service
service = OpenRouterService()

# Model-independent interface
response = await service.chat_completion(
    messages=messages,
    model="x-ai/grok-4.1-fast:free",
    enable_web_search=True
)
```

## 🔧 Class Reference

### **OpenRouterService**

#### **Initialization**
```python
service = OpenRouterService()
```

**Configuration:**
- Loads API key from `OPENROUTER_API_KEY` environment variable
- Configures base URL from `OPENROUTER_BASE_URL` (default: OpenRouter API)
- Initializes model configurations with specific parameters

#### **Model Configuration**
```python
# Get model configuration
config = service.get_model_config("x-ai/grok-4.1-fast:free")
# Returns: {
#     "max_tokens": 4000,
#     "supports_web_search": True,
#     "context_window": 131072,
#     "cost_tier": "free"
# }

# Check web search support
supports_search = service.supports_web_search("x-ai/grok-4.1-fast:free")
# Returns: True

# Get available models
models = service.get_available_models()
# Returns: ["x-ai/grok-4.1-fast", "x-ai/grok-4.1-fast:free", ...]
```

## 🚀 Core Methods

### **chat_completion**
Single model chat completion with optional web search.

```python
async def chat_completion(
    messages: List[Dict[str, str]],
    model: str,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    enable_web_search: bool = False,
    **kwargs
) -> str
```

**Parameters:**
- `messages`: List of message dictionaries with 'role' and 'content'
- `model`: Model identifier (e.g., "x-ai/grok-4.1-fast:free")
- `temperature`: Sampling temperature (0.0 to 2.0)
- `max_tokens`: Maximum tokens to generate (uses model default if None)
- `enable_web_search`: Whether to enable web search tools
- `**kwargs`: Additional parameters for the API call

**Returns:** Generated response text as string

**Example:**
```python
response = await service.chat_completion(
    messages=[
        {"role": "system", "content": "You are a financial analyst."},
        {"role": "user", "content": "Analyze this compensation data..."}
    ],
    model="x-ai/grok-4.1-fast:free",
    temperature=0.3,
    max_tokens=2000,
    enable_web_search=True
)
```

### **chat_completion_with_fallback**
Chat completion with automatic fallback to other models.

```python
async def chat_completion_with_fallback(
    messages: List[Dict[str, str]],
    primary_model: str,
    fallback_models: List[str],
    **kwargs
) -> str
```

**Parameters:**
- `messages`: List of message dictionaries
- `primary_model`: Primary model to try first
- `fallback_models`: List of fallback models to try if primary fails
- `**kwargs`: Additional parameters for chat_completion

**Returns:** Generated response text from the first successful model

**Example:**
```python
response = await service.chat_completion_with_fallback(
    messages=messages,
    primary_model="x-ai/grok-4.1-fast:free",
    fallback_models=[
        "anthropic/claude-3.5-sonnet",
        "anthropic/claude-3-sonnet"
    ],
    temperature=0.7,
    enable_web_search=True
)
```

## 🔍 Web Search Integration

### **Web Search Tools**
When `enable_web_search=True`, the service automatically configures OpenRouter's function calling:

```python
# Web search is enabled automatically
response = await service.chat_completion(
    messages=[{
        "role": "user", 
        "content": "What are the current SEC executive compensation requirements?"
    }],
    model="x-ai/grok-4.1-fast:free",
    enable_web_search=True
)
```

**Web Search Configuration:**
```python
tools = [{
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the web for real-time information",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                }
            },
            "required": ["query"]
        }
    }
}]
```

## 📊 Model Configurations

### **Supported Models**
```python
{
    "x-ai/grok-4.1-fast": {
        "max_tokens": 4000,
        "supports_web_search": True,
        "context_window": 131072,
        "cost_tier": "free"
    },
    "x-ai/grok-4.1-fast:free": {
        "max_tokens": 4000,
        "supports_web_search": True,
        "context_window": 131072,
        "cost_tier": "free"
    },
    "anthropic/claude-3.5-sonnet": {
        "max_tokens": 8192,
        "supports_web_search": True,
        "context_window": 200000,
        "cost_tier": "paid"
    },
    "anthropic/claude-3-sonnet": {
        "max_tokens": 4096,
        "supports_web_search": True,
        "context_window": 200000,
        "cost_tier": "paid"
    }
}
```

## 🛡️ Error Handling

### **Exception Types**
- `ValueError`: Invalid API key or configuration
- `OpenAI API Errors`: Network, authentication, or API errors
- `Model-specific errors`: Rate limits, context length, etc.

### **Error Handling Example**
```python
try:
    response = await service.chat_completion(
        messages=messages,
        model="x-ai/grok-4.1-fast:free"
    )
except ValueError as e:
    print(f"Configuration error: {e}")
except Exception as e:
    print(f"API error: {e}")
    # Fallback logic
    response = await service.chat_completion_with_fallback(
        messages=messages,
        primary_model="x-ai/grok-4.1-fast:free",
        fallback_models=["anthropic/claude-3.5-sonnet"]
    )
```

## 📝 Logging

The service provides comprehensive logging:

```python
import structlog
logger = structlog.get_logger(__name__)

# Logs include:
# - Service initialization
# - API request details
# - Response metadata
# - Error information
# - Performance metrics
```

## 🎯 Best Practices

### **Model Selection**
1. **Use Grok for free tier**: `x-ai/grok-4.1-fast:free` for development
2. **Use Claude for production**: Higher quality, larger context
3. **Always provide fallbacks**: Ensure reliability

### **Web Search Usage**
1. **Enable selectively**: Only when real-time information needed
2. **Optimize queries**: Clear, specific search terms
3. **Handle empty responses**: Web search may return no results

### **Performance Optimization**
1. **Set appropriate max_tokens**: Avoid unnecessary generation
2. **Use temperature wisely**: Lower for factual, higher for creative
3. **Cache responses**: For repeated queries

---

**The OpenRouterService provides enterprise-grade, model-independent access to OpenRouter's powerful LLM capabilities.** 🚀🔧
