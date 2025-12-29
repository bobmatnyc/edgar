# Recipe Model Design for EDGAR Platform

**Date:** 2025-12-29
**Objective:** Design a recipe/workflow system for EDGAR that separates reusable workflows (like `fortune100`) from core CLI commands.

---

## Executive Summary

Based on research of AI coding tools (Block's Goose), data pipeline systems (Prefect, Dagster, dbt), and CLI recipe patterns (Just, Makefile, npm scripts), this document recommends a **YAML-based recipe model** for EDGAR that balances declarative configuration with Python extensibility.

**Key Recommendations:**
1. **File Format:** YAML (primary) + JSON (secondary) for recipes
2. **Discovery:** Directory convention (`recipes/`) + optional registry
3. **Parameterization:** Jinja2 templating for dynamic values
4. **Composition:** Recipes can reference other recipes (sub-recipes)
5. **Validation:** Pydantic models for schema enforcement

---

## 1. Research Summary

### 1.1 Block's Goose (AI Coding Tool)

**Architecture:**
- **File Format:** YAML or JSON recipe files
- **Discovery:** Local files via `goose run --recipe <FILE>` or GitHub repo via `GOOSE_RECIPE_GITHUB_REPO` environment variable
- **Extension Model:** MCP (Model Context Protocol) servers for tool integration

**Recipe Schema:**
```yaml
version: "1.0.0"
title: "Recipe Name"
description: "What the recipe does"
instructions: "Guide AI agent behavior and capabilities"
prompt: "Initial task: use {{ required_param }}"
parameters:
  - key: required_param
    input_type: string
    requirement: required  # or optional, user_prompt
    description: "Parameter description"
  - key: optional_param
    input_type: string
    requirement: optional
    default: "default value"
extensions:
  - type: stdio
    name: codesearch
    cmd: uvx
    args: ["mcp_codesearch@latest"]
    timeout: 300
settings:
  goose_provider: "anthropic"
  goose_model: "claude-sonnet-4-20250514"
  temperature: 0.7
retry:
  max_retries: 3
  timeout_seconds: 30
  checks:
    - type: shell
      command: "validation command"
  on_failure: "cleanup command"
```

**Key Features:**
- **Parameterization:** Jinja2-style `{{ variable }}` syntax
- **Retry Logic:** Built-in retry mechanism with validation checks
- **Model Settings:** Per-recipe AI model configuration
- **Activities:** Example prompts displayed as clickable UI elements
- **Portability:** `{{ recipe_dir }}` for relative file paths

**Invocation:**
```bash
goose run --recipe recipe.yaml
goose recipe open recipe.yaml  # Desktop UI
```

**Sources:**
- [Goose Recipe Reference](https://block.github.io/goose/docs/guides/recipes/recipe-reference/)
- [Shareable Recipes](https://block.github.io/goose/docs/guides/recipes/session-recipes/)
- [Subrecipes Blog](https://block.github.io/goose/blog/2025/09/15/subrecipes-in-goose/)

### 1.2 Data Pipeline Systems

#### Prefect (Python Workflows)

**Model:** Python decorator-based
```python
from prefect import flow, task

@task(retries=3, retry_delay_seconds=10)
def extract_data(source: str):
    """Extract from source."""
    return data

@flow(name="ETL Pipeline")
def etl_pipeline(sources: list[str]):
    """Orchestrate ETL."""
    for source in sources:
        data = extract_data(source)
```

**Key Features:**
- **Tasks:** Decorated functions with retry/timeout configs
- **Flows:** Orchestrate tasks with dependencies
- **Type Safety:** Python type hints for validation
- **Concurrency:** Built-in async support and task mapping

**Sources:**
- [How to write workflows - Prefect](https://docs.prefect.io/v3/how-to-guides/workflows/write-and-run)
- [Write tasks - Prefect](https://docs-3.prefect.io/v3/develop/write-tasks)

#### Dagster (Data Assets)

**Model:** Asset-oriented with Python decorators
```python
import dagster as dg

class MyOpConfig(dg.Config):
    api_endpoint: str

@dg.asset
def my_asset():
    """Define data asset."""
    pass

@dg.op
def ingest_data(config: MyOpConfig):
    """Data ingestion logic."""
    data = requests.get(f"{config.api_endpoint}/data").json()
    return data
```

**Key Features:**
- **Assets:** First-class data products
- **Ops:** Composable computation units
- **Lineage:** Built-in data lineage tracking
- **Observability:** Integrated monitoring

**Sources:**
- [Dagster Documentation](https://docs.dagster.io/)
- [Intro to ops and jobs](https://docs.dagster.io/guides/dagster/intro-to-ops-jobs/single-op-job)

#### dbt (Data Transformation)

**Model:** SQL + YAML configuration
```yaml
# schema.yml
version: 2
models:
  - name: my_first_dbt_model
    description: "A starter dbt model"
    columns:
      - name: id
        description: "The primary key"
        data_tests:
          - unique
          - not_null
```

```sql
-- models/my_model.sql
{{ config(
    materialized = "table",
    tags = ["core", "events"]
) }}

select * from {{ ref('raw_events') }}
```

**Key Features:**
- **Declarative:** YAML for metadata, SQL for logic
- **Testing:** Built-in data quality tests
- **Modularity:** `ref()` for model dependencies
- **Configuration Hierarchy:** Project → Model → Column

**Sources:**
- [dbt YAML Files Guide](https://medium.com/@23saini/a-beginners-guide-to-dbt-yaml-files-3e718719fd9c)
- [Model configurations - dbt](https://docs.getdbt.com/reference/model-configs)

### 1.3 CLI Recipe Patterns

#### Just (Command Runner)

**Model:** Makefile-inspired but simpler
```just
# justfile
version := 'dev'

# Build the project
build:
    go build -ldflags "-X main.Version={{version}}" -o bin/app

# Run tests
test:
    go test ./...

# Format and generate
swag: format
    swag init --pd -d ./internal/controllers

# Recipe with arguments
salute guy:
    @echo "Hello {{guy}}!"
```

**Key Features:**
- **Simple Syntax:** Recipe name + commands
- **Variables:** `variable := value`
- **Dependencies:** `recipe: dependency`
- **Arguments:** `recipe arg1 arg2:`
- **Multi-language:** Write recipes in any language
- **Parallel Execution:** `[parallel]` attribute

**Sources:**
- [Just - Command Runner](https://github.com/casey/just)
- [Justfile became my favorite task runner](https://tduyng.medium.com/justfile-became-my-favorite-task-runner-7a89e3f45d9a)

#### Makefile

**Model:** Target-based build system
```makefile
.PHONY: clean test build

VERSION := dev

build:
	go build -ldflags "-X main.Version=$(VERSION)" -o bin/app

test: build
	go test ./...

clean:
	rm -rf bin/
```

**Key Features:**
- **Phony Targets:** `.PHONY` for non-file targets
- **Dependencies:** Target dependencies via `target: dep1 dep2`
- **Pattern Rules:** `%.o: %.c` for wildcards
- **Variables:** `$(VARIABLE)` syntax

**Sources:**
- [Phony Targets - GNU make](https://www.gnu.org/software/make/manual/html_node/Phony-Targets.html)
- [Makefile Tutorial by Example](https://makefiletutorial.com/)

#### npm scripts

**Model:** JSON configuration
```json
{
  "scripts": {
    "start": "node app.js",
    "test": "jest ./test",
    "build": "webpack --mode production",
    "pretest": "eslint .",
    "postbuild": "echo 'Build complete!'"
  }
}
```

**Key Features:**
- **Pre/Post Hooks:** `pre<script>` and `post<script>`
- **Chaining:** `&&` for sequential, `&` for parallel
- **Argument Passing:** `npm run test -- --coverage`
- **Shorthand:** `npm test` → `npm run test`

**Sources:**
- [npm scripts documentation](https://docs.npmjs.com/cli/v8/using-npm/scripts/)
- [Package JSON Scripts Guide](https://www.upgrad.com/blog/introduction-to-package-json-scripts-in-node-js/)

### 1.4 LangChain/LangGraph (AI Agent Workflows)

#### LangChain LCEL (Expression Language)

**Model:** Pipe-based composition
```python
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

prompt = PromptTemplate.from_template("Describe {city}.")
model = ChatOpenAI(model="gpt-4o-mini")

chain = prompt | model
result = chain.invoke({"city": "Paris"})
```

**Key Features:**
- **Declarative:** `|` pipe operator for composition
- **Streaming:** Built-in streaming support
- **Async:** Native async/await
- **Parallel:** `RunnableParallel` for concurrent execution

**Sources:**
- [LangChain LCEL Guide](https://docs.langchain.com/oss/python/langchain/overview)
- [How to Create LCEL Chains](https://dev.to/stephenc222/how-to-create-lcel-chains-in-langchain-2lno)

#### LangGraph (State Machines)

**Model:** Graph-based state management
```python
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

class MyGraphState(TypedDict):
    count: int
    msg: str

workflow = StateGraph(MyGraphState)
workflow.add_node("increment", lambda state: {"count": state["count"] + 1})
workflow.add_edge(START, "increment")
workflow.add_edge("increment", END)

app = workflow.compile()
result = app.invoke({"count": 0})
```

**Key Features:**
- **State-driven:** Typed state management
- **Nodes:** Individual computation units
- **Edges:** Workflow transitions
- **Persistence:** Built-in state persistence

**Sources:**
- [LangGraph Documentation](https://docs.langchain.com/oss/python/langgraph/graph-api)
- [LangGraph State Machines](https://dev.to/jamesli/langgraph-state-machines-managing-complex-agent-task-flows-in-production-36f4)

---

## 2. Recipe Model Recommendation for EDGAR

### 2.1 Design Principles

1. **Declarative First, Imperative When Needed:** YAML for structure, Python for logic
2. **Human-Readable:** Clear, self-documenting syntax
3. **Type-Safe:** Pydantic validation for schemas
4. **Composable:** Recipes can reference sub-recipes
5. **Portable:** Relative paths and environment variable support
6. **Extensible:** Easy to add new recipe types

### 2.2 File Format: YAML (Primary) + JSON (Secondary)

**Rationale:**
- **Goose uses YAML/JSON** - proven in AI coding tools
- **dbt uses YAML** - proven in data transformation
- **YAML is human-friendly** - easier to write and read than JSON
- **JSON is machine-friendly** - easier for programmatic generation
- **Pydantic supports both** - single schema definition

**Location:**
```
edgar/
├── recipes/                 # Recipe directory
│   ├── fortune100.yaml      # Fortune 100 pipeline
│   ├── tax_analysis.yaml    # Tax expense analysis
│   ├── compensation.yaml    # Executive compensation
│   └── custom/              # User custom recipes
│       └── my_workflow.yaml
├── src/
│   └── edgar_analyzer/
│       └── recipes/
│           ├── __init__.py
│           ├── schema.py    # Pydantic models
│           ├── loader.py    # Recipe loader
│           └── executor.py  # Recipe executor
```

### 2.3 Recipe Schema (YAML)

```yaml
# recipes/fortune100.yaml
version: "1.0"
name: fortune100_pipeline
title: Fortune 100 Full Pipeline
description: |
  Extract SCT (executive compensation) and Tax data for Fortune 100 companies.
  Supports parallel processing and custom output formats.

# Recipe metadata
metadata:
  author: EDGAR Team
  tags: [fortune100, sct, tax, pipeline]
  created: "2025-12-29"
  category: extraction

# Input parameters (with type validation)
parameters:
  - name: rank_start
    type: integer
    required: true
    default: 1
    description: Starting Fortune 100 rank
    validation:
      min: 1
      max: 100

  - name: rank_end
    type: integer
    required: true
    default: 100
    description: Ending Fortune 100 rank
    validation:
      min: 1
      max: 100

  - name: sector
    type: string
    required: false
    default: null
    description: Filter by sector (Technology, Healthcare, etc.)
    validation:
      choices: [Technology, Healthcare, Retail, Energy, Financial]

  - name: output_dir
    type: path
    required: false
    default: "output/fortune100"
    description: Output directory for results

  - name: format
    type: string
    required: false
    default: json
    description: Output format
    validation:
      choices: [json, csv, both]

  - name: max_concurrent
    type: integer
    required: false
    default: 5
    description: Maximum concurrent workers
    validation:
      min: 1
      max: 20

# Environment requirements
environment:
  python_version: ">=3.11"
  required_packages:
    - edgar-analyzer
    - rich
    - pydantic
  env_vars:
    - SEC_API_KEY  # Optional: For higher rate limits

# Steps in the recipe (sequential execution)
steps:
  - name: validate_inputs
    type: python
    module: edgar_analyzer.recipes.validators
    function: validate_fortune100_params
    inputs:
      rank_start: "{{ rank_start }}"
      rank_end: "{{ rank_end }}"
      sector: "{{ sector }}"
    on_failure: exit

  - name: load_companies
    type: python
    module: edgar_analyzer.data.fortune100
    function: get_companies
    inputs:
      rank_start: "{{ rank_start }}"
      rank_end: "{{ rank_end }}"
      sector: "{{ sector }}"
    outputs:
      companies: companies_list

  - name: extract_sct
    type: sub_recipe
    recipe: sct_extraction
    inputs:
      companies: "{{ steps.load_companies.outputs.companies }}"
      output_dir: "{{ output_dir }}/sct"
      format: "{{ format }}"
    parallel: true
    max_workers: "{{ max_concurrent }}"

  - name: extract_tax
    type: sub_recipe
    recipe: tax_extraction
    inputs:
      companies: "{{ steps.load_companies.outputs.companies }}"
      output_dir: "{{ output_dir }}/tax"
      format: "{{ format }}"
    parallel: true
    max_workers: "{{ max_concurrent }}"

  - name: merge_results
    type: python
    module: edgar_analyzer.recipes.mergers
    function: merge_fortune100_results
    inputs:
      sct_results: "{{ steps.extract_sct.outputs.results }}"
      tax_results: "{{ steps.extract_tax.outputs.results }}"
      output_dir: "{{ output_dir }}"
      format: "{{ format }}"
    outputs:
      final_results: merged_data

# Error handling
error_handling:
  strategy: continue  # or: stop, retry
  max_retries: 3
  retry_delay_seconds: 10
  on_failure:
    - type: log
      message: "Fortune 100 pipeline failed: {{ error.message }}"
    - type: cleanup
      function: edgar_analyzer.recipes.cleanup.remove_temp_files

# Output specification
outputs:
  - name: results
    type: file
    path: "{{ output_dir }}/fortune100_results.{{ format }}"
    description: Combined SCT and Tax data

  - name: summary
    type: file
    path: "{{ output_dir }}/summary.json"
    description: Execution summary with stats

# Post-execution hooks
post_execution:
  - type: notification
    enabled: false
    channel: slack
    message: "Fortune 100 pipeline completed. {{ outputs.summary.success_count }}/{{ outputs.summary.total_count }} companies processed."
```

### 2.4 Sub-Recipe Example (SCT Extraction)

```yaml
# recipes/sct_extraction.yaml
version: "1.0"
name: sct_extraction
title: Summary Compensation Table Extraction
description: Extract executive compensation data from DEF 14A filings

parameters:
  - name: companies
    type: array
    required: true
    description: List of companies to process

  - name: output_dir
    type: path
    required: true
    description: Output directory

  - name: format
    type: string
    default: json
    validation:
      choices: [json, csv]

steps:
  - name: fetch_def14a
    type: python
    module: edgar_analyzer.services.sec_api
    function: fetch_def14a_filings
    inputs:
      companies: "{{ companies }}"
    outputs:
      filings: def14a_filings

  - name: extract_sct_tables
    type: extractor
    extractor_id: sct_fortune100_adapter
    inputs:
      filings: "{{ steps.fetch_def14a.outputs.filings }}"
    outputs:
      sct_data: extracted_tables

  - name: save_results
    type: python
    module: edgar_analyzer.recipes.io
    function: save_results
    inputs:
      data: "{{ steps.extract_sct_tables.outputs.sct_data }}"
      output_dir: "{{ output_dir }}"
      format: "{{ format }}"

outputs:
  - name: results
    type: variable
    value: "{{ steps.extract_sct_tables.outputs.sct_data }}"
```

### 2.5 Pydantic Schema (Python)

```python
# src/edgar_analyzer/recipes/schema.py
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator


class ParameterType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    PATH = "path"
    ARRAY = "array"
    OBJECT = "object"


class ParameterValidation(BaseModel):
    min: Optional[Union[int, float]] = None
    max: Optional[Union[int, float]] = None
    choices: Optional[List[str]] = None
    pattern: Optional[str] = None


class Parameter(BaseModel):
    name: str
    type: ParameterType
    required: bool = False
    default: Optional[Any] = None
    description: str
    validation: Optional[ParameterValidation] = None


class StepType(str, Enum):
    PYTHON = "python"
    SUB_RECIPE = "sub_recipe"
    EXTRACTOR = "extractor"
    SHELL = "shell"


class Step(BaseModel):
    name: str
    type: StepType
    module: Optional[str] = None
    function: Optional[str] = None
    recipe: Optional[str] = None  # For sub_recipe
    extractor_id: Optional[str] = None  # For extractor
    command: Optional[str] = None  # For shell
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Optional[Dict[str, str]] = None
    parallel: bool = False
    max_workers: Optional[int] = None
    on_failure: Literal["exit", "continue", "retry"] = "continue"


class ErrorHandling(BaseModel):
    strategy: Literal["continue", "stop", "retry"] = "continue"
    max_retries: int = 3
    retry_delay_seconds: int = 10
    on_failure: List[Dict[str, Any]] = Field(default_factory=list)


class OutputSpec(BaseModel):
    name: str
    type: Literal["file", "variable", "stdout"]
    path: Optional[str] = None
    value: Optional[str] = None
    description: str


class Recipe(BaseModel):
    version: str
    name: str
    title: str
    description: str

    metadata: Optional[Dict[str, Any]] = None
    parameters: List[Parameter] = Field(default_factory=list)
    environment: Optional[Dict[str, Any]] = None
    steps: List[Step]
    error_handling: Optional[ErrorHandling] = None
    outputs: List[OutputSpec] = Field(default_factory=list)
    post_execution: List[Dict[str, Any]] = Field(default_factory=list)

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate version format."""
        if not v.startswith("1."):
            raise ValueError("Only version 1.x is supported")
        return v
```

### 2.6 Recipe Discovery and Registration

**Discovery Mechanism:**

1. **Directory Convention:**
   - Primary: `recipes/` directory in project root
   - User custom: `recipes/custom/`
   - System: `edgar_analyzer/recipes/builtin/`

2. **Registry (Optional):**
   ```json
   {
     "recipes": {
       "fortune100": {
         "path": "recipes/fortune100.yaml",
         "category": "extraction",
         "tags": ["fortune100", "sct", "tax"]
       },
       "tax_analysis": {
         "path": "recipes/tax_analysis.yaml",
         "category": "analysis",
         "tags": ["tax", "10-k"]
       }
     }
   }
   ```

3. **CLI Discovery:**
   ```bash
   # List available recipes
   edgar recipes list

   # Show recipe details
   edgar recipes info fortune100

   # Validate recipe syntax
   edgar recipes validate recipes/fortune100.yaml
   ```

**Loader Implementation:**

```python
# src/edgar_analyzer/recipes/loader.py
import json
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from pydantic import ValidationError

from .schema import Recipe


class RecipeLoader:
    """Load and validate EDGAR recipes."""

    def __init__(self, recipe_dir: Path = Path("recipes")):
        self.recipe_dir = recipe_dir
        self._registry: Dict[str, Recipe] = {}

    def load(self, path: Path) -> Recipe:
        """Load a recipe from YAML or JSON file."""
        if not path.exists():
            raise FileNotFoundError(f"Recipe not found: {path}")

        # Determine format
        if path.suffix in [".yaml", ".yml"]:
            with open(path) as f:
                data = yaml.safe_load(f)
        elif path.suffix == ".json":
            with open(path) as f:
                data = json.load(f)
        else:
            raise ValueError(f"Unsupported format: {path.suffix}")

        # Validate with Pydantic
        try:
            recipe = Recipe(**data)
            self._registry[recipe.name] = recipe
            return recipe
        except ValidationError as e:
            raise ValueError(f"Invalid recipe schema: {e}")

    def discover(self) -> List[Recipe]:
        """Discover all recipes in recipe directory."""
        recipes = []
        for pattern in ["*.yaml", "*.yml", "*.json"]:
            for path in self.recipe_dir.rglob(pattern):
                try:
                    recipe = self.load(path)
                    recipes.append(recipe)
                except Exception as e:
                    print(f"Skipping {path}: {e}")
        return recipes

    def get(self, name: str) -> Optional[Recipe]:
        """Get recipe by name from registry."""
        return self._registry.get(name)
```

### 2.7 Recipe Executor

```python
# src/edgar_analyzer/recipes/executor.py
import asyncio
from typing import Any, Dict

import structlog
from jinja2 import Template

from .schema import Recipe, Step, StepType

logger = structlog.get_logger(__name__)


class RecipeExecutor:
    """Execute EDGAR recipes."""

    def __init__(self, recipe: Recipe):
        self.recipe = recipe
        self.context: Dict[str, Any] = {}

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute recipe with parameters."""
        # 1. Validate parameters
        self._validate_params(params)

        # 2. Initialize context
        self.context = {"params": params, "steps": {}}

        # 3. Execute steps sequentially
        for step in self.recipe.steps:
            logger.info(f"Executing step: {step.name}")
            result = await self._execute_step(step)
            self.context["steps"][step.name] = {"outputs": result}

        # 4. Collect outputs
        outputs = self._collect_outputs()

        # 5. Run post-execution hooks
        await self._run_post_hooks()

        return outputs

    async def _execute_step(self, step: Step) -> Any:
        """Execute a single step."""
        # Resolve inputs with Jinja2 templating
        resolved_inputs = self._resolve_inputs(step.inputs)

        if step.type == StepType.PYTHON:
            return await self._execute_python_step(step, resolved_inputs)
        elif step.type == StepType.SUB_RECIPE:
            return await self._execute_sub_recipe(step, resolved_inputs)
        elif step.type == StepType.EXTRACTOR:
            return await self._execute_extractor(step, resolved_inputs)
        elif step.type == StepType.SHELL:
            return await self._execute_shell(step, resolved_inputs)
        else:
            raise ValueError(f"Unknown step type: {step.type}")

    def _resolve_inputs(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve Jinja2 templates in inputs."""
        resolved = {}
        for key, value in inputs.items():
            if isinstance(value, str):
                template = Template(value)
                resolved[key] = template.render(**self.context)
            else:
                resolved[key] = value
        return resolved

    async def _execute_python_step(self, step: Step, inputs: Dict[str, Any]) -> Any:
        """Execute Python function."""
        import importlib

        module = importlib.import_module(step.module)
        func = getattr(module, step.function)

        if asyncio.iscoroutinefunction(func):
            return await func(**inputs)
        else:
            return func(**inputs)

    async def _execute_sub_recipe(self, step: Step, inputs: Dict[str, Any]) -> Any:
        """Execute sub-recipe."""
        from .loader import RecipeLoader

        loader = RecipeLoader()
        sub_recipe = loader.load(Path(f"recipes/{step.recipe}.yaml"))
        executor = RecipeExecutor(sub_recipe)
        return await executor.execute(inputs)

    async def _execute_extractor(self, step: Step, inputs: Dict[str, Any]) -> Any:
        """Execute extractor by ID."""
        from edgar_analyzer.extractors.registry import get_extractor

        extractor = get_extractor(step.extractor_id)
        return await extractor.extract(**inputs)

    async def _execute_shell(self, step: Step, inputs: Dict[str, Any]) -> Any:
        """Execute shell command."""
        import subprocess

        template = Template(step.command)
        cmd = template.render(**inputs)

        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True
        )

        if result.returncode != 0:
            raise RuntimeError(f"Command failed: {result.stderr}")

        return result.stdout

    def _validate_params(self, params: Dict[str, Any]) -> None:
        """Validate provided parameters against schema."""
        for param_def in self.recipe.parameters:
            value = params.get(param_def.name, param_def.default)

            if param_def.required and value is None:
                raise ValueError(f"Required parameter missing: {param_def.name}")

            # Type validation
            # ... (implement type checking)

            # Custom validation
            if param_def.validation:
                # ... (implement validation rules)
                pass

    def _collect_outputs(self) -> Dict[str, Any]:
        """Collect final outputs."""
        outputs = {}
        for output_spec in self.recipe.outputs:
            if output_spec.type == "variable":
                template = Template(output_spec.value)
                outputs[output_spec.name] = template.render(**self.context)
            # ... handle file outputs
        return outputs

    async def _run_post_hooks(self) -> None:
        """Run post-execution hooks."""
        for hook in self.recipe.post_execution:
            # ... implement hook execution
            pass
```

### 2.8 CLI Integration

```python
# src/edgar_analyzer/cli/commands/recipes.py
import click
from pathlib import Path
from rich.console import Console
from rich.table import Table

from edgar_analyzer.recipes.loader import RecipeLoader
from edgar_analyzer.recipes.executor import RecipeExecutor

console = Console()


@click.group(name="recipes")
def recipes_cli():
    """Recipe management commands."""
    pass


@recipes_cli.command(name="list")
def list_recipes():
    """List available recipes."""
    loader = RecipeLoader()
    recipes = loader.discover()

    table = Table(title="Available Recipes")
    table.add_column("Name", style="cyan")
    table.add_column("Title", style="green")
    table.add_column("Category", style="yellow")
    table.add_column("Tags", style="magenta")

    for recipe in recipes:
        tags = ", ".join(recipe.metadata.get("tags", []))
        category = recipe.metadata.get("category", "N/A")
        table.add_row(recipe.name, recipe.title, category, tags)

    console.print(table)


@recipes_cli.command(name="run")
@click.argument("recipe_name")
@click.option("--param", "-p", multiple=True, help="Parameter: key=value")
@click.option("--config", "-c", type=click.Path(exists=True), help="Config file (YAML/JSON)")
def run_recipe(recipe_name: str, param: tuple, config: str):
    """Run a recipe."""
    loader = RecipeLoader()
    recipe_path = Path(f"recipes/{recipe_name}.yaml")
    recipe = loader.load(recipe_path)

    # Parse parameters
    params = {}
    if config:
        # Load from config file
        import yaml
        with open(config) as f:
            params = yaml.safe_load(f)

    for p in param:
        key, value = p.split("=", 1)
        params[key] = value

    # Execute
    executor = RecipeExecutor(recipe)
    result = asyncio.run(executor.execute(params))

    console.print(f"[green]Recipe completed successfully![/green]")
    console.print(result)


@recipes_cli.command(name="validate")
@click.argument("recipe_path", type=click.Path(exists=True))
def validate_recipe(recipe_path: str):
    """Validate recipe syntax."""
    try:
        loader = RecipeLoader()
        recipe = loader.load(Path(recipe_path))
        console.print(f"[green]✓[/green] Recipe is valid: {recipe.name}")
    except Exception as e:
        console.print(f"[red]✗[/red] Validation failed: {e}")
        raise click.Abort()


@recipes_cli.command(name="info")
@click.argument("recipe_name")
def recipe_info(recipe_name: str):
    """Show recipe details."""
    loader = RecipeLoader()
    recipe_path = Path(f"recipes/{recipe_name}.yaml")
    recipe = loader.load(recipe_path)

    console.print(f"[bold]{recipe.title}[/bold]")
    console.print(f"Name: {recipe.name}")
    console.print(f"Version: {recipe.version}")
    console.print(f"\n{recipe.description}")

    # Parameters table
    if recipe.parameters:
        table = Table(title="Parameters")
        table.add_column("Name")
        table.add_column("Type")
        table.add_column("Required")
        table.add_column("Default")
        table.add_column("Description")

        for param in recipe.parameters:
            table.add_row(
                param.name,
                param.type,
                "Yes" if param.required else "No",
                str(param.default) if param.default else "-",
                param.description
            )

        console.print(table)
```

**Usage:**
```bash
# List all recipes
edgar recipes list

# Show recipe info
edgar recipes info fortune100

# Validate recipe
edgar recipes validate recipes/fortune100.yaml

# Run recipe with inline parameters
edgar recipes run fortune100 -p rank_start=1 -p rank_end=10 -p format=json

# Run recipe with config file
edgar recipes run fortune100 --config configs/fortune100_params.yaml
```

---

## 3. Example Recipe for Fortune 100

See [Section 2.3](#23-recipe-schema-yaml) for the complete `fortune100.yaml` example.

**Key Features Demonstrated:**
1. ✅ **Parameterization:** 6 typed parameters with validation
2. ✅ **Sub-recipes:** Calls `sct_extraction` and `tax_extraction` sub-recipes
3. ✅ **Parallel Execution:** SCT and Tax extraction run concurrently
4. ✅ **Error Handling:** Retry logic with configurable strategy
5. ✅ **Output Specification:** Multiple output files with descriptions
6. ✅ **Post-Execution Hooks:** Optional Slack notifications
7. ✅ **Environment Requirements:** Python version and package dependencies

---

## 4. Implementation Plan

### Phase 1: Core Infrastructure (Week 1)

**Tasks:**
1. ✅ Create `recipes/` directory structure
2. ✅ Implement Pydantic schema (`schema.py`)
3. ✅ Implement recipe loader (`loader.py`)
4. ✅ Write unit tests for loader and schema validation
5. ✅ Add basic CLI commands (`recipes list`, `recipes validate`)

**Deliverables:**
- `src/edgar_analyzer/recipes/schema.py`
- `src/edgar_analyzer/recipes/loader.py`
- `tests/unit/test_recipe_loader.py`
- `src/edgar_analyzer/cli/commands/recipes.py`

### Phase 2: Recipe Executor (Week 2)

**Tasks:**
1. ✅ Implement executor framework (`executor.py`)
2. ✅ Add Jinja2 templating support
3. ✅ Implement step types: Python, Sub-Recipe, Extractor
4. ✅ Add error handling and retry logic
5. ✅ Write integration tests
6. ✅ Add `recipes run` command

**Deliverables:**
- `src/edgar_analyzer/recipes/executor.py`
- `tests/integration/test_recipe_executor.py`
- Updated CLI with `recipes run`

### Phase 3: Fortune 100 Migration (Week 3)

**Tasks:**
1. ✅ Create `recipes/fortune100.yaml`
2. ✅ Create sub-recipes: `sct_extraction.yaml`, `tax_extraction.yaml`
3. ✅ Migrate current `fortune100` CLI to use recipe executor
4. ✅ Add parallel execution support
5. ✅ Write end-to-end tests
6. ✅ Update documentation

**Deliverables:**
- `recipes/fortune100.yaml`
- `recipes/sct_extraction.yaml`
- `recipes/tax_extraction.yaml`
- Updated `fortune100` commands using recipes
- `docs/recipes/README.md`

### Phase 4: Advanced Features (Week 4)

**Tasks:**
1. ✅ Add recipe registry with search/filter
2. ✅ Implement shell command step type
3. ✅ Add output file handling
4. ✅ Implement post-execution hooks (notifications)
5. ✅ Add recipe generation wizard (`recipes create`)
6. ✅ Write comprehensive user documentation

**Deliverables:**
- Recipe registry (`recipes.json`)
- Shell step type support
- `recipes create` wizard
- `docs/recipes/user_guide.md`
- `docs/recipes/api_reference.md`

### Phase 5: Additional Recipes (Ongoing)

**Example Recipes to Create:**
- `tax_analysis.yaml` - Tax expense comparative analysis
- `compensation_trends.yaml` - Executive compensation trends
- `filing_search.yaml` - Search across EDGAR filings
- `custom_extraction.yaml` - User-defined extraction workflow

---

## 5. Comparison Matrix

| Feature | Goose | Prefect | Dagster | dbt | Just | EDGAR Recipe Model |
|---------|-------|---------|---------|-----|------|-------------------|
| **File Format** | YAML/JSON | Python | Python | YAML+SQL | Justfile | YAML/JSON |
| **Parameterization** | ✅ Jinja2 | ✅ Function args | ✅ Config class | ✅ Jinja2 | ✅ Variables | ✅ Jinja2 |
| **Type Safety** | ⚠️ Partial | ✅ Type hints | ✅ Type hints | ⚠️ Limited | ❌ No | ✅ Pydantic |
| **Composition** | ✅ Sub-recipes | ✅ Task deps | ✅ Op graphs | ✅ `ref()` | ✅ Dependencies | ✅ Sub-recipes |
| **Validation** | ⚠️ Runtime | ✅ Runtime | ✅ Runtime | ✅ Schema tests | ❌ No | ✅ Schema + Runtime |
| **Retry Logic** | ✅ Built-in | ✅ Built-in | ✅ Built-in | ❌ No | ❌ No | ✅ Built-in |
| **Parallel Execution** | ⚠️ Limited | ✅ Full | ✅ Full | ✅ Full | ✅ `[parallel]` | ✅ Step-level |
| **Discovery** | File/GitHub | Code | Code | Convention | File | Directory + Registry |
| **AI Integration** | ✅ MCP servers | ❌ No | ❌ No | ❌ No | ❌ No | ✅ Extractor registry |
| **Learning Curve** | Low | Medium | High | Medium | Very Low | Low-Medium |

**Legend:**
- ✅ Full support
- ⚠️ Partial support
- ❌ No support

---

## 6. Design Questions Answered

### Q1: File format: YAML vs JSON vs Python?

**Answer:** **YAML (primary) + JSON (secondary)**

**Rationale:**
- YAML is human-readable and easier to write/edit
- JSON is machine-friendly for programmatic generation
- Both supported by Pydantic with single schema definition
- Follows Goose and dbt patterns (proven in similar domains)
- Python used only for step implementation, not workflow definition

### Q2: Discovery: Directory convention vs registry?

**Answer:** **Directory convention (`recipes/`) + Optional registry**

**Rationale:**
- **Directory convention** provides zero-config discovery (like dbt models)
- **Optional registry** enables advanced features:
  - Categorization and tagging
  - Search and filtering
  - Metadata storage
  - GitHub recipe sharing (like Goose)
- Best of both worlds: simplicity + extensibility

**Discovery Flow:**
```
1. Check recipes/ directory (primary)
2. Check recipes/custom/ (user recipes)
3. Check recipes.json registry (if exists)
4. Check EDGAR_RECIPES_REPO env var (GitHub recipes)
```

### Q3: Parameterization: How to pass variables?

**Answer:** **Jinja2 templating** with typed parameters

**Rationale:**
- Jinja2 is proven (Goose, dbt, Ansible use it)
- Supports complex expressions: `{{ rank_start }}`, `{{ steps.load.outputs.data }}`
- Familiar syntax for Python developers
- Type validation via Pydantic before template rendering
- Environment variable support: `{{ env.SEC_API_KEY }}`

**Example:**
```yaml
parameters:
  - name: rank_start
    type: integer
    default: 1

steps:
  - name: load_companies
    inputs:
      rank_start: "{{ rank_start }}"  # Template resolved at runtime
      rank_end: "{{ rank_end }}"
```

### Q4: Composition: Can recipes call other recipes?

**Answer:** **Yes, via sub-recipes**

**Rationale:**
- Enables modular, reusable components
- Follows Goose sub-recipe pattern
- Similar to dbt's `ref()` but for entire workflows
- Prevents duplication (DRY principle)

**Example:**
```yaml
# Main recipe
steps:
  - name: extract_sct
    type: sub_recipe
    recipe: sct_extraction  # References recipes/sct_extraction.yaml
    inputs:
      companies: "{{ companies }}"
```

**Composition Graph:**
```
fortune100.yaml
├── sct_extraction.yaml
│   ├── fetch_def14a (Python step)
│   ├── extract_sct_tables (Extractor step)
│   └── save_results (Python step)
└── tax_extraction.yaml
    ├── fetch_10k (Python step)
    ├── extract_tax_data (Extractor step)
    └── save_results (Python step)
```

### Q5: Validation: Schema enforcement?

**Answer:** **Pydantic models for schema validation**

**Rationale:**
- **Compile-time validation** via Pydantic
- **Runtime validation** during parameter resolution
- **Type safety** for all recipe fields
- **Custom validators** for business logic
- **Clear error messages** for debugging

**Validation Layers:**
1. **Schema validation** (Pydantic): Recipe structure correctness
2. **Parameter validation** (Pydantic): Type and constraint checks
3. **Step validation** (Executor): Input/output compatibility
4. **Runtime validation** (Executor): Data quality checks

**Example:**
```python
# Schema validation
recipe = Recipe(**yaml_data)  # Raises ValidationError if invalid

# Parameter validation
@field_validator("rank_start")
def validate_rank_start(cls, v):
    if v < 1 or v > 100:
        raise ValueError("rank_start must be between 1 and 100")
    return v
```

---

## 7. Migration Path for Existing fortune100 CLI

### Current State

```python
# src/edgar_analyzer/cli/commands/fortune100.py
@click.group(name="fortune100")
def fortune100_cli():
    pass

@fortune100_cli.command(name="extract")
@click.option("--rank-start", type=int, default=1)
@click.option("--rank-end", type=int, default=100)
# ... 10+ options
def extract(rank_start, rank_end, sector, output, format, max_concurrent, verbose):
    # 200+ lines of implementation
    pass
```

**Problems:**
- ❌ Hardcoded workflow logic in CLI
- ❌ Difficult to test (Click integration tests needed)
- ❌ Not reusable outside CLI
- ❌ Parameters scattered across decorators
- ❌ No validation beyond Click types

### Future State (Recipe-based)

**Step 1: Create Recipe Definition**
```yaml
# recipes/fortune100.yaml
# (See Section 2.3 for full example)
```

**Step 2: Simplify CLI to Recipe Dispatcher**
```python
# src/edgar_analyzer/cli/commands/fortune100.py
from edgar_analyzer.recipes import RecipeLoader, RecipeExecutor

@click.group(name="fortune100")
def fortune100_cli():
    """Fortune 100 pipeline (recipe-based)."""
    pass

@fortune100_cli.command(name="extract")
@click.option("--rank-start", "-s", type=int, default=1)
@click.option("--rank-end", "-e", type=int, default=100)
@click.option("--sector", type=str)
@click.option("--output", "-o", type=click.Path(), default="output/fortune100")
@click.option("--format", "-f", type=click.Choice(["json", "csv"]), default="json")
@click.option("--config", "-c", type=click.Path(exists=True), help="Recipe config file")
def extract(rank_start, rank_end, sector, output, format, config):
    """Extract Fortune 100 data (uses recipe system)."""
    # Load recipe
    loader = RecipeLoader()
    recipe = loader.load(Path("recipes/fortune100.yaml"))

    # Build parameters
    params = {
        "rank_start": rank_start,
        "rank_end": rank_end,
        "sector": sector,
        "output_dir": output,
        "format": format,
    }

    # Override with config file if provided
    if config:
        import yaml
        with open(config) as f:
            params.update(yaml.safe_load(f))

    # Execute recipe
    executor = RecipeExecutor(recipe)
    result = asyncio.run(executor.execute(params))

    console.print("[green]✓[/green] Fortune 100 extraction complete!")
    console.print(f"Results: {result}")
```

**Benefits:**
- ✅ **Separation of Concerns:** Workflow in YAML, CLI is thin wrapper
- ✅ **Testability:** Test recipe independently of CLI
- ✅ **Reusability:** Recipe can be run from CLI, API, or cron job
- ✅ **Maintainability:** Workflow changes don't require code changes
- ✅ **Validation:** Pydantic ensures type safety
- ✅ **Documentation:** Recipe YAML is self-documenting

**Migration Checklist:**
- [ ] Create `recipes/fortune100.yaml`
- [ ] Create sub-recipes: `sct_extraction.yaml`, `tax_extraction.yaml`
- [ ] Implement Python step functions (extract logic from CLI)
- [ ] Update CLI to use recipe executor
- [ ] Add backward compatibility layer (deprecation warnings)
- [ ] Write integration tests for recipe-based flow
- [ ] Update documentation
- [ ] Deprecate old CLI implementation (3-month sunset period)

---

## 8. Future Enhancements

### Recipe Versioning
```yaml
version: "2.0"  # Breaking changes allowed
migrations:
  from: "1.0"
  script: migrations/fortune100_v1_to_v2.py
```

### Recipe Templates
```bash
edgar recipes create --template extraction
# Interactive wizard generates recipe from template
```

### Recipe Marketplace
```bash
edgar recipes install community/tax-analysis
# Install recipe from GitHub: edgar-recipes/community/tax-analysis
```

### Visual Recipe Builder
```python
# Web UI for building recipes graphically
edgar recipes ui
```

### Recipe Linting
```bash
edgar recipes lint recipes/fortune100.yaml
# Check for anti-patterns, optimize steps
```

### Recipe Testing Framework
```yaml
# recipe_test.yaml
tests:
  - name: test_fortune100_top10
    recipe: fortune100
    inputs:
      rank_start: 1
      rank_end: 10
    expect:
      outputs.results: not_empty
      outputs.summary.success_count: gte(8)
```

---

## 9. Conclusion

The recommended recipe model for EDGAR provides:

1. **Declarative Workflows:** YAML/JSON for clear, version-controlled workflow definitions
2. **Type Safety:** Pydantic validation for schema enforcement
3. **Composability:** Sub-recipes enable modular, reusable components
4. **Extensibility:** Easy to add new step types and integrations
5. **Developer Experience:** Familiar syntax (Jinja2, YAML), clear error messages
6. **Production-Ready:** Built-in retry logic, error handling, parallel execution

**Next Steps:**
1. Review this design with team
2. Implement Phase 1 (Core Infrastructure)
3. Create POC recipe for `fortune100`
4. Gather feedback and iterate
5. Roll out to production gradually

**Key Decision Points:**
- ✅ **File Format:** YAML/JSON
- ✅ **Discovery:** Directory + Registry
- ✅ **Parameterization:** Jinja2
- ✅ **Composition:** Sub-recipes
- ✅ **Validation:** Pydantic

This design balances the proven patterns from Goose (AI coding tools), data pipeline systems (Prefect, Dagster, dbt), and CLI tools (Just, Makefile), tailored specifically for EDGAR's extraction and analysis workflows.

---

## Appendix A: References

### AI/ML Workflow Systems
- [Block Goose - GitHub](https://github.com/block/goose)
- [Goose Recipe Reference](https://block.github.io/goose/docs/guides/recipes/recipe-reference/)
- [Building Gift Tag Generator with Goose](https://www.nickyt.co/blog/advent-of-ai-2025-day-9-building-a-gift-tag-generator-with-goose-recipes-3i73/)
- [Subrecipes in Goose](https://block.github.io/goose/blog/2025/09/15/subrecipes-in-goose/)
- [Prefect Workflows](https://docs.prefect.io/v3/how-to-guides/workflows/write-and-run)
- [Dagster Documentation](https://docs.dagster.io/)
- [dbt YAML Files Guide](https://medium.com/@23saini/a-beginners-guide-to-dbt-yaml-files-3e718719fd9c)

### CLI Recipe Patterns
- [Just Command Runner](https://github.com/casey/just)
- [Justfile Tutorial](https://tduyng.medium.com/justfile-became-my-favorite-task-runner-7a89e3f45d9a)
- [GNU Make - Phony Targets](https://www.gnu.org/software/make/manual/html_node/Phony-Targets.html)
- [Makefile Tutorial](https://makefiletutorial.com/)
- [npm scripts documentation](https://docs.npmjs.com/cli/v8/using-npm/scripts/)

### LangChain/LangGraph
- [LangChain LCEL](https://docs.langchain.com/oss/python/langchain/overview)
- [LangGraph State Machines](https://dev.to/jamesli/langgraph-state-machines-managing-complex-agent-task-flows-in-production-36f4)
- [LangGraph Documentation](https://docs.langchain.com/oss/python/langgraph/graph-api)

### Python Libraries
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Jinja2 Documentation](https://jinja.palletsprojects.com/)
- [Click CLI Framework](https://click.palletsprojects.com/)
- [Rich Console Library](https://rich.readthedocs.io/)

---

## Appendix B: Glossary

- **Recipe:** A declarative workflow definition in YAML/JSON format
- **Sub-recipe:** A recipe referenced by another recipe for composition
- **Step:** An individual unit of work in a recipe (Python function, extractor, sub-recipe, shell command)
- **Parameter:** A typed input variable for a recipe
- **Jinja2:** Template engine for dynamic value resolution
- **Pydantic:** Python library for data validation using type hints
- **Extractor:** EDGAR component that extracts data from SEC filings
- **Registry:** Optional catalog of available recipes with metadata
- **Discovery:** Process of finding and loading available recipes
- **Executor:** Component that runs recipe steps and manages workflow execution

---

**Document Version:** 1.0
**Last Updated:** 2025-12-29
**Author:** Research Agent
**Review Status:** Draft - Awaiting Team Review
