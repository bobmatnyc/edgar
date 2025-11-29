# Context Management and Auto-Session Compaction Research

**Research Date**: 2025-11-28
**Research Focus**: Automatic session compaction at 75% context usage for EDGAR chat interface
**Objective**: Prevent hitting token limits while preserving conversation continuity

---

## Executive Summary

**Current State**: SimpleChatbotMemory uses basic sliding window (100 exchanges, last 3 in prompt) with NO token counting or automatic compaction.

**Key Finding**: No existing summarization prompts or token counting in codebase. Simple truncation strategy risks context loss.

**Recommendation**: Implement tiered summarization system with accurate token counting at 75% threshold (recommended: ~150K tokens for 200K context window).

**Risk**: Current approach will hit token limits on long conversations, causing abrupt failures.

---

## 1. Current Memory Management Architecture

### 1.1 SimpleChatbotMemory Implementation

**File**: `/Users/masa/Clients/Zach/projects/edgar/src/cli_chatbot/core/controller.py`

**Key Characteristics**:
- **Storage**: In-memory list of conversation exchanges
- **Capacity**: `max_history = 100` exchanges (configurable)
- **Retention**: Simple sliding window - keeps last 100 exchanges
- **Prompt Context**: Uses last 3 exchanges in conversation prompt (line 517)
- **Token Counting**: **NONE** - no awareness of token usage
- **Compaction**: Basic truncation only (drops oldest when > 100)

**Code Evidence**:
```python
class SimpleChatbotMemory(ConversationMemory):
    """Simple in-memory conversation storage."""

    def __init__(self, max_history: int = 100):
        self.history = []
        self.max_history = max_history

    async def add_exchange(
        self,
        user_input: str,
        controller_response: str,
        context_used: List[ContextInfo],
        scripts_executed: List[ScriptResult],
    ):
        """Add a conversation exchange to memory."""

        exchange = {
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "controller_response": controller_response,
            "context_used": [ctx.source for ctx in context_used],
            "scripts_executed": len(scripts_executed),
            "script_success": all(script.success for script in scripts_executed),
        }

        self.history.append(exchange)

        # Trim history if too long
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
```

**Prompt Building Logic** (line 495-531):
```python
async def _build_conversation_prompt(
    self, user_input: str, context: List[ContextInfo]
) -> str:
    """Build the conversation prompt with dynamic context injection."""

    prompt_parts = []

    # Add self-awareness
    if self._self_awareness:
        prompt_parts.append("CONTROLLER SELF-AWARENESS:")
        prompt_parts.append(self._self_awareness.content)
        prompt_parts.append("")

    # Add application context
    if context:
        prompt_parts.append("RELEVANT APPLICATION CONTEXT:")
        for ctx in context:
            prompt_parts.append(f"**{ctx.source}** ({ctx.content_type}):")
            prompt_parts.append(ctx.content)
            prompt_parts.append("")

    # Add conversation history (ONLY LAST 3 EXCHANGES)
    recent_history = await self.memory.get_conversation_history(limit=3)
    if recent_history:
        prompt_parts.append("RECENT CONVERSATION:")
        for exchange in recent_history:
            prompt_parts.append(f"User: {exchange['user_input']}")
            prompt_parts.append(
                f"Controller: {exchange['controller_response'][:200]}..."
            )
            prompt_parts.append("")

    # Add current user input
    prompt_parts.append("CURRENT USER INPUT:")
    prompt_parts.append(user_input)

    return "\n".join(prompt_parts)
```

**Critical Observations**:
1. **No Token Awareness**: System doesn't know how many tokens are being used
2. **Fixed Window**: Always uses last 3 exchanges regardless of size
3. **Truncation Risk**: Controller responses truncated to 200 chars in history
4. **Context Injection**: Application context can be LARGE (from DynamicContextInjector)
5. **No Summarization**: Old exchanges are simply dropped, not summarized

### 1.2 ConversationMemory Interface

**File**: `/Users/masa/Clients/Zach/projects/edgar/src/cli_chatbot/core/interfaces.py`

