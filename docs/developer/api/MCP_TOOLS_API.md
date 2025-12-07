# MCP Tools API Reference

**Version**: 1.0.0
**Last Updated**: 2025-12-04

---

## Overview

This document provides complete API specifications for all 15 MCP tools in the Extract & Transform Platform. Each tool follows the Model Context Protocol (MCP) specification and returns standardized JSON responses.

### Tool Categories

1. **Project Management** (5 tools) - CRUD operations for projects
2. **Analysis & Code Generation** (3 tools) - Pattern detection and code generation
3. **Data Sources** (4 tools) - Data source introspection and testing
4. **Setup & Configuration** (3 tools) - Platform configuration and templates

---

## Quick Reference

| Tool Name | Category | Purpose | Avg Latency |
|-----------|----------|---------|-------------|
| `project_create` | Project | Create new project | <200ms |
| `project_list` | Project | List all projects | <100ms |
| `project_validate` | Project | Validate project config | <150ms |
| `project_delete` | Project | Delete project | <100ms |
| `project_info` | Project | Get project details | <100ms |
| `analyze_project` | Analysis | Detect transformation patterns | <2s |
| `generate_code` | Analysis | Generate extractor code | <10s |
| `run_extraction` | Analysis | Execute extractor | <5s |
| `data_source_test` | Data | Test data source connection | <500ms |
| `data_source_read` | Data | Read sample data | <1s |
| `excel_inspect` | Data | Inspect Excel file | <500ms |
| `pdf_inspect` | Data | Inspect PDF file | <500ms |
| `setup_test` | Setup | Test API key | <500ms |
| `setup_init` | Setup | Initialize configuration | <200ms |
| `get_templates` | Setup | List project templates | <50ms |

---

## Project Management Tools

### project_create

**Purpose**: Create a new project from a template

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "name": {
      "type": "string",
      "description": "Project name (alphanumeric, underscores, hyphens)",
      "pattern": "^[a-zA-Z0-9_-]+$",
      "minLength": 1,
      "maxLength": 100,
      "examples": ["weather_api", "sales-dashboard", "invoice_parser"]
    },
    "template": {
      "type": "string",
      "enum": ["weather", "news_scraper", "minimal"],
      "default": "minimal",
      "description": "Project template to use"
    },
    "description": {
      "type": "string",
      "description": "Optional project description",
      "maxLength": 500
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
    "status": {
      "type": "string",
      "enum": ["success", "error"]
    },
    "project_name": {
      "type": "string"
    },
    "project_path": {
      "type": "string",
      "description": "Absolute path to created project"
    },
    "message": {
      "type": "string",
      "description": "Human-readable success/error message"
    },
    "metadata": {
      "type": "object",
      "properties": {
        "template_used": {"type": "string"},
        "directories_created": {
          "type": "array",
          "items": {"type": "string"}
        },
        "files_created": {
          "type": "array",
          "items": {"type": "string"}
        },
        "execution_time_ms": {"type": "number"}
      }
    }
  }
}
```

**Example Request**:
```python
result = await client.call_tool("project_create", {
    "name": "weather_api",
    "template": "weather",
    "description": "Weather API data extraction"
})
```

**Example Response (Success)**:
```json
{
  "status": "success",
  "project_name": "weather_api",
  "project_path": "/Users/user/edgar_projects/projects/weather_api",
  "message": "Project 'weather_api' created successfully",
  "metadata": {
    "template_used": "weather",
    "directories_created": [
      "examples",
      "src",
      "tests",
      "output"
    ],
    "files_created": [
      "project.yaml",
      "README.md"
    ],
    "execution_time_ms": 145
  }
}
```

**Example Response (Error)**:
```json
{
  "status": "error",
  "message": "Project 'weather_api' already exists",
  "error": {
    "code": "resource_already_exists",
    "message": "Project 'weather_api' already exists at /Users/user/edgar_projects/projects/weather_api",
    "details": {
      "project_name": "weather_api",
      "existing_path": "/Users/user/edgar_projects/projects/weather_api"
    }
  },
  "metadata": {
    "execution_time_ms": 12
  }
}
```

**Error Codes**:
- `invalid_input` - Invalid project name or template
- `resource_already_exists` - Project already exists
- `permission_denied` - Cannot write to output directory
- `execution_failed` - Unexpected error during creation

---

### project_list

**Purpose**: List all projects in the projects directory

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
      "description": "Custom projects directory to list"
    },
    "include_invalid": {
      "type": "boolean",
      "default": false,
      "description": "Include projects with invalid configurations"
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
          "modified_at": {"type": "string", "format": "date-time"},
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
    },
    "count": {"type": "integer"},
    "message": {"type": "string"}
  }
}
```

