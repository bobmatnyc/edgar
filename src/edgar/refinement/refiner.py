"""Self-refinement module for EDGAR extractors.

Analyzes extraction failures and generates improvements.
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup, Tag

from edgar.data.fortune100 import Company
from edgar.services.sec_edgar_client import SecEdgarClient


@dataclass
class ExtractionFailure:
    """Details of a failed extraction.

    Attributes:
        company: Company that failed extraction
        form_type: SEC form type (e.g., "DEF 14A", "10-K")
        html_sample: First 50KB of HTML for analysis
        error_message: Error message from extraction
        extractor_type: Type of extractor that failed
        filing_url: URL to the full filing
    """

    company: Company
    form_type: str
    html_sample: str
    error_message: str
    extractor_type: str
    filing_url: str = ""


@dataclass
class RefinementSuggestion:
    """Suggested improvement for an extractor.

    Attributes:
        pattern_type: Type of pattern to refine (e.g., "table_header", "cell_format")
        current_pattern: Pattern currently being used
        suggested_pattern: Suggested new pattern
        confidence: Confidence score (0.0-1.0)
        example_html: HTML snippet showing the pattern
        reasoning: Explanation of why this pattern should work
        company_name: Company where pattern was found
    """

    pattern_type: str
    current_pattern: str
    suggested_pattern: str
    confidence: float
    example_html: str
    reasoning: str
    company_name: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert suggestion to dictionary for JSON serialization."""
        return {
            "pattern_type": self.pattern_type,
            "current_pattern": self.current_pattern,
            "suggested_pattern": self.suggested_pattern,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "company_name": self.company_name,
            "example_html_length": len(self.example_html),
        }