**Abstract Interface**:
```python
class ConversationMemory(ABC):
    """Abstract interface for conversation memory management."""

    @abstractmethod
    async def add_exchange(
        self,
        user_input: str,
        controller_response: str,
        context_used: List[ContextInfo],
        scripts_executed: List[ScriptResult]
    ):
        """Add a conversation exchange to memory."""
        pass

    @abstractmethod
    async def get_conversation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation history."""
        pass

    @abstractmethod
    async def search_memory(self, query: str) -> List[Dict[str, Any]]:
        """Search conversation memory for relevant exchanges."""
        pass
```

**Gap Analysis**:
- No `get_token_count()` method
- No `summarize_old_exchanges()` method
- No `compact_memory()` method
- No threshold management interface

---

## 2. Existing Summarization Patterns in Codebase

### 2.1 Search Results

**Searched Locations**:
- `src/cli_chatbot/` - No summarization prompts found
- `src/self_improving_code/` - Found engineer prompts, but NO summarization
- `src/edgar_analyzer/` - Found LLM prompts for financial analysis

**Finding**: **NO existing conversation summarization prompts in codebase.**

### 2.2 Similar LLM Prompt Patterns

**Found in**: `/Users/masa/Clients/Zach/projects/edgar/src/self_improving_code/llm/engineer.py`

**Pattern**: Structured prompts with JSON responses for code analysis
```python
prompt = f"""You are the ENGINEER in a self-improving code system.

TASK: [Clear task description]

CONSTRAINTS:
1. Make minimal, focused changes
2. Preserve existing functionality
3. Follow best practices

OUTPUT (JSON only):
{{
  "changes_made": true,
  "summary": "Brief description",
  "details": [...]
}}
```

**Application to Summarization**: Can use similar structured approach for conversation summarization.

---

## 3. Token Counting Analysis

### 3.1 Current State

**Dependencies Checked**: `pyproject.toml`
- **tiktoken**: **NOT INSTALLED**
- **openai**: Installed (AsyncOpenAI client)
- No token counting utilities detected

### 3.2 Token Counting Options

**Option 1: tiktoken (Recommended)**
```python
import tiktoken

def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Count tokens using tiktoken encoder."""
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))
```

**Pros**:
- Accurate token counting for OpenAI/Anthropic models
- Fast and efficient
- Industry standard

**Cons**:
- Requires additional dependency (`tiktoken`)
- Model-specific encodings (though "cl100k_base" works for most modern models)

**Option 2: Character-based Approximation**
```python
def estimate_tokens(text: str) -> int:
    """Estimate tokens using character count (rough approximation)."""
    # Average: 1 token ≈ 4 characters for English text
    return len(text) // 4
```

**Pros**:
- No dependencies
- Fast
- Good enough for threshold detection

**Cons**:
- Inaccurate (can be off by 20-30%)
- Unsafe for hard limits

**Option 3: OpenAI/OpenRouter API Token Counting**
```python
# OpenRouter returns token usage in response metadata
response = await client.chat.completions.create(...)
tokens_used = response.usage.total_tokens
```

**Pros**:
- Exact count from API
- No additional dependencies

**Cons**:
- Only available AFTER API call
- Can't prevent overruns proactively

**Recommendation**: **Use tiktoken for proactive monitoring** with character-based fallback for quick estimates.

---

## 4. Best Practices for Conversation Summarization

### 4.1 Industry Standard Approaches

**Strategy 1: Rolling Summarization (Recommended)**
- Keep recent N messages in full
- Summarize older messages into compact format
- Preserve important facts and context

**Strategy 2: Hierarchical Summarization**
- Keep last N exchanges verbatim
- Summarize N-2N exchanges into bullet points
- Ultra-compress 2N+ exchanges into single summary

**Strategy 3: Semantic Compression**
- Extract key facts, entities, decisions from old messages
- Store as structured knowledge base
- Reconstruct context on demand

**Benchmark: Anthropic's Approach**
- Claude 3.5 Sonnet has 200K context window
- Recommended: Compact at 75% (150K tokens)
- Keep last 10-20 messages verbatim
- Summarize rest into "conversation summary" section

### 4.2 What to Preserve vs. Summarize

**Always Preserve**:
1. **Last N exchanges** (5-10 recommended) - full conversation flow
2. **Key decisions** - critical context for future queries
3. **Important facts** - CIK numbers, company names, analysis results
4. **Unresolved questions** - things user asked but weren't fully answered
5. **Error context** - if recent issues occurred, keep for debugging

