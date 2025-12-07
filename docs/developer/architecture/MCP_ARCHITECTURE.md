# MCP Architecture for Extract & Transform Platform

**Version**: 1.0.0
**Status**: Design Phase
**Last Updated**: 2025-12-04

---

## Executive Summary

This document proposes a three-tier Model Context Protocol (MCP) architecture to transform the Extract & Transform Platform into a universally accessible system. The architecture exposes all CLI capabilities as MCP tools, enabling both conversational interfaces and external integrations while maintaining the CLI as the primary user interface.

### Key Design Principles

1. **CLI-First**: Existing CLI commands remain the primary interface - no changes to current workflows
2. **MCP as Universal Interface**: MCP server wraps CLI functionality, exposing it as tools for AI agents and external apps
3. **Minimal Code Changes**: Leverage existing service layer with thin MCP adapter
4. **Progressive Enhancement**: Deploy incrementally - start with core tools, expand gradually

### Success Metrics

- ✅ **All CLI commands** available as MCP tools
- ✅ **Chat interface** can execute full project workflow via MCP
- ✅ **External apps** can integrate via HTTP/SSE MCP endpoint
- ✅ **Zero breaking changes** to existing CLI or service layer
- ✅ **< 2000 LOC** for complete MCP implementation

---

## Three-Tier Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Tier 1: MCP Server                    │
│                    Universal Interface Layer                  │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   stdio      │  │  HTTP/SSE    │  │  WebSocket   │      │
│  │  Transport   │  │  Transport   │  │  Transport   │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                            │                                 │
│         ┌──────────────────┴──────────────────┐              │
│         │    MCP Protocol Handler              │              │
│         │  (Tools, Resources, Prompts)         │              │
│         └──────────────────┬──────────────────┘              │
│                            │                                 │
│         ┌──────────────────┴──────────────────┐              │
│         │      CLI Command Adapter             │              │
│         │  (Maps MCP calls → CLI functions)    │              │
│         └──────────────────┬──────────────────┘              │
└────────────────────────────┼──────────────────────────────────┘
                             │
┌────────────────────────────┼──────────────────────────────────┐
│                        Tier 2: CLI Layer                      │
│                     Command Interface                         │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           Click Command Handlers                      │   │
│  │  • project create/list/validate/delete                │   │
│  │  • analyze-project                                    │   │
│  │  • generate-code                                      │   │
│  │  • run-extraction                                     │   │
│  │  • setup (test, init, configure)                      │   │
│  └────────────────────┬─────────────────────────────────┘   │
└─────────────────────────┼──────────────────────────────────────┘
                          │
┌─────────────────────────┼──────────────────────────────────────┐
│                     Tier 3: Service Layer                      │
│                   Business Logic                               │
│                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐   │
│  │ ProjectManager │  │ CodeGenerator  │  │SchemaAnalyzer│   │
│  │ (CRUD ops)     │  │ (AI code gen)  │  │(Pattern det.)│   │
│  └────────────────┘  └────────────────┘  └──────────────┘   │
│                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐   │
│  │  Data Sources  │  │ ExampleParser  │  │ Validators   │   │
│  │ (Excel/PDF/API)│  │ (Transform)    │  │              │   │
│  └────────────────┘  └────────────────┘  └──────────────┘   │
└───────────────────────────────────────────────────────────────┘
```

### Client Interaction Flows

#### Flow 1: Chat Interface via MCP (stdio)
```
User Input → Chat UI → MCP Client (stdio) → MCP Server → CLI Adapter
→ ProjectManager.create_project() → Response → MCP Client → Chat UI
```

#### Flow 2: External App via MCP (HTTP/SSE)
```
External App → HTTP Request → MCP Server → CLI Adapter
→ Service Layer → Response → HTTP Response → External App
```

#### Flow 3: Direct CLI (unchanged)
```
User Input → CLI Command → Service Layer → Response → Terminal Output
```

---

## Tier 1: MCP Server Layer

### Location
```
src/extract_transform_platform/mcp/
├── __init__.py
├── server.py              # FastMCP server implementation
├── transports/            # Transport protocol handlers
│   ├── stdio_transport.py # For chat interfaces
│   ├── http_transport.py  # For external apps
│   └── ws_transport.py    # WebSocket support (future)
├── tools/                 # MCP tool definitions
│   ├── __init__.py
│   ├── project_tools.py   # Project management tools
│   ├── analysis_tools.py  # Analysis & generation tools
│   ├── data_tools.py      # Data source tools
│   └── setup_tools.py     # Setup & configuration tools
├── adapters/              # CLI command adapters
│   ├── __init__.py
│   ├── cli_adapter.py     # Base CLI adapter
│   └── command_executor.py # Command execution wrapper
├── auth/                  # Authentication & authorization
│   ├── __init__.py
│   ├── api_key_auth.py    # API key validation
│   └── rate_limiter.py    # Rate limiting
└── config.py              # MCP server configuration
```

### MCP Server Implementation (FastMCP)

```python
# src/extract_transform_platform/mcp/server.py
from fastmcp import FastMCP
from .tools.project_tools import register_project_tools
from .tools.analysis_tools import register_analysis_tools
from .tools.data_tools import register_data_tools
from .tools.setup_tools import register_setup_tools

# Initialize MCP server
mcp = FastMCP("Extract & Transform Platform")

# Register all tool categories
register_project_tools(mcp)
register_analysis_tools(mcp)
register_data_tools(mcp)
register_setup_tools(mcp)

# Run server (stdio by default, HTTP/SSE via --transport flag)
if __name__ == "__main__":
    mcp.run()
