# 💾 Session History

This directory contains saved interactive chat sessions from the EDGAR Platform.

## 📋 Overview

When using the interactive chat mode, you can save your session to resume work later. Sessions are stored here as markdown files with conversation history and context.

## 🎯 Session Management

### Saving a Session

In interactive chat mode:
```bash
edgar> save my_session_name
✅ Session saved: my_session_name
```

Or save without a name (auto-generated):
```bash
edgar> save
✅ Session saved: session-2025-12-07-143022
```

### Resuming a Session

Resume the last session:
```bash
edgar --resume last
# or
edgar chat --resume last
```

Resume a specific session:
```bash
edgar --resume my_session_name
# or
edgar chat --resume my_session_name
```

### Listing Sessions

List all saved sessions:
```bash
edgar chat --list-sessions
```

## 📁 Session Files

Session files are named:
```
session-{name}-{timestamp}.md
# or
{custom-name}-{timestamp}.md
```

Each session file contains:
- Session metadata (timestamp, project, etc.)
- Conversation history
- Analysis results
- Generated code
- Confidence threshold settings

## 🔧 Session File Format

Session files are markdown documents with the following structure:

```markdown
# Session: {name}

**Created**: {timestamp}
**Project**: {project_path}
**Confidence Threshold**: {threshold}

## Conversation History

### User
{user message}

### Assistant
{assistant response}

...

## Analysis Results

{analysis output}

## Generated Code

{code output}
```

## 📞 Related Documentation

- **[Interactive Chat Mode](../user/INTERACTIVE_CHAT_MODE.md)** - Learn about the chat interface
- **[Quick Start Guide](../user/QUICK_START.md)** - Get started with the platform

---

**Quick Links**: [Main Docs](../README.md) | [User Docs](../user/README.md)

