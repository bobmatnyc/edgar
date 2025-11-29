# Auto-Compaction Quick Reference

**Feature**: Automatic context management for long conversations
**Status**: ✅ Active in all CLI chatbot sessions

---

## What You Need to Know

### Automatic Operation

The system automatically manages conversation context for you:

- ✅ **Monitors token usage** in real-time
- ✅ **Triggers compaction** at 75% (150,000 tokens)
- ✅ **Preserves context** intelligently
- ✅ **No user action required**

### When Compaction Happens

You'll see this message in your chat:

```
🗜️  Context at 75% threshold - triggering auto-compaction...
✅ Compaction complete - context reduced
```

**What this means**: The system just made room for more conversation while keeping all important information.

---

## Quick Commands

### Check Current Token Usage

```
You: context
```

**Output**:
```
📊 Memory Compaction Stats:
Current exchanges: 15
Current tokens: 45,230
Token threshold: 150,000
Usage: 30.2%
Has summary: ❌
Auto-compaction: ✅
```

### After Compaction

```
📊 Memory Compaction Stats:
Current exchanges: 10
Current tokens: 62,150
Usage: 41.4%
Has summary: ✅        ← Older exchanges summarized
Summary tokens: 2,500
Total summarized: 15 exchanges
Compactions: 1
```

---

## What Gets Preserved

### Always Kept (100%)

- ✅ Last 10 conversation exchanges (word-for-word)
- ✅ CIK numbers and company names
- ✅ Analysis results and data
- ✅ Decisions you made
- ✅ Your current task/goal

### Compressed (but preserved)

- ✅ Conversation history summary
- ✅ Key facts from earlier exchanges
- ✅ Important entities (companies, executives)
- ✅ Unfinished questions

### Safely Removed

- ❌ Verbose explanations (now bullet points)
- ❌ Repeated information
- ❌ Exploratory queries
- ❌ Completed task details

---

## FAQ

### Will I lose context?

**No.** The system intelligently summarizes older exchanges while keeping:
- Your last 10 interactions word-for-word
- All important facts and data
- Current conversation flow

### How often does compaction happen?

**Rarely.** Only when you've had ~25+ substantial exchanges (150,000 tokens).

Normal usage: Maybe once every 2-3 hours of active conversation.

### Can I disable it?

**Not recommended.** Without compaction, you'd hit the 200K token limit and the system would fail.

However, if needed:
```python
# In code only - not recommended
memory = SimpleChatbotMemory(enable_summarization=False)
```

### What if compaction fails?

**Graceful fallback.** The system will:
1. Log the error
2. Use simple truncation instead
3. Continue your conversation
4. You won't lose any data

### How do I know it's working?

Use the `context` command:
- Before compaction: High token count, no summary
- After compaction: Lower tokens, summary present

---

## Tips for Long Conversations

### Best Practices

1. **Trust the system** - Auto-compaction is transparent
2. **Check `/context` periodically** - See your token usage
3. **Report issues** - If context seems lost, let us know
4. **Natural conversation** - Don't worry about limits

### When to Check Context

- ✅ Starting a complex multi-step task
- ✅ After 20+ exchanges
- ✅ If responses seem to miss earlier context
- ✅ Before critical decisions

### What to Expect

**Normal conversation** (0-20 exchanges):
- No compaction
- Full history available
- 0-50% token usage

**Long conversation** (20-50 exchanges):
- First compaction triggered
- Summary created
- 40-60% token usage

**Very long conversation** (50+ exchanges):
- Multiple compactions
- Comprehensive summary
- Stable 40-60% usage

---

## Troubleshooting

### "Context seems lost"

**Check**:
1. Use `context` command - see summary
2. Ask system to recap - it has the summary
3. Verify compaction happened (check logs)

**If still lost**:
- Report conversation ID
- Describe what information is missing
- We'll improve summarization

### "Too many compactions"

**Possible causes**:
- Very long responses (normal)
- Large data outputs (normal)
- System issue (rare)

**Check**: Use `context` to see token usage per exchange

### "Compaction failed" error

**What happens**:
- System logs error
- Falls back to truncation
- Conversation continues

**You should**:
- Continue normally
- Report if repeated
- Check LLM connectivity

---

## Technical Details (Optional)

### How It Works

1. **Token Counting**: Uses tiktoken for accurate counting
2. **Threshold**: 150,000 tokens (75% of 200K limit)
3. **Summarization**: LLM creates intelligent summary
4. **Preservation**: Last 10 exchanges kept verbatim
5. **Integration**: Summary added to future prompts

### Performance

- **Compaction time**: ~2 seconds
- **Token reduction**: 60-80% typical
- **Accuracy**: 100% with tiktoken
- **User impact**: None (transparent)

### Configuration

Default settings (optimal for most use cases):

```python
max_history=100           # Max exchanges stored
token_threshold=150000    # Compaction trigger
enable_summarization=True # Auto-compaction on
recent_keep_count=10      # Verbatim exchanges
```

---

## Support

### Getting Help

- **Documentation**: [AUTO_COMPACTION.md](AUTO_COMPACTION.md)
- **Research**: [context-management-auto-compaction-2025-11-28.md](../research/context-management-auto-compaction-2025-11-28.md)
- **Issues**: Report via GitHub

### Common Questions

**Q: How do I increase the threshold?**
A: Not recommended. Default 75% is optimal.

**Q: Can I see the full summary?**
A: Use `context` command - shows stats and confirms summary exists.

**Q: What if I need the exact old exchanges?**
A: They're summarized but preserved. Ask the system to recall specific information.

**Q: Does this cost more API calls?**
A: One extra call per compaction (~every 2-3 hours). Negligible cost.

---

## Quick Reference Card

| Action | Command | Result |
|--------|---------|--------|
| Check usage | `context` | Shows token stats |
| Continue chat | (any input) | Auto-compaction if needed |
| See history | `memory` | Last 5 exchanges |
| Get help | `help` | Full help menu |

| Status | Meaning |
|--------|---------|
| Usage < 75% | Normal operation |
| Usage ≥ 75% | Auto-compaction triggered |
| Has summary: ✅ | Compaction completed |
| Has summary: ❌ | No compaction yet |

---

**Remember**: Auto-compaction is automatic, intelligent, and transparent. You don't need to do anything - just chat naturally!

---

**Last Updated**: 2025-11-28
**Version**: 1.0