```

### Design Decisions

#### Decision 1: Use FastMCP Framework ✅
**Chosen Approach**: FastMCP (high-level abstraction)

**Rationale**:
- Decorator-based tool definition (`@mcp.tool()`)
- Built-in transport handling (stdio, HTTP/SSE)
- Automatic schema generation from type hints
- Active maintenance and community support
- Reduces implementation to ~1500 LOC vs ~4000 LOC with low-level SDK

**Alternative Considered**: Low-level `mcp` Python SDK (rejected - too verbose)

#### Decision 2: CLI Adapter Pattern ✅
**Chosen Approach**: Thin adapter layer that invokes CLI functions directly

**Rationale**:
- Reuses all existing CLI logic (zero duplication)
- Services already isolated behind CLI commands
- Minimal maintenance burden (CLI changes auto-propagate to MCP)
- Preserves Click decorators and argument parsing

**Architecture**:
```python
# MCP Tool → CLI Adapter → CLI Command Function → Service Layer
@mcp.tool()
async def project_create(name: str, template: str = "minimal") -> dict:
    """Create new project from template."""
    return await cli_adapter.invoke_command(
        "project.create",
        name=name,
        template=template
    )
```

#### Decision 3: Transport Protocol Strategy ✅
**Chosen Approach**: Multi-transport with runtime selection

**Protocols Supported**:
- **stdio**: Chat interfaces, local development (default)
- **HTTP/SSE**: External apps, remote access (production)
- **WebSocket**: Real-time updates (future enhancement)

**Configuration**:
```bash
# Chat interface (stdio)
python -m extract_transform_platform.mcp.server

# External HTTP API (port 8000)
python -m extract_transform_platform.mcp.server --transport http --port 8000

# HTTPS with authentication
python -m extract_transform_platform.mcp.server --transport http --port 8000 \
    --cert cert.pem --key key.pem --api-key-file keys.json
```

---

## MCP Tool Inventory

### Project Management Tools (5 tools)

#### 1. `project_create`
**Purpose**: Create new project from template

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "name": {
      "type": "string",
      "description": "Project name (alphanumeric, underscores, hyphens)",
      "pattern": "^[a-zA-Z0-9_-]+$"
    },
    "template": {
      "type": "string",
      "enum": ["weather", "news_scraper", "minimal"],
      "default": "minimal",
      "description": "Project template to use"
    },
    "description": {
      "type": "string",
      "description": "Optional project description"
    },
    "output_dir": {
      "type": "string",
      "description": "Custom output directory (defaults to $EDGAR_ARTIFACTS_DIR/projects)"
    }
  },
  "required": ["name"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "status": {"type": "string", "enum": ["success", "error"]},
    "project_name": {"type": "string"},
    "project_path": {"type": "string"},
    "message": {"type": "string"},
    "metadata": {
      "type": "object",
      "properties": {
        "template_used": {"type": "string"},
        "directories_created": {"type": "array", "items": {"type": "string"}},
        "files_created": {"type": "array", "items": {"type": "string"}}
      }
    }
  }
}
```

**CLI Mapping**: `edgar-analyzer project create <name> --template <template>`

---

#### 2. `project_list`
**Purpose**: List all projects

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "format": {
      "type": "string",
      "enum": ["table", "tree", "json"],
      "default": "json",
      "description": "Output format (json recommended for MCP)"
    },
    "output_dir": {
      "type": "string",
      "description": "Projects directory to list"
    }
  }
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "status": {"type": "string"},
    "projects": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": {"type": "string"},
          "path": {"type": "string"},
          "description": {"type": "string"},
          "version": {"type": "string"},
          "template": {"type": "string"},
          "is_valid": {"type": "boolean"},
          "created_at": {"type": "string", "format": "date-time"},
          "modified_at": {"type": "string", "format": "date-time"}
        }
      }
    },
    "count": {"type": "integer"}
  }
}
```

**CLI Mapping**: `edgar-analyzer project list --format json`

---

#### 3. `project_validate`
**Purpose**: Validate project configuration and structure

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "name": {
      "type": "string",
      "description": "Project name to validate"
    },
    "verbose": {
      "type": "boolean",
      "default": false,
      "description": "Include detailed validation output"
    }
  },
  "required": ["name"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "status": {"type": "string"},
    "project_name": {"type": "string"},
    "is_valid": {"type": "boolean"},
    "errors": {"type": "array", "items": {"type": "string"}},
    "warnings": {"type": "array", "items": {"type": "string"}},
    "recommendations": {"type": "array", "items": {"type": "string"}},
    "checks_performed": {
      "type": "object",
      "properties": {
        "config_syntax": {"type": "boolean"},
        "directory_structure": {"type": "boolean"},
        "example_files": {"type": "boolean"},
        "data_sources": {"type": "boolean"}
      }
    }
  }
}
```

**CLI Mapping**: `edgar-analyzer project validate <name> --verbose`

---

#### 4. `project_delete`
**Purpose**: Delete a project

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "name": {
      "type": "string",
      "description": "Project name to delete"
    },
    "force": {
      "type": "boolean",
      "default": false,
      "description": "Skip confirmation prompt"
    }
  },
  "required": ["name"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "status": {"type": "string"},
    "project_name": {"type": "string"},
    "deleted": {"type": "boolean"},
    "message": {"type": "string"}
  }
}
```

**CLI Mapping**: `edgar-analyzer project delete <name> --force`

---

#### 5. `project_info`
**Purpose**: Get detailed project information

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "name": {
      "type": "string",
      "description": "Project name"
    }
  },
  "required": ["name"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "status": {"type": "string"},
    "project": {
      "type": "object",
      "properties": {
        "name": {"type": "string"},
        "path": {"type": "string"},
        "config": {"type": "object"},
        "statistics": {
          "type": "object",
          "properties": {
            "example_count": {"type": "integer"},
            "source_files": {"type": "integer"},
            "test_files": {"type": "integer"}
          }
        }
      }
    }
  }
}
```