**Safe to Summarize**:
1. **Old exploratory queries** - "what is X", "how does Y work"
2. **Completed tasks** - script executions that finished successfully
3. **Redundant information** - repeated questions/answers
4. **Verbose responses** - long explanations that can be bullet-pointed

**Never Discard**:
1. **Session context** - current task/goal
2. **Active data** - CIK being analyzed, current company
3. **Recent errors** - debugging context

---

## 5. Recommended 75% Threshold Architecture

### 5.1 System Design

**Components**:
```
ChatbotController
    ├── SimpleChatbotMemory (current)
    │   ├── Add: get_token_count() method
    │   ├── Add: should_compact() method
    │   └── Add: compact_memory() method
    │
    ├── ConversationSummarizer (NEW)
    │   ├── summarize_exchanges() - LLM-based summarization
    │   ├── extract_key_facts() - entity/fact extraction
    │   └── generate_compact_summary() - create summary prompt
    │
    └── TokenCounter (NEW)
        ├── count_prompt_tokens() - estimate current usage
        ├── count_exchange_tokens() - measure exchange size
        └── is_threshold_reached() - check 75% threshold
```

### 5.2 Compaction Workflow

```
User Input
    ↓
Check Token Usage
    ↓
[Token Count > 75%?] → NO → Process Normally
    ↓ YES
    ↓
Trigger Compaction
    ↓
1. Keep last 10 exchanges verbatim
2. Summarize exchanges 11-50 → bullet points
3. Extract facts from exchanges 51+ → knowledge base
    ↓
Generate Summary Prompt Section
    ↓
Build New Prompt with:
    - Conversation Summary (compact)
    - Recent Exchanges (full)
    - Current Input
    ↓
Process Request
    ↓
Save Updated Memory
```

### 5.3 Token Threshold Calculation

**Target Context Window**: 200,000 tokens (Sonnet 4.5)
**Compaction Threshold**: 75% = 150,000 tokens
**Safety Buffer**: 25% = 50,000 tokens for response

**Prompt Breakdown** (estimated):
- System Prompt: ~500 tokens
- Self-Awareness Context: ~1,000 tokens
- Application Context: ~5,000 tokens (varies)
- Conversation Summary: ~3,000 tokens (after compaction)
- Recent Exchanges (10): ~10,000 tokens (1K per exchange avg)
- Current Input: ~500 tokens

**Total**: ~20,000 tokens (well within 150K threshold)

**Monitor**:
```python
def check_token_usage(self) -> Dict[str, int]:
    """Check current token usage breakdown."""
    return {
        "system_prompt": count_tokens(self.personality.get_system_prompt()),
        "self_awareness": count_tokens(self._self_awareness.content),
        "application_context": sum(count_tokens(ctx.content) for ctx in context),
        "conversation_history": self._count_history_tokens(),
        "total": total_tokens,
        "threshold": 150000,
        "usage_percent": (total_tokens / 200000) * 100
    }
```

---

## 6. Proposed Summarization Prompt Template

### 6.1 Conversation Summarizer Prompt

```python
SUMMARIZATION_PROMPT = """You are a conversation summarization expert specializing in preserving critical context while compacting conversation history.

TASK: Summarize the following conversation exchanges into a compact format that preserves essential information.

CONVERSATION EXCHANGES:
{exchanges_json}

SUMMARIZATION GUIDELINES:
1. **Preserve Facts**: Keep all factual information (CIK numbers, company names, dates, analysis results)
2. **Preserve Decisions**: Document any decisions made or actions taken
3. **Compress Verbosity**: Convert long explanations into bullet points
4. **Extract Entities**: List key entities mentioned (companies, people, metrics)
5. **Maintain Chronology**: Keep rough timeline of conversation flow
6. **Flag Unresolved**: Note any questions that weren't fully answered

OUTPUT FORMAT (JSON):
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
  ],
  "token_savings": 85.5  # percentage of tokens saved
}}

Provide ONLY the JSON output, no additional text."""
```

### 6.2 Compact Prompt Integration

**Before Compaction**:
```
CONTROLLER SELF-AWARENESS:
[1000 tokens]

RELEVANT APPLICATION CONTEXT:
[5000 tokens]

RECENT CONVERSATION:
User: What is Apple's CIK?
Controller: Apple Inc. (AAPL) has CIK 0000320193. This is the unique...
[Full verbatim for last 20 exchanges = 25,000 tokens]

CURRENT USER INPUT:
Extract 2023 compensation data
```

