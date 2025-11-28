"""
OpenRouter Client for Sonnet 4.5 API access.

This module provides a clean, typed interface to the OpenRouter API,
specifically optimized for Sonnet 4.5 code generation tasks.

Design Decisions:
- **Async-First**: All API calls are async for better performance
- **Type Safety**: Full type hints for all methods
- **Error Handling**: Comprehensive error handling with retries
- **Rate Limiting**: Built-in support for API rate limits
- **Logging**: Structured logging for debugging and monitoring

Usage:
    >>> client = OpenRouterClient(api_key="sk-or-v1-...", model="anthropic/claude-sonnet-4.5")
    >>> response = await client.chat_completion(
    ...     messages=[{"role": "user", "content": "Hello"}],
    ...     temperature=0.3
    ... )
"""

import asyncio
import os
from typing import Dict, List, Optional, Any

import structlog
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


# ============================================================================
# CONFIGURATION MODELS
# ============================================================================


class OpenRouterConfig(BaseModel):
    """Configuration for OpenRouter API.

    Example:
        >>> config = OpenRouterConfig(
        ...     api_key="sk-or-v1-...",
        ...     base_url="https://openrouter.ai/api/v1",
        ...     model="anthropic/claude-sonnet-4.5"
        ... )
    """

    api_key: str = Field(
        ...,
        description="OpenRouter API key"
    )

    base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        description="OpenRouter API base URL"
    )

    model: str = Field(
        default="anthropic/claude-sonnet-4.5",
        description="Model identifier"
    )

    timeout: int = Field(
        default=120,
        description="Request timeout in seconds"
    )

    max_retries: int = Field(
        default=3,
        description="Maximum retry attempts"
    )


class ModelCapabilities(BaseModel):
    """Capabilities of a specific model.

    Example:
        >>> caps = ModelCapabilities(
        ...     max_tokens=8000,
        ...     context_window=1000000,
        ...     supports_tools=True,
        ...     supports_web_search=True
        ... )
    """

    max_tokens: int = Field(
        ...,
        description="Maximum tokens the model can generate"
    )

    context_window: int = Field(
        ...,
        description="Maximum context window size"
    )

    supports_tools: bool = Field(
        default=False,
        description="Whether model supports tool use"
    )

    supports_web_search: bool = Field(
        default=False,
        description="Whether model supports web search"
    )

    supports_json_mode: bool = Field(
        default=False,
        description="Whether model supports JSON output mode"
    )


# ============================================================================
# OPENROUTER CLIENT
# ============================================================================