**CLI Mapping**: N/A (uses ProjectManager service directly)

---

### Analysis & Code Generation Tools (3 tools)

#### 6. `analyze_project`
**Purpose**: Analyze examples and detect transformation patterns

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "project_name": {
      "type": "string",
      "description": "Project name to analyze"
    },
    "confidence_threshold": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 1.0,
      "default": 0.8,
      "description": "Minimum confidence for pattern detection"
    }
  },
  "required": ["project_name"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "status": {"type": "string"},
    "project_name": {"type": "string"},
    "analysis": {
      "type": "object",
      "properties": {
        "patterns_found": {"type": "integer"},
        "confidence_avg": {"type": "number"},
        "patterns": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "type": {"type": "string"},
              "confidence": {"type": "number"},
              "source_path": {"type": "string"},
              "target_path": {"type": "string"},
              "transformation": {"type": "string"}
            }
          }
        },
        "schema": {
          "type": "object",
          "properties": {
            "input": {"type": "object"},
            "output": {"type": "object"}
          }
        }
      }
    }
  }
}
```

**CLI Mapping**: `edgar-analyzer analyze-project <project_name>`

---

#### 7. `generate_code`
**Purpose**: Generate extractor code from analysis

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "project_name": {
      "type": "string",
      "description": "Project name"
    },
    "model": {
      "type": "string",
      "enum": ["claude-sonnet-4.5", "gpt-4o", "gpt-4-turbo"],
      "default": "claude-sonnet-4.5",
      "description": "AI model for code generation"
    },
    "dry_run": {
      "type": "boolean",
      "default": false,
      "description": "Preview generated code without writing files"
    }
  },
  "required": ["project_name"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "status": {"type": "string"},
    "project_name": {"type": "string"},
    "generation": {
      "type": "object",
      "properties": {
        "files_generated": {"type": "array", "items": {"type": "string"}},
        "tests_generated": {"type": "array", "items": {"type": "string"}},
        "validation": {
          "type": "object",
          "properties": {
            "syntax_valid": {"type": "boolean"},
            "imports_valid": {"type": "boolean"},
            "interface_compliant": {"type": "boolean"}
          }
        },
        "preview": {
          "type": "string",
          "description": "Generated code preview (if dry_run=true)"
        }
      }
    }
  }
}
```

**CLI Mapping**: `edgar-analyzer generate-code <project_name> --dry-run`

---

#### 8. `run_extraction`
**Purpose**: Execute generated extractor

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "project_name": {
      "type": "string",
      "description": "Project name"
    },
    "input_file": {
      "type": "string",
      "description": "Optional input file path (overrides project config)"
    },
    "output_format": {
      "type": "string",
      "enum": ["json", "csv", "excel", "parquet"],
      "default": "json",
      "description": "Output format"
    }
  },
  "required": ["project_name"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "status": {"type": "string"},
    "project_name": {"type": "string"},
    "extraction": {
      "type": "object",
      "properties": {
        "records_extracted": {"type": "integer"},
        "output_file": {"type": "string"},
        "execution_time_ms": {"type": "number"},
        "errors": {"type": "array", "items": {"type": "string"}},
        "sample_output": {
          "type": "array",
          "description": "First 3 records for preview"
        }
      }
    }
  }
}
```

**CLI Mapping**: `edgar-analyzer run-extraction <project_name>`

---

### Data Source Tools (4 tools)

#### 9. `data_source_test`
**Purpose**: Test data source connectivity

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "source_type": {
      "type": "string",
      "enum": ["api", "file", "excel", "pdf", "jina"],
      "description": "Data source type"
    },
    "config": {
      "type": "object",
      "description": "Data source configuration"
    }
  },
  "required": ["source_type", "config"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "status": {"type": "string"},
    "source_type": {"type": "string"},
    "connection_status": {"type": "string", "enum": ["success", "failed"]},
    "response_time_ms": {"type": "number"},
    "error": {"type": "string"},
    "sample_data": {"type": "object", "description": "First record"}
  }
}
```

**CLI Mapping**: N/A (new functionality)

---

#### 10. `data_source_read`
**Purpose**: Read sample data from source

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "project_name": {
      "type": "string",
      "description": "Project name"
    },
    "limit": {
      "type": "integer",
      "default": 5,
      "minimum": 1,
      "maximum": 100,
      "description": "Maximum records to read"
    }
  },
  "required": ["project_name"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "status": {"type": "string"},
    "project_name": {"type": "string"},
    "records": {"type": "array"},
    "count": {"type": "integer"},
    "schema_detected": {"type": "object"}
  }
}
```

**CLI Mapping**: N/A (new functionality)

---

#### 11. `excel_inspect`
**Purpose**: Inspect Excel file structure

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "file_path": {
      "type": "string",
      "description": "Path to Excel file"
    }
  },
  "required": ["file_path"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "status": {"type": "string"},
    "file_path": {"type": "string"},
    "sheets": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": {"type": "string"},
          "rows": {"type": "integer"},
          "columns": {"type": "integer"},
          "header_row": {"type": "integer"},
          "sample_data": {"type": "array"}
        }
      }
    }
  }
}
```