**Example Request**:
```python
result = await client.call_tool("project_list", {
    "format": "json"
})
```

**Example Response**:
```json
{
  "status": "success",
  "projects": [
    {
      "name": "weather_api",
      "path": "/Users/user/edgar_projects/projects/weather_api",
      "description": "Weather API data extraction",
      "version": "0.1.0",
      "template": "weather",
      "is_valid": true,
      "created_at": "2025-12-01T10:30:00Z",
      "modified_at": "2025-12-04T14:20:00Z",
      "statistics": {
        "example_count": 7,
        "source_files": 3,
        "test_files": 2
      }
    },
    {
      "name": "sales_data",
      "path": "/Users/user/edgar_projects/projects/sales_data",
      "description": "Sales data transformation",
      "version": "0.1.0",
      "template": "minimal",
      "is_valid": true,
      "created_at": "2025-12-02T09:15:00Z",
      "modified_at": "2025-12-02T09:15:00Z",
      "statistics": {
        "example_count": 3,
        "source_files": 0,
        "test_files": 0
      }
    }
  ],
  "count": 2,
  "message": "Found 2 projects"
}
```

---

### project_validate

**Purpose**: Validate project configuration and directory structure

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
    "errors": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Critical errors that prevent execution"
    },
    "warnings": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Non-critical issues"
    },
    "recommendations": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Best practice suggestions"
    },
    "checks_performed": {
      "type": "object",
      "properties": {
        "config_syntax": {"type": "boolean"},
        "config_schema": {"type": "boolean"},
        "directory_structure": {"type": "boolean"},
        "example_files": {"type": "boolean"},
        "data_sources": {"type": "boolean"}
      }
    },
    "message": {"type": "string"}
  }
}
```

**Example Request**:
```python
result = await client.call_tool("project_validate", {
    "name": "weather_api",
    "verbose": true
})
```

**Example Response (Valid)**:
```json
{
  "status": "success",
  "project_name": "weather_api",
  "is_valid": true,
  "errors": [],
  "warnings": [],
  "recommendations": [
    "Consider adding more example files (currently 7, recommended 10+)",
    "Add .gitignore to prevent committing sensitive data"
  ],
  "checks_performed": {
    "config_syntax": true,
    "config_schema": true,
    "directory_structure": true,
    "example_files": true,
    "data_sources": true
  },
  "message": "Project 'weather_api' is valid"
}
```

**Example Response (Invalid)**:
```json
{
  "status": "error",
  "project_name": "broken_project",
  "is_valid": false,
  "errors": [
    "Missing required field: project.name in project.yaml",
    "Invalid data source type: 'invalid_type'",
    "No example files found in examples/"
  ],
  "warnings": [
    "Missing directory: tests/",
    "project.yaml is using deprecated 'data_source' field (use 'data_sources' array)"
  ],
  "recommendations": [
    "Run 'setup init' to generate valid configuration",
    "Add at least 2-3 example files to examples/"
  ],
  "checks_performed": {
    "config_syntax": true,
    "config_schema": false,
    "directory_structure": true,
    "example_files": true,
    "data_sources": false
  },
  "message": "Project 'broken_project' has 3 critical errors"
}
```

---

### project_delete

**Purpose**: Delete a project and all its files

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
      "description": "Skip confirmation prompt (use with caution)"
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
    "message": {"type": "string"},
    "metadata": {
      "type": "object",
      "properties": {
        "files_deleted": {"type": "integer"},
        "directories_deleted": {"type": "integer"},
        "execution_time_ms": {"type": "number"}
      }
    }
  }
}
```

**Example Request**:
```python
result = await client.call_tool("project_delete", {
    "name": "old_project",
    "force": true
})
```

**Example Response (Success)**:
```json
{
  "status": "success",
  "project_name": "old_project",
  "deleted": true,
  "message": "Project 'old_project' deleted successfully",
  "metadata": {
    "files_deleted": 15,
    "directories_deleted": 4,
    "execution_time_ms": 45
  }
}
```

**Error Codes**:
- `resource_not_found` - Project does not exist
- `permission_denied` - Cannot delete project (permissions)
- `confirmation_required` - force=false and confirmation needed (interactive only)

---

### project_info

