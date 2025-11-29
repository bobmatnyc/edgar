"""Architecture constraint definitions for code generation.

This module defines the architecture constraints that generated code
must follow, including interface requirements and design patterns.
"""

from typing import Any

from pydantic import BaseModel, Field


class InterfaceRequirement(BaseModel):
    """Required interface definition.

    Attributes:
        name: Interface name
        methods: Required method signatures
        description: Interface purpose
    """

    name: str = Field(..., description="Interface name")
    methods: list[str] = Field(..., description="Required method signatures")
    description: str = Field(..., description="Interface purpose")


class DesignPattern(BaseModel):
    """Required design pattern.

    Attributes:
        pattern: Pattern name
        requirements: Pattern requirements
        examples: Example implementations
    """

    pattern: str = Field(..., description="Pattern name (DI, Repository, etc.)")
    requirements: list[str] = Field(..., description="Pattern requirements")
    examples: list[str] = Field(default_factory=list, description="Example code")


class CodeQualityRule(BaseModel):
    """Code quality requirement.

    Attributes:
        rule: Rule name
        description: Rule description
        severity: Rule severity (error, warning, info)
    """

    rule: str = Field(..., description="Rule name")
    description: str = Field(..., description="Rule description")
    severity: str = Field(
        default="error",
        description="error|warning|info",
    )


class ArchitectureConstraints(BaseModel):
    """Complete architecture constraints for code generation.

    This model defines all architecture requirements that generated code
    must satisfy, used by Coder Mode and validation pipeline.

    Attributes:
        interfaces: Required interfaces to implement
        design_patterns: Required design patterns
        type_safety: Type safety requirements
        code_quality: Code quality rules
        forbidden_patterns: Patterns to avoid
    """

    interfaces: list[InterfaceRequirement] = Field(
        default_factory=list,
        description="Required interfaces",
    )
    design_patterns: list[DesignPattern] = Field(
        default_factory=list,
        description="Required design patterns",
    )
    type_safety: dict[str, Any] = Field(
        default_factory=lambda: {
            "require_type_hints": True,
            "require_return_types": True,
            "forbid_any_type": True,
            "require_pydantic_models": True,
        },
        description="Type safety requirements",
    )
    code_quality: list[CodeQualityRule] = Field(
        default_factory=list,
        description="Code quality rules",
    )
    forbidden_patterns: list[str] = Field(
        default_factory=lambda: [
            "global variables",
            "hardcoded configuration",
            "bare except clauses",
            "mutable default arguments",
        ],
        description="Patterns to avoid",
    )

    @classmethod
    def default(cls) -> "ArchitectureConstraints":
        """Create default architecture constraints.

        Returns:
            ArchitectureConstraints with standard requirements
        """
        return cls(
            interfaces=[
                InterfaceRequirement(
                    name="IDataSource",
                    methods=["async def fetch(self) -> dict[str, Any]"],
                    description="Interface for fetching raw data from external sources",
                ),
                InterfaceRequirement(
                    name="IDataExtractor",
                    methods=["def extract(self, raw_data: dict[str, Any]) -> BaseModel"],
                    description="Interface for extracting structured data",
                ),
            ],
            design_patterns=[
                DesignPattern(
                    pattern="Dependency Injection",
                    requirements=[
                        "Use frozen dataclasses",
                        "Inject all dependencies via constructor",
                        "No hardcoded configuration",
                    ],
                ),
                DesignPattern(
                    pattern="Pydantic Validation",
                    requirements=[
                        "Use Pydantic BaseModel for all data structures",
                        "Add field validators for complex validation",
                        "Document all fields with descriptions",
                    ],
                ),
            ],
            code_quality=[
                CodeQualityRule(
                    rule="PEP 8 Compliance",
                    description="Follow Python style guide",
                    severity="error",
                ),
                CodeQualityRule(
                    rule="Docstring Coverage",
                    description="All public APIs must have docstrings",
                    severity="error",
                ),
                CodeQualityRule(
                    rule="Max Function Length",
                    description="Functions should be <50 lines",
                    severity="warning",
                ),
            ],
        )