**CLI Mapping**: N/A (new functionality)

---

#### 12. `pdf_inspect`
**Purpose**: Inspect PDF file structure

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "file_path": {
      "type": "string",
      "description": "Path to PDF file"
    },
    "page_number": {
      "type": "integer",
      "default": 0,
      "description": "Page to inspect (0-indexed)"
    }
  },
  "required": ["file_path"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "status": {"type": "string"},
    "file_path": {"type": "string"},
    "total_pages": {"type": "integer"},
    "page_analysis": {
      "type": "object",
      "properties": {
        "page_number": {"type": "integer"},
        "tables_found": {"type": "integer"},
        "text_blocks": {"type": "integer"},
        "sample_table": {"type": "array"}
      }
    }
  }
}
```

**CLI Mapping**: N/A (new functionality)

---

### Setup & Configuration Tools (3 tools)

#### 13. `setup_test`
**Purpose**: Test API key and configuration

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "api_key": {
      "type": "string",
      "description": "OpenRouter API key to test"
    }
  },
  "required": ["api_key"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "status": {"type": "string"},
    "api_key_valid": {"type": "boolean"},
    "models_available": {"type": "array", "items": {"type": "string"}},
    "credits_remaining": {"type": "number"},
    "error": {"type": "string"}
  }
}
```

**CLI Mapping**: `edgar-analyzer setup test`

---

#### 14. `setup_init`
**Purpose**: Initialize platform configuration

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "api_key": {
      "type": "string",
      "description": "OpenRouter API key"
    },
    "artifacts_dir": {
      "type": "string",
      "description": "External artifacts directory path"
    }
  },
  "required": ["api_key"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "status": {"type": "string"},
    "config_path": {"type": "string"},
    "artifacts_dir": {"type": "string"},
    "message": {"type": "string"}
  }
}
```

**CLI Mapping**: `edgar-analyzer setup init`

---

#### 15. `get_templates`
**Purpose**: List available project templates

**Input Schema**:
```json
{
  "type": "object",
  "properties": {}
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "status": {"type": "string"},
    "templates": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": {"type": "string"},
          "description": {"type": "string"},
          "data_source_type": {"type": "string"},
          "use_cases": {"type": "array", "items": {"type": "string"}}
        }
      }
    }
  }
}
```

**CLI Mapping**: N/A (metadata extraction from templates/)

---

## Tool Summary Table

| Tool ID | Tool Name | Category | CLI Mapping | New Functionality |
|---------|-----------|----------|-------------|-------------------|
| 1 | `project_create` | Project Management | ✅ Direct | No |
| 2 | `project_list` | Project Management | ✅ Direct | No |
| 3 | `project_validate` | Project Management | ✅ Direct | No |
| 4 | `project_delete` | Project Management | ✅ Direct | No |
| 5 | `project_info` | Project Management | ⚡ Service | Yes |
| 6 | `analyze_project` | Analysis | ✅ Direct | No |
| 7 | `generate_code` | Analysis | ✅ Direct | No |
| 8 | `run_extraction` | Analysis | ✅ Direct | No |
| 9 | `data_source_test` | Data Sources | ⚡ Service | Yes |
| 10 | `data_source_read` | Data Sources | ⚡ Service | Yes |
| 11 | `excel_inspect` | Data Sources | ⚡ Service | Yes |
| 12 | `pdf_inspect` | Data Sources | ⚡ Service | Yes |
| 13 | `setup_test` | Setup | ✅ Direct | No |
| 14 | `setup_init` | Setup | ✅ Direct | No |
| 15 | `get_templates` | Setup | ⚡ Service | Yes |

**Legend**:
- ✅ Direct: Maps directly to existing CLI command
- ⚡ Service: Calls service layer directly (no CLI command)

---

## Chat Interface Integration

### Conversational Workflow Engine

The chat interface uses MCP tools to execute multi-step workflows through natural language interactions.

#### Example Conversation Flow

```
User: "Create a weather API project"

Chat Agent:
1. Calls project_create(name="weather_api", template="weather")
2. Checks response status
3. Responds: "✅ Project created at projects/weather_api/.
   The project includes 7 example weather API responses.

   Would you like me to:
   - Analyze the examples to detect patterns?
   - View the project configuration?
   - Add more examples?"

User: "Analyze the examples"

Chat Agent:
1. Calls analyze_project(project_name="weather_api", confidence_threshold=0.8)
2. Parses analysis results
3. Responds: "📊 Analysis complete! Found 12 transformation patterns:

   High confidence patterns (>0.9):
   - Field mapping: temp → temperature_celsius
   - Type conversion: string → float for coordinates
   - Nested access: main.temp → temperature

   Average confidence: 95%

   Ready to generate extraction code?"

User: "Yes, generate code"

Chat Agent:
1. Calls generate_code(project_name="weather_api", model="claude-sonnet-4.5")
2. Waits for completion
3. Calls run_extraction(project_name="weather_api", output_format="json")
4. Responds: "✅ Code generated and tested!

   Generated files:
   - src/weather_api/extractor.py (245 LOC)
   - tests/test_extractor.py (18 tests)

   Test results: 18/18 passed

   Extracted 7 weather records → output/weather_data.json

   Would you like to see the generated code or sample output?"