@dataclass(frozen=True)
class ExtractorRefiner:
    """Analyzes extraction failures and suggests/applies refinements.

    Self-refinement workflow:
    1. Collect failed extractions with HTML samples
    2. Analyze HTML to identify missing patterns
    3. Generate pattern suggestions
    4. Apply refinements to extractors
    5. Verify improvements

    Attributes:
        sec_client: SEC EDGAR API client for fetching filings
        min_confidence: Minimum confidence threshold for suggestions
    """

    sec_client: SecEdgarClient
    min_confidence: float = 0.7

    async def analyze_failures(
        self,
        failures: list[ExtractionFailure],
    ) -> list[RefinementSuggestion]:
        """Analyze failed extractions and suggest refinements.

        For each failure:
        1. Parse the HTML
        2. Search for alternative table patterns
        3. Identify why current patterns don't match
        4. Suggest new patterns

        Args:
            failures: List of extraction failures to analyze

        Returns:
            List of refinement suggestions with confidence scores
        """
        suggestions: list[RefinementSuggestion] = []

        for failure in failures:
            soup = BeautifulSoup(failure.html_sample, "html.parser")

            if failure.extractor_type == "SCTExtractor":
                suggestions.extend(self._analyze_sct_failure(soup, failure))
            elif failure.extractor_type == "TaxExtractor":
                suggestions.extend(self._analyze_tax_failure(soup, failure))

        # Filter by confidence threshold
        return [s for s in suggestions if s.confidence >= self.min_confidence]

    def _analyze_sct_failure(
        self,
        soup: BeautifulSoup,
        failure: ExtractionFailure,
    ) -> list[RefinementSuggestion]:
        """Analyze why SCT extraction failed.

        Searches for compensation-related tables that weren't detected
        by current patterns.

        Args:
            soup: Parsed HTML
            failure: Failure details

        Returns:
            List of suggestions for SCT extractor improvements
        """
        suggestions: list[RefinementSuggestion] = []

        # Keywords that indicate compensation data
        compensation_keywords = [
            "compensation",
            "salary",
            "bonus",
            "stock",
            "award",
            "executive",
            "officer",
            "named",
            "neo",
            "pay",
            "total",
        ]

        # Find all tables
        tables = soup.find_all("table")

        for table in tables:
            table_text = table.get_text().lower()

            # Count keyword matches
            keyword_matches = sum(1 for kw in compensation_keywords if kw in table_text)

            # If table has many compensation keywords, it's likely the SCT
            if keyword_matches >= 4:
                # Analyze why it wasn't detected
                suggestions.extend(self._analyze_sct_table_structure(table, failure.company.name))

        return suggestions

    def _analyze_sct_table_structure(
        self, table: Tag, company_name: str
    ) -> list[RefinementSuggestion]:
        """Analyze the structure of a potential SCT table.

        Args:
            table: HTML table element
            company_name: Company name for tracking

        Returns:
            List of suggestions for handling this table structure
        """
        suggestions: list[RefinementSuggestion] = []

        # Check header patterns
        headers = self._extract_table_headers(table)
        if headers:
            header_text = " | ".join(headers).lower()

            # Check if "summary compensation table" is in header
            if "summary compensation" not in header_text:
                # Found compensation table with different header
                suggestions.append(
                    RefinementSuggestion(
                        pattern_type="table_header",
                        current_pattern="summary compensation table",
                        suggested_pattern=header_text[:100],
                        confidence=0.85,
                        example_html=str(table)[:1000],
                        reasoning=(
                            f"Table contains compensation data but uses alternative header. "
                            f"Header text: '{header_text[:100]}'. "
                            f"Suggest adding this pattern to header detection."
                        ),
                        company_name=company_name,
                    )
                )

        # Analyze table structure (row/column patterns)
        structure = self._analyze_table_structure(table)
        if structure:
            suggestions.append(
                RefinementSuggestion(
                    pattern_type="table_structure",
                    current_pattern="Standard 8-column SCT",
                    suggested_pattern=structure,
                    confidence=0.75,
                    example_html=str(table)[:1000],
                    reasoning=(
                        f"Table has non-standard structure. {structure}. "
                        f"May need custom column mapping."
                    ),
                    company_name=company_name,
                )
            )

        return suggestions

    def _analyze_tax_failure(
        self,
        soup: BeautifulSoup,
        failure: ExtractionFailure,
    ) -> list[RefinementSuggestion]:
        """Analyze why tax extraction failed or returned zeros.

        Args:
            soup: Parsed HTML
            failure: Failure details

        Returns:
            List of suggestions for tax extractor improvements
        """
        suggestions: list[RefinementSuggestion] = []

        tax_keywords = [
            "income tax",
            "provision for",
            "tax expense",
            "deferred tax",
            "current tax",
            "federal",
            "state",
            "foreign",
        ]

        tables = soup.find_all("table")

        for table in tables:
            table_text = table.get_text().lower()
            keyword_matches = sum(1 for kw in tax_keywords if kw in table_text)

            # Found a tax-related table
            if keyword_matches >= 3:
                suggestions.extend(self._analyze_tax_table_structure(table, failure.company.name))

        return suggestions

    def _analyze_tax_table_structure(
        self, table: Tag, company_name: str
    ) -> list[RefinementSuggestion]:
        """Analyze the structure of a potential tax table.

        Args:
            table: HTML table element
            company_name: Company name for tracking

        Returns:
            List of suggestions for handling this table structure
        """
        suggestions: list[RefinementSuggestion] = []

        # Extract structure
        rows = table.find_all("tr")
        structure = self._extract_table_structure(table)

        # Check for year columns
        year_pattern = self._find_year_columns(table)

        suggestions.append(
            RefinementSuggestion(
                pattern_type="tax_table_structure",
                current_pattern="Standard current/deferred federal/state/foreign",
                suggested_pattern=structure[:200],
                confidence=0.80,
                example_html=str(table)[:1500],
                reasoning=(
                    f"Found tax table with {len(rows)} rows. Year pattern: {year_pattern}. "
                    f"Structure: {structure[:100]}. May need custom parsing logic."
                ),
                company_name=company_name,
            )
        )

        # Check for alternative section headers
        section_headers = self._find_section_headers(table)
        if section_headers:
            suggestions.append(
                RefinementSuggestion(
                    pattern_type="tax_section_headers",
                    current_pattern="'Current:' and 'Deferred:' section headers",
                    suggested_pattern=" | ".join(section_headers),
                    confidence=0.75,
                    example_html=str(table)[:1000],
                    reasoning=(
                        f"Table uses alternative section headers: {section_headers}. "
                        f"Current extractor expects 'Current:' and 'Deferred:' with colons."
                    ),
                    company_name=company_name,
                )
            )

        return suggestions

    def _extract_table_headers(self, table: Tag) -> list[str]:
        """Extract header row from table.

        Args:
            table: HTML table element

        Returns:
            List of header cell texts
        """
        # Find first row (usually header)
        first_row = table.find("tr")
        if not first_row:
            return []

        # Extract text from header cells
        cells = first_row.find_all(["th", "td"])
        return [self._clean_text(cell.get_text()) for cell in cells if cell.get_text().strip()]

    def _analyze_table_structure(self, table: Tag) -> str:
        """Analyze table structure and return description.

        Args:
            table: HTML table element

        Returns:
            Description of table structure
        """
        rows = table.find_all("tr")
        if not rows:
            return "Empty table"

        # Count columns
        max_cols = 0
        for row in rows[:10]:  # Check first 10 rows
            cells = row.find_all(["td", "th"])
            max_cols = max(max_cols, len(cells))

        # Check for rowspan/colspan
        has_rowspan = bool(table.find_all(attrs={"rowspan": True}))
        has_colspan = bool(table.find_all(attrs={"colspan": True}))

        description = f"{len(rows)} rows, {max_cols} columns"
        if has_rowspan:
            description += ", uses rowspan"
        if has_colspan:
            description += ", uses colspan"

        return description

    def _extract_table_structure(self, table: Tag) -> str:
        """Extract first few rows of table as structure sample.

        Args:
            table: HTML table element

        Returns:
            String showing structure of first 5 rows
        """
        rows = table.find_all("tr")[:5]
        structure_lines: list[str] = []

        for i, row in enumerate(rows):
            cells = row.find_all(["td", "th"])
            cell_texts = [self._clean_text(c.get_text())[:30] for c in cells[:6]]
            structure_lines.append(f"Row {i}: {' | '.join(cell_texts)}")

        return "\n".join(structure_lines)

    def _find_year_columns(self, table: Tag) -> str:
        """Find which columns contain year data.

        Args:
            table: HTML table element

        Returns:
            Description of year column pattern
        """
        rows = table.find_all("tr")
        for row in rows[:5]:
            cells = row.find_all(["td", "th"])
            year_positions: list[int] = []

            for i, cell in enumerate(cells):
                text = self._clean_text(cell.get_text())
                if text.isdigit() and 2000 <= int(text) <= 2030:
                    year_positions.append(i)

            if year_positions:
                return f"Years in columns: {year_positions}"

        return "No year columns found"

    def _find_section_headers(self, table: Tag) -> list[str]:
        """Find section headers in table (e.g., 'Current', 'Deferred').

        Args:
            table: HTML table element

        Returns:
            List of section header texts
        """
        section_keywords = ["current", "deferred", "provision", "benefit", "expense"]
        headers: list[str] = []

        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all(["td", "th"])
            for cell in cells:
                text = self._clean_text(cell.get_text()).lower()
                # Check if cell contains section keyword and colon
                if any(kw in text for kw in section_keywords):
                    if ":" in text or len(cells) == 1:  # Section headers often span full row
                        headers.append(self._clean_text(cell.get_text()))

        return headers[:10]  # Return first 10 to avoid duplicates

    def _clean_text(self, text: str) -> str:
        """Clean text from HTML cells.

        Args:
            text: Raw text from HTML

        Returns:
            Cleaned text
        """
        # Remove footnote markers
        text = re.sub(r"\(\d+\)", "", text)
        text = re.sub(r"\[\d+\]", "", text)
        text = re.sub(r"\*+", "", text)
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    async def apply_refinements(
        self,
        suggestions: list[RefinementSuggestion],
        extractor_path: Path,
    ) -> bool:
        """Apply suggested refinements to an extractor.

        This is a placeholder for automated code modification.
        For now, it saves suggestions to a JSON file for manual review.

        Args:
            suggestions: List of refinement suggestions
            extractor_path: Path to extractor module

        Returns:
            True if suggestions were saved successfully
        """
        # Save suggestions to JSON file for manual review
        output_path = extractor_path.parent / f"{extractor_path.stem}_refinements.json"

        refinements_data = {
            "extractor": str(extractor_path),
            "suggestions_count": len(suggestions),
            "suggestions": [s.to_dict() for s in suggestions],
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(refinements_data, f, indent=2)

        return True

    async def verify_refinement(
        self,
        company: Company,
        form_type: str,
        extractor: Any,
    ) -> bool:
        """Verify that refinement fixed the extraction.

        Re-runs extraction and checks for success.

        Args:
            company: Company to test
            form_type: Form type to extract
            extractor: Extractor instance to test

        Returns:
            True if extraction now succeeds
        """
        try:
            # Fetch latest filing
            filing = await self.sec_client.get_latest_filing(company.cik, form_type)

            # Fetch HTML
            html = await self.sec_client.fetch_filing_html(filing["url"])

            # Try extraction
            result = extractor.extract({"html": html, "filing": filing})

            # Check if extraction produced valid data
            # For SCT: at least one executive
            if hasattr(result, "executives"):
                return len(result.executives) > 0

            # For Tax: at least one tax year with non-zero values
            if hasattr(result, "tax_years"):
                return any(
                    ty.total_tax_expense > 0 for ty in result.tax_years if ty.total_tax_expense
                )

            return True

        except Exception:
            return False

    def generate_refinement_report(self, suggestions: list[RefinementSuggestion]) -> str:
        """Generate human-readable refinement report.

        Args:
            suggestions: List of refinement suggestions

        Returns:
            Formatted report string
        """
        report_lines = [
            "=" * 80,
            "EXTRACTOR REFINEMENT REPORT",
            "=" * 80,
            "",
            f"Total Suggestions: {len(suggestions)}",
            "",
        ]

        # Group by pattern type
        by_type: dict[str, list[RefinementSuggestion]] = {}
        for suggestion in suggestions:
            by_type.setdefault(suggestion.pattern_type, []).append(suggestion)

        for pattern_type, type_suggestions in sorted(by_type.items()):
            report_lines.extend(
                [
                    f"\n## {pattern_type.replace('_', ' ').title()}",
                    f"   Count: {len(type_suggestions)}",
                    "",
                ]
            )

            for i, suggestion in enumerate(type_suggestions[:3], 1):  # Show top 3
                report_lines.extend(
                    [
                        f"   {i}. Company: {suggestion.company_name}",
                        f"      Confidence: {suggestion.confidence:.2f}",
                        f"      Current: {suggestion.current_pattern[:60]}",
                        f"      Suggested: {suggestion.suggested_pattern[:60]}",
                        f"      Reason: {suggestion.reasoning[:100]}",
                        "",
                    ]
                )

        return "\n".join(report_lines)
