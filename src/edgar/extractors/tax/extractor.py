"""Income tax extractor implementation."""

import re
from dataclasses import dataclass
from typing import Any

from bs4 import BeautifulSoup, Tag

from edgar.extractors.tax.models import TaxData, TaxYear


@dataclass(frozen=True)
class TaxExtractor:
    """Extractor for income tax data from SEC 10-K filings.

    Implements IDataExtractor protocol for extracting corporate income tax
    data from SEC 10-K annual reports.

    Extraction Strategy:
    1. Locate "Provision for Income Taxes" or "Income Tax Expense" section
    2. Parse income tax expense table (current/deferred, federal/state/foreign)
    3. Extract effective tax rate if available
    4. Parse cash taxes paid from cash flow statement (optional)

    Attributes:
        company: Company name for extracted data
        cik: SEC CIK number
    """

    company: str = "Unknown"
    cik: str = ""

    def extract(self, raw_data: dict[str, Any]) -> TaxData:
        """Extract tax data from raw 10-K filing data.

        Args:
            raw_data: Dictionary with 'html' key containing filing HTML,
                     or 'filing' key with metadata and 'html' with content.

        Returns:
            TaxData with extracted income tax information

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

        # Find Income Tax Expense table
        tax_table = self._find_income_tax_table(soup)
        if not tax_table:
            raise ValueError("Income tax expense table not found")

        # Extract tax years
        tax_years = self._extract_tax_years(tax_table)

        # Try to find effective tax rate
        effective_rate = self._find_effective_rate(soup)
        if effective_rate > 0 and tax_years:
            tax_years[0].effective_tax_rate = effective_rate

        # Get filing metadata
        filing_date = raw_data.get("filing", {}).get("filing_date", "")
        fiscal_year_end = raw_data.get("filing", {}).get("fiscal_year_end", "")

        return TaxData(
            company=self.company,
            cik=self.cik,
            filing_date=filing_date,
            fiscal_year_end=fiscal_year_end,
            tax_years=tax_years,
        )

    def _find_income_tax_table(self, soup: BeautifulSoup) -> Tag | None:
        """Find the Income Tax Expense table in the document.

        Searches for table following tax-related header text.
        Prioritizes detailed tables with component breakdowns.
        """
        # Look for income tax section headers
        tax_patterns = [
            "provision for income taxes",
            "income tax expense",
            "components of income tax",
            "income taxes",
        ]

        # Strategy: Collect ALL candidate tables, then prioritize detailed ones
        candidate_tables: list[tuple[Tag, bool]] = []  # (table, is_detailed)

        for tag in soup.find_all(["h1", "h2", "h3", "h4", "p", "b", "strong", "span"]):
            text = tag.get_text(strip=True).lower()
            if any(pattern in text for pattern in tax_patterns):
                # Skip narrative sections and footnotes
                if "narrative" not in text and "footnote" not in text and "note" not in text:
                    # Find next table
                    table = tag.find_next("table")
                    if table and self._looks_like_tax_table(table):
                        # Check if it's a detailed table
                        is_detailed = self._is_detailed_tax_table(table)
                        candidate_tables.append((table, is_detailed))

        if not candidate_tables:
            return None

        # Prioritize detailed tables
        detailed_tables = [t for t, is_det in candidate_tables if is_det]
        if detailed_tables:
            return detailed_tables[0]

        # Fall back to first candidate
        return candidate_tables[0][0]

    def _is_detailed_tax_table(self, table: Tag) -> bool:
        """Check if table has detailed component breakdown.

        Returns True if table contains federal/state/foreign AND current/deferred breakdowns.
        """
        text = table.get_text().lower()

        has_federal = "federal" in text
        has_state = "state" in text
        has_foreign = "foreign" in text or "international" in text
        has_current = "current" in text
        has_deferred = "deferred" in text

        # Detailed table must have geographic (federal/state/foreign) AND timing (current/deferred) dimensions
        has_geographic = (has_federal and has_state) or (has_federal and has_foreign)
        has_timing = has_current and has_deferred

        return has_geographic and has_timing

    def _looks_like_tax_table(self, table: Tag) -> bool:
        """Check if table looks like an income tax expense table.

        Validates table contains tax-related keywords.
        Supports both detailed tables (federal/state/foreign, current/deferred)
        and simplified summary tables (provision for income taxes with years).
        """
        text = table.get_text().lower()

        # Pattern 1: Detailed table with geographic and timing breakdowns
        location_indicators = ["federal", "state", "foreign"]
        timing_indicators = ["current", "deferred"]

        has_location = any(indicator in text for indicator in location_indicators)
        has_timing = any(indicator in text for indicator in timing_indicators)

        if has_location and has_timing:
            return True

        # Pattern 2: Simplified summary table (Apple, Alphabet style)
        # Look for "provision for income taxes" or "income tax expense" WITH years
        has_provision = "provision for income tax" in text or "income tax expense" in text
        has_years = bool(re.search(r"20[12][0-9]", text))  # Years like 2020-2029

        if has_provision and has_years:
            return True

        return False

    def _extract_tax_years(self, table: Tag) -> list[TaxYear]:
        """Extract tax year data from income tax expense table.

        Tries detailed extraction first (federal/state/foreign, current/deferred).
        Falls back to simplified extraction if detailed parsing finds no meaningful data.
        """
        # Try detailed extraction first
        detailed_results = self._extract_detailed_tax_years(table)

        # Check if detailed extraction found meaningful data (non-zero tax amounts)
        if detailed_results and any(year.total_tax_expense > 0 for year in detailed_results):
            return detailed_results

        # Fallback to simplified extraction for summary tables
        return self._extract_simplified_tax_years(table)

    def _extract_detailed_tax_years(self, table: Tag) -> list[TaxYear]:
        """Extract from detailed tax tables with federal/state/foreign, current/deferred breakdown.

        Parses table rows to build TaxYear objects with current/deferred
        federal/state/foreign tax components.

        Handles two table patterns:
        1. Section-based: "Current:", "Deferred:" as headers with components below
        2. Component-based: "Federal:", "State:", "Foreign:" with Current/Deferred rows under each
        """
        tax_years_dict: dict[int, TaxYear] = {}
        rows = table.find_all("tr")

        # First pass: find years in header row
        years: list[int] = []
        year_indices: list[int] = []  # Track column indices of years

        for row in rows:
            cells = row.find_all(["td", "th"])
            if len(cells) < 2:
                continue

            # Extract cell values
            values = [self._clean_cell(cell.get_text()) for cell in cells]

            # Check if this is a header row with years
            for i, val in enumerate(values):
                if val.isdigit() and 2000 <= int(val) <= 2030:
                    years.append(int(val))
                    year_indices.append(i)

            if years:
                # Initialize TaxYear objects
                for year in years:
                    tax_years_dict[year] = TaxYear(year=year)
                break

        if not years:
            return []

        # Second pass: parse tax data rows
        # Track context: which geographic component (federal/state/foreign) and timing (current/deferred)
        current_geographic = None  # federal, state, or foreign

        for row in rows:
            cells = row.find_all(["td", "th"])
            if len(cells) < 2:
                continue

            values = [self._clean_cell(cell.get_text()) for cell in cells]
            row_label = values[0].lower() if values else ""

            # Pattern 1: Detect geographic section headers (Apple style)
            # "Federal:", "State:", "Foreign:" indicate component sections
            if "federal:" in row_label or "federal" == row_label:
                current_geographic = "federal"
                continue
            elif "state:" in row_label or "state" == row_label:
                current_geographic = "state"
                continue
            elif "foreign:" in row_label or ("foreign" in row_label and ":" in row_label):
                current_geographic = "foreign"
                continue
            elif "international:" in row_label or ("international" in row_label and ":" in row_label):
                current_geographic = "foreign"
                continue

            # Pattern 2: Detect timing rows within geographic sections
            # "Current" or "Deferred" rows contain actual tax amounts
            timing = None
            if row_label == "current":
                timing = "current"
            elif row_label == "deferred":
                timing = "deferred"

            # Extract tax amounts if we have both geographic and timing context
            if current_geographic and timing:
                # Strategy: Find all numeric values in the row, then map to years
                # Collect all non-zero numeric values from the row (skip first column which is label)
                amounts: list[float] = []
                for val in values[1:]:  # Skip first column (label)
                    amount = self._to_number(val)
                    if amount != 0:  # Found non-zero value
                        amounts.append(amount)

                # Map amounts to years (should be same length or close)
                # Typically we expect 3 years -> 3 amounts
                for i, year in enumerate(years):
                    if i < len(amounts):
                        field_name = f"{timing}_{current_geographic}"
                        setattr(tax_years_dict[year], field_name, amounts[i])

        # Calculate totals for each year
        for year, tax_year in tax_years_dict.items():
            tax_year.total_current = (
                tax_year.current_federal + tax_year.current_state + tax_year.current_foreign
            )
            tax_year.total_deferred = (
                tax_year.deferred_federal + tax_year.deferred_state + tax_year.deferred_foreign
            )
            tax_year.total_tax_expense = tax_year.total_current + tax_year.total_deferred

        # Return list sorted by year (most recent first)
        return sorted(tax_years_dict.values(), key=lambda x: x.year, reverse=True)

    def _extract_simplified_tax_years(self, table: Tag) -> list[TaxYear]:
        """Extract from simplified tax summary tables (Apple, Alphabet style).

        These tables have "Provision for income taxes" row with total amounts per year,
        but no breakdown by federal/state/foreign or current/deferred.
        """
        tax_years_dict: dict[int, TaxYear] = {}
        rows = table.find_all("tr")

        # First pass: find years in header row
        years: list[int] = []
        year_indices: list[int] = []

        for row in rows:
            cells = row.find_all(["td", "th"])
            if len(cells) < 2:
                continue

            values = [self._clean_cell(cell.get_text()) for cell in cells]

            # Check if this is a header row with years
            for i, val in enumerate(values):
                if val.isdigit() and 2000 <= int(val) <= 2030:
                    years.append(int(val))
                    year_indices.append(i)

            if years:
                # Initialize TaxYear objects
                for year in years:
                    tax_years_dict[year] = TaxYear(year=year)
                break

        if not years:
            return []

        # Second pass: find row with "provision for income tax" or "income tax expense"
        for row in rows:
            cells = row.find_all(["td", "th"])
            if len(cells) < 2:
                continue

            values = [self._clean_cell(cell.get_text()) for cell in cells]
            row_label = values[0].lower() if values else ""

            # Look for provision row
            if "provision for income tax" in row_label or "income tax expense" in row_label:
                # Extract tax amounts - find all numeric values that look like tax amounts
                # Build list of (column_index, amount) pairs
                amounts_found: list[tuple[int, float]] = []

                for col_idx, val in enumerate(values[1:], start=1):  # Skip first column (label)
                    # Try to parse as number (handles $ signs, commas, etc.)
                    amount = self._to_number(val)
                    # Tax amounts are typically > 0 and in millions (> 100)
                    if amount > 100:  # Filter out small numbers like percentages
                        amounts_found.append((col_idx, amount))

                # Match amounts to years based on proximity
                # For each year, find the closest amount column that comes after it
                for idx, year_idx in enumerate(year_indices):
                    year = years[idx]

                    # Find first amount column that's after this year column
                    for amt_col, amt_val in amounts_found:
                        if amt_col > year_idx:
                            tax_years_dict[year].total_tax_expense = amt_val
                            # Remove this amount so it's not matched again
                            amounts_found.remove((amt_col, amt_val))
                            break

        # Return list sorted by year (most recent first)
        return sorted(tax_years_dict.values(), key=lambda x: x.year, reverse=True)

    def _apply_tax_data(
        self,
        tax_years_dict: dict[int, TaxYear],
        years: list[int],
        tax_data: dict[int, float],
        section: str,
        row_label: str,
    ) -> None:
        """Apply parsed tax data to appropriate TaxYear fields."""
        # Determine which field to update based on row label and section
        field_map = {
            ("current", "federal"): "current_federal",
            ("current", "state"): "current_state",
            ("current", "foreign"): "current_foreign",
            ("deferred", "federal"): "deferred_federal",
            ("deferred", "state"): "deferred_state",
            ("deferred", "foreign"): "deferred_foreign",
        }

        # Identify tax component
        component = None
        if "federal" in row_label:
            component = "federal"
        elif "state" in row_label:
            component = "state"
        elif "foreign" in row_label or "international" in row_label:
            component = "foreign"

        if component:
            field_name = field_map.get((section, component))
            if field_name:
                for i, year in enumerate(years):
                    if i in tax_data:
                        setattr(tax_years_dict[year], field_name, tax_data[i])

    def _parse_tax_row(self, values: list[str], row_label: str) -> dict[int, float]:
        """Parse a single row of tax data.

        Returns dict mapping column index to monetary value.
        """
        # Skip total rows and section headers
        if not row_label or "total" in row_label or ":" in row_label:
            return {}

        # Parse monetary values from columns (skip first column which is label)
        result: dict[int, float] = {}
        for i, val in enumerate(values[1:]):
            number = self._to_number(val)
            result[i] = number

        return result

    def _to_number(self, value: str) -> float:
        """Convert currency/number string to float.

        Handles:
        - $1,234,567 -> 1234567.0
        - (1,234) -> -1234.0  (parentheses = negative)
        - — or - -> 0.0
        - 1.5B -> 1500000000.0
        - 1.5M -> 1500000.0
        """
        if not value:
            return 0.0

        # Handle dashes and N/A as zero
        if value in ["—", "–", "-", "N/A", "n/a", ""]:
            return 0.0

        # Check for parentheses (negative)
        is_negative = "(" in value and ")" in value

        # Remove currency symbols, parentheses, and commas
        value = re.sub(r"[$,()]", "", value)
        value = value.strip()

        # Handle billions and millions
        multiplier = 1.0
        if value.endswith("B") or value.endswith("b"):
            multiplier = 1_000_000_000
            value = value[:-1]
        elif value.endswith("M") or value.endswith("m"):
            multiplier = 1_000_000
            value = value[:-1]

        try:
            result = float(value) * multiplier
            return -result if is_negative else result
        except ValueError:
            return 0.0

    def _clean_cell(self, value: str) -> str:
        """Clean a table cell value.

        Removes footnote markers and normalizes whitespace.
        PRESERVES parenthesized numbers (negative values in financial tables).
        """
        # Remove footnote markers like [1], [2], etc.
        # BUT preserve parenthesized numbers like (1,234) which indicate negative values
        value = re.sub(r"\[\d+\]", "", value)

        # Remove asterisks (footnote markers)
        value = re.sub(r"\*+", "", value)

        # Normalize whitespace
        value = re.sub(r"\s+", " ", value)

        return value.strip()

    def _find_effective_rate(self, soup: BeautifulSoup) -> float:
        """Find effective tax rate from rate reconciliation table.

        Searches for effective tax rate disclosure, typically in a
        "Rate Reconciliation" table or narrative text.
        """
        # Look for rate reconciliation section
        rate_patterns = [
            "effective tax rate",
            "rate reconciliation",
            "statutory rate",
        ]

        for tag in soup.find_all(["h1", "h2", "h3", "h4", "p", "b", "strong", "span"]):
            text = tag.get_text(strip=True).lower()
            if any(pattern in text for pattern in rate_patterns):
                # Try to extract percentage from nearby text
                # Look in next few siblings
                for sibling in tag.find_next_siblings(limit=10):
                    sibling_text = sibling.get_text()
                    # Look for percentage patterns like "21.5%", "21.5 %", "0.215"
                    matches = re.findall(r"(\d+\.?\d*)\s*%", sibling_text)
                    for match in matches:
                        rate = float(match)
                        # Effective tax rates typically between 0-50%
                        if 0 < rate <= 50:
                            return rate / 100.0  # Convert to decimal

                # Also check for decimal format in table
                table = tag.find_next("table")
                if table:
                    table_text = table.get_text()
                    # Look for rates in decimal format (0.XXX)
                    matches = re.findall(r"0\.(\d{1,3})", table_text)
                    for match in matches:
                        rate = float(f"0.{match}")
                        if 0 < rate <= 0.5:
                            return rate

        return 0.0