**Purpose**: Get detailed information about a project

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
        "config": {
          "type": "object",
          "description": "Full project configuration"
        },
        "statistics": {
          "type": "object",
          "properties": {
            "example_count": {"type": "integer"},
            "source_files": {"type": "integer"},
            "test_files": {"type": "integer"},
            "total_size_bytes": {"type": "integer"}
          }
        },
        "last_analysis": {
          "type": "object",
          "description": "Most recent analysis results (if available)"
        }
      }
    }
  }
}
```

**Example Response**:
```json
{
  "status": "success",
  "project": {
    "name": "weather_api",
    "path": "/Users/user/edgar_projects/projects/weather_api",
    "config": {
      "project": {
        "name": "weather_api",
        "version": "0.1.0",
        "description": "Weather API data extraction"
      },
      "data_sources": [
        {
          "type": "api",
          "name": "openweathermap",
          "endpoint": "https://api.openweathermap.org/data/2.5/weather"
        }
      ],
      "output": {
        "formats": [
          {"type": "json", "path": "output/weather.json"}
        ]
      }
    },
    "statistics": {
      "example_count": 7,
      "source_files": 3,
      "test_files": 2,
      "total_size_bytes": 125000
    },
    "last_analysis": {
      "timestamp": "2025-12-04T14:20:00Z",
      "patterns_found": 12,
      "confidence_avg": 0.95
    }
  }
}
```

---

## Analysis & Code Generation Tools

### analyze_project

**Purpose**: Analyze example files and detect transformation patterns

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
    },
    "max_patterns": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100,
      "default": 50,
      "description": "Maximum patterns to return"
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
        "execution_time_ms": {"type": "number"},
        "patterns": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "type": {
                "type": "string",
                "enum": [
                  "FIELD_MAPPING",
                  "CONCATENATION",
                  "TYPE_CONVERSION",
                  "BOOLEAN_CONVERSION",
                  "VALUE_MAPPING",
                  "FIELD_EXTRACTION",
                  "NESTED_ACCESS",
                  "LIST_AGGREGATION",
                  "CONDITIONAL",
                  "DATE_PARSING",
                  "MATH_OPERATION",
                  "STRING_FORMATTING",
                  "DEFAULT_VALUE",
                  "CUSTOM"
                ]
              },
              "confidence": {"type": "number"},
              "source_path": {"type": "string"},
              "target_path": {"type": "string"},
              "transformation": {"type": "string"},
              "examples": {"type": "array"}
            }
          }
        },
        "schema": {
          "type": "object",
          "properties": {
            "input": {
              "type": "object",
              "description": "Detected input schema"
            },
            "output": {
              "type": "object",
              "description": "Detected output schema"
            }
          }
        }
      }
    },
    "message": {"type": "string"}
  }
}
```

**Example Response**:
```json
{
  "status": "success",
  "project_name": "weather_api",
  "analysis": {
    "patterns_found": 12,
    "confidence_avg": 0.95,
    "execution_time_ms": 1450,
    "patterns": [
      {
        "type": "FIELD_MAPPING",
        "confidence": 1.0,
        "source_path": "main.temp",
        "target_path": "temperature_celsius",
        "transformation": "Direct field rename",
        "examples": [
          {"input": 20.5, "output": 20.5},
          {"input": 15.3, "output": 15.3}
        ]
      },
      {
        "type": "NESTED_ACCESS",
        "confidence": 1.0,
        "source_path": "coord",
        "target_path": "coordinates",
        "transformation": "Extract nested object",
        "examples": [
          {
            "input": {"lat": 51.5074, "lon": -0.1278},
            "output": {"latitude": 51.5074, "longitude": -0.1278}
          }
        ]
      }
    ],
    "schema": {
      "input": {
        "type": "object",
        "properties": {
          "main": {
            "type": "object",
            "properties": {
              "temp": {"type": "number"}
            }
          },
          "coord": {
            "type": "object",
            "properties": {
              "lat": {"type": "number"},
              "lon": {"type": "number"}
            }
          }
        }
      },
      "output": {
        "type": "object",
        "properties": {
          "temperature_celsius": {"type": "number"},
          "coordinates": {
            "type": "object",
            "properties": {
              "latitude": {"type": "number"},
              "longitude": {"type": "number"}
            }
          }
        }
      }
    }
  },
  "message": "Analysis complete: 12 patterns detected with 95% average confidence"
}
```