**After Compaction (75% threshold hit)**:
```
CONTROLLER SELF-AWARENESS:
[1000 tokens]

RELEVANT APPLICATION CONTEXT:
[5000 tokens]

CONVERSATION SUMMARY:
User has been analyzing Apple Inc. (CIK: 0000320193) executive compensation.
Key facts established:
- Apple CIK: 0000320193
- Focus year: 2023
- Extraction method: XBRL (for better accuracy)
- Target: CEO and CFO compensation data

Recent actions:
- Retrieved Apple company information
- Discussed XBRL vs HTML parsing approaches
- Decided on XBRL extraction for 2x success rate

Entities: Apple Inc., Tim Cook (CEO), Luca Maestri (CFO)
Unresolved: Need to verify CFO data source
[~2000 tokens instead of 25,000]

RECENT EXCHANGES (last 5):
User: Show me the XBRL concepts for compensation
Controller: Here are the key XBRL concepts: us-gaap:...
[5000 tokens verbatim for continuity]

CURRENT USER INPUT:
Extract 2023 compensation data
```

**Token Savings**: 25,000 → 7,000 = **72% reduction** in conversation history

---

## 7. Implementation Plan

### 7.1 Phase 1: Add Token Counting (Week 1)

**Tasks**:
1. Add `tiktoken` to dependencies
2. Create `TokenCounter` utility class
3. Add `get_token_count()` to SimpleChatbotMemory
4. Add token usage monitoring to controller

**Files to Modify**:
- `pyproject.toml` - add tiktoken dependency
- `src/cli_chatbot/utils/token_counter.py` - NEW file
- `src/cli_chatbot/core/controller.py` - add token counting

**Acceptance Criteria**:
- [ ] Can accurately count tokens in conversation history
- [ ] Controller logs token usage after each exchange
- [ ] Token count visible in `/context` command

### 7.2 Phase 2: Implement Summarization (Week 2)

**Tasks**:
1. Create `ConversationSummarizer` class
2. Implement summarization prompt
3. Add `compact_memory()` to SimpleChatbotMemory
4. Test summarization quality

**Files to Create**:
- `src/cli_chatbot/utils/summarizer.py` - NEW file

**Files to Modify**:
- `src/cli_chatbot/core/controller.py` - integrate summarizer
- `src/cli_chatbot/core/interfaces.py` - add summarization methods

**Acceptance Criteria**:
- [ ] Summarizer produces accurate, compact summaries
- [ ] Key facts and decisions preserved
- [ ] Token reduction >60% for old exchanges

### 7.3 Phase 3: Integrate 75% Threshold (Week 3)

**Tasks**:
1. Add threshold checking to prompt building
2. Trigger compaction at 75% usage
3. Add user notification when compaction occurs
4. Add configuration for threshold percentage

**Files to Modify**:
- `src/cli_chatbot/core/controller.py` - add threshold logic
- `src/cli_chatbot/core/controller.py` - update `_build_conversation_prompt()`

**Acceptance Criteria**:
- [ ] Compaction triggers automatically at 75% (150K tokens)
- [ ] User informed when compaction occurs
- [ ] No context loss in user experience
- [ ] System never hits 100% token limit

### 7.4 Phase 4: Testing & Validation (Week 4)

**Tasks**:
1. Create long conversation test scenarios
2. Measure token usage and summarization quality
3. Test with different LLM models (Grok, Claude, GPT-4)
4. Performance benchmarking

**Test Scenarios**:
- 50-exchange conversation → should compact
- Mixed queries (exploration + analysis)
- Repeated questions (test deduplication)
- Multi-session continuity

**Files to Create**:
- `tests/integration/test_memory_compaction.py` - NEW file
- `tests/unit/test_token_counter.py` - NEW file
- `tests/unit/test_summarizer.py` - NEW file

**Acceptance Criteria**:
- [ ] All tests pass
- [ ] Token usage stays < 80% even in long conversations
- [ ] User satisfaction with context preservation
- [ ] Performance: summarization < 2 seconds

---

## 8. Fallback Strategy

### 8.1 Graceful Degradation

**If Summarization Fails**:
1. Log error
2. Fall back to simple truncation (keep last N exchanges)
3. Notify user: "Conversation history compacted due to length"