class OpenRouterClient:
    """
    Client for OpenRouter API with Sonnet 4.5 optimization.

    This client provides a clean interface to the OpenRouter API,
    handling authentication, retries, rate limiting, and error handling.

    Design Decision: Async-first architecture for better performance
    in code generation pipelines that may need multiple API calls.

    Example:
        >>> client = OpenRouterClient(
        ...     api_key="sk-or-v1-...",
        ...     model="anthropic/claude-sonnet-4.5"
        ... )
        >>> response = await client.chat_completion(
        ...     messages=[{"role": "user", "content": "Generate code..."}],
        ...     temperature=0.3,
        ...     max_tokens=8000
        ... )
    """

    # Model capabilities configuration
    MODEL_CAPABILITIES = {
        "anthropic/claude-sonnet-4.5": ModelCapabilities(
            max_tokens=8192,
            context_window=1000000,
            supports_tools=True,
            supports_web_search=True,
            supports_json_mode=True
        ),
        "anthropic/claude-3.5-sonnet": ModelCapabilities(
            max_tokens=8192,
            context_window=200000,
            supports_tools=True,
            supports_web_search=True,
            supports_json_mode=True
        ),
        "x-ai/grok-4.1-fast": ModelCapabilities(
            max_tokens=4000,
            context_window=131072,
            supports_tools=True,
            supports_web_search=True,
            supports_json_mode=False
        ),
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "anthropic/claude-sonnet-4.5",
        base_url: str = "https://openrouter.ai/api/v1",
        timeout: int = 120,
        max_retries: int = 3
    ):
        """
        Initialize OpenRouter client.

        Args:
            api_key: OpenRouter API key (defaults to OPENROUTER_API_KEY env var)
            model: Model identifier
            base_url: API base URL
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts

        Raises:
            ValueError: If API key is not provided and not in environment
        """
        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenRouter API key must be provided via api_key parameter "
                "or OPENROUTER_API_KEY environment variable"
            )

        self.model = model
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries

        # Initialize AsyncOpenAI client
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=timeout
        )

        logger.info(
            "OpenRouterClient initialized",
            model=self.model,
            base_url=self.base_url,
            timeout=self.timeout
        )

    def get_capabilities(self, model: Optional[str] = None) -> ModelCapabilities:
        """
        Get capabilities for a specific model.

        Args:
            model: Model identifier (defaults to client's model)

        Returns:
            ModelCapabilities object

        Example:
            >>> caps = client.get_capabilities()
            >>> print(f"Max tokens: {caps.max_tokens}")
        """
        target_model = model or self.model
        return self.MODEL_CAPABILITIES.get(
            target_model,
            ModelCapabilities(
                max_tokens=4000,
                context_window=4096,
                supports_tools=False,
                supports_web_search=False,
                supports_json_mode=False
            )
        )

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Make a chat completion request.

        Args:
            messages: List of message dictionaries
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            model: Model to use (defaults to client's model)
            **kwargs: Additional API parameters

        Returns:
            Generated response text

        Raises:
            Exception: If API call fails after retries

        Example:
            >>> response = await client.chat_completion(
            ...     messages=[
            ...         {"role": "system", "content": "You are a code generator"},
            ...         {"role": "user", "content": "Generate a weather extractor"}
            ...     ],
            ...     temperature=0.3,
            ...     max_tokens=8000
            ... )
        """
        target_model = model or self.model
        capabilities = self.get_capabilities(target_model)

        # Use model's max_tokens if not specified
        if max_tokens is None:
            max_tokens = capabilities.max_tokens

        # Prepare request parameters
        request_params = {
            "model": target_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs
        }

        logger.debug(
            "Making chat completion request",
            model=target_model,
            temperature=temperature,
            max_tokens=max_tokens,
            message_count=len(messages)
        )

        # Retry logic
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = await self.client.chat.completions.create(**request_params)

                # Extract content
                content = response.choices[0].message.content
                if content is None:
                    content = ""

                content = content.strip()

                logger.debug(
                    "Chat completion successful",
                    model=target_model,
                    response_length=len(content),
                    attempt=attempt + 1
                )

                return content

            except Exception as e:
                last_error = e
                logger.warning(
                    "Chat completion attempt failed",
                    model=target_model,
                    attempt=attempt + 1,
                    max_attempts=self.max_retries,
                    error=str(e),
                    error_type=type(e).__name__
                )

                # Wait before retry (exponential backoff)
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # 1s, 2s, 4s
                    logger.debug(f"Waiting {wait_time}s before retry")
                    await asyncio.sleep(wait_time)

        # All retries failed
        logger.error(
            "Chat completion failed after all retries",
            model=target_model,
            max_attempts=self.max_retries,
            final_error=str(last_error)
        )
        raise last_error

    async def chat_completion_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Make a chat completion request with JSON output mode.

        This method attempts to use the model's JSON mode if supported,
        otherwise falls back to requesting JSON in the prompt.

        Args:
            messages: List of message dictionaries
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            model: Model to use
            **kwargs: Additional API parameters

        Returns:
            JSON response as string

        Example:
            >>> response = await client.chat_completion_json(
            ...     messages=[{"role": "user", "content": "Generate plan JSON"}],
            ...     temperature=0.3
            ... )
        """
        target_model = model or self.model
        capabilities = self.get_capabilities(target_model)

        # Add JSON mode if supported
        if capabilities.supports_json_mode:
            kwargs["response_format"] = {"type": "json_object"}

            logger.debug(
                "Using JSON output mode",
                model=target_model
            )
        else:
            # Fallback: Add JSON instruction to system message
            if messages and messages[0].get("role") == "system":
                messages[0]["content"] += "\n\nPlease respond with valid JSON only."
            else:
                messages.insert(0, {
                    "role": "system",
                    "content": "Please respond with valid JSON only."
                })

            logger.debug(
                "JSON mode not supported, using prompt instruction",
                model=target_model
            )

        return await self.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            model=target_model,
            **kwargs
        )

    async def stream_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
        **kwargs
    ):
        """
        Make a streaming chat completion request.

        Args:
            messages: List of message dictionaries
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            model: Model to use
            **kwargs: Additional API parameters

        Yields:
            Response chunks as they arrive

        Example:
            >>> async for chunk in client.stream_completion(messages):
            ...     print(chunk, end="", flush=True)
        """
        target_model = model or self.model
        capabilities = self.get_capabilities(target_model)

        if max_tokens is None:
            max_tokens = capabilities.max_tokens

        request_params = {
            "model": target_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
            **kwargs
        }

        logger.debug(
            "Starting streaming completion",
            model=target_model,
            temperature=temperature,
            max_tokens=max_tokens
        )

        stream = await self.client.chat.completions.create(**request_params)

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def supports_json_mode(self, model: Optional[str] = None) -> bool:
        """Check if model supports JSON output mode."""
        capabilities = self.get_capabilities(model)
        return capabilities.supports_json_mode

    def supports_web_search(self, model: Optional[str] = None) -> bool:
        """Check if model supports web search."""
        capabilities = self.get_capabilities(model)
        return capabilities.supports_web_search
