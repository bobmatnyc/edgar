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

        Searches for table following SCT header text or containing SCT text.
        Uses multiple strategies to handle different proxy formats.
        """
        # Strategy 1: Find table with strong compensation indicators
        # (most reliable - checks actual table content)
        # This catches Amazon, Berkshire, and other non-standard formats
        candidate_tables: list[Tag] = []
        for table in soup.find_all("table"):
            if self._is_likely_compensation_table(table):
                candidate_tables.append(table)

        # Return first strong candidate
        if candidate_tables:
            return candidate_tables[0]

        # Strategy 2: Search for "Summary Compensation Table" header followed by table
        # (handles standard formats like Apple)
        sct_patterns = [
            "summary compensation table",
            "summary of compensation",
        ]

        # Look within reasonable distance (next 10 tables)
        for tag in soup.find_all(["h1", "h2", "h3", "h4", "p", "b", "strong", "span", "div"]):
            text = tag.get_text(strip=True).lower()
            if any(pattern in text for pattern in sct_patterns):
                if "narrative" not in text and "footnote" not in text:
                    # Find next table (try multiple candidates)
                    next_element = tag
                    for _ in range(10):  # Look at next 10 siblings/descendants
                        next_element = next_element.find_next("table")
                        if next_element and self._looks_like_sct(next_element):
                            return next_element
                        if not next_element:
                            break

        # Strategy 3: Search tables directly containing SCT text
        # (handles cases where "Summary Compensation Table" is in <td> cells)
        for table in soup.find_all("table"):
            table_text = table.get_text().lower()
            # Check if table contains SCT pattern
            if any(pattern in table_text for pattern in sct_patterns):
                # Exclude tables with narrative/footnote text
                if "narrative" not in table_text and "footnote" not in table_text[:200]:
                    if self._looks_like_sct(table):
                        return table

        return None

    def _is_likely_compensation_table(self, table: Tag) -> bool:
        """Check if table is likely a compensation table based on structure.

        More strict than _looks_like_sct - requires executive names + compensation data.
        Requires multiple executives to avoid summary tables.
        """
        text = table.get_text().lower()

        # Must have key compensation columns
        has_salary = "salary" in text
        has_stock = "stock" in text or "award" in text
        has_total = "total" in text
        has_year = "year" in text or "20" in text[:500]  # Year in early part of table

        if not (has_salary and has_stock and has_total and has_year):
            return False

        # Must have executive-like content (names with titles)
        # Look for common titles
        executive_titles = [
            "chief executive", "ceo", "president",
            "chief financial", "cfo",
            "chief operating", "coo",
            "vice president", "vp",
            "officer", "founder"
        ]

        has_exec_title = any(title in text for title in executive_titles)
        if not has_exec_title:
            return False

        # Must have monetary values (dollar signs)
        has_dollars = "$" in table.get_text()
        if not has_dollars:
            return False

        # CRITICAL: Must have multiple executives (at least 3) to avoid summary tables
        # Count potential executive rows (rows with names and titles)
        rows = table.find_all("tr")
        exec_row_count = 0

        for row in rows:
            cells = row.find_all(["td", "th"])
            if len(cells) < 3:  # Need at least 3 columns
                continue

            # Check first few columns for name-like content
            for cell in cells[:3]:
                cell_text = cell.get_text(strip=True)
                # Skip headers and non-name content
                if not cell_text or len(cell_text) < 5:
                    continue
                if any(h in cell_text.lower() for h in ["name", "year", "salary", "total", "position"]):
                    continue
                if cell_text[0].isdigit():
                    continue

                # Check if cell has title indicators
                cell_lower = cell_text.lower()
                if any(title in cell_lower for title in ["officer", "president", "chief", "vice", "ceo", "cfo", "coo"]):
                    exec_row_count += 1
                    break

        # Require at least 3 executive rows to be a valid SCT table
        # This filters out single-executive summary tables (like Apple's Tim Cook summary)
        return exec_row_count >= 3

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

            # Get cell values - preserve newlines for name cells
            values = []
            for i, cell in enumerate(cells):
                # Preserve line breaks for first few cells (name might be in column 0, 1, or 2)
                if i < 3:
                    values.append(self._get_cell_text_with_newlines(cell))
                else:
                    values.append(self._clean_cell(cell.get_text()))

            # Skip header rows
            if self._is_header_row(values):
                continue

            # Check for new executive (name might be in first non-empty column)
            # Amazon has empty first column, so check first 3 columns
            name_info = None
            for col_idx in range(min(3, len(values))):
                name_info = self._extract_name_title(values[col_idx])
                if name_info:
                    break

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
        """Clean a table cell value.

        Removes footnote markers but preserves parenthesized numbers (negative values).
        """
        # Remove footnote markers like [1], [2], etc.
        # BUT preserve parenthesized numbers like (1,234) which may appear in compensation tables
        value = re.sub(r"\[\d+\]", "", value)

        # Remove asterisks (footnote markers)
        value = re.sub(r"\*+", "", value)

        # Remove zero-width spaces (common in modern HTML tables)
        value = value.replace("\u200b", "")

        # Normalize whitespace (but preserve newlines)
        lines = value.split("\n")
        cleaned_lines = [re.sub(r"\s+", " ", line).strip() for line in lines]
        return "\n".join(cleaned_lines)

    def _is_header_row(self, values: list[str]) -> bool:
        """Check if row is a header row."""
        # Check all non-empty values (not just first column)
        # Some tables have empty first column with headers in column 2+
        non_empty_values = [v.lower() for v in values if v.strip()]

        if not non_empty_values:
            return False

        # Check first non-empty value for header indicators
        first = non_empty_values[0]

        # Common header patterns
        headers = [
            "name", "principal", "position", "year", "fiscal",
            "salary", "bonus", "stock", "award", "option",
            "non-equity", "pension", "total", "compensation",
            "and principal position"  # Specific to Amazon format
        ]

        # Header if first value contains header keywords
        if any(h in first for h in headers):
            return True

        # Also check if multiple values look like column headers
        # (e.g., "Name", "Year", "Salary", "Total")
        header_count = sum(1 for v in non_empty_values[:6] if any(h in v for h in headers))
        return header_count >= 3  # If 3+ columns look like headers, it's a header row

    def _extract_name_title(self, text: str) -> dict[str, str] | None:
        """Extract executive name and title from text."""
        if not text or len(text.strip()) < 3:
            return None

        # Strip leading/trailing whitespace
        text = text.strip()

        # Skip if starts with number (likely year)
        if text[0].isdigit():
            return None

        # Skip if common non-name words
        lower = text.lower()
        skip_words = ["total", "subtotal", "sum", "page", "continued"]
        if any(word in lower for word in skip_words):
            return None

        # Split by common delimiters and filter out empty parts
        parts = [p.strip() for p in re.split(r"[\n\r]+", text) if p.strip()]

        if len(parts) >= 2:
            name = parts[0]
            title = parts[1]
            if len(name) > 2 and not name[0].isdigit():
                return {"name": name, "title": title}
        elif len(parts) == 1:
            # Single line - might be just name
            name = parts[0]
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

        # Extract monetary values (filter out empty cells and footnote markers)
        # Try to convert each value to number, keeping only valid numbers
        monetary_values = []
        for v in values_after_year:
            # Skip truly empty values and whitespace-only cells
            if not v or not v.strip():
                continue
            # Skip footnote markers like (1), (2), (3)(4)
            if v.strip().startswith('(') and v.strip().endswith(')'):
                continue
            # Try to convert to number
            num = self._to_number(v)
            # Keep all valid numbers (including 0)
            monetary_values.append(num)

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
            elif len(monetary_values) >= 4:
                # Simplified table (Berkshire style): Salary, Bonus, Other, Total
                return CompensationYear(
                    year=year,
                    salary=monetary_values[0],
                    bonus=monetary_values[1],
                    other_compensation=monetary_values[2],
                    total=monetary_values[3],
                    stock_awards=0.0,
                    option_awards=0.0,
                    non_equity_incentive=0.0,
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
