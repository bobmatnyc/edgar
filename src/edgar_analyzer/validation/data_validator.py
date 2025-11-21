"""Data validation framework for Edgar Analyzer."""

import re
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Union

import structlog
from pydantic import BaseModel, Field

from edgar_analyzer.models.company import ExecutiveCompensation, TaxExpense

logger = structlog.get_logger(__name__)


class ValidationResult(BaseModel):
    """Result of a data validation check."""
    
    is_valid: bool = Field(..., description="Whether the validation passed")
    confidence_score: float = Field(..., description="Confidence score (0.0-1.0)")
    message: str = Field(..., description="Validation message")
    severity: str = Field(..., description="Severity level: INFO, WARNING, ERROR, CRITICAL")
    field_name: Optional[str] = Field(None, description="Field that was validated")
    expected_value: Optional[Union[str, float, int]] = Field(None, description="Expected value")
    actual_value: Optional[Union[str, float, int]] = Field(None, description="Actual value")
    suggestion: Optional[str] = Field(None, description="Suggestion for fixing the issue")


class DataValidator:
    """Comprehensive data validation framework."""
    
    def __init__(self):
        """Initialize data validator."""
        self.validation_rules = self._load_validation_rules()
        logger.info("Data validator initialized")
    
    def _load_validation_rules(self) -> Dict:
        """Load validation rules and thresholds."""
        return {
            "tax_expense": {
                "min_value": 0,
                "max_value": 1_000_000_000_000,  # $1T max
                "reasonable_range": (1_000_000, 100_000_000_000),  # $1M - $100B
                "negative_tolerance": 0.05,  # 5% can be negative (refunds)
            },
            "executive_compensation": {
                "min_value": 0,
                "max_value": 1_000_000_000,  # $1B max
                "reasonable_range": (100_000, 100_000_000),  # $100K - $100M
                "ceo_multiplier_max": 1000,  # CEO shouldn't be >1000x median
            },
            "effective_tax_rate": {
                "min_value": -1.0,  # Can be negative (refunds)
                "max_value": 1.0,   # 100% max
                "reasonable_range": (0.0, 0.35),  # 0% - 35%
            },
            "company_names": {
                "min_length": 3,
                "max_length": 200,
                "required_patterns": [r"[A-Za-z]"],  # Must contain letters
                "forbidden_patterns": [r"^\d+$"],    # Can't be all numbers
            }
        }
    
    def validate_tax_expense(self, tax_expense: TaxExpense) -> List[ValidationResult]:
        """Validate tax expense data."""
        results = []
        rules = self.validation_rules["tax_expense"]
        
        # Validate total tax expense
        if tax_expense.total_tax_expense is not None:
            total_tax = float(tax_expense.total_tax_expense)
            results.extend(self._validate_numeric_field(
                "total_tax_expense", total_tax, rules, "Tax Expense"
            ))
        else:
            results.append(ValidationResult(
                is_valid=False,
                confidence_score=0.0,
                message="Total tax expense is null",
                severity="ERROR",
                field_name="total_tax_expense",
                suggestion="Ensure tax expense data is properly extracted"
            ))
            return results

        # Validate current vs deferred consistency
        current_tax = float(tax_expense.current_tax_expense) if tax_expense.current_tax_expense is not None else 0.0
        deferred_tax = float(tax_expense.deferred_tax_expense) if tax_expense.deferred_tax_expense is not None else 0.0
        calculated_total = current_tax + deferred_tax
        
        if abs(calculated_total - total_tax) > max(abs(total_tax) * 0.01, 1000):  # 1% or $1K tolerance
            results.append(ValidationResult(
                is_valid=False,
                confidence_score=0.3,
                message=f"Tax components don't sum to total: {current_tax:,.0f} + {deferred_tax:,.0f} ≠ {total_tax:,.0f}",
                severity="WARNING",
                field_name="tax_expense_consistency",
                expected_value=calculated_total,
                actual_value=total_tax,
                suggestion="Check if there are additional tax components not captured"
            ))
        else:
            results.append(ValidationResult(
                is_valid=True,
                confidence_score=0.9,
                message="Tax expense components are consistent",
                severity="INFO",
                field_name="tax_expense_consistency"
            ))
        
        # Note: Effective tax rate calculation would need to be added to the model
        # For now, we skip this validation as the field doesn't exist in TaxExpense
        
        return results
    
    def validate_executive_compensation(self, compensation: ExecutiveCompensation) -> List[ValidationResult]:
        """Validate executive compensation data."""
        results = []
        rules = self.validation_rules["executive_compensation"]
        
        # Validate total compensation
        if compensation.total_compensation is not None:
            total_comp = float(compensation.total_compensation)
            results.extend(self._validate_numeric_field(
                "total_compensation", total_comp, rules, "Total Compensation"
            ))
        else:
            results.append(ValidationResult(
                is_valid=False,
                confidence_score=0.0,
                message="Total compensation is null",
                severity="ERROR",
                field_name="total_compensation",
                suggestion="Ensure compensation data is properly extracted"
            ))
            return results

        # Validate component consistency
        components = [
            float(compensation.salary) if compensation.salary is not None else 0.0,
            float(compensation.bonus) if compensation.bonus is not None else 0.0,
            float(compensation.stock_awards) if compensation.stock_awards is not None else 0.0,
            float(compensation.option_awards) if compensation.option_awards is not None else 0.0,
            float(compensation.other_compensation) if compensation.other_compensation is not None else 0.0
        ]
        calculated_total = sum(components)
        
        if abs(calculated_total - total_comp) > max(abs(total_comp) * 0.01, 1000):  # 1% or $1K tolerance
            results.append(ValidationResult(
                is_valid=False,
                confidence_score=0.4,
                message=f"Compensation components don't sum to total: {calculated_total:,.0f} ≠ {total_comp:,.0f}",
                severity="WARNING",
                field_name="compensation_consistency",
                expected_value=calculated_total,
                actual_value=total_comp,
                suggestion="Verify all compensation components are captured correctly"
            ))
        else:
            results.append(ValidationResult(
                is_valid=True,
                confidence_score=0.9,
                message="Compensation components are consistent",
                severity="INFO",
                field_name="compensation_consistency"
            ))
        
        # Validate executive title
        title_validation = self._validate_executive_title(compensation.title)
        results.append(title_validation)
        
        # Validate name format
        name_validation = self._validate_executive_name(compensation.executive_name)
        results.append(name_validation)
        
        return results

    def _validate_numeric_field(
        self,
        field_name: str,
        value: float,
        rules: Dict,
        display_name: str,
        is_percentage: bool = False
    ) -> List[ValidationResult]:
        """Validate a numeric field against rules."""
        results = []

        # Check for basic validity
        if value is None or (isinstance(value, float) and (value != value)):  # NaN check
            results.append(ValidationResult(
                is_valid=False,
                confidence_score=0.0,
                message=f"{display_name} is null or invalid",
                severity="ERROR",
                field_name=field_name,
                actual_value=value,
                suggestion=f"Ensure {display_name} is properly extracted from source document"
            ))
            return results

        # Check minimum value
        if value < rules["min_value"]:
            severity = "WARNING" if value >= rules["min_value"] * 0.9 else "ERROR"
            results.append(ValidationResult(
                is_valid=False,
                confidence_score=0.2 if severity == "WARNING" else 0.0,
                message=f"{display_name} below minimum: {value:,.2f} < {rules['min_value']:,.2f}",
                severity=severity,
                field_name=field_name,
                expected_value=rules["min_value"],
                actual_value=value,
                suggestion=f"Verify {display_name} extraction - unusually low value"
            ))

        # Check maximum value
        elif value > rules["max_value"]:
            results.append(ValidationResult(
                is_valid=False,
                confidence_score=0.0,
                message=f"{display_name} exceeds maximum: {value:,.2f} > {rules['max_value']:,.2f}",
                severity="ERROR",
                field_name=field_name,
                expected_value=rules["max_value"],
                actual_value=value,
                suggestion=f"Check {display_name} units - value seems unreasonably high"
            ))

        # Check reasonable range
        elif "reasonable_range" in rules:
            min_reasonable, max_reasonable = rules["reasonable_range"]
            if value < min_reasonable:
                results.append(ValidationResult(
                    is_valid=True,
                    confidence_score=0.6,
                    message=f"{display_name} below typical range: {value:,.2f} < {min_reasonable:,.2f}",
                    severity="INFO",
                    field_name=field_name,
                    actual_value=value,
                    suggestion=f"Unusually low {display_name} - verify extraction accuracy"
                ))
            elif value > max_reasonable:
                results.append(ValidationResult(
                    is_valid=True,
                    confidence_score=0.7,
                    message=f"{display_name} above typical range: {value:,.2f} > {max_reasonable:,.2f}",
                    severity="WARNING",
                    field_name=field_name,
                    actual_value=value,
                    suggestion=f"Unusually high {display_name} - double-check extraction"
                ))
            else:
                results.append(ValidationResult(
                    is_valid=True,
                    confidence_score=0.95,
                    message=f"{display_name} within reasonable range",
                    severity="INFO",
                    field_name=field_name,
                    actual_value=value
                ))

        return results

    def _validate_executive_title(self, title: str) -> ValidationResult:
        """Validate executive title."""
        if not title or not title.strip():
            return ValidationResult(
                is_valid=False,
                confidence_score=0.0,
                message="Executive title is empty",
                severity="ERROR",
                field_name="executive_title",
                suggestion="Ensure executive title is properly extracted"
            )

        # Common executive titles
        common_titles = [
            "chief executive officer", "ceo", "president", "chief financial officer", "cfo",
            "chief operating officer", "coo", "chief technology officer", "cto",
            "chief information officer", "cio", "executive vice president", "evp",
            "senior vice president", "svp", "vice president", "vp", "chairman", "director"
        ]

        title_lower = title.lower()
        is_common_title = any(common in title_lower for common in common_titles)

        if is_common_title:
            confidence = 0.9
            severity = "INFO"
            message = f"Recognized executive title: {title}"
        else:
            confidence = 0.6
            severity = "WARNING"
            message = f"Unusual executive title: {title}"

        return ValidationResult(
            is_valid=True,
            confidence_score=confidence,
            message=message,
            severity=severity,
            field_name="executive_title",
            actual_value=title,
            suggestion="Verify title extraction if unusual" if not is_common_title else None
        )

    def _validate_executive_name(self, name: str) -> ValidationResult:
        """Validate executive name format."""
        if not name or not name.strip():
            return ValidationResult(
                is_valid=False,
                confidence_score=0.0,
                message="Executive name is empty",
                severity="ERROR",
                field_name="executive_name",
                suggestion="Ensure executive name is properly extracted"
            )

        name = name.strip()

        # Basic name validation
        if len(name) < 2:
            return ValidationResult(
                is_valid=False,
                confidence_score=0.1,
                message=f"Executive name too short: '{name}'",
                severity="WARNING",
                field_name="executive_name",
                actual_value=name,
                suggestion="Verify name extraction - seems incomplete"
            )

        # Check for reasonable name pattern
        name_pattern = r"^[A-Za-z\s\.\-']+$"
        if not re.match(name_pattern, name):
            return ValidationResult(
                is_valid=False,
                confidence_score=0.3,
                message=f"Executive name contains unusual characters: '{name}'",
                severity="WARNING",
                field_name="executive_name",
                actual_value=name,
                suggestion="Check for extraction artifacts or encoding issues"
            )

        # Check for multiple words (first + last name)
        words = name.split()
        if len(words) < 2:
            confidence = 0.6
            severity = "INFO"
            message = f"Executive name has single word: '{name}'"
            suggestion = "Verify if full name was extracted"
        else:
            confidence = 0.9
            severity = "INFO"
            message = f"Executive name format looks good: '{name}'"
            suggestion = None

        return ValidationResult(
            is_valid=True,
            confidence_score=confidence,
            message=message,
            severity=severity,
            field_name="executive_name",
            actual_value=name,
            suggestion=suggestion
        )
