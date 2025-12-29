"""Summary Compensation Table extractor implementation."""

import re
from dataclasses import dataclass
from typing import Any

from bs4 import BeautifulSoup, Tag

from edgar.extractors.sct.models import CompensationYear, ExecutiveCompensation, SCTData


@dataclass(frozen=True)
class SCTExtractor:
    """Extractor for Summary Compensation Table from SEC DEF 14A filings.

    Implements IDataExtractor protocol for extracting executive compensation
    data from SEC proxy statement filings.

    Attributes:
        company: Company name for extracted data
        cik: SEC CIK number
    """

    company: str = "Unknown"
    cik: str = ""

    def extract(self, raw_data: dict[str, Any]) -> SCTData:
        """Extract SCT data from raw filing data.

        Args:
            raw_data: Dictionary with 'html' key containing filing HTML,
                     or 'filing' key with metadata and 'html' with content.

        Returns:
            SCTData with extracted executive compensation

        Raises:
            ValueError: If required data not found in HTML
        """
        # Get HTML content
        html = raw_data.get("html", "")
        if not html and "content" in raw_data:
            html = raw_data["content"]

        if not html:
            raise ValueError("No HTML content provided in raw_data")

        # Parse HTML
        soup = BeautifulSoup(html, "html.parser")

        # Find Summary Compensation Table
        sct_table = self._find_sct_table(soup)
        if not sct_table:
            raise ValueError("Summary Compensation Table not found")

        # Extract executives
        executives = self._extract_executives(sct_table)

        # Get filing metadata
        filing_date = raw_data.get("filing", {}).get("filing_date", "")

        return SCTData(
            company=self.company,
            cik=self.cik,
            filing_date=filing_date,
            executives=executives,
        )

    def _find_sct_table(self, soup: BeautifulSoup) -> Tag | None:
        """Find the Summary Compensation Table in the document.

        Searches for table following SCT header text.
        """
        # Look for SCT header
        sct_patterns = [
            "summary compensation table",
            "summary of compensation",
        ]

        for tag in soup.find_all(["h1", "h2", "h3", "h4", "p", "b", "strong", "span"]):
            text = tag.get_text(strip=True).lower()
            if any(pattern in text for pattern in sct_patterns):
                if "narrative" not in text and "footnote" not in text:
                    # Find next table
                    table = tag.find_next("table")
                    if table and self._looks_like_sct(table):
                        return table

        return None

    def _looks_like_sct(self, table: Tag) -> bool:
        """Check if table looks like a Summary Compensation Table."""
        text = table.get_text().lower()
        # SCT should have salary, stock awards, and total columns
        indicators = ["salary", "stock", "total"]
        return sum(1 for i in indicators if i in text) >= 2

    def _extract_executives(self, table: Tag) -> list[ExecutiveCompensation]:
        """Extract executive compensation data from table."""
        executives: list[ExecutiveCompensation] = []
        current_exec: ExecutiveCompensation | None = None

        rows = table.find_all("tr")

        for row in rows:
            cells = row.find_all(["td", "th"])
            if len(cells) < 3:
                continue

            # Get cell values - preserve newlines for first cell (name/title)
            values = []
            for i, cell in enumerate(cells):
                if i == 0:
                    # First cell: preserve line breaks for name/title extraction
                    values.append(self._get_cell_text_with_newlines(cell))
                else:
                    # Other cells: normal cleaning
                    values.append(self._clean_cell(cell.get_text()))

            # Skip header rows
            if self._is_header_row(values):
                continue

            # Check for new executive (name in first column)
            name_info = self._extract_name_title(values[0])
            if name_info:
                current_exec = ExecutiveCompensation(
                    name=name_info["name"],
                    title=name_info.get("title", ""),
                    compensation=[],
                )
                executives.append(current_exec)

            # Try to extract compensation data
            if current_exec:
                comp_data = self._parse_compensation_row(values)
                if comp_data:
                    current_exec.compensation.append(comp_data)

        return executives

    def _get_cell_text_with_newlines(self, cell: Tag) -> str:
        """Extract text from cell, preserving line breaks from br tags."""
        # Replace br tags with newlines
        for br in cell.find_all("br"):
            br.replace_with("\n")
        return self._clean_cell(cell.get_text())

    def _clean_cell(self, value: str) -> str:
        """Clean a table cell value."""
        # Remove footnote markers
        value = re.sub(r"\(\d+\)", "", value)
        value = re.sub(r"\[\d+\]", "", value)
        value = re.sub(r"\*+", "", value)
        # Normalize whitespace (but preserve newlines)
        lines = value.split("\n")
        cleaned_lines = [re.sub(r"\s+", " ", line).strip() for line in lines]
        return "\n".join(cleaned_lines)

    def _is_header_row(self, values: list[str]) -> bool:
        """Check if row is a header row."""
        first = values[0].lower()
        headers = ["name", "principal", "position", "year", "fiscal"]
        return any(h in first for h in headers)

    def _extract_name_title(self, text: str) -> dict[str, str] | None:
        """Extract executive name and title from text."""
        if not text or len(text) < 3:
            return None

        # Skip if starts with number (likely year)
        if text[0].isdigit():
            return None

        # Skip if common non-name words
        lower = text.lower()
        skip_words = ["total", "subtotal", "sum", "page", "continued"]
        if any(word in lower for word in skip_words):
            return None

        # Split by common delimiters
        parts = re.split(r"[\n\r]+", text)
        if len(parts) >= 2:
            name = parts[0].strip()
            title = parts[1].strip()
            if len(name) > 2 and not name[0].isdigit():
                return {"name": name, "title": title}
        elif len(parts) == 1:
            # Single line - might be just name
            name = parts[0].strip()
            if len(name) > 2 and not name[0].isdigit():
                return {"name": name, "title": ""}

        return None

    def _parse_compensation_row(self, values: list[str]) -> CompensationYear | None:
        """Parse a row of compensation data.

        Dynamically finds year column and parses compensation values relative to it.
        Handles tables with empty columns and varying structures.
        """
        # Find year in values (search first 5 columns)
        year = None
        year_idx = None
        for i, val in enumerate(values[:5]):
            if val.isdigit() and 2000 <= int(val) <= 2030:
                year = int(val)
                year_idx = i
                break

        if not year or year_idx is None:
            return None

        # Parse all values after year (including zeros/dashes)
        # Standard order: Salary, Bonus, Stock, Options, Non-Equity, Pension, Other, Total
        values_after_year = values[year_idx + 1 :]

        # Extract monetary values
        monetary_values = [self._to_number(v) for v in values_after_year if v]

        # Determine structure based on number of non-empty values
        # Filter to numeric values only (exclude empty strings and footnote markers)
        try:
            if len(monetary_values) >= 8:
                # Full table with all columns: Salary, Bonus, Stock, Options, Non-Equity, Pension, Other, Total
                return CompensationYear(
                    year=year,
                    salary=monetary_values[0],
                    bonus=monetary_values[1],
                    stock_awards=monetary_values[2],
                    option_awards=monetary_values[3],
                    non_equity_incentive=monetary_values[4],
                    pension_change=monetary_values[5],
                    other_compensation=monetary_values[6],
                    total=monetary_values[7],
                )
            elif len(monetary_values) >= 5:
                # Condensed table (Apple style): Salary, Stock, Non-Equity, Other, Total
                return CompensationYear(
                    year=year,
                    salary=monetary_values[0],
                    stock_awards=monetary_values[1],
                    non_equity_incentive=monetary_values[2],
                    other_compensation=monetary_values[3],
                    total=monetary_values[4],
                    bonus=0.0,
                    option_awards=0.0,
                    pension_change=0.0,
                )
            else:
                # Not enough data
                return None
        except (IndexError, ValueError):
            return None

    def _to_number(self, value: str) -> float:
        """Convert currency string to number."""
        if not value:
            return 0.0

        # Handle dashes as zero
        if value in ["—", "–", "-", "N/A", "n/a", ""]:
            return 0.0

        # Remove currency symbols and formatting
        value = re.sub(r"[$,()]", "", value)
        value = value.strip()

        try:
            return float(value)
        except ValueError:
            return 0.0
