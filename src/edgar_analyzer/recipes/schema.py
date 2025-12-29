"""Recipe schema definitions using Pydantic for validation.

This module defines the data models for recipes, steps, and parameters.
All recipe YAML files are validated against these schemas.
"""

from enum import Enum
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator, computed_field


class ParameterType(str, Enum):
    """Supported parameter types for recipe inputs."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"


class Parameter(BaseModel):
    """Recipe parameter definition.

    Parameters can be required or optional, with default values and validation rules.

    Example:
        name: rank_start
        type: integer
        required: true
        description: Starting rank for Fortune 100 companies
        validation:
          min: 1
          max: 100
    """

    name: str = Field(..., description="Parameter name")
    type: ParameterType = Field(default=ParameterType.STRING, description="Data type")
    required: bool = Field(default=False, description="Whether parameter is required")
    default: Optional[Any] = Field(default=None, description="Default value if not provided")
    description: Optional[str] = Field(default=None, description="Human-readable description")
    validation: Optional[dict[str, Any]] = Field(
        default=None, description="Validation rules (min, max, pattern, etc.)"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure parameter names are valid Python identifiers."""
        if not v.isidentifier():
            raise ValueError(f"Parameter name must be a valid identifier: {v}")
        return v


class StepType(str, Enum):
    """Supported step types for recipe execution."""

    PYTHON = "python"  # Execute Python function
    EXTRACTOR = "extractor"  # Run EDGAR extractor (SCT, Tax, etc.)
    SUB_RECIPE = "sub_recipe"  # Execute another recipe
    SHELL = "shell"  # Execute shell command (use sparingly)


class PythonStep(BaseModel):
    """Python function execution step.

    Example:
        type: python
        function: edgar_analyzer.utils.format_results
        inputs:
          data: $steps.extract_sct.output
    """

    function: str = Field(..., description="Fully qualified function name")


class ExtractorStep(BaseModel):
    """EDGAR extractor execution step.

    Example:
        type: extractor
        extractor: SCTAdapter
        filing_type: DEF 14A
        inputs:
          cik: $params.cik
    """

    extractor: str = Field(..., description="Extractor class name (SCTAdapter, TaxAdapter)")
    filing_type: str = Field(..., description="SEC filing type (DEF 14A, 10-K, etc.)")


class SubRecipeStep(BaseModel):
    """Sub-recipe execution step.

    Example:
        type: sub_recipe
        recipe: sct_extraction.yaml
        inputs:
          cik: $params.cik
    """

    recipe: str = Field(..., description="Path to sub-recipe YAML file")


class ShellStep(BaseModel):
    """Shell command execution step (use with caution).

    Example:
        type: shell
        command: wget $params.url -O /tmp/data.json
    """

    command: str = Field(..., description="Shell command to execute")


class Step(BaseModel):
    """Recipe execution step.

    Each step has a type and type-specific configuration. Steps can reference
    previous step outputs and recipe parameters using $steps.* and $params.* syntax.

    Example:
        - name: extract_sct
          type: extractor
          extractor: SCTAdapter
          filing_type: DEF 14A
          inputs:
            cik: $params.cik
          outputs:
            - sct_data
          condition: $params.include_sct == true
    """

    name: str = Field(..., description="Step identifier (unique within recipe)")
    type: StepType = Field(..., description="Step type")

    # Type-specific configurations (only one should be set based on type)
    python: Optional[PythonStep] = Field(default=None, description="Python step config")
    extractor: Optional[ExtractorStep] = Field(default=None, description="Extractor step config")
    sub_recipe: Optional[SubRecipeStep] = Field(default=None, description="Sub-recipe step config")
    shell: Optional[ShellStep] = Field(default=None, description="Shell step config")

    # Common fields
    inputs: Optional[dict[str, Any]] = Field(
        default=None, description="Input data (can reference $params.* and $steps.*)"
    )
    outputs: Optional[list[str]] = Field(default=None, description="Output variable names")
    condition: Optional[str] = Field(
        default=None, description="Conditional execution expression"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure step names are valid identifiers."""
        if not v.isidentifier():
            raise ValueError(f"Step name must be a valid identifier: {v}")
        return v


class Recipe(BaseModel):
    """Recipe definition for EDGAR data extraction pipelines.

    A recipe defines a sequence of steps to extract and process data from SEC filings.
    Recipes can be parameterized and composed using sub-recipes.

    Directory Structure:
        recipes/
        ├── recipe_name/
        │   ├── config.yaml      # Recipe definition
        │   ├── input/           # Input files (optional)
        │   └── output/          # Output files (generated)

    Example YAML (config.yaml):
        version: "1.0"
        name: fortune100_pipeline
        title: Fortune 100 SCT + Tax Extraction
        description: Extract executive compensation and tax data
        parameters:
          - name: rank_start
            type: integer
            required: true
          - name: rank_end
            type: integer
            required: true
        steps:
          - name: load_companies
            type: python
            function: load_fortune_100_companies
          - name: extract_sct
            type: sub_recipe
            recipe: sct_extraction
    """

    version: str = Field(default="1.0", description="Recipe schema version")
    name: str = Field(..., description="Recipe identifier (used for references)")
    title: Optional[str] = Field(default=None, description="Human-readable title")
    description: Optional[str] = Field(default=None, description="Recipe description")
    parameters: list[Parameter] = Field(default_factory=list, description="Recipe parameters")
    steps: list[Step] = Field(default_factory=list, description="Execution steps")
    error_handling: Optional[dict[str, Any]] = Field(
        default=None, description="Error handling configuration"
    )

    # Recipe directory metadata (set by loader)
    recipe_dir: Optional[Path] = Field(
        default=None,
        description="Absolute path to recipe directory",
        exclude=True  # Not part of YAML definition
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure recipe names are valid identifiers."""
        if not v.isidentifier():
            raise ValueError(f"Recipe name must be a valid identifier: {v}")
        return v

    @field_validator("steps")
    @classmethod
    def validate_steps(cls, v: list[Step]) -> list[Step]:
        """Ensure step names are unique within recipe."""
        step_names = [step.name for step in v]
        if len(step_names) != len(set(step_names)):
            raise ValueError("Step names must be unique within a recipe")
        return v

    @computed_field
    @property
    def input_dir(self) -> Optional[Path]:
        """Get the input directory for this recipe.

        Returns:
            Path to input/ subdirectory if recipe_dir is set, None otherwise
        """
        if self.recipe_dir:
            return self.recipe_dir / "input"
        return None

    @computed_field
    @property
    def output_dir(self) -> Optional[Path]:
        """Get the output directory for this recipe.

        Returns:
            Path to output/ subdirectory if recipe_dir is set, None otherwise
        """
        if self.recipe_dir:
            return self.recipe_dir / "output"
        return None

    @computed_field
    @property
    def config_path(self) -> Optional[Path]:
        """Get the config.yaml path for this recipe.

        Returns:
            Path to config.yaml if recipe_dir is set, None otherwise
        """
        if self.recipe_dir:
            return self.recipe_dir / "config.yaml"
        return None