**Error Codes**:
- `resource_not_found` - Project not found
- `invalid_input` - No example files found
- `execution_failed` - Analysis service error

---

### generate_code

**Purpose**: Generate extractor code from analysis results

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
    },
    "include_tests": {
      "type": "boolean",
      "default": true,
      "description": "Generate test files"
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
        "model_used": {"type": "string"},
        "files_generated": {
          "type": "array",
          "items": {"type": "string"}
        },
        "tests_generated": {
          "type": "array",
          "items": {"type": "string"}
        },
        "validation": {
          "type": "object",
          "properties": {
            "syntax_valid": {"type": "boolean"},
            "imports_valid": {"type": "boolean"},
            "interface_compliant": {"type": "boolean"},
            "errors": {"type": "array", "items": {"type": "string"}}
          }
        },
        "preview": {
          "type": "string",
          "description": "Generated code preview (if dry_run=true)"
        },
        "execution_time_ms": {"type": "number"}
      }
    },
    "message": {"type": "string"}
  }
}
```

**Example Response (Success)**:
```json
{
  "status": "success",
  "project_name": "weather_api",
  "generation": {
    "model_used": "claude-sonnet-4.5",
    "files_generated": [
      "src/weather_api/extractor.py",
      "src/weather_api/__init__.py",
      "src/weather_api/models.py"
    ],
    "tests_generated": [
      "tests/test_extractor.py",
      "tests/test_models.py"
    ],
    "validation": {
      "syntax_valid": true,
      "imports_valid": true,
      "interface_compliant": true,
      "errors": []
    },
    "execution_time_ms": 8750
  },
  "message": "Code generation complete: 3 source files, 2 test files generated"
}
```

**Error Codes**:
- `resource_not_found` - Project or analysis not found
- `dependency_error` - Missing API key or invalid model
- `execution_failed` - Code generation failed
- `validation_failed` - Generated code failed validation

---

### run_extraction

**Purpose**: Execute generated extractor and produce output

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
    },
    "dry_run": {
      "type": "boolean",
      "default": false,
      "description": "Preview extraction without writing output"
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
        "output_format": {"type": "string"},
        "execution_time_ms": {"type": "number"},
        "errors": {
          "type": "array",
          "items": {"type": "string"}
        },
        "sample_output": {
          "type": "array",
          "description": "First 3 records for preview"
        }
      }
    },
    "message": {"type": "string"}
  }
}
```

**Example Response**:
```json
{
  "status": "success",
  "project_name": "weather_api",
  "extraction": {
    "records_extracted": 7,
    "output_file": "/Users/user/edgar_projects/projects/weather_api/output/weather.json",
    "output_format": "json",
    "execution_time_ms": 2340,
    "errors": [],
    "sample_output": [
      {
        "temperature_celsius": 20.5,
        "coordinates": {"latitude": 51.5074, "longitude": -0.1278},
        "city": "London"
      },
      {
        "temperature_celsius": 15.3,
        "coordinates": {"latitude": 40.7128, "longitude": -74.0060},
        "city": "New York"
      },
      {
        "temperature_celsius": 25.8,
        "coordinates": {"latitude": 35.6762, "longitude": 139.6503},
        "city": "Tokyo"
      }
    ]
  },
  "message": "Extraction complete: 7 records written to weather.json"
}
```

---

## Data Source Tools

### data_source_test

**Purpose**: Test data source connectivity and configuration

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
      "description": "Data source configuration",
      "additionalProperties": true
    }
  },
  "required": ["source_type", "config"]
}
```

**Example Request (API)**:
```python
result = await client.call_tool("data_source_test", {
    "source_type": "api",
    "config": {
        "endpoint": "https://api.openweathermap.org/data/2.5/weather",
        "params": {"q": "London", "appid": "YOUR_API_KEY"}
    }
})
```

**Example Response (Success)**:
```json
{
  "status": "success",
  "source_type": "api",
  "connection_status": "success",
  "response_time_ms": 245,
  "sample_data": {
    "coord": {"lon": -0.1257, "lat": 51.5085},
    "main": {"temp": 285.32, "pressure": 1013}
  },
  "message": "API connection successful"
}
```

**Example Response (Failed)**:
```json
{
  "status": "error",
  "source_type": "api",
  "connection_status": "failed",
  "response_time_ms": 5000,
  "error": {
    "code": "connection_timeout",
    "message": "Request timed out after 5000ms",
    "details": {
      "endpoint": "https://api.example.com/data",
      "timeout": 5000
    }
  }
}
```

---

### data_source_read

**Purpose**: Read sample data from configured data source

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

**Example Response**:
```json
{
  "status": "success",
  "project_name": "weather_api",
  "records": [
    {"coord": {"lon": -0.1257, "lat": 51.5085}, "main": {"temp": 285.32}},
    {"coord": {"lon": -74.0060, "lat": 40.7128}, "main": {"temp": 278.15}}
  ],
  "count": 2,
  "schema_detected": {
    "coord": {
      "type": "object",
      "properties": {
        "lon": {"type": "number"},
        "lat": {"type": "number"}
      }
    },
    "main": {
      "type": "object",
      "properties": {
        "temp": {"type": "number"}
      }
    }
  },
  "message": "Read 2 records from API data source"
}
```

---

### excel_inspect

**Purpose**: Inspect Excel file structure without loading full data

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "file_path": {
      "type": "string",
      "description": "Path to Excel file (absolute or project-relative)"
    }
  },
  "required": ["file_path"]
}
```

