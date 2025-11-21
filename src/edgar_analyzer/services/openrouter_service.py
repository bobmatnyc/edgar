#!/usr/bin/env python3
"""
OpenRouter Service - Centralized API Interface

PURPOSE:
    Provides a single, model-independent interface to OpenRouter API with
    centralized configuration, error handling, and feature support.

FUNCTION:
    Centralized OpenRouter API management:
    - Single API client with unified configuration
    - Model-independent request handling
    - Centralized web search integration
    - Unified error handling and fallback logic
    - Model-specific parameter management

USAGE:
    from edgar_analyzer.services.openrouter_service import OpenRouterService
    
    service = OpenRouterService()
    response = await service.chat_completion(
        messages=messages,
        model="x-ai/grok-4.1-fast",
        temperature=0.7,
        enable_web_search=True
    )

MODIFICATION HISTORY:
    2025-11-21 System - Initial creation
    - WHY: Centralize OpenRouter API calls for better maintainability
    - HOW: Single service with model-independent interface
    - IMPACT: Cleaner architecture and easier model management

DEPENDENCIES:
    - OpenAI client library (for OpenRouter compatibility)
    - Environment configuration
    - Structured logging

AUTHOR: EDGAR CLI System
CREATED: 2025-11-21
LAST_MODIFIED: 2025-11-21
"""

import os
import asyncio
from typing import Dict, List, Optional, Any, Union
from openai import AsyncOpenAI
from dotenv import load_dotenv
import structlog

# Load environment variables
load_dotenv('.env.local')

logger = structlog.get_logger(__name__)


class OpenRouterService:
    """
    Centralized OpenRouter API service with model-independent interface.
    
    WHY: Provides single point of API interaction with unified configuration
    HOW: Abstracts model-specific details behind clean interface
    WHEN: Enhanced 2025-11-21 for centralized API management
    """
    
    def __init__(self):
        """Initialize OpenRouter service with centralized configuration."""
        # Load configuration from environment
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")
        
        self.base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        
        # Initialize OpenAI client for OpenRouter
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        # Model configuration with specific parameters
        self.model_configs = {
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
        
        logger.info("OpenRouter service initialized",
                   base_url=self.base_url,
                   models_configured=len(self.model_configs))
    
    def get_model_config(self, model: str) -> Dict[str, Any]:
        """Get configuration for a specific model."""
        return self.model_configs.get(model, {
            "max_tokens": 2000,
            "supports_web_search": False,
            "context_window": 4096,
            "cost_tier": "unknown"
        })
    
    def prepare_web_search_tools(self) -> List[Dict[str, Any]]:
        """Prepare web search tools configuration for OpenRouter."""
        return [{
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
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        enable_web_search: bool = False,
        **kwargs
    ) -> str:
        """
        Make a chat completion request to OpenRouter.
        
        Args:
            messages: List of message dictionaries
            model: Model identifier (e.g., "x-ai/grok-4.1-fast")
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate (uses model default if None)
            enable_web_search: Whether to enable web search tools
            **kwargs: Additional parameters for the API call
        
        Returns:
            Generated response text
        """
        # Get model configuration
        model_config = self.get_model_config(model)
        
        # Prepare request parameters
        request_params = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens or model_config["max_tokens"],
            **kwargs
        }
        
        # Add web search tools if enabled and supported
        if enable_web_search and model_config.get("supports_web_search", False):
            request_params["tools"] = self.prepare_web_search_tools()
            request_params["tool_choice"] = "auto"
            
            logger.debug("Web search enabled for request",
                        model=model,
                        tools_count=len(request_params["tools"]))
        
        try:
            logger.debug("Making OpenRouter API request",
                        model=model,
                        temperature=temperature,
                        max_tokens=request_params["max_tokens"],
                        web_search_enabled=enable_web_search)
            
            response = await self.client.chat.completions.create(**request_params)
            content = response.choices[0].message.content
            
            if content is None:
                content = ""
            
            content = content.strip()
            
            logger.debug("OpenRouter API response received",
                        model=model,
                        response_length=len(content),
                        preview=content[:100] + "..." if len(content) > 100 else content)
            
            return content
            
        except Exception as e:
            logger.error("OpenRouter API request failed",
                        model=model,
                        error=str(e),
                        error_type=type(e).__name__)
            raise
    
    async def chat_completion_with_fallback(
        self,
        messages: List[Dict[str, str]],
        primary_model: str,
        fallback_models: List[str],
        **kwargs
    ) -> str:
        """
        Make a chat completion request with automatic fallback to other models.
        
        Args:
            messages: List of message dictionaries
            primary_model: Primary model to try first
            fallback_models: List of fallback models to try if primary fails
            **kwargs: Additional parameters for chat_completion
        
        Returns:
            Generated response text
        """
        models_to_try = [primary_model] + fallback_models
        last_error = None
        
        for i, model in enumerate(models_to_try):
            try:
                if i > 0:
                    logger.warning(f"Trying fallback model {i}",
                                 model=model,
                                 previous_error=str(last_error))
                
                return await self.chat_completion(
                    messages=messages,
                    model=model,
                    **kwargs
                )
                
            except Exception as e:
                last_error = e
                logger.warning(f"Model {model} failed",
                             error=str(e),
                             remaining_models=len(models_to_try) - i - 1)
                
                if i == len(models_to_try) - 1:
                    # Last model failed
                    logger.error("All models failed",
                               models_tried=models_to_try,
                               final_error=str(e))
                    raise e
        
        # Should never reach here
        raise RuntimeError("Unexpected fallback logic error")
    
    def get_available_models(self) -> List[str]:
        """Get list of configured models."""
        return list(self.model_configs.keys())
    
    def supports_web_search(self, model: str) -> bool:
        """Check if a model supports web search."""
        return self.get_model_config(model).get("supports_web_search", False)