**If Token Counting Unavailable**:
1. Use character-based estimation (text_length // 4)
2. Add 20% safety margin to threshold
3. Log warning about inaccurate counting

**If LLM Call for Summarization Fails**:
1. Retry once with exponential backoff
2. Fall back to rule-based summarization (extract entities only)
3. Continue conversation with truncated history

### 8.2 Configuration Options

**Environment Variables**:
```bash
# Context management settings
CHATBOT_MAX_HISTORY=100
CHATBOT_TOKEN_THRESHOLD=150000  # 75% of 200K
CHATBOT_RECENT_EXCHANGES_KEEP=10
CHATBOT_ENABLE_SUMMARIZATION=true
CHATBOT_SUMMARIZATION_MODEL=x-ai/grok-4.1-fast

# Fallback settings
CHATBOT_USE_TIKTOKEN=true
CHATBOT_FALLBACK_TO_CHAR_COUNT=true
```

**User Configuration**:
```python
controller = ChatbotController(
    llm_client=llm_client,
    application_root=root,
    memory=SimpleChatbotMemory(
        max_history=100,
        token_threshold=150000,
        enable_summarization=True
    )
)
```

---

## 9. Risks and Mitigations

### 9.1 Identified Risks

**Risk 1: Information Loss**
- **Impact**: Critical context lost in summarization
- **Probability**: Medium
- **Mitigation**:
  - Test summarization quality extensively
  - Always preserve last N exchanges verbatim
  - Add "important" flag for exchanges user can mark

**Risk 2: Performance Overhead**
- **Impact**: Slow responses due to summarization LLM calls
- **Probability**: Low
- **Mitigation**:
  - Only summarize when threshold hit (infrequent)
  - Use fast model for summarization (Grok 4.1 Fast)
  - Cache summaries, only regenerate when needed

**Risk 3: Token Counting Accuracy**
- **Impact**: Still hit token limits if counting is off
- **Probability**: Low (with tiktoken)
- **Mitigation**:
  - Use tiktoken for accurate counting
  - Add 10% safety buffer to threshold
  - Monitor actual API token usage vs estimates

**Risk 4: Summarization Quality**
- **Impact**: Poor summaries lose context
- **Probability**: Medium
- **Mitigation**:
  - Use high-quality model (Claude Sonnet 4.5 preferred)
  - Test prompts extensively
  - Provide examples in prompt for better output
  - Add validation of summary quality

### 9.2 Success Metrics

**Key Metrics**:
1. **Token Usage**: Keep < 80% of context window
2. **Summarization Ratio**: Achieve >60% token reduction
3. **Context Preservation**: >90% of key facts retained
4. **User Satisfaction**: No complaints about lost context
5. **Performance**: Summarization < 2 seconds
6. **Reliability**: Zero token limit errors in production

---

## 10. Alternative Approaches Considered

### 10.1 Approach A: Fixed Sliding Window (Current)
- **Pro**: Simple, predictable
- **Con**: No token awareness, will fail on long conversations
- **Verdict**: ❌ Inadequate for production use

### 10.2 Approach B: Hard Truncation at Limit
- **Pro**: Prevents errors
- **Con**: Abrupt context loss, poor UX
- **Verdict**: ❌ Better than nothing, but not recommended

### 10.3 Approach C: External Memory Store (Vector DB)
- **Pro**: Semantic search, infinite memory
- **Con**: Complex, requires infrastructure, slow
- **Verdict**: ⚠️ Overkill for current needs, consider for v2.0

### 10.4 Approach D: LLM-Based Summarization (Recommended)
- **Pro**: Intelligent compression, preserves context
- **Con**: Requires LLM call, some overhead
- **Verdict**: ✅ Best balance of quality and simplicity

### 10.5 Approach E: Hybrid (Summarization + Vector Store)
- **Pro**: Best of both worlds
- **Con**: Most complex, highest overhead
- **Verdict**: ⚠️ Consider for future if Approach D insufficient

---

## 11. Code Snippets - Proof of Concept

### 11.1 Token Counter Implementation

```python
# src/cli_chatbot/utils/token_counter.py

import tiktoken
from typing import Dict, List, Any

class TokenCounter:
    """Token counting utility for conversation memory management."""

    def __init__(self, model: str = "gpt-4"):
        """Initialize token counter with model-specific encoding."""
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fallback to cl100k_base for unknown models
            self.encoding = tiktoken.get_encoding("cl100k_base")

        self.model = model

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken."""
        return len(self.encoding.encode(text))

    def count_messages_tokens(self, messages: List[Dict[str, str]]) -> int:
        """Count tokens in OpenAI-style message list."""
        total = 0
        for message in messages:
            # Account for message formatting overhead
            total += 4  # <|start|>role<|message|>content<|end|>
            total += self.count_tokens(message.get("content", ""))
        total += 2  # <|start|>assistant<|message|>
        return total

    def count_exchange_tokens(self, exchange: Dict[str, Any]) -> int:
        """Count tokens in a conversation exchange."""
        tokens = 0
        tokens += self.count_tokens(exchange.get("user_input", ""))
        tokens += self.count_tokens(exchange.get("controller_response", ""))
        # Add overhead for formatting
        tokens += 20  # Timestamp, labels, etc.
        return tokens

    def estimate_tokens_fast(self, text: str) -> int:
        """Fast token estimation using character count (fallback)."""
        # Rough approximation: 1 token ≈ 4 characters
        return len(text) // 4
```

### 11.2 Conversation Summarizer Implementation

```python
# src/cli_chatbot/utils/summarizer.py

import json
from typing import Dict, List, Any, Callable
import structlog

logger = structlog.get_logger(__name__)

class ConversationSummarizer:
    """LLM-based conversation summarization for memory compaction."""

    def __init__(self, llm_client: Callable):
        """Initialize summarizer with LLM client."""
        self.llm_client = llm_client

    async def summarize_exchanges(
        self,
        exchanges: List[Dict[str, Any]],
        preserve_recent: int = 10
    ) -> Dict[str, Any]:
        """
        Summarize conversation exchanges into compact format.

        Args:
            exchanges: List of conversation exchanges to summarize
            preserve_recent: Number of recent exchanges to keep verbatim

        Returns:
            Summary dict with key facts, entities, and conversation flow
        """
        if len(exchanges) <= preserve_recent:
            # No summarization needed
            return {
                "summary": "Recent conversation only, no summarization needed",
                "key_facts": [],
                "decisions_made": [],
                "entities": {},
                "unresolved_questions": [],
                "conversation_flow": [],
                "exchanges_to_summarize": 0
            }

        # Separate exchanges to summarize vs keep
        to_summarize = exchanges[:-preserve_recent]

        # Build summarization prompt
        exchanges_json = json.dumps(to_summarize, indent=2)

        prompt = f"""You are a conversation summarization expert specializing in preserving critical context while compacting conversation history.

TASK: Summarize the following conversation exchanges into a compact format that preserves essential information.

CONVERSATION EXCHANGES ({len(to_summarize)} exchanges):
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

        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert at summarizing conversations while preserving critical context. Always output valid JSON."
                },
                {"role": "user", "content": prompt}
            ]

            response = await self.llm_client(messages)

            # Parse JSON response
            summary = self._parse_json_response(response)
            summary["exchanges_to_summarize"] = len(to_summarize)

            logger.info(
                "Conversation summarization complete",
                exchanges_summarized=len(to_summarize),
                key_facts=len(summary.get("key_facts", [])),
                entities=len(summary.get("entities", {}).get("companies", []))
            )

            return summary

        except Exception as e:
            logger.error("Summarization failed", error=str(e))
            # Fallback: basic summarization
            return self._fallback_summarization(to_summarize)

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from LLM response."""
        # Remove markdown formatting
        if response.startswith('```json'):
            response = response[7:]
        if response.endswith('```'):
            response = response[:-3]

        # Extract JSON
        json_start = response.find('{')
        json_end = response.rfind('}') + 1

        if json_start >= 0 and json_end > json_start:
            json_content = response[json_start:json_end]
            return json.loads(json_content)
        else:
            return json.loads(response)

    def _fallback_summarization(self, exchanges: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Simple rule-based summarization fallback."""
        return {
            "summary": f"Summarized {len(exchanges)} exchanges (LLM summarization failed)",
            "key_facts": [],
            "decisions_made": [],
            "entities": {},
            "unresolved_questions": [],
            "conversation_flow": [
                f"{i+1}. {exchange['user_input'][:50]}..."
                for i, exchange in enumerate(exchanges[:5])
            ],
            "exchanges_to_summarize": len(exchanges)
        }

    def format_summary_for_prompt(self, summary: Dict[str, Any]) -> str:
        """Format summary dict into readable prompt section."""
        parts = []

        parts.append("CONVERSATION SUMMARY:")
        parts.append(summary.get("summary", "No summary available"))
        parts.append("")

        if summary.get("key_facts"):
            parts.append("Key facts established:")
            for fact in summary["key_facts"]:
                parts.append(f"- {fact}")
            parts.append("")

        if summary.get("decisions_made"):
            parts.append("Decisions made:")
            for decision in summary["decisions_made"]:
                parts.append(f"- {decision}")
            parts.append("")

        entities = summary.get("entities", {})
        if any(entities.values()):
            parts.append("Entities mentioned:")
            for entity_type, entity_list in entities.items():
                if entity_list:
                    parts.append(f"- {entity_type.title()}: {', '.join(entity_list)}")
            parts.append("")

        if summary.get("unresolved_questions"):
            parts.append("Unresolved questions:")
            for question in summary["unresolved_questions"]:
                parts.append(f"- {question}")
            parts.append("")

        return "\n".join(parts)
```

### 11.3 Enhanced SimpleChatbotMemory with Compaction

```python
# src/cli_chatbot/core/controller.py (modifications)

from ..utils.token_counter import TokenCounter
from ..utils.summarizer import ConversationSummarizer

class SimpleChatbotMemory(ConversationMemory):
    """Simple in-memory conversation storage with token-aware compaction."""

    def __init__(
        self,
        max_history: int = 100,
        token_threshold: int = 150000,
        enable_summarization: bool = True,
        llm_client: Optional[Callable] = None
    ):
        self.history = []
        self.max_history = max_history
        self.token_threshold = token_threshold
        self.enable_summarization = enable_summarization

        # Initialize token counter and summarizer
        self.token_counter = TokenCounter()
        self.summarizer = ConversationSummarizer(llm_client) if llm_client else None

        # Compact summary storage
        self.summary = None
        self.summarized_exchanges_count = 0

    async def add_exchange(
        self,
        user_input: str,
        controller_response: str,
        context_used: List[ContextInfo],
        scripts_executed: List[ScriptResult],
    ):
        """Add exchange and check for compaction."""
        exchange = {
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "controller_response": controller_response,
            "context_used": [ctx.source for ctx in context_used],
            "scripts_executed": len(scripts_executed),
            "script_success": all(script.success for script in scripts_executed),
        }

        self.history.append(exchange)

        # Trim history if too long
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

        # Check if compaction needed
        if self.enable_summarization and self.should_compact():
            await self.compact_memory()

    def get_token_count(self) -> int:
        """Get total token count of conversation history."""
        total = 0

        # Count summary if exists
        if self.summary:
            summary_text = self.summarizer.format_summary_for_prompt(self.summary)
            total += self.token_counter.count_tokens(summary_text)

        # Count individual exchanges
        for exchange in self.history:
            total += self.token_counter.count_exchange_tokens(exchange)

        return total

    def should_compact(self) -> bool:
        """Check if token threshold reached."""
        if not self.enable_summarization:
            return False

        current_tokens = self.get_token_count()
        return current_tokens >= self.token_threshold

    async def compact_memory(self, preserve_recent: int = 10):
        """Compact memory by summarizing old exchanges."""
        if not self.summarizer:
            logger.warning("Summarizer not available, skipping compaction")
            return

        if len(self.history) <= preserve_recent:
            logger.info("Not enough history to compact")
            return

        logger.info(
            "Compacting conversation memory",
            current_exchanges=len(self.history),
            current_tokens=self.get_token_count(),
            threshold=self.token_threshold
        )

        try:
            # Summarize old exchanges
            summary = await self.summarizer.summarize_exchanges(
                self.history,
                preserve_recent=preserve_recent
            )

            # Keep only recent exchanges
            self.history = self.history[-preserve_recent:]

            # Store summary
            self.summary = summary
            self.summarized_exchanges_count += summary.get("exchanges_to_summarize", 0)

            new_token_count = self.get_token_count()
            token_savings = ((self.token_threshold - new_token_count) / self.token_threshold) * 100

            logger.info(
                "Memory compaction complete",
                new_exchanges=len(self.history),
                new_tokens=new_token_count,
                token_savings_percent=round(token_savings, 1),
                total_exchanges_summarized=self.summarized_exchanges_count
            )

        except Exception as e:
            logger.error("Memory compaction failed", error=str(e))
            # Fallback: simple truncation
            self.history = self.history[-preserve_recent:]
```

### 11.4 Modified Prompt Builder with Summary Integration

```python
# src/cli_chatbot/core/controller.py (modifications)

async def _build_conversation_prompt(
    self, user_input: str, context: List[ContextInfo]
) -> str:
    """Build conversation prompt with summary if available."""

    prompt_parts = []

    # Add self-awareness
    if self._self_awareness:
        prompt_parts.append("CONTROLLER SELF-AWARENESS:")
        prompt_parts.append(self._self_awareness.content)
        prompt_parts.append("")

    # Add application context
    if context:
        prompt_parts.append("RELEVANT APPLICATION CONTEXT:")
        for ctx in context:
            prompt_parts.append(f"**{ctx.source}** ({ctx.content_type}):")
            prompt_parts.append(ctx.content)
            prompt_parts.append("")

    # Add conversation summary if available
    if hasattr(self.memory, 'summary') and self.memory.summary:
        summary_text = self.memory.summarizer.format_summary_for_prompt(
            self.memory.summary
        )
        prompt_parts.append(summary_text)
        prompt_parts.append("")

    # Add recent conversation history
    recent_history = await self.memory.get_conversation_history(limit=10)
    if recent_history:
        prompt_parts.append("RECENT EXCHANGES:")
        for exchange in recent_history:
            prompt_parts.append(f"User: {exchange['user_input']}")
            prompt_parts.append(f"Controller: {exchange['controller_response']}")
            prompt_parts.append("")

    # Add current user input
    prompt_parts.append("CURRENT USER INPUT:")
    prompt_parts.append(user_input)

    return "\n".join(prompt_parts)
```

---

## 12. Conclusion

### Summary of Findings

**Current State**: No token counting, no summarization, simple truncation only.

**Recommendation**: Implement tiered summarization system with accurate token counting at 75% threshold (150K tokens for 200K context window).

**Best Approach**: LLM-based summarization with tiktoken for accurate token counting.

**Implementation Effort**: 4 weeks (Token Counter → Summarizer → Integration → Testing)

**Key Benefits**:
- Prevents token limit errors
- Preserves conversation context intelligently
- Scales to very long conversations
- Better user experience (no abrupt context loss)

### Next Steps

1. **Immediate**: Add tiktoken dependency and basic token counting
2. **Short-term**: Implement conversation summarizer with test cases
3. **Medium-term**: Integrate 75% threshold auto-compaction
4. **Long-term**: Monitor and optimize summarization quality

### Files to Create/Modify

**New Files**:
- `src/cli_chatbot/utils/token_counter.py`
- `src/cli_chatbot/utils/summarizer.py`
- `tests/unit/test_token_counter.py`
- `tests/unit/test_summarizer.py`
- `tests/integration/test_memory_compaction.py`

**Modified Files**:
- `pyproject.toml` (add tiktoken)
- `src/cli_chatbot/core/controller.py` (enhance SimpleChatbotMemory)
- `src/cli_chatbot/core/interfaces.py` (add compaction methods)

### Research Complete

**Status**: ✅ Research Complete
**Next Action**: Review with team and approve implementation plan
**Priority**: High (prevents production issues with long conversations)

---

## Appendix: References

**Token Counting**:
- tiktoken documentation: https://github.com/openai/tiktoken
- OpenAI token counting guide: https://platform.openai.com/docs/guides/tokens

**Conversation Management**:
- Anthropic Claude best practices: https://docs.anthropic.com/claude/docs/managing-context
- OpenAI chat completion guide: https://platform.openai.com/docs/guides/chat

**Similar Implementations**:
- LangChain ConversationSummaryMemory: https://python.langchain.com/docs/modules/memory/types/summary
- LlamaIndex memory management: https://docs.llamaindex.ai/en/stable/module_guides/storing/chat_memory/

**EDGAR Project Context**:
- Project structure: `/Users/masa/Clients/Zach/projects/edgar/`
- CLI chatbot code: `src/cli_chatbot/`
- Current memory: SimpleChatbotMemory (100 exchange limit, no compaction)