```

### Context Management

The chat interface maintains conversation context across multiple tool calls:

**Session State**:
```json
{
  "current_project": "weather_api",
  "last_analysis": {
    "patterns_found": 12,
    "confidence_avg": 0.95
  },
  "workflow_stage": "code_generated",
  "user_preferences": {
    "verbose": false,
    "auto_test": true
  }
}
```

**Context Persistence**:
- Store in-memory for session duration
- Serialize to JSON for multi-session workflows
- Reset context when starting new project

### Multi-Step Workflow Patterns

#### Pattern 1: Project Creation & Analysis
```
project_create → project_validate → analyze_project → generate_code
```

#### Pattern 2: Iterative Development
```
analyze_project → review_patterns → add_examples → analyze_project → generate_code
```

#### Pattern 3: Debugging & Refinement
```
run_extraction → review_errors → data_source_test → fix_config → run_extraction
```

---

## External MCP Service

### Deployment Architecture

#### Option A: Standalone MCP Server (Recommended)
```
Docker Container
├── Python 3.11 runtime
├── extract_transform_platform package
├── MCP server (FastMCP)
├── HTTP/SSE transport
└── nginx reverse proxy (HTTPS termination)
```

**Advantages**:
- Isolated environment
- Easy scaling (multiple instances)
- Standard deployment (Docker Compose/Kubernetes)
- Built-in health checks

**Configuration**:
```yaml
# docker-compose.yml
version: '3.8'
services:
  mcp-server:
    build: .
    ports:
      - "8000:8000"
    environment:
      - EDGAR_ARTIFACTS_DIR=/data/artifacts
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - MCP_API_KEYS_FILE=/config/api_keys.json
    volumes:
      - ./data:/data
      - ./config:/config
    command: python -m extract_transform_platform.mcp.server
             --transport http --port 8000 --workers 4
```

#### Option B: Embedded MCP Server
```
Web Application (FastAPI/Flask)
└── MCP server as middleware
    └── Expose MCP tools as REST endpoints
```

**Advantages**:
- Integrate with existing web app
- Share authentication/authorization
- Unified logging and monitoring

**Use Case**: When platform already has web interface

---

### Security Model

#### Authentication

**API Key Authentication** (Primary)
```python
# Header-based API key
Authorization: Bearer mcp_sk_1234567890abcdef

# Query parameter (fallback for webhooks)
GET /mcp/tools?api_key=mcp_sk_1234567890abcdef
```

**API Key Storage**:
```json
{
  "api_keys": [
    {
      "key": "mcp_sk_1234567890abcdef",
      "name": "External App 1",
      "permissions": ["project:create", "project:list", "analyze:*"],
      "rate_limit": "100/hour",
      "created_at": "2025-12-04T10:00:00Z",
      "expires_at": "2026-12-04T10:00:00Z"
    }
  ]
}
```

**Key Generation**:
```bash
# Generate new API key
python -m extract_transform_platform.mcp.auth generate-key \
    --name "External App" \
    --permissions "project:*,analyze:read" \
    --rate-limit "100/hour"

# Output: mcp_sk_1234567890abcdef
```

#### Authorization

**Permission Model**:
- `project:create` - Create projects
- `project:read` - List and view projects
- `project:update` - Modify projects
- `project:delete` - Delete projects
- `analyze:*` - All analysis operations
- `data_source:test` - Test data sources
- `setup:*` - Configuration management

**Permission Enforcement**:
```python
@mcp.tool()
@require_permission("project:create")
async def project_create(name: str, template: str) -> dict:
    # Only executes if API key has permission
    ...
```

#### Rate Limiting

**Strategy**: Token bucket algorithm

**Configuration**:
```python
# Per-API-key limits
rate_limits = {
    "default": "100/hour",      # 100 requests per hour
    "premium": "1000/hour",     # Premium tier
    "development": "10/minute"  # Development/testing
}

# Per-tool limits (burst protection)
tool_limits = {
    "generate_code": "5/minute",      # AI-intensive
    "run_extraction": "20/minute",    # Resource-intensive
    "project_list": "100/minute"      # Lightweight
}
```

**Rate Limit Response**:
```json
{
  "error": {
    "code": "rate_limit_exceeded",
    "message": "Rate limit exceeded: 100 requests per hour",
    "retry_after": 3600,
    "rate_limit": {
      "limit": 100,
      "remaining": 0,
      "reset": "2025-12-04T11:00:00Z"
    }
  }
}
```

#### Project Isolation (Multi-Tenancy)

**Strategy**: Directory-based isolation per API key

**Architecture**:
```
$EDGAR_ARTIFACTS_DIR/
├── tenants/
│   ├── api_key_1_hash/       # Isolated tenant directory
│   │   ├── projects/         # Tenant's projects
│   │   ├── output/           # Tenant's output files
│   │   └── data/             # Tenant's data cache
│   └── api_key_2_hash/
│       └── ...
```

**Enforcement**:
```python
class TenantContext:
    """Inject tenant-specific paths into all operations."""

    def __init__(self, api_key: str):
        self.tenant_id = hashlib.sha256(api_key.encode()).hexdigest()[:16]
        self.base_dir = Path(os.getenv("EDGAR_ARTIFACTS_DIR")) / "tenants" / self.tenant_id

    def get_projects_dir(self) -> Path:
        return self.base_dir / "projects"

    def get_output_dir(self) -> Path:
        return self.base_dir / "output"
```

#### Audit Logging

**Log Format** (JSON):
```json
{
  "timestamp": "2025-12-04T10:30:45Z",
  "api_key_name": "External App 1",
  "tool": "project_create",
  "parameters": {"name": "weather_api", "template": "weather"},
  "result": "success",
  "execution_time_ms": 245,
  "ip_address": "203.0.113.42",
  "user_agent": "mcp-client/1.0.0"
}
```

**Audit Queries**:
```bash
# View all project creation events
cat audit.log | jq 'select(.tool == "project_create")'

