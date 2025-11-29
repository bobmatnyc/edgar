# Auto-Compaction: Intelligent Context Management

**Feature**: Automatic session compaction at 75% context usage
**Status**: ✅ Implemented (2025-11-28)
**Research**: [context-management-auto-compaction-2025-11-28.md](../research/context-management-auto-compaction-2025-11-28.md)

---

## Overview

The EDGAR CLI chatbot now includes intelligent auto-compaction that prevents hitting token limits during long conversations while preserving critical context.

### Key Features

- **Automatic triggering** at 75% context usage (150,000 tokens)
- **LLM-based summarization** preserving facts, decisions, and entities
- **Token counting** via tiktoken for accurate monitoring
- **Graceful fallbacks** if summarization fails
- **Transparent operation** with logging for debugging

---

## How It Works

### 1. Token Counting

The system continuously monitors token usage using `tiktoken`:

```python
from cli_chatbot.utils.token_counter import TokenCounter

counter = TokenCounter()
tokens = counter.count_tokens("Your text here")
```

**Accuracy**: Uses model-specific encodings (GPT-4, Claude compatible)
**Fallback**: Character-based estimation if tiktoken unavailable

### 2. Compaction Trigger

When conversation reaches 150,000 tokens (75% of 200K context window):

```
Current tokens: 150,000
Threshold: 150,000
→ Auto-compaction triggered
```

### 3. Summarization Process

**LLM-based intelligent summarization**:

1. Keep last 10 exchanges verbatim
2. Summarize older exchanges into compact format
3. Extract key facts, entities, decisions
4. Merge with existing summary if multiple compactions

**Result**: 60-80% token reduction while preserving context

### 4. Summary Integration

Compacted summary included in future prompts:

```
CONVERSATION SUMMARY:
User has been analyzing Apple Inc. (CIK: 0000320193)...

Key facts established:
- Apple CIK: 0000320193
- Focus year: 2023
- Extraction method: XBRL

RECENT EXCHANGES:
[Last 10 exchanges verbatim]

CURRENT USER INPUT:
[User's current query]
```

---

## Configuration

### Default Settings

```python
SimpleChatbotMemory(
    max_history=100,           # Maximum exchanges to store
    token_threshold=150000,    # 75% of 200K context window
    enable_summarization=True, # Enable auto-compaction
    recent_keep_count=10,      # Exchanges to keep verbatim
    llm_client=llm_client      # Required for summarization
)
```

### Environment Variables

Set in `.env.local`:

```bash
# Context management settings
CHATBOT_MAX_HISTORY=100
CHATBOT_TOKEN_THRESHOLD=150000
CHATBOT_RECENT_EXCHANGES_KEEP=10
CHATBOT_ENABLE_SUMMARIZATION=true
```

### Disable Auto-Compaction

```python
memory = SimpleChatbotMemory(
    enable_summarization=False  # Disable auto-compaction
)
```

---

## Usage Examples

### Check Current Token Usage

Use the `/context` command in the chat interface:

```
You: context

📊 Memory Compaction Stats:
Current exchanges: 25
Current tokens: 45,230
Token threshold: 150,000
Usage: 30.2%
Has summary: ❌
Auto-compaction: ✅
```

### During Compaction

System automatically logs compaction activity:

```
You: [Your query]

🗜️  Context at 75% threshold - triggering auto-compaction...
✅ Compaction complete - context reduced

🤖 Controller: [Response with preserved context]
```

### After Compaction

```
You: context

📊 Memory Compaction Stats:
Current exchanges: 10
Current tokens: 62,150
Token threshold: 150,000
Usage: 41.4%
Has summary: ✅
Summary tokens: 2,500
Total summarized: 15 exchanges
Compactions: 1
Auto-compaction: ✅
```

---

## Summarization Quality

### What Gets Preserved

✅ **Always Preserved**:
- CIK numbers, company names, dates
- Analysis results and metrics
- Decisions made during conversation
- Unresolved questions
- Last 10 exchanges (verbatim)

✅ **Compressed but Preserved**:
- Conversation flow timeline
- Key entities (companies, executives)
- Important context from older exchanges

❌ **Safely Discarded**:
- Verbose explanations
- Redundant information
- Exploratory queries
- Completed task details

### Summarization Prompt

The system uses a specialized prompt to ensure quality:

```
SUMMARIZATION GUIDELINES:
1. Preserve Facts: CIK numbers, company names, dates, results
2. Preserve Decisions: Actions taken, choices made
3. Compress Verbosity: Convert explanations to bullet points
4. Extract Entities: Companies, people, metrics
5. Maintain Chronology: Timeline of conversation flow
6. Flag Unresolved: Questions not fully answered
```

---

## Performance

### Token Reduction

**Typical Results**:
- Before compaction: 150,000 tokens (25 exchanges)
- After compaction: 60,000 tokens (10 recent + summary)
- **Savings**: 60% token reduction

### Latency

**Summarization Speed**:
- LLM call: ~1-2 seconds
- Token counting: <100ms
- Total overhead: ~2 seconds (once per threshold hit)

**User Experience**: Transparent operation, no noticeable delay