**Example Response**:
```json
{
  "status": "success",
  "file_path": "/Users/user/data/sales.xlsx",
  "sheets": [
    {
      "name": "Sales Data",
      "index": 0,
      "rows": 1500,
      "columns": 12,
      "header_row": 0,
      "column_names": [
        "Date",
        "Product",
        "Quantity",
        "Price",
        "Total"
      ],
      "sample_data": [
        {"Date": "2025-01-01", "Product": "Widget A", "Quantity": 10, "Price": 15.99, "Total": 159.90},
        {"Date": "2025-01-02", "Product": "Widget B", "Quantity": 5, "Price": 25.50, "Total": 127.50}
      ]
    },
    {
      "name": "Summary",
      "index": 1,
      "rows": 50,
      "columns": 5,
      "header_row": 0
    }
  ],
  "message": "Excel file has 2 sheets with 1550 total rows"
}
```

---

### pdf_inspect

**Purpose**: Inspect PDF file structure and detect tables

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

**Example Response**:
```json
{
  "status": "success",
  "file_path": "/Users/user/data/invoice.pdf",
  "total_pages": 3,
  "page_analysis": {
    "page_number": 0,
    "width": 612.0,
    "height": 792.0,
    "tables_found": 2,
    "text_blocks": 15,
    "tables": [
      {
        "bbox": [50, 100, 562, 400],
        "rows": 10,
        "columns": 5,
        "sample_data": [
          ["Item", "Quantity", "Unit Price", "Total"],
          ["Widget A", "2", "$15.00", "$30.00"],
          ["Service B", "1", "$50.00", "$50.00"]
        ]
      }
    ]
  },
  "message": "PDF page 1/3: 2 tables found"
}
```

---

## Setup & Configuration Tools

### setup_test

**Purpose**: Test OpenRouter API key and configuration

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

**Example Response (Valid)**:
```json
{
  "status": "success",
  "api_key_valid": true,
  "models_available": [
    "anthropic/claude-sonnet-4.5",
    "openai/gpt-4o",
    "openai/gpt-4-turbo"
  ],
  "credits_remaining": 50.00,
  "rate_limits": {
    "requests_per_minute": 60,
    "tokens_per_minute": 100000
  },
  "message": "API key is valid with $50.00 credits remaining"
}
```

**Example Response (Invalid)**:
```json
{
  "status": "error",
  "api_key_valid": false,
  "error": {
    "code": "invalid_api_key",
    "message": "API key is invalid or expired",
    "details": {
      "key_prefix": "sk-or-v1-123..."
    }
  }
}
```

---

