"""
Token counting utility for conversation memory management.

Provides accurate token counting using tiktoken with fallback to character-based estimation.
"""

from typing import Any, Dict, List

import structlog

logger = structlog.get_logger(__name__)


class TokenCounter:
    """
    Token counting utility for conversation memory management.

    Supports multiple LLM models with accurate token counting via tiktoken.
    Falls back to character-based estimation if tiktoken is unavailable.

    Design Decision: Using tiktoken for accurate counting
    - Rationale: Accurate token counting prevents context overflow
    - Trade-off: Additional dependency vs. accuracy (chose accuracy)
    - Fallback: Character estimation (1 token ≈ 4 chars) if unavailable
    """

    def __init__(self, model: str = "gpt-4"):
        """
        Initialize token counter with model-specific encoding.

        Args:
            model: Model name for encoding (default: gpt-4)
                   Supports: gpt-4, gpt-3.5-turbo, claude, etc.
        """
        self.model = model
        self.encoding = None
        self.use_tiktoken = False

        try:
            import tiktoken

            try:
                # Try model-specific encoding
                self.encoding = tiktoken.encoding_for_model(model)
                self.use_tiktoken = True
                logger.info(
                    "TokenCounter initialized with tiktoken",
                    model=model,
                    encoding=self.encoding.name,
                )
            except KeyError:
                # Fallback to cl100k_base (GPT-4, Claude compatible)
                self.encoding = tiktoken.get_encoding("cl100k_base")
                self.use_tiktoken = True
                logger.info(
                    "TokenCounter using fallback encoding",
                    model=model,
                    encoding="cl100k_base",
                )
        except ImportError:
            logger.warning(
                "tiktoken not available, using character-based estimation",
                model=model,
            )
            self.use_tiktoken = False

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using tiktoken or character estimation.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens

        Performance: O(n) where n is text length
        """
        if not text:
            return 0

        if self.use_tiktoken and self.encoding:
            try:
                return len(self.encoding.encode(text))
            except Exception as e:
                logger.warning(
                    "tiktoken encoding failed, falling back to estimation", error=str(e)
                )
                return self.estimate_tokens_fast(text)
        else:
            return self.estimate_tokens_fast(text)

    def count_messages_tokens(self, messages: List[Dict[str, str]]) -> int:
        """
        Count tokens in OpenAI-style message list.

        Accounts for message formatting overhead:
        - 4 tokens per message for role/formatting
        - 2 tokens for assistant response start

        Args:
            messages: List of message dicts with 'role' and 'content'

        Returns:
            Total token count including formatting

        Example:
            messages = [
                {"role": "system", "content": "You are helpful"},
                {"role": "user", "content": "Hello"}
            ]
            tokens = counter.count_messages_tokens(messages)
        """
        total = 0

        for message in messages:
            # Message formatting overhead
            total += 4  # <|start|>role<|message|>content<|end|>
            total += self.count_tokens(message.get("content", ""))

        # Assistant response formatting
        total += 2  # <|start|>assistant<|message|>

        return total

    def count_exchange_tokens(self, exchange: Dict[str, Any]) -> int:
        """
        Count tokens in a conversation exchange.

        Args:
            exchange: Dict with 'user_input' and 'controller_response'

        Returns:
            Total token count for exchange including formatting overhead
        """
        tokens = 0

        # User input
        tokens += self.count_tokens(exchange.get("user_input", ""))

        # Controller response
        tokens += self.count_tokens(exchange.get("controller_response", ""))

        # Formatting overhead (timestamp, labels, etc.)
        tokens += 20

        return tokens

    def estimate_tokens_fast(self, text: str) -> int:
        """
        Fast token estimation using character count.

        Approximation: 1 token ≈ 4 characters for English text
        Accuracy: ±20-30% variance from actual tokens

        Args:
            text: Text to estimate

        Returns:
            Estimated token count

        Use Case: Quick checks when exact count not critical
        """
        return max(1, len(text) // 4)

    def get_token_usage_stats(
        self, total_tokens: int, threshold: int
    ) -> Dict[str, Any]:
        """
        Calculate token usage statistics.

        Args:
            total_tokens: Current token count
            threshold: Maximum token threshold

        Returns:
            Dict with usage statistics
        """
        usage_percent = (total_tokens / threshold * 100) if threshold > 0 else 0

        return {
            "total_tokens": total_tokens,
            "threshold": threshold,
            "usage_percent": round(usage_percent, 1),
            "remaining": max(0, threshold - total_tokens),
            "over_threshold": total_tokens >= threshold,
        }