# Security: Failed authentication attempts
cat audit.log | jq 'select(.result == "auth_failed")'

# Performance: Slow operations (>5s)
cat audit.log | jq 'select(.execution_time_ms > 5000)'
```

---

### External Client Integration

#### Python Client Example

```python
from mcp import Client

# Initialize MCP client
client = Client(
    endpoint="https://api.example.com/mcp",
    api_key="mcp_sk_1234567890abcdef"
)

# Create project
result = await client.call_tool("project_create", {
    "name": "sales_data",
    "template": "minimal"
})

print(f"Project created: {result['project_path']}")

# Analyze project
analysis = await client.call_tool("analyze_project", {
    "project_name": "sales_data",
    "confidence_threshold": 0.8
})

print(f"Patterns found: {analysis['analysis']['patterns_found']}")

# Generate code
generation = await client.call_tool("generate_code", {
    "project_name": "sales_data",
    "model": "claude-sonnet-4.5"
})

print(f"Files generated: {generation['generation']['files_generated']}")
```

#### TypeScript Client Example

```typescript
import { MCPClient } from '@modelcontextprotocol/client';

// Initialize client
const client = new MCPClient({
  endpoint: 'https://api.example.com/mcp',
  apiKey: 'mcp_sk_1234567890abcdef'
});

// Create project
const result = await client.callTool('project_create', {
  name: 'sales_data',
  template: 'minimal'
});

console.log(`Project created: ${result.project_path}`);

// Analyze project
const analysis = await client.callTool('analyze_project', {
  project_name: 'sales_data',
  confidence_threshold: 0.8
});

console.log(`Patterns found: ${analysis.analysis.patterns_found}`);
```

#### curl Example (REST API)

```bash
# Create project
curl -X POST https://api.example.com/mcp/tools/project_create \
  -H "Authorization: Bearer mcp_sk_1234567890abcdef" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "sales_data",
    "template": "minimal"
  }'

# Analyze project
curl -X POST https://api.example.com/mcp/tools/analyze_project \
  -H "Authorization: Bearer mcp_sk_1234567890abcdef" \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "sales_data",
    "confidence_threshold": 0.8
  }'