### setup_init

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
      "description": "External artifacts directory path (optional)"
    },
    "overwrite": {
      "type": "boolean",
      "default": false,
      "description": "Overwrite existing configuration"
    }
  },
  "required": ["api_key"]
}
```

**Example Response**:
```json
{
  "status": "success",
  "config_path": "/Users/user/.config/edgar/config.json",
  "artifacts_dir": "/Users/user/edgar_projects",
  "api_key_valid": true,
  "message": "Configuration initialized successfully"
}
```

---

### get_templates

**Purpose**: List available project templates

**Input Schema**:
```json
{
  "type": "object",
  "properties": {}
}
```

**Example Response**:
```json
{
  "status": "success",
  "templates": [
    {
      "name": "weather",
      "description": "Weather API data extraction template",
      "data_source_type": "api",
      "features": [
        "7 example API responses",
        "REST API authentication",
        "Rate limiting configuration",
        "Caching support"
      ],
      "use_cases": [
        "REST API extraction",
        "JSON data transformation",
        "Time-series data"
      ],
      "example_count": 7,
      "file_count": 468
    },
    {
      "name": "news_scraper",
      "description": "Web scraping template using Jina.ai",
      "data_source_type": "jina",
      "features": [
        "JS-heavy site scraping",
        "Markdown extraction",
        "Bearer token authentication"
      ],
      "use_cases": [
        "Web scraping",
        "Content extraction",
        "Article parsing"
      ],
      "example_count": 3,
      "file_count": 263
    },
    {
      "name": "minimal",
      "description": "Bare-bones starter template",
      "data_source_type": "file",
      "features": [
        "Essential configuration only",
        "Step-by-step guide",
        "No pre-configured examples"
      ],
      "use_cases": [
        "Custom projects",
        "Learning platform",
        "Experimentation"
      ],
      "example_count": 0,
      "file_count": 144
    }
  ],
  "count": 3,
  "message": "Found 3 project templates"
}
```

---

## Error Response Format

All tools return errors in this standardized format:

```json
{
  "status": "error",
  "message": "Human-readable error message",
  "error": {
    "code": "error_code",
    "message": "Detailed error message",
    "details": {
      "additional": "context"
    }
  },
  "metadata": {
    "tool_name": "string",
    "execution_time_ms": 0,
    "timestamp": "2025-12-04T10:30:45Z"
  }
}
```

### Common Error Codes

| Error Code | Description | Typical Cause |
|------------|-------------|---------------|
| `invalid_input` | Invalid parameters | Missing required field, invalid format |
| `resource_not_found` | Resource not found | Project/file doesn't exist |
| `resource_already_exists` | Resource already exists | Duplicate project name |
| `permission_denied` | Authorization failure | Missing permissions, API key invalid |
| `rate_limit_exceeded` | Rate limit hit | Too many requests |
| `execution_failed` | Tool execution error | Service failure, unexpected error |
| `dependency_error` | Missing dependency | API key missing, service unavailable |
| `validation_failed` | Validation error | Invalid configuration, failed checks |
| `timeout` | Operation timeout | Long-running operation exceeded limit |

---

## Rate Limiting

All tools are subject to rate limiting based on API key tier:

| Tier | Rate Limit | Burst Limit |
|------|------------|-------------|
| **Free** | 10 requests/minute | 20 requests |
| **Development** | 100 requests/hour | 50 requests |
| **Standard** | 100 requests/hour | 100 requests |
| **Premium** | 1000 requests/hour | 200 requests |

**Rate Limit Headers** (HTTP/SSE transport):
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1733311200
```

**Rate Limit Exceeded Response**:
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

---

## Tool-Specific Rate Limits

Some tools have additional limits due to resource intensity:

| Tool | Additional Limit | Reason |
|------|------------------|--------|
| `generate_code` | 5/minute | AI model usage |
| `run_extraction` | 20/minute | Resource intensive |
| `analyze_project` | 10/minute | Computation intensive |

---

## Authentication

All tools require authentication via API key (HTTP/SSE transport) or stdio trust (local chat interface).

**HTTP Header**:
```
Authorization: Bearer mcp_sk_1234567890abcdef
```

**Query Parameter** (webhook fallback):
```
POST /mcp/tools/project_create?api_key=mcp_sk_1234567890abcdef
```

---

## Pagination

Tools that return lists support pagination:

**Parameters**:
- `limit` (integer): Maximum results per page (default: 20, max: 100)
- `offset` (integer): Number of results to skip (default: 0)

**Response**:
```json
{
  "status": "success",
  "data": [...],
  "pagination": {
    "limit": 20,
    "offset": 0,
    "total": 150,
    "has_more": true,
    "next_offset": 20
  }
}
```

---

## Versioning

MCP Tools API follows semantic versioning:

**Current Version**: 1.0.0

**Version Header** (HTTP/SSE):
```
X-API-Version: 1.0.0
```

**Deprecation Notice**: Tools will be deprecated with 6-month notice in response headers:
```
Deprecation: true
Sunset: 2026-06-04T00:00:00Z
Link: <https://docs.example.com/api/migration>; rel="deprecation"
```

---

## Support

- **Documentation**: https://docs.example.com/mcp-api
- **Issues**: https://github.com/example/edgar/issues
- **Email**: support@example.com

**API Status**: https://status.example.com/mcp
