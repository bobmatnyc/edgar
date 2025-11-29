"""
Conversation summarization utility for memory compaction.

LLM-based intelligent summarization that preserves critical context while
reducing token usage by 60-80%.
"""

import json
from typing import Any, Callable, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)


class ConversationSummarizer:
    """
    LLM-based conversation summarization for memory compaction.

    Design Decision: LLM-based summarization over rule-based
    - Rationale: Better context preservation, semantic understanding
    - Trade-off: Additional LLM call vs. quality (chose quality)
    - Fallback: Simple rule-based if LLM fails
    - Performance: ~2 seconds per summarization (acceptable)

    Success Metrics:
    - Token reduction: >60% target
    - Context preservation: >90% of key facts
    - User satisfaction: No complaints about lost context
    """

    # Summarization prompt template
    SUMMARIZATION_PROMPT = """You are a conversation summarization expert specializing in preserving critical context while compacting conversation history.

TASK: Summarize the following conversation exchanges into a compact format that preserves essential information.

CONVERSATION EXCHANGES ({num_exchanges} exchanges):
{exchanges_json}

SUMMARIZATION GUIDELINES:
1. **Preserve Facts**: Keep all factual information (CIK numbers, company names, dates, analysis results)
2. **Preserve Decisions**: Document any decisions made or actions taken
3. **Compress Verbosity**: Convert long explanations into bullet points
4. **Extract Entities**: List key entities mentioned (companies, people, metrics)
5. **Maintain Chronology**: Keep rough timeline of conversation flow
6. **Flag Unresolved**: Note any questions that weren't fully answered

OUTPUT FORMAT (JSON only, no additional text):
{{
  "summary": "2-3 sentence overview of conversation flow",
  "key_facts": [
    "Fact 1: CIK 0000320193 is Apple Inc.",
    "Fact 2: Analyzed executive compensation for fiscal year 2023"
  ],
  "decisions_made": [
    "Decision to use XBRL extraction for better accuracy"
  ],
  "entities": {{
    "companies": ["Apple Inc.", "Microsoft"],
    "executives": ["Tim Cook"],
    "metrics": ["total_compensation", "stock_awards"]
  }},
  "unresolved_questions": [
    "Need to verify CFO compensation data source"
  ],
  "conversation_flow": [
    "User asked about Apple's CIK",
    "Controller provided CIK and suggested extraction",
    "User requested 2023 compensation data",
    "Controller initiated XBRL extraction"
  ]
}}

Provide ONLY the JSON output, no additional text."""

    def __init__(self, llm_client: Optional[Callable] = None):
        """
        Initialize summarizer with LLM client.

        Args:
            llm_client: Async function to call LLM
                       Signature: async def llm_client(messages: List[Dict]) -> str
        """
        self.llm_client = llm_client

    async def summarize_exchanges(
        self, exchanges: List[Dict[str, Any]], preserve_recent: int = 10
    ) -> Dict[str, Any]:
        """
        Summarize conversation exchanges into compact format.

        Args:
            exchanges: List of conversation exchanges to summarize
            preserve_recent: Number of recent exchanges to keep verbatim

        Returns:
            Summary dict with key facts, entities, and conversation flow

        Error Handling:
            - LLM call fails: Returns fallback rule-based summary
            - JSON parse fails: Returns minimal summary
            - Empty exchanges: Returns empty summary

        Example:
            summary = await summarizer.summarize_exchanges(
                exchanges=history,
                preserve_recent=10
            )
        """
        if not exchanges:
            return self._empty_summary()

        if len(exchanges) <= preserve_recent:
            # No summarization needed
            return {
                "summary": "Recent conversation only, no summarization needed",
                "key_facts": [],
                "decisions_made": [],
                "entities": {},
                "unresolved_questions": [],
                "conversation_flow": [],
                "exchanges_to_summarize": 0,
            }

        # Separate exchanges to summarize vs keep
        to_summarize = (
            exchanges[:-preserve_recent] if preserve_recent > 0 else exchanges
        )

        logger.info(
            "Starting conversation summarization",
            total_exchanges=len(exchanges),
            to_summarize=len(to_summarize),
            preserve_recent=preserve_recent,
        )

        if not self.llm_client:
            logger.warning("LLM client not available, using fallback summarization")
            return self._fallback_summarization(to_summarize)

        # Build summarization prompt
        exchanges_json = json.dumps(to_summarize, indent=2, default=str)

        prompt = self.SUMMARIZATION_PROMPT.format(
            num_exchanges=len(to_summarize), exchanges_json=exchanges_json
        )

        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert at summarizing conversations while preserving critical context. Always output valid JSON.",
                },
                {"role": "user", "content": prompt},
            ]

            response = await self.llm_client(messages)

            # Parse JSON response
            summary = self._parse_json_response(response)
            summary["exchanges_to_summarize"] = len(to_summarize)

            logger.info(
                "Conversation summarization complete",
                exchanges_summarized=len(to_summarize),
                key_facts=len(summary.get("key_facts", [])),
                entities_companies=len(
                    summary.get("entities", {}).get("companies", [])
                ),
            )

            return summary

        except Exception as e:
            logger.error("Summarization failed, using fallback", error=str(e))
            return self._fallback_summarization(to_summarize)

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        Parse JSON from LLM response.

        Handles:
        - Markdown code blocks (```json...```)
        - Extra whitespace
        - Text before/after JSON

        Args:
            response: Raw LLM response

        Returns:
            Parsed JSON dict

        Raises:
            json.JSONDecodeError: If JSON parsing fails
        """
        # Remove markdown formatting
        if "```json" in response:
            # Extract JSON from markdown code block
            start = response.find("```json") + 7
            end = response.find("```", start)
            if end > start:
                response = response[start:end]
        elif "```" in response:
            # Generic code block
            start = response.find("```") + 3
            end = response.find("```", start)
            if end > start:
                response = response[start:end]

        # Find JSON boundaries
        json_start = response.find("{")
        json_end = response.rfind("}") + 1

        if json_start >= 0 and json_end > json_start:
            json_content = response[json_start:json_end]
            return json.loads(json_content)
        else:
            # Try parsing entire response
            return json.loads(response.strip())

    def _fallback_summarization(
        self, exchanges: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Simple rule-based summarization fallback.

        Used when LLM summarization fails or is unavailable.

        Args:
            exchanges: Exchanges to summarize

        Returns:
            Basic summary with limited information
        """
        logger.info("Using fallback summarization", exchanges=len(exchanges))

        # Extract basic information
        conversation_flow = []
        for i, exchange in enumerate(exchanges[:5]):  # First 5 only
            user_input = exchange.get("user_input", "")[:50]
            conversation_flow.append(f"{i+1}. {user_input}...")

        return {
            "summary": f"Summarized {len(exchanges)} exchanges (LLM summarization unavailable)",
            "key_facts": [],
            "decisions_made": [],
            "entities": {"companies": [], "executives": [], "metrics": []},
            "unresolved_questions": [],
            "conversation_flow": conversation_flow,
            "exchanges_to_summarize": len(exchanges),
            "fallback_mode": True,
        }

    def _empty_summary(self) -> Dict[str, Any]:
        """Return empty summary structure."""
        return {
            "summary": "No conversation history to summarize",
            "key_facts": [],
            "decisions_made": [],
            "entities": {},
            "unresolved_questions": [],
            "conversation_flow": [],
            "exchanges_to_summarize": 0,
        }

    def format_summary_for_prompt(self, summary: Dict[str, Any]) -> str:
        """
        Format summary dict into readable prompt section.

        Args:
            summary: Summary dict from summarize_exchanges()

        Returns:
            Formatted string ready for prompt injection

        Example Output:
            CONVERSATION SUMMARY:
            User has been analyzing Apple Inc. (CIK: 0000320193)...

            Key facts established:
            - Apple CIK: 0000320193
            - Focus year: 2023

            Decisions made:
            - Use XBRL extraction

            Entities mentioned:
            - Companies: Apple Inc., Microsoft
        """
        if not summary:
            return ""

        parts = []

        # Main summary
        parts.append("CONVERSATION SUMMARY:")
        parts.append(summary.get("summary", "No summary available"))
        parts.append("")

        # Key facts
        if summary.get("key_facts"):
            parts.append("Key facts established:")
            for fact in summary["key_facts"]:
                parts.append(f"- {fact}")
            parts.append("")

        # Decisions
        if summary.get("decisions_made"):
            parts.append("Decisions made:")
            for decision in summary["decisions_made"]:
                parts.append(f"- {decision}")
            parts.append("")

        # Entities
        entities = summary.get("entities", {})
        if any(entities.values()):
            parts.append("Entities mentioned:")
            for entity_type, entity_list in entities.items():
                if entity_list:
                    parts.append(f"- {entity_type.title()}: {', '.join(entity_list)}")
            parts.append("")

        # Unresolved questions
        if summary.get("unresolved_questions"):
            parts.append("Unresolved questions:")
            for question in summary["unresolved_questions"]:
                parts.append(f"- {question}")
            parts.append("")

        # Add metadata
        if summary.get("fallback_mode"):
            parts.append("(Note: Summary generated using fallback mode)")
            parts.append("")

        return "\n".join(parts)

    def extract_key_facts(self, summary: Dict[str, Any]) -> List[str]:
        """
        Extract key facts from summary for quick reference.

        Args:
            summary: Summary dict

        Returns:
            List of key facts
        """
        return summary.get("key_facts", [])