```

---

## Implementation Plan

### Phase 1: MCP Server Foundation (3-4 days)

**Deliverables**:
- MCP server package structure
- FastMCP server implementation
- 5 core project management tools
- stdio transport (for local development)
- CLI adapter base implementation

**Tickets**:
1. **MCP-001**: Create MCP package structure (~2 hours)
2. **MCP-002**: Implement FastMCP server with stdio transport (~4 hours)
3. **MCP-003**: Implement CLI adapter base class (~3 hours)
4. **MCP-004**: Implement project management tools (5 tools) (~6 hours)
5. **MCP-005**: Integration tests for project tools (~3 hours)
6. **MCP-006**: Documentation: MCP server setup guide (~2 hours)

**Success Criteria**:
- ✅ All 5 project tools functional via stdio
- ✅ CLI adapter successfully invokes CLI commands
- ✅ Integration tests passing (100% coverage)

---

### Phase 2: Analysis & Data Source Tools (3-4 days)

**Deliverables**:
- 3 analysis tools (analyze, generate, extract)
- 4 data source tools (test, read, excel_inspect, pdf_inspect)
- Tool-level validation and error handling
- Progress tracking for long-running operations

**Tickets**:
1. **MCP-007**: Implement analysis tools (3 tools) (~5 hours)
2. **MCP-008**: Implement data source tools (4 tools) (~6 hours)
3. **MCP-009**: Add progress tracking for long operations (~3 hours)
4. **MCP-010**: Error handling and validation (~3 hours)
5. **MCP-011**: Integration tests for analysis/data tools (~4 hours)
6. **MCP-012**: Documentation: Tool reference guide (~2 hours)

**Success Criteria**:
- ✅ All 7 tools functional
- ✅ Progress updates streamed to client
- ✅ Comprehensive error messages

---

### Phase 3: HTTP/SSE Transport & Security (2-3 days)

**Deliverables**:
- HTTP/SSE transport implementation
- API key authentication
- Rate limiting
- Project isolation (multi-tenancy)
- Audit logging

**Tickets**:
1. **MCP-013**: Implement HTTP/SSE transport (~4 hours)
2. **MCP-014**: API key authentication system (~3 hours)
3. **MCP-015**: Rate limiting middleware (~3 hours)
4. **MCP-016**: Tenant isolation and project paths (~3 hours)
5. **MCP-017**: Audit logging system (~2 hours)
6. **MCP-018**: Security tests (auth, rate limits) (~3 hours)
7. **MCP-019**: Documentation: Security guide (~2 hours)

**Success Criteria**:
- ✅ HTTP/SSE server running on configurable port
- ✅ API key authentication working
- ✅ Rate limits enforced per API key
- ✅ Tenant isolation verified

---

### Phase 4: Chat Interface (3-4 days)

**Deliverables**:
- Chat interface package
- Conversational workflow engine
- Context management
- Example conversations
- Terminal UI (Rich-based)

**Tickets**:
1. **MCP-020**: Create chat interface package structure (~2 hours)
2. **MCP-021**: Implement workflow engine (~5 hours)
3. **MCP-022**: Context management system (~3 hours)
4. **MCP-023**: Terminal UI with Rich (~4 hours)
5. **MCP-024**: Example conversation templates (~2 hours)
6. **MCP-025**: Chat interface tests (~3 hours)
7. **MCP-026**: Documentation: Chat interface guide (~2 hours)

**Success Criteria**:
- ✅ Chat interface can complete full project workflow
- ✅ Context preserved across multi-turn conversations
- ✅ Rich terminal UI with progress indicators

---

### Phase 5: External Deployment & Client SDKs (2-3 days)

**Deliverables**:
- Docker deployment configuration
- Python client SDK
- TypeScript client SDK (optional)
- Integration examples
- Production deployment guide

**Tickets**:
1. **MCP-027**: Create Dockerfile and docker-compose.yml (~3 hours)
2. **MCP-028**: Python client SDK (~4 hours)
3. **MCP-029**: TypeScript client SDK (~4 hours, optional)
4. **MCP-030**: Integration examples (3 languages) (~3 hours)
5. **MCP-031**: Deployment guide and operations runbook (~3 hours)
6. **MCP-032**: Load testing and performance benchmarks (~3 hours)

**Success Criteria**:
- ✅ Docker container runs successfully
- ✅ Python SDK functional with all tools
- ✅ External apps can integrate via HTTP/SSE
- ✅ Performance meets targets (<500ms tool response)

---

### Total Effort Estimate

| Phase | Duration | LOC Estimate | Test Coverage |
|-------|----------|--------------|---------------|
| Phase 1: Foundation | 3-4 days | ~600 LOC | 95%+ |
| Phase 2: Tools | 3-4 days | ~800 LOC | 90%+ |
| Phase 3: Security | 2-3 days | ~400 LOC | 95%+ |
| Phase 4: Chat Interface | 3-4 days | ~500 LOC | 85%+ |
| Phase 5: Deployment | 2-3 days | ~200 LOC | N/A |
| **Total** | **13-18 days** | **~2500 LOC** | **90%+** |

**Critical Path**: Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5

**Parallel Opportunities**:
- Phase 4 (Chat) can start after Phase 1 complete
- Phase 5 (Deployment) can be prepared during Phase 3-4

---

## Technical Specifications

### Standardized Response Format

All MCP tools return JSON responses following this schema:

```json
{
  "status": "success|error",
  "data": { ... },           // Tool-specific data
  "message": "string",        // Human-readable message
  "metadata": {
    "tool_name": "string",
    "execution_time_ms": 150,
    "tool_version": "1.0.0",
    "timestamp": "2025-12-04T10:30:45Z"
  },
  "error": {                  // Present only if status=error
    "code": "string",
    "message": "string",
    "details": { ... }
  }
}
```

### Error Handling

**Error Codes**:
- `invalid_input` - Invalid parameters
- `resource_not_found` - Project/file not found
- `permission_denied` - Authorization failure
- `rate_limit_exceeded` - Rate limit hit
- `execution_failed` - Tool execution error
- `dependency_error` - Missing dependency (API key, etc.)

**Error Response Example**:
```json
{
  "status": "error",
  "message": "Project 'nonexistent' not found",
  "error": {
    "code": "resource_not_found",
    "message": "Project 'nonexistent' does not exist",
    "details": {
      "project_name": "nonexistent",
      "projects_dir": "/data/projects",
      "available_projects": ["weather_api", "sales_data"]
    }
  },
  "metadata": {
    "tool_name": "project_validate",
    "execution_time_ms": 12,
    "tool_version": "1.0.0",
    "timestamp": "2025-12-04T10:30:45Z"
  }
}
```

### Progress Tracking

For long-running operations (code generation, extraction), stream progress updates:

**SSE Progress Stream**:
```
event: progress
data: {"status": "in_progress", "progress": 0.25, "message": "Analyzing examples..."}

event: progress
data: {"status": "in_progress", "progress": 0.50, "message": "Generating code..."}

event: progress
data: {"status": "in_progress", "progress": 0.75, "message": "Validating generated code..."}