---

## Error Handling

### Graceful Fallbacks

**If summarization fails**:
1. Log error
2. Fall back to simple truncation
3. Keep last 10 exchanges
4. Continue conversation without interruption

**If tiktoken unavailable**:
1. Use character-based estimation (1 token ≈ 4 chars)
2. Add 20% safety margin to threshold
3. Log warning about accuracy

**If LLM call fails**:
1. Retry once with exponential backoff
2. Fall back to rule-based summarization
3. Extract basic conversation flow only

### Error Logs

```
2025-11-28 [error] Memory compaction failed error="LLM timeout"
2025-11-28 [info] Fallback truncation applied remaining_exchanges=10
```

---

## Architecture

### Components

```
ChatbotController
├── SimpleChatbotMemory (enhanced)
│   ├── TokenCounter - Accurate token counting
│   ├── ConversationSummarizer - LLM-based summarization
│   ├── get_token_count() - Current usage
│   ├── should_compact() - Threshold check
│   └── compact_memory() - Execute compaction
│
├── process_input() - Auto-compaction trigger
└── _build_conversation_prompt() - Summary integration
```

### Files

**New Files**:
- `src/cli_chatbot/utils/token_counter.py` - Token counting utility
- `src/cli_chatbot/utils/summarizer.py` - Conversation summarizer
- `src/cli_chatbot/utils/__init__.py` - Utils package

**Modified Files**:
- `src/cli_chatbot/core/controller.py` - Enhanced SimpleChatbotMemory
- `pyproject.toml` - Added tiktoken dependency

---

## Testing

### Run Tests

```bash
# Quick verification test
python test_auto_compaction.py

# Full integration test suite
pytest tests/integration/test_memory_compaction.py

# Unit tests
pytest tests/unit/test_token_counter.py
pytest tests/unit/test_summarizer.py
```

### Expected Results

```
✅ TokenCounter working correctly
✅ ConversationSummarizer working correctly
✅ SimpleChatbotMemory auto-compaction working correctly
```

---

## Monitoring

### Log Output

**Normal Operation**:
```
[info] SimpleChatbotMemory initialized with auto-compaction
[info] Current token count: 45,230 / 150,000 (30.2%)
```

**Compaction Triggered**:
```
[info] Context at 75% threshold - triggering auto-compaction
[info] Compacting conversation memory
       current_exchanges=25
       current_tokens=150,000
       threshold=150,000
[info] Conversation summarization complete
       exchanges_summarized=15
       key_facts=12
[info] Memory compaction complete
       new_exchanges=10
       new_tokens=62,150
       token_savings=87,850
       savings_percent=58.6%
```

### Metrics

Track in production:
- Token usage percentage over time
- Compaction frequency
- Token savings per compaction
- Summarization success rate
- Context preservation quality

---

## Best Practices

### For Users

1. **Monitor token usage**: Use `/context` command periodically
2. **Trust the system**: Auto-compaction is transparent
3. **Report issues**: If context seems lost, report conversation ID
4. **Long sessions**: System handles arbitrarily long conversations

### For Developers

1. **Respect thresholds**: Don't disable auto-compaction in production
2. **Test summarization**: Verify prompt changes don't break summarization
3. **Monitor logs**: Watch for compaction failures or excessive triggers
4. **Adjust threshold**: Only if context window changes significantly

---

## Troubleshooting

### Issue: Context Lost After Compaction

**Symptoms**: Important information not available in later exchanges

**Solution**:
1. Check compaction logs for summary content
2. Verify summarization prompt includes all key fact types
3. Consider lowering `recent_keep_count` (keep more verbatim)
4. Report as bug if critical context consistently lost

### Issue: Frequent Compactions

**Symptoms**: Compaction triggered every few exchanges

**Solution**:
1. Check token usage with `/context`
2. Verify threshold is reasonable (should be 150K)
3. Check if exchanges are unusually large
4. Consider reducing verbosity of responses

### Issue: Compaction Fails

**Symptoms**: Error logs showing compaction failures

**Solution**:
1. Check LLM client is available and responding
2. Verify tiktoken is installed (`pip list | grep tiktoken`)
3. Check summarization prompt is valid
4. System falls back gracefully, conversation continues

---

## Future Enhancements

### Planned (v2.0)

- [ ] Vector store integration for semantic search
- [ ] User-marked "important" exchanges
- [ ] Configurable summarization models
- [ ] Multi-tier compaction (summary of summaries)
- [ ] Export conversation with full context

### Under Consideration

- [ ] Manual compaction trigger command
- [ ] Compaction preview before execution
- [ ] Summary quality scoring
- [ ] A/B testing different summarization prompts

---

## References

- **Research Document**: [context-management-auto-compaction-2025-11-28.md](../research/context-management-auto-compaction-2025-11-28.md)
- **tiktoken Documentation**: https://github.com/openai/tiktoken
- **Claude Context Management**: https://docs.anthropic.com/claude/docs/managing-context
- **Implementation PR**: [Link when merged]

---

**Status**: ✅ Production Ready
**Last Updated**: 2025-11-28
**Maintainer**: EDGAR Team