event: complete
data: {"status": "success", "data": { ... }}
```

### Performance Targets

| Operation | Target Latency | Max Latency |
|-----------|----------------|-------------|
| project_create | <200ms | 500ms |
| project_list | <100ms | 300ms |
| project_validate | <150ms | 400ms |
| analyze_project | <2s | 5s |
| generate_code | <10s | 30s |
| run_extraction | <5s | 15s |

### Logging Configuration

**Structured Logging (structlog)**:
```python
logger.info(
    "mcp_tool_executed",
    tool_name="project_create",
    parameters={"name": "weather_api", "template": "weather"},
    result="success",
    execution_time_ms=245,
    api_key_name="External App 1"
)
```

**Log Levels**:
- `DEBUG`: Internal state, detailed execution flow
- `INFO`: Tool execution, success/failure
- `WARNING`: Rate limits, deprecations
- `ERROR`: Execution failures, system errors
- `CRITICAL`: Security violations, system unavailable

---

## Top 3 Design Decisions Requiring Approval

### Decision 1: MCP Tool Count ⚠️ **REQUIRES APPROVAL**

**Question**: Should we implement all 15 tools in Phase 1-2, or start with a minimal set (8 tools) and expand based on usage?

**Option A: All 15 Tools (Recommended)**
- **Pros**: Complete feature parity with CLI, chat interface fully functional
- **Cons**: Longer initial development (13-18 days)
- **Timeline**: 13-18 days total

**Option B: Minimal 8 Tools (Fast Start)**
- **Pros**: Faster initial deployment (8-10 days), validate architecture early
- **Cons**: Incomplete chat workflows, missing data source introspection
- **Timeline**: 8-10 days initial, 3-5 days for remaining tools
- **Tools**: project_create, project_list, project_validate, analyze_project, generate_code, run_extraction, setup_test, setup_init

**Recommendation**: **Option A (All 15 Tools)** - Provides complete experience, chat interface can demo full workflow

---

### Decision 2: External Service Transport ⚠️ **REQUIRES APPROVAL**

**Question**: Which transport protocol(s) should be prioritized for external service deployment?

**Option A: HTTP/SSE Only (Recommended)**
- **Pros**: Standard protocol, easy to deploy, widely supported clients
- **Cons**: Not ideal for real-time bidirectional communication
- **Use Case**: External app integrations, webhook receivers, REST API clients

**Option B: WebSocket + HTTP/SSE**
- **Pros**: Real-time bidirectional, better for long-running operations
- **Cons**: More complex client implementation, requires sticky sessions for load balancing
- **Use Case**: Real-time dashboards, live progress tracking

**Option C: stdio Only (Development)**
- **Pros**: Simplest implementation, no network security concerns
- **Cons**: No external access, local-only
- **Use Case**: Chat interface only, no external integrations

**Recommendation**: **Option A (HTTP/SSE)** in Phase 3, add WebSocket in future if needed

---

### Decision 3: Multi-Tenancy Strategy ⚠️ **REQUIRES APPROVAL**

**Question**: How should we isolate projects and data between different API keys (tenants)?

**Option A: Directory-Based Isolation (Recommended)**
- **Pros**: Simple implementation, file system-based, easy to backup
- **Cons**: Shared file system limits, no fine-grained permissions
- **Architecture**: `$EDGAR_ARTIFACTS_DIR/tenants/{tenant_id}/projects/`

**Option B: Database-Backed Multi-Tenancy**
- **Pros**: Fine-grained permissions, better for SaaS deployment
- **Cons**: Requires database (PostgreSQL), more complex, ~2x development time
- **Architecture**: Projects stored in database with tenant_id foreign key

**Option C: No Isolation (Single Tenant)**
- **Pros**: Simplest, no overhead
- **Cons**: Not suitable for external service, security risk
- **Use Case**: Internal use only, trusted users

**Recommendation**: **Option A (Directory-Based)** for MVP, migrate to Option B if SaaS deployment needed

---

## Recommended First Phase

### Phase 1A: Proof of Concept (3-4 days) ✅ **RECOMMENDED START**

**Goal**: Validate MCP architecture with minimal viable toolset

**Deliverables**:
1. MCP server with stdio transport
2. CLI adapter base implementation
3. 5 project management tools
4. Basic chat interface (terminal UI)
5. End-to-end demo: Create project → Analyze → Generate → Extract

**Success Criteria**:
- ✅ Chat interface can complete full workflow
- ✅ All tools return standardized responses
- ✅ Integration tests passing
- ✅ Demo video showing end-to-end flow

**Why Start Here**:
- Validates core architecture decisions
- Demonstrates value immediately (chat interface working)
- Low risk - stdio transport, no external dependencies
- Can pivot based on feedback before investing in HTTP/SSE

---

## Estimated Timeline for Full Implementation

### Conservative Estimate (18 days)
```
Week 1: Phase 1 (Foundation) - 4 days
Week 2: Phase 2 (Tools) - 4 days
Week 3: Phase 3 (Security) + Phase 4 (Chat) - 5 days
Week 4: Phase 5 (Deployment) + Testing - 3 days
Week 4-5: Buffer for issues, documentation - 2 days
```

### Aggressive Estimate (13 days)
```
Week 1: Phase 1 + Phase 2 - 6 days
Week 2: Phase 3 + Phase 4 - 5 days
Week 3: Phase 5 + Final Testing - 2 days
```

### Phased Rollout (Recommended)
```
Sprint 1 (1 week): Phase 1A (Proof of Concept) - Validate architecture
Sprint 2 (1 week): Complete Phase 1 + Phase 2 - All tools working
Sprint 3 (1 week): Phase 3 + Phase 4 - External service + Chat UI
Sprint 4 (3 days): Phase 5 - Production deployment
```

---

## Next Steps

### Immediate Actions (This Week)
1. ✅ **Review & Approve** this architecture document
2. ✅ **Decision**: Approve 3 design decisions (tools count, transport, multi-tenancy)
3. 🔄 **Create Tickets**: MCP-001 through MCP-032 in Linear
4. 🔄 **Setup Environment**: Install FastMCP, create MCP package structure

### Week 1 Sprint
1. Implement MCP server foundation (Phase 1)
2. Daily demos of progress
3. Iterate based on feedback

### Success Metrics
- **Technical**: All 15 tools functional, 90%+ test coverage
- **User Experience**: Chat interface completes full workflow in <5 turns
- **Performance**: Tool response <500ms (p95), code generation <10s
- **Security**: API key auth working, rate limits enforced

---

## Appendix

### References

1. **MCP Specification**: https://modelcontextprotocol.io/specification/2025-06-18
2. **FastMCP Documentation**: https://github.com/jlowin/fastmcp
3. **MCP Python SDK**: https://github.com/modelcontextprotocol/python-sdk
4. **MCP Best Practices**: https://modelcontextprotocol.info/docs/best-practices/

### Related Documents

- [Platform API Reference](../api/PLATFORM_API.md)
- [Platform Usage Guide](../guides/PLATFORM_USAGE.md)
- [Project Management Guide](../guides/PROJECT_MANAGEMENT.md)
- [Security Guidelines](../guides/SECURITY.md)

---

**Document Status**: 🟡 Draft - Awaiting Approval
**Authors**: Research Agent (Claude Code)
**Reviewers**: Project Stakeholders
**Approval Date**: TBD
